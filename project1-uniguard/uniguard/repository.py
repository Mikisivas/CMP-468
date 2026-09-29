"""Encrypted, deduplicated backup repository.

On-disk layout (everything except config.json is encrypted):

    repo/
      config.json               salt, KDF cost, key-check value, version
      objects/ab/abcd...        zlib-compressed, AES-GCM encrypted data chunks
      snapshots/<id>.snap       encrypted JSON manifest of one backup

Files are split into fixed 1 MiB chunks. A chunk that already exists is not
stored again, so every backup after the first is incremental by construction
while each snapshot still restores on its own (no fragile backup chains).
"""

import base64
import json
import os
import secrets
import shutil
import stat
import zlib
from datetime import datetime, timezone
from pathlib import Path

from .crypto import KEY_CHECK_PLAINTEXT, SCRYPT_N, IntegrityError, KeyRing

CHUNK_SIZE = 1 << 20
REPO_VERSION = 1


class RepositoryError(Exception):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_snapshot_id(when: datetime | None = None) -> str:
    when = when or utcnow()
    return when.strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(3)


def _write_immutable(path: Path, data: bytes) -> None:
    """Write atomically, then drop write permission (simple WORM protection)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    os.chmod(path, stat.S_IRUSR | stat.S_IRGRP)


def _remove(path: Path) -> None:
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    path.unlink()


class Repository:
    def __init__(self, root: Path, keys: KeyRing):
        self.root = Path(root)
        self.keys = keys
        self.objects = self.root / "objects"
        self.snapshots = self.root / "snapshots"

    # ---------- lifecycle ----------
    @classmethod
    def init(cls, root, passphrase: str, scrypt_n: int = SCRYPT_N) -> "Repository":
        root = Path(root)
        if (root / "config.json").exists():
            raise RepositoryError(f"repository already exists at {root}")
        if len(passphrase) < 12:
            raise RepositoryError("passphrase must be at least 12 characters")
        salt = secrets.token_bytes(16)
        keys = KeyRing.from_passphrase(passphrase, salt, scrypt_n)
        (root / "objects").mkdir(parents=True, exist_ok=True)
        (root / "snapshots").mkdir(parents=True, exist_ok=True)
        cfg = {
            "version": REPO_VERSION,
            "created": utcnow().isoformat(),
            "kdf": {"name": "scrypt", "n": scrypt_n, "r": 8, "p": 1},
            "salt": base64.b64encode(salt).decode(),
            "key_check": base64.b64encode(keys.encrypt(KEY_CHECK_PLAINTEXT, b"key-check")).decode(),
            "cipher": "AES-256-GCM",
            "chunk_size": CHUNK_SIZE,
        }
        (root / "config.json").write_text(json.dumps(cfg, indent=2))
        return cls(root, keys)

    @classmethod
    def open(cls, root, passphrase: str) -> "Repository":
        root = Path(root)
        cfg_path = root / "config.json"
        if not cfg_path.exists():
            raise RepositoryError(f"no repository at {root}. Run 'init' first.")
        cfg = json.loads(cfg_path.read_text())
        keys = KeyRing.from_passphrase(passphrase, base64.b64decode(cfg["salt"]), cfg["kdf"]["n"])
        try:
            keys.decrypt(base64.b64decode(cfg["key_check"]), b"key-check")
        except IntegrityError:
            raise RepositoryError("wrong passphrase") from None
        return cls(root, keys)

    # ---------- objects ----------
    def _obj_path(self, oid: str) -> Path:
        return self.objects / oid[:2] / oid

    def has_object(self, oid: str) -> bool:
        return self._obj_path(oid).exists()

    def put_object(self, data: bytes) -> tuple[str, int]:
        """Store a chunk. Returns (object id, bytes written; 0 if deduplicated)."""
        oid = self.keys.object_id(data)
        path = self._obj_path(oid)
        if path.exists():
            return oid, 0
        blob = self.keys.encrypt(zlib.compress(data, 6), aad=oid.encode())
        _write_immutable(path, blob)
        return oid, len(blob)

    def get_object(self, oid: str) -> bytes:
        path = self._obj_path(oid)
        if not path.exists():
            raise IntegrityError(f"missing object {oid[:12]}")
        data = zlib.decompress(self.keys.decrypt(path.read_bytes(), aad=oid.encode()))
        if self.keys.object_id(data) != oid:
            raise IntegrityError(f"object {oid[:12]} content does not match its id")
        return data

    def all_object_ids(self) -> set[str]:
        return {p.name for p in self.objects.glob("*/*") if not p.name.endswith(".tmp")}

    # ---------- snapshots ----------
    def save_snapshot(self, manifest: dict) -> str:
        sid = manifest["id"]
        body = json.dumps(manifest, sort_keys=True).encode()
        _write_immutable(self.snapshots / f"{sid}.snap", self.keys.encrypt(body, aad=f"snapshot:{sid}".encode()))
        return sid

    def load_snapshot(self, sid: str) -> dict:
        path = self.snapshots / f"{sid}.snap"
        if not path.exists():
            raise RepositoryError(f"snapshot {sid} not found")
        return json.loads(self.keys.decrypt(path.read_bytes(), aad=f"snapshot:{sid}".encode()))

    def list_snapshot_ids(self) -> list[str]:
        return sorted(p.stem for p in self.snapshots.glob("*.snap"))

    def list_snapshots(self) -> list[dict]:
        """Snapshot summaries, oldest first (file lists stripped)."""
        out = []
        for sid in self.list_snapshot_ids():
            m = self.load_snapshot(sid)
            m.pop("files", None)
            out.append(m)
        return out

    def latest_snapshot(self, clean_only: bool = False) -> dict | None:
        for sid in reversed(self.list_snapshot_ids()):
            m = self.load_snapshot(sid)
            if not clean_only or m.get("clean", True):
                return m
        return None

    def delete_snapshot(self, sid: str) -> None:
        _remove(self.snapshots / f"{sid}.snap")

    # ---------- maintenance ----------
    def garbage_collect(self) -> int:
        """Delete objects no snapshot references. Returns number removed."""
        live = set()
        for sid in self.list_snapshot_ids():
            for entry in self.load_snapshot(sid)["files"].values():
                live.update(entry["chunks"])
        removed = 0
        for oid in self.all_object_ids() - live:
            _remove(self._obj_path(oid))
            removed += 1
        return removed

    def verify(self, full: bool = True) -> dict:
        """Check every snapshot and (optionally) decrypt every referenced object."""
        problems, checked = [], set()
        for sid in self.list_snapshot_ids():
            try:
                manifest = self.load_snapshot(sid)
            except IntegrityError as exc:
                problems.append(f"snapshot {sid}: {exc}")
                continue
            for path, entry in manifest["files"].items():
                for oid in entry["chunks"]:
                    if oid in checked:
                        continue
                    checked.add(oid)
                    try:
                        if full:
                            self.get_object(oid)
                        elif not self.has_object(oid):
                            raise IntegrityError("missing")
                    except (IntegrityError, zlib.error) as exc:
                        problems.append(f"{sid}:{path}: {exc}")
        return {"ok": not problems, "objects_checked": len(checked), "problems": problems}

    def size_bytes(self) -> int:
        return sum(p.stat().st_size for p in self.root.rglob("*") if p.is_file())

    def replicate_to(self, dest, max_bytes: int | None = None) -> dict:
        """Copy new encrypted objects, then snapshots, to a second location (offsite copy).

        The destination only ever sees ciphertext, so it can be an untrusted
        cloud bucket, a partner university's server or an external drive.
        max_bytes caps how much one run sends over a slow or metered link; the
        rest goes on the next run. Snapshots are copied only after all objects
        are there, so the offsite copy never holds a snapshot it cannot restore.
        """
        dest = Path(dest)
        copied, sent, complete = 0, 0, True

        def copy(src: Path) -> None:
            nonlocal copied, sent
            target = dest / src.relative_to(self.root)
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_name(target.name + ".part")
            shutil.copy2(src, tmp)
            os.replace(tmp, target)
            copied += 1
            sent += src.stat().st_size

        for src in [self.root / "config.json", *sorted(self.objects.glob("*/*"))]:
            if src.name.endswith(".tmp") or (dest / src.relative_to(self.root)).exists():
                continue
            if max_bytes is not None and sent + src.stat().st_size > max_bytes:
                complete = False
                break
            copy(src)
        if complete:
            for src in sorted(self.snapshots.glob("*.snap")):
                if not (dest / src.relative_to(self.root)).exists():
                    copy(src)
        return {"destination": str(dest), "files_copied": copied, "bytes_sent": sent, "complete": complete}
