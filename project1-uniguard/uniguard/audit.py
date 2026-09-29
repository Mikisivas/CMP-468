"""Tamper-evident event store (SQLite).

Every event row stores the SHA-256 of the previous row plus its own content.
Editing or deleting any past row breaks the chain, so an insider who alters
the log to hide a result-sheet change is detected by verify_chain().
"""

import hashlib
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

GENESIS = "0" * 64

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    data TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS metrics (
    ts TEXT NOT NULL,
    name TEXT NOT NULL,
    value REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_metrics ON metrics(name, ts);
CREATE TABLE IF NOT EXISTS state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

SEVERITIES = ["info", "warning", "critical"]


def _row_hash(prev_hash, ts, kind, severity, message, data) -> str:
    body = json.dumps([prev_hash, ts, kind, severity, message, data], separators=(",", ":"))
    return hashlib.sha256(body.encode()).hexdigest()


class AuditLog:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.executescript(SCHEMA)
        self._db.execute("PRAGMA journal_mode=WAL")  # survives abrupt power loss better
        self._db.commit()

    def record(self, kind: str, message: str, severity: str = "info", data: dict | None = None) -> dict:
        ts = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(data or {}, sort_keys=True, default=str)
        with self._lock:
            row = self._db.execute("SELECT hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
            prev = row[0] if row else GENESIS
            h = _row_hash(prev, ts, kind, severity, message, payload)
            cur = self._db.execute(
                "INSERT INTO events (ts, kind, severity, message, data, prev_hash, hash) VALUES (?,?,?,?,?,?,?)",
                (ts, kind, severity, message, payload, prev, h))
            self._db.commit()
        return {"seq": cur.lastrowid, "ts": ts, "kind": kind, "severity": severity,
                "message": message, "data": data or {}, "hash": h}

    def events(self, limit: int = 50, kind: str | None = None, min_severity: str = "info") -> list[dict]:
        allowed = SEVERITIES[SEVERITIES.index(min_severity):]
        q = f"SELECT seq, ts, kind, severity, message, data FROM events WHERE severity IN ({','.join('?' * len(allowed))})"
        args: list = list(allowed)
        if kind:
            q += " AND kind = ?"
            args.append(kind)
        q += " ORDER BY seq DESC LIMIT ?"
        args.append(limit)
        with self._lock:
            rows = self._db.execute(q, args).fetchall()
        return [{"seq": r[0], "ts": r[1], "kind": r[2], "severity": r[3], "message": r[4],
                 "data": json.loads(r[5])} for r in rows]

    def verify_chain(self) -> dict:
        prev = GENESIS
        with self._lock:
            rows = self._db.execute(
                "SELECT seq, ts, kind, severity, message, data, prev_hash, hash FROM events ORDER BY seq").fetchall()
        expected_seq = None
        for seq, ts, kind, sev, msg, data, prev_hash, h in rows:
            if expected_seq is not None and seq != expected_seq:
                return {"ok": False, "broken_at": seq, "reason": f"row(s) before seq {seq} were deleted"}
            if prev_hash != prev or _row_hash(prev, ts, kind, sev, msg, data) != h:
                return {"ok": False, "broken_at": seq, "reason": "row content or order was altered"}
            prev, expected_seq = h, seq + 1
        return {"ok": True, "events": len(rows), "head": prev}

    def metric(self, name: str, value: float) -> None:
        with self._lock:
            self._db.execute("INSERT INTO metrics VALUES (?,?,?)",
                             (datetime.now(timezone.utc).isoformat(), name, float(value)))
            self._db.commit()

    def metric_series(self, name: str, limit: int = 60) -> list[tuple[str, float]]:
        with self._lock:
            rows = self._db.execute(
                "SELECT ts, value FROM metrics WHERE name=? ORDER BY ts DESC LIMIT ?", (name, limit)).fetchall()
        return list(reversed(rows))

    def get_state(self, key: str, default=None):
        with self._lock:
            row = self._db.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_state(self, key: str, value) -> None:
        with self._lock:
            self._db.execute("INSERT OR REPLACE INTO state VALUES (?,?)", (key, json.dumps(value, default=str)))
            self._db.commit()

    def close(self):
        self._db.close()
