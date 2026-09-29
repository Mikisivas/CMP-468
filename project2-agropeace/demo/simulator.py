"""Simulated GPS collars. Each collar signs its messages with its own key,
exactly as a real device would.

Scenario:
  H1  Guma: treks toward a Yelwata yam farm (early warning, then incursion)
  H2  Guma: grazes inside the Guma East Grazing Reserve (no alerts)
  H3  Agatu: follows stock route R1 to water; farms that have crept onto the
      route trigger an early warning, a common real-world problem
  H4  Logo: drifts toward farms near Ugba (approach warning)

    python demo/simulator.py            # posts to the running server
"""

import json
import os
import secrets
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from agropeace.engine import device_key, load_config, master_key_from_env  # noqa: E402
from agropeace.geo import bearing_deg, destination, haversine_km  # noqa: E402
from agropeace.layers import MapLayers  # noqa: E402
from agropeace.security import sign_message  # noqa: E402


def line_path(a, b, step_km):
    """Points from a to b (lat, lon) every step_km."""
    d = haversine_km(*a, *b)
    n = max(1, int(d / step_km))
    brg = bearing_deg(*a, *b)
    return [destination(*a, brg, d * i / n) for i in range(n + 1)]


def plan_paths(layers: MapLayers, step_km: float = 0.6) -> dict[str, list]:
    def farm_near(name):
        c = layers.community_by_name(name)
        lon, lat = c["geometry"]["coordinates"]
        return min((f for f in layers.farms if f["properties"]["community"] == name),
                   key=lambda f: haversine_km(lat, lon, *f["_centroid"]))

    # H1: approach a Yelwata farm from the north on a line that crosses no other farm
    tfarm = farm_near("Yelwata")
    target = tfarm["_centroid"]
    h1 = None
    for b in sorted(range(0, 360, 10), key=lambda b: min(abs(b - 15), 360 - abs(b - 15))):
        cand = line_path(destination(*target, b, 7.0), target, step_km)
        hits = [layers.farm_at(*p) for p in cand]
        clean = all(f is None or f is tfarm for f in hits)
        if clean and layers.nearest_farm(*cand[0])[1] > 1.5:
            h1 = cand + [target] * 4
            break
    h1 = h1 or line_path(destination(*target, 15, 7.0), target, step_km) + [target] * 4

    # H2: slow loop inside the Guma East reserve
    rc = next(r for r in layers.reserves if "Guma" in r["properties"]["name"])["_centroid"]
    h2 = [destination(*rc, a, 1.0) for a in range(0, 360, 20)] * 2

    # H3: along stock route R1 (stays on the corridor)
    r1 = next(r for r in layers.routes if r["properties"]["name"].startswith("Route R1"))["geometry"]["coordinates"]
    h3 = []
    for i in range(len(r1) - 1):
        h3 += line_path((r1[i][1], r1[i][0]), (r1[i + 1][1], r1[i + 1][0]), step_km)

    # H4: from the Logo reserve toward farms near Ugba, stopping about 300 m short
    tgt4 = farm_near("Ugba")
    lr = next(r for r in layers.reserves if "Logo" in r["properties"]["name"])["_centroid"]
    from agropeace.geo import dist_point_polygon_km
    h4 = [p for p in line_path(lr, tgt4["_centroid"], step_km * 0.7)
          if dist_point_polygon_km(*p, tgt4["geometry"]["coordinates"]) > 0.3]
    h4 += [h4[-1]] * 6
    return {"COLLAR-01": h1, "COLLAR-02": h2, "COLLAR-03": h3, "COLLAR-04": h4}


def signed_fix(master: bytes, device_id: str, lat: float, lon: float, ts: float) -> tuple[dict, str]:
    body = {"device_id": device_id, "lat": round(lat, 6), "lon": round(lon, 6), "ts": ts,
            "nonce": secrets.token_hex(8)}
    return body, sign_message(device_key(master, device_id), body)


def post(url, body, sig):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "X-Signature": sig})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main():
    cfg = load_config(HERE / "demo_config.json")
    master = master_key_from_env(cfg)
    layers = MapLayers.load(cfg["layers"])
    paths = plan_paths(layers)
    url = f"http://{cfg['dashboard']['host']}:{cfg['dashboard']['port']}/api/tracker"
    interval = float(os.environ.get("SIM_INTERVAL", "2"))
    steps = max(len(p) for p in paths.values())
    print(f"Simulating {len(paths)} collars, {steps} fixes each, every {interval}s -> {url}")
    for i in range(steps):
        for dev, path in paths.items():
            lat, lon = path[min(i, len(path) - 1)]
            body, sig = signed_fix(master, dev, lat, lon, time.time())
            code, text = post(url, body, sig)
            if code != 200 or '"events": []' not in text.replace('"events":[]', '"events": []'):
                print(f"  {dev} step {i}: {code} {text.strip()}")
        time.sleep(interval)
    print("done")


if __name__ == "__main__":
    main()
