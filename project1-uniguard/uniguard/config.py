"""Configuration loading. Paths in the config file are relative to the file itself."""

import json
import os
from pathlib import Path

DEFAULTS = {
    "institution": "University",
    "excludes": [],
    "intervals": {"monitor_s": 30, "backup_s": 3600, "peak_backup_s": 900},
    "peak_periods": [],
    "retention": {"keep_last": 24, "keep_daily": 14, "keep_weekly": 8, "keep_monthly": 12},
    "offsite": None,
    "services": [],
    "power": {"source": "psutil", "emergency_backup_below_percent": 60, "critical_below_percent": 25},
    "protected_paths": [],
    "integrity": {},
    "thresholds": {"cpu": 90, "memory": 90, "disk": 85},
    "auto_recover": True,
    "alerts": [{"type": "console", "min_severity": "info"}],
    "alert_cooldown_s": 900,
    "passphrase_env": "UNIGUARD_PASSPHRASE",
    "dashboard": {"host": "127.0.0.1", "port": 8080, "password_env": "UNIGUARD_DASHBOARD_PASSWORD"},
}

PATH_KEYS = ["source", "repository", "state_dir", "quarantine_dir"]


def load_config(path) -> dict:
    path = Path(path).resolve()
    raw = json.loads(path.read_text(encoding="utf-8"))
    cfg = {**DEFAULTS, **raw}
    for k in ("intervals", "retention", "power", "thresholds", "dashboard"):
        cfg[k] = {**DEFAULTS[k], **raw.get(k, {})}
    base = path.parent

    def resolve(p):
        return str((base / p).resolve()) if p else p

    for k in PATH_KEYS:
        if k in cfg:
            cfg[k] = resolve(cfg[k])
    cfg.setdefault("state_dir", str(Path(cfg["repository"]).parent / "state"))
    cfg.setdefault("quarantine_dir", str(Path(cfg["state_dir"]) / "quarantine"))
    if cfg.get("offsite"):
        cfg["offsite"] = {**cfg["offsite"], "path": resolve(cfg["offsite"]["path"])}
    if cfg["power"].get("status_file"):
        cfg["power"]["status_file"] = resolve(cfg["power"]["status_file"])
    for a in cfg["alerts"]:
        if a.get("path"):
            a["path"] = resolve(a["path"])
        # secrets never live in the config file; they are read from the environment
        for key, val in list(a.items()):
            if isinstance(val, str) and val.startswith("env:"):
                a[key] = os.environ.get(val[4:], "")
    cfg["config_path"] = str(path)
    return cfg


def get_passphrase(cfg: dict) -> str:
    value = os.environ.get(cfg["passphrase_env"])
    if not value:
        raise SystemExit(f"Set the backup passphrase in the {cfg['passphrase_env']} environment variable.")
    return value
