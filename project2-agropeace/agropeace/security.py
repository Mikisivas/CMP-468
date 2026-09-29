"""Security controls.

In farmer/herder conflict, information itself can kill: a forged "attack"
report can trigger a reprisal, and a leaked informant's phone number can get
them targeted. These controls exist for that reason.

  DeviceAuth     HMAC-SHA256 signatures on tracker messages, with a timestamp
                 window and nonce cache to stop forgery and replay
  IdentityVault  AES-256-GCM encryption of reporter phone numbers; public
                 records carry only a keyed pseudonym
  RateLimiter    stops one number flooding the system with reports
  Roles          role-based access: what each user may see and do
  AuditChain     hash-chained, append-only log of every action
"""

import hashlib
import hmac
import json
import os
import sqlite3
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def sign_message(key: bytes, body: dict) -> str:
    return hmac.new(key, canonical(body), hashlib.sha256).hexdigest()


class AuthError(Exception):
    pass


class DeviceAuth:
    """Verifies messages from GPS collars and field phones."""

    def __init__(self, device_keys: dict[str, bytes], window_s: int = 120):
        self.keys = device_keys
        self.window_s = window_s
        self._seen: dict[str, float] = {}
        self._lock = threading.Lock()

    def verify(self, body: dict, signature: str, now: float | None = None) -> None:
        now = time.time() if now is None else now
        dev = body.get("device_id")
        key = self.keys.get(dev)
        if key is None:
            raise AuthError(f"unknown device {dev!r}")
        if not hmac.compare_digest(sign_message(key, body), signature or ""):
            raise AuthError(f"bad signature from {dev}")
        ts = float(body.get("ts", 0))
        if abs(now - ts) > self.window_s:
            raise AuthError(f"stale or future timestamp from {dev} ({now - ts:+.0f}s)")
        nonce = f"{dev}:{body.get('nonce')}"
        with self._lock:
            for k in [k for k, t in self._seen.items() if now - t > 2 * self.window_s]:
                del self._seen[k]
            if nonce in self._seen:
                raise AuthError(f"replayed message from {dev}")
            self._seen[nonce] = now


class IdentityVault:
    """Protects informants. Phone numbers are encrypted at rest and only the
    protection officer role can decrypt them. Everyone else sees a pseudonym."""

    def __init__(self, master_key: bytes):
        self._aes = AESGCM(HKDF(hashes.SHA256(), 32, None, b"agropeace-pii").derive(master_key))
        self._pkey = HKDF(hashes.SHA256(), 32, None, b"agropeace-pseudonym").derive(master_key)

    def pseudonym(self, phone: str) -> str:
        return "R-" + hmac.new(self._pkey, phone.encode(), hashlib.sha256).hexdigest()[:10]

    def seal(self, phone: str) -> str:
        nonce = os.urandom(12)
        return (nonce + self._aes.encrypt(nonce, phone.encode(), b"phone")).hex()

    def unseal(self, token: str) -> str:
        raw = bytes.fromhex(token)
        try:
            return self._aes.decrypt(raw[:12], raw[12:], b"phone").decode()
        except InvalidTag:
            raise AuthError("sealed identity was tampered with") from None


class RateLimiter:
    def __init__(self, limit: int, per_s: int):
        self.limit, self.per_s = limit, per_s
        self._hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        q = self._hits[key]
        while q and now - q[0] > self.per_s:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True


# role -> permissions
ROLES = {
    "coordinator": {"view_precise", "view_all_lgas", "manage_cases", "view_unverified", "view_audit"},
    "mediator": {"view_precise", "manage_cases", "view_unverified"},
    "protection_officer": {"view_precise", "view_all_lgas", "reveal_identity", "view_audit"},
    "public": set(),
}


def can(user: dict | None, perm: str) -> bool:
    return bool(user) and perm in ROLES.get(user.get("role", "public"), set())


def sees_lga(user: dict | None, lga: str) -> bool:
    if can(user, "view_all_lgas"):
        return True
    return bool(user) and lga in user.get("lgas", [])


GENESIS = "0" * 64


class AuditChain:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, "
                         "actor TEXT, action TEXT, detail TEXT, prev TEXT, hash TEXT)")
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.commit()
        self._lock = threading.Lock()

    @staticmethod
    def _h(prev, ts, actor, action, detail):
        return hashlib.sha256(canonical([prev, ts, actor, action, detail])).hexdigest()

    def record(self, actor: str, action: str, detail: dict | None = None) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        d = json.dumps(detail or {}, sort_keys=True, default=str)
        with self._lock:
            row = self._db.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
            prev = row[0] if row else GENESIS
            self._db.execute("INSERT INTO audit (ts, actor, action, detail, prev, hash) VALUES (?,?,?,?,?,?)",
                             (ts, actor, action, d, prev, self._h(prev, ts, actor, action, d)))
            self._db.commit()

    def verify(self) -> dict:
        prev, expect = GENESIS, None
        with self._lock:
            rows = self._db.execute("SELECT seq, ts, actor, action, detail, prev, hash FROM audit ORDER BY seq").fetchall()
        for seq, ts, actor, action, d, p, h in rows:
            if (expect is not None and seq != expect) or p != prev or self._h(p, ts, actor, action, d) != h:
                return {"ok": False, "broken_at": seq}
            prev, expect = h, seq + 1
        return {"ok": True, "entries": len(rows)}

    def recent(self, n=30) -> list[dict]:
        with self._lock:
            rows = self._db.execute("SELECT seq, ts, actor, action, detail FROM audit ORDER BY seq DESC LIMIT ?", (n,)).fetchall()
        return [{"seq": r[0], "ts": r[1], "actor": r[2], "action": r[3], "detail": json.loads(r[4])} for r in rows]
