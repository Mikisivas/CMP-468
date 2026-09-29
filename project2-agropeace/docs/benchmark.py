"""Measure risk-grid and message-handling speed.

    python docs/benchmark.py
"""

import json
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "demo"))

from agropeace.engine import Engine, load_config  # noqa: E402
from simulator import plan_paths, signed_fix  # noqa: E402

MASTER = b"b" * 32


def main():
    cfg = load_config(ROOT / "demo" / "demo_config.json")
    cfg["state_dir"] = tempfile.mkdtemp()
    now = [datetime(2026, 9, 29, 6, 0, tzinfo=timezone.utc)]
    t = time.perf_counter()
    eng = Engine(cfg, MASTER, clock=lambda: now[0])
    out = {"grid_cells": len(eng.risk.cells), "startup_incl_static_layers_s": round(time.perf_counter() - t, 2)}
    t = time.perf_counter()
    for _ in range(5):
        eng.recompute_risk()
    out["risk_recompute_s"] = round((time.perf_counter() - t) / 5, 3)

    paths = plan_paths(eng.layers)
    n = 0
    t = time.perf_counter()
    for i in range(max(len(p) for p in paths.values())):
        now[0] += timedelta(minutes=10)
        for dev, p in paths.items():
            body, sig = signed_fix(MASTER, dev, *p[min(i, len(p) - 1)], now[0].timestamp())
            eng.ingest_position(body, sig)
            n += 1
    el = time.perf_counter() - t
    out["gps_messages"] = n
    out["ms_per_message_incl_verify_geofence"] = round(el / n * 1000, 2)

    t = time.perf_counter()
    for i in range(200):
        eng.report_limiter.allow = lambda k, now=None: True
        eng.submit_report(rtype="sighting", channel="ussd", phone=f"+23480{i:08d}", community="Ugba")
    out["ms_per_report_incl_rescore"] = round((time.perf_counter() - t) / 200 * 1000, 2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
