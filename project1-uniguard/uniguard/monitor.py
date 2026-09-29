"""Monitoring: server health, campus services, power supply and file integrity."""

import math
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .backup import DEFAULT_EXCLUDES, iter_files
from .crypto import sha256_file

try:
    import psutil
except ImportError:  # the rest of UniGuard still works without it
    psutil = None


@dataclass
class Finding:
    kind: str
    severity: str
    message: str
    data: dict = field(default_factory=dict)


# ---------------------------------------------------------------- server health

def check_host(disk_paths, cpu_warn=90, mem_warn=90, disk_warn=85) -> tuple[dict, list[Finding]]:
    metrics, findings = {}, []
    if psutil:
        metrics["cpu_percent"] = psutil.cpu_percent(interval=0.2)
        metrics["mem_percent"] = psutil.virtual_memory().percent
    for p in disk_paths:
        usage = shutil.disk_usage(p)
        pct = round(usage.used / usage.total * 100, 1)
        metrics[f"disk_percent:{p}"] = pct
        if pct >= disk_warn:
            findings.append(Finding("disk", "critical" if pct >= 95 else "warning",
                                    f"Disk {p} is {pct}% full. Backups will fail when it fills.",
                                    {"path": p, "percent": pct}))
    if metrics.get("cpu_percent", 0) >= cpu_warn:
        findings.append(Finding("cpu", "warning", f"CPU at {metrics['cpu_percent']}%"))
    if metrics.get("mem_percent", 0) >= mem_warn:
        findings.append(Finding("memory", "warning", f"Memory at {metrics['mem_percent']}%"))
    return metrics, findings


# ---------------------------------------------------------------- services

