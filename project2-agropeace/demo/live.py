"""One-command live demo: map data and the AgroPeace dashboard.

    python demo/live.py            # keep existing demo state
    python demo/live.py --fresh    # clear cases, reports and the audit log first

Then, in a second terminal, start the GPS collars:
    python demo/simulator.py

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

os.environ.setdefault("AGROPEACE_MASTER_KEY", "demo-master-key-CMP468-agropeace")
os.environ.setdefault("AGROPEACE_USSD_TOKEN", "ussd-demo-token-468")

import generate_data  # noqa: E402
from agropeace.engine import Engine, load_config, master_key_from_env  # noqa: E402
from agropeace.server import serve  # noqa: E402


def main():
    if "--fresh" in sys.argv and (HERE / "sandbox").exists():
        shutil.rmtree(HERE / "sandbox")
        print("Old demo state removed.")
    if not (HERE.parent / "data" / "benue_layers.geojson").exists():
        generate_data.main()
    cfg = load_config(HERE / "demo_config.json")
    host, port = cfg["dashboard"]["host"], cfg["dashboard"]["port"]
    url = f"http://{host}:{port}"
    print(f"\nOpen {url}")
    print("Staff logins:  coordinator / peace-coord-2026   guma_mediator / guma-mediator-2026   "
          "protection / protect-2026")
    print("Start the collars in a second terminal:  python demo/simulator.py")
    print("Press Ctrl+C here to stop.\n")
    threading.Thread(target=lambda: (time.sleep(2), webbrowser.open(url)), daemon=True).start()
    try:
        serve(Engine(cfg, master_key_from_env(cfg)), host, port)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
