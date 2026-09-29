"""Backup, retention and restore engines."""

import fnmatch
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from .crypto import sha256_file
from .repository import CHUNK_SIZE, Repository, new_snapshot_id, utcnow

DEFAULT_EXCLUDES = ["*.tmp", "~$*", ".DS_Store", "Thumbs.db", "__pycache__/*"]


def _excluded(rel: str, patterns: list[str]) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(name, p) for p in patterns)


def iter_files(source: Path, excludes: list[str]):
    for dirpath, dirnames, filenames in os.walk(source):
        dirnames.sort()
        for fn in sorted(filenames):
            full = Path(dirpath) / fn
            rel = full.relative_to(source).as_posix()
            if full.is_symlink() or _excluded(rel, excludes):
                continue
            yield rel, full


def create_backup(repo: Repository, source, tag: str = "scheduled", excludes=None,
                  clean: bool = True, reason: str = "") -> dict:
    """Snapshot `source` into `repo`.

    Unchanged files (same size and mtime as in the previous snapshot) reuse the
    previous chunk list without being read again, which keeps nightly backups
    of large result archives fast on low-end hardware.
    """
    source = Path(source).resolve()
    excludes = DEFAULT_EXCLUDES + list(excludes or [])
    started = time.monotonic()
    parent = repo.latest_snapshot()
    parent_files = parent["files"] if parent and parent.get("source") == str(source) else {}

    files, stats = {}, {"files": 0, "bytes_scanned": 0, "bytes_stored": 0,
                        "files_new": 0, "files_changed": 0, "files_unchanged": 0}
    for rel, full in iter_files(source, excludes):
        st = full.stat()
        prev = parent_files.get(rel)
        stats["files"] += 1
        stats["bytes_scanned"] += st.st_size
        if prev and prev["size"] == st.st_size and prev["mtime"] == st.st_mtime:
            files[rel] = prev
            stats["files_unchanged"] += 1
            continue
        chunks = []
        with open(full, "rb") as f:
            while True:
                data = f.read(CHUNK_SIZE)
                if not data and chunks:
                    break
                oid, written = repo.put_object(data)
                chunks.append(oid)
                stats["bytes_stored"] += written
                if not data:
                    break
        files[rel] = {"chunks": chunks, "size": st.st_size, "mtime": st.st_mtime,
                      "mode": st.st_mode & 0o777, "sha256": sha256_file(full)}
        stats["files_changed" if prev else "files_new"] += 1

    removed = sorted(set(parent_files) - set(files))
    stats["files_deleted"] = len(removed)
    stats["duration_s"] = round(time.monotonic() - started, 3)
    manifest = {
        "id": new_snapshot_id(),
        "created": utcnow().isoformat(),
        "source": str(source),
        "host": os.uname().nodename if hasattr(os, "uname") else "unknown",
        "tag": tag,
        "clean": clean,
        "reason": reason,
        "parent": parent["id"] if parent else None,
        "stats": stats,
        "files": files,
    }
    repo.save_snapshot(manifest)
    manifest = dict(manifest)
    manifest.pop("files")
    return manifest


def apply_retention(repo: Repository, keep_last: int = 7, keep_daily: int = 14,
                    keep_weekly: int = 8, keep_monthly: int = 12, now: datetime | None = None) -> dict:
    """Grandfather-father-son retention. Snapshots tagged 'pinned' are never deleted.

    The newest snapshot marked clean is also always kept, so a long ransomware
    dwell time cannot age out the last good copy.
    """
    snaps = repo.list_snapshots()
    keep: set[str] = set()
    ordered = sorted(snaps, key=lambda s: s["created"], reverse=True)
    keep.update(s["id"] for s in ordered[:keep_last])
    for s in ordered:
        if s.get("tag") == "pinned":
            keep.add(s["id"])
    last_clean = next((s for s in ordered if s.get("clean", True)), None)
    if last_clean:
        keep.add(last_clean["id"])

    def bucket(fmt, limit):
        seen = []
        for s in ordered:
            key = datetime.fromisoformat(s["created"]).strftime(fmt)
            if key not in seen:
                seen.append(key)
                if len(seen) > limit:
                    break
                keep.add(s["id"])

    bucket("%Y-%m-%d", keep_daily)
    bucket("%G-W%V", keep_weekly)
    bucket("%Y-%m", keep_monthly)

    deleted = [s["id"] for s in snaps if s["id"] not in keep]
    for sid in deleted:
        repo.delete_snapshot(sid)
    gc = repo.garbage_collect() if deleted else 0
    return {"kept": len(keep & {s["id"] for s in snaps}), "deleted": deleted, "objects_removed": gc}


def restore_snapshot(repo: Repository, snapshot_id: str, target, paths=None,
                     overwrite: bool = True) -> dict:
    """Restore a snapshot (or selected paths) and verify each file's SHA-256."""
    started = time.monotonic()
    manifest = repo.load_snapshot(snapshot_id)
    target = Path(target).resolve()
    wanted = manifest["files"]
    if paths:
        wanted = {p: e for p, e in wanted.items()
                  if any(p == q or p.startswith(q.rstrip("/") + "/") for q in paths)}
    restored, skipped, failed = 0, 0, []
    for rel, entry in wanted.items():
        dest = (target / rel).resolve()
        if target not in dest.parents:
            failed.append(f"{rel}: path escapes restore target")
            continue
        if dest.exists() and not overwrite:
            skipped += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".uniguard-restore")
        try:
            with open(tmp, "wb") as f:
                for oid in entry["chunks"]:
                    f.write(repo.get_object(oid))
            if sha256_file(tmp) != entry["sha256"]:
                raise ValueError("checksum mismatch after restore")
            os.chmod(tmp, entry["mode"])
            os.replace(tmp, dest)
            os.utime(dest, (entry["mtime"], entry["mtime"]))
            restored += 1
        except Exception as exc:  # keep restoring the rest, report every failure
            tmp.unlink(missing_ok=True)
            failed.append(f"{rel}: {exc}")
    return {"snapshot": snapshot_id, "target": str(target), "restored": restored,
            "skipped": skipped, "failed": failed,
            "duration_s": round(time.monotonic() - started, 3)}


def diff_against_snapshot(repo: Repository, snapshot_id: str, source, excludes=None) -> dict:
    """Compare live files with a snapshot: what changed since the last good backup?"""
    manifest = repo.load_snapshot(snapshot_id)
    source = Path(source).resolve()
    live = {rel: full for rel, full in iter_files(source, DEFAULT_EXCLUDES + list(excludes or []))}
    old = manifest["files"]
    added = sorted(set(live) - set(old))
    deleted = sorted(set(old) - set(live))
    modified = sorted(rel for rel in set(live) & set(old) if sha256_file(live[rel]) != old[rel]["sha256"])
    return {"added": added, "deleted": deleted, "modified": modified}


def snapshot_age_hours(snapshot: dict | None) -> float | None:
    if not snapshot:
        return None
    created = datetime.fromisoformat(snapshot["created"])
    return (datetime.now(timezone.utc) - created).total_seconds() / 3600