def check_service(svc: dict, timeout: float = 5.0) -> dict:
    """svc = {"name": "Student Portal", "type": "http"|"tcp", "target": url or host:port}."""
    started = time.monotonic()
    result = {"name": svc["name"], "type": svc["type"], "target": svc["target"], "up": False, "detail": ""}
    try:
        if svc["type"] == "http":
            req = urllib.request.Request(svc["target"], headers={"User-Agent": "UniGuard/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result["up"] = resp.status < 500
                result["detail"] = f"HTTP {resp.status}"
        elif svc["type"] == "tcp":
            host, port = svc["target"].rsplit(":", 1)
            with socket.create_connection((host, int(port)), timeout=timeout):
                result["up"] = True
                result["detail"] = "port open"
        else:
            result["detail"] = f"unknown check type {svc['type']}"
    except urllib.error.HTTPError as exc:
        result["up"] = exc.code < 500
        result["detail"] = f"HTTP {exc.code}"
    except Exception as exc:
        result["detail"] = type(exc).__name__ + (f": {exc.reason}" if hasattr(exc, "reason") else "")
    result["latency_ms"] = round((time.monotonic() - started) * 1000, 1)
    return result


# ---------------------------------------------------------------- power supply

def read_power_status(cfg: dict) -> dict:
    """Return {"on_mains": bool|None, "battery_percent": float|None, "source": str}.

    Nigerian campuses switch between grid, generator and inverter many times a
    day. UniGuard needs to know when it is running on battery so it can take an
    emergency backup before the UPS dies.

    Supported sources:
      psutil : laptop / small server battery
      nut    : Network UPS Tools (`upsc`), common with APC and Mercury UPS units
      file   : a status file written by any script (used in the demo)
    """
    mode = cfg.get("source", "psutil")
    try:
        if mode == "file":
            text = Path(cfg["status_file"]).read_text().strip().split()
            return {"on_mains": text[0].upper() in ("MAINS", "OL", "GEN"),
                    "battery_percent": float(text[1]) if len(text) > 1 else None, "source": "file"}
        if mode == "nut":
            out = subprocess.run(["upsc", cfg.get("ups", "ups@localhost")], capture_output=True,
                                 text=True, timeout=5).stdout
            vals = dict(line.split(": ", 1) for line in out.splitlines() if ": " in line)
            status = vals.get("ups.status", "")
            charge = vals.get("battery.charge")
            return {"on_mains": "OL" in status, "battery_percent": float(charge) if charge else None,
                    "source": "nut"}
        if mode == "psutil" and psutil and psutil.sensors_battery():
            b = psutil.sensors_battery()
            return {"on_mains": bool(b.power_plugged), "battery_percent": b.percent, "source": "psutil"}
    except Exception:
        pass
    return {"on_mains": None, "battery_percent": None, "source": "unavailable"}


# ---------------------------------------------------------------- file integrity

def shannon_entropy(data: bytes) -> float:
    """Bits per byte (0 to 8). Encrypted or compressed data is close to 8."""
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return -sum(c / n * math.log2(c / n) for c in counts.values())


RANSOM_EXTENSIONS = {".locked", ".encrypted", ".enc", ".crypt", ".crypted", ".lockbit", ".ryk",
                     ".wncry", ".phobos", ".djvu", ".akira", ".zzz"}
RANSOM_NOTE_HINTS = ("readme", "decrypt", "restore", "recover", "how_to", "ransom", "your_files")
# File types that are already compressed; high entropy there is normal.
NATURALLY_HIGH_ENTROPY = {".zip", ".gz", ".7z", ".rar", ".jpg", ".jpeg", ".png", ".mp4", ".mp3",
                          ".pdf", ".docx", ".xlsx", ".pptx"}


def _sample(path: Path, size: int = 65536) -> bytes:
    try:
        with open(path, "rb") as f:
            return f.read(size)
    except OSError:
        return b""


class IntegrityMonitor:
    """Compares the live file tree against the last clean backup.

    Two jobs:
      1. Ransomware / mass-destruction detection (many files changed at once,
         high entropy, ransom extensions, ransom notes).
      2. Protected-path watch: result sheets and student records may only
         change inside approved windows (for example, the Senate-approved
         result upload period). Any other change is flagged as possible
         grade tampering.
    """

    def __init__(self, source, excludes=None, protected=None, thresholds=None):
        self.source = Path(source).resolve()
        self.excludes = DEFAULT_EXCLUDES + list(excludes or [])
        self.protected = protected or []
        t = thresholds or {}
        self.mass_change_ratio = t.get("mass_change_ratio", 0.2)
        self.mass_change_min_files = t.get("mass_change_min_files", 5)
        self.entropy_threshold = t.get("entropy_threshold", 7.2)
        self.baseline: dict[str, dict] = {}
        self.baseline_id: str | None = None

    def set_baseline(self, manifest: dict) -> None:
        self.baseline = manifest["files"]
        self.baseline_id = manifest["id"]

    def scan(self) -> dict:
        live = {rel: full for rel, full in iter_files(self.source, self.excludes)}
        added, modified = [], []
        for rel, full in live.items():
            old = self.baseline.get(rel)
            if old is None:
                added.append(rel)
                continue
            st = full.stat()
            if st.st_size == old["size"] and st.st_mtime == old["mtime"]:
                continue
            if sha256_file(full) != old["sha256"]:
                modified.append(rel)
        deleted = [rel for rel in self.baseline if rel not in live]
        return {"live": live, "added": added, "modified": modified, "deleted": deleted}

    def analyse(self, scan: dict, now: datetime | None = None) -> list[Finding]:
        findings: list[Finding] = []
        live = scan["live"]
        touched = scan["added"] + scan["modified"]
        total = max(len(self.baseline), 1)

        # --- ransomware indicators
        ext_hits = [p for p in scan["added"] if Path(p).suffix.lower() in RANSOM_EXTENSIONS]
        notes = [p for p in scan["added"]
                 if Path(p).suffix.lower() in (".txt", ".html", ".hta")
                 and any(h in Path(p).name.lower() for h in RANSOM_NOTE_HINTS)]
        high_entropy = []
        for rel in touched:
            if Path(rel).suffix.lower() in NATURALLY_HIGH_ENTROPY:
                continue
            e = shannon_entropy(_sample(live[rel]))
            if e >= self.entropy_threshold:
                high_entropy.append(rel)
        destroyed = len(scan["modified"]) + len(scan["deleted"])
        ratio = destroyed / total

        score = 0
        reasons = []
        if destroyed >= self.mass_change_min_files and ratio >= self.mass_change_ratio:
            score += 40
            reasons.append(f"{destroyed} of {total} files ({ratio:.0%}) modified or deleted")
        if len(high_entropy) >= 3:
            score += 30
            reasons.append(f"{len(high_entropy)} changed files look encrypted (entropy >= {self.entropy_threshold})")
        if ext_hits:
            score += 20
            reasons.append(f"{len(ext_hits)} files with ransomware extensions, e.g. {ext_hits[0]}")
        if notes:
            score += 20
            reasons.append(f"possible ransom note: {notes[0]}")

        if score >= 50:
            findings.append(Finding("ransomware", "critical",
                                    "Ransomware or mass destruction detected: " + "; ".join(reasons),
                                    {"score": score, "reasons": reasons, "modified": scan["modified"][:50],
                                     "deleted": scan["deleted"][:50], "suspicious_added": (ext_hits + notes)[:50]}))
        elif score >= 20:
            findings.append(Finding("integrity", "warning",
                                    "Unusual file activity: " + "; ".join(reasons), {"score": score}))

        # --- protected paths (results, transcripts, admissions lists)
        now = now or datetime.now()
        for rule in self.protected:
            hits = [p for p in scan["modified"] + scan["deleted"] + scan["added"]
                    if p == rule["path"] or p.startswith(rule["path"].rstrip("/") + "/")]
            if not hits or _in_window(now, rule.get("allowed_windows", [])):
                continue
            findings.append(Finding(
                "tamper", "critical",
                f"{len(hits)} protected file(s) under '{rule['path']}' ({rule.get('label', 'records')}) "
                f"changed outside an approved window: {', '.join(hits[:3])}",
                {"rule": rule["path"], "files": hits[:50]}))
        return findings


def _in_window(now: datetime, windows: list[dict]) -> bool:
    """windows: [{"start": "2026-10-01T08:00", "end": "2026-10-14T18:00"}]"""
    for w in windows:
        if datetime.fromisoformat(w["start"]) <= now <= datetime.fromisoformat(w["end"]):
            return True
    return False
