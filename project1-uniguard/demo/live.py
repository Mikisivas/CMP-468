"""One-command live demo: sample data, encrypted repository, Student Portal and dashboard.

    python demo/live.py            # keep existing demo data
    python demo/live.py --fresh    # wipe demo/sandbox and start clean

Then, in a second terminal, stage incidents:
    python demo/simulate_incident.py power-off | power-on | battery-low
    python demo/simulate_incident.py portal-down | portal-up
    python demo/simulate_incident.py tamper
    python demo/simulate_incident.py ransomware

Uses demo-only secrets. Never reuse them for real data.
"""

import os
import shutil
import sys
import threading
import time
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

os.environ.setdefault("UNIGUARD_PASSPHRASE", "demo-passphrase-CMP468-2026")
os.environ.setdefault("UNIGUARD_DASHBOARD_PASSWORD", "cmp468")

import fake_portal  # noqa: E402
import seed_data  # noqa: E402
from uniguard.config import load_config  # noqa: E402
from uniguard.dashboard import serve  # noqa: E402
from uniguard.engine import UniGuard  # noqa: E402
from uniguard.repository import Repository  # noqa: E402


def main():
    sandbox = HERE / "sandbox"
    if "--fresh" in sys.argv and sandbox.exists():
        shutil.rmtree(sandbox, onerror=lambda f, p, e: (os.chmod(p, 0o700), f(p)))
        print("Old demo data removed.")
    if not (sandbox / "university_data" / seed_data.MARKER).exists():
        seed_data.main()
    cfg = load_config(HERE / "demo_config.json")
    if not (Path(cfg["repository"]) / "config.json").exists():
        Repository.init(cfg["repository"], os.environ["UNIGUARD_PASSPHRASE"])
        print("Encrypted backup repository created.")

    try:
        portal = fake_portal.make_server()
        threading.Thread(target=portal.serve_forever, daemon=True).start()
        print("Student Portal running on http://127.0.0.1:8099")
    except OSError:
        print("Port 8099 is busy, so the stand-in Student Portal was not started.")

    host, port = cfg["dashboard"]["host"], cfg["dashboard"]["port"]
    url = f"http://{host}:{port}"
    print(f"\nOpen {url}  and log in with password: {os.environ['UNIGUARD_DASHBOARD_PASSWORD']}")
    print("Press Ctrl+C here to stop.\n")
    threading.Thread(target=lambda: (time.sleep(2), webbrowser.open(url)), daemon=True).start()
    eng = UniGuard(cfg, os.environ["UNIGUARD_PASSPHRASE"])
    try:
        serve(eng, host, port, os.environ["UNIGUARD_DASHBOARD_PASSWORD"])
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
