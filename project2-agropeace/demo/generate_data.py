"""Generate the demonstration map layers and incident history for Benue State.

Town positions are approximate and every farm, reserve, herd, incident and
phone number is SYNTHETIC. A real deployment would load surveyed farm
boundaries, gazetted grazing reserves and ACLED incident records instead.

    python demo/generate_data.py
"""

import json
import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from agropeace.geo import destination  # noqa: E402

OUT = HERE.parent / "data"

# name, lga, lat, lon (approximate)
COMMUNITIES = [
    ("Yelwata", "Guma", 7.905, 8.830), ("Daudu", "Guma", 7.815, 8.700), ("Gbajimba", "Guma", 7.955, 8.860),
    ("Abinsi", "Guma", 7.760, 8.960), ("Obagaji", "Agatu", 7.935, 7.905), ("Ochekwu", "Agatu", 7.860, 8.010),
    ("Ugba", "Logo", 7.690, 9.140), ("Anyiin", "Logo", 7.600, 9.230), ("Naka", "Gwer West", 7.585, 8.205),
    ("Makurdi North Bank", "Makurdi", 7.760, 8.540),
]
LGAS = {
    "Agatu": [7.75, 7.80, 8.10, 8.15], "Guma": [7.70, 8.60, 8.10, 9.02], "Makurdi": [7.62, 8.40, 7.85, 8.60],
    "Logo": [7.45, 9.02, 7.85, 9.35], "Gwer West": [7.45, 8.05, 7.75, 8.40],
}
GRAZING_RESERVES = [
    ("Agatu North Grazing Reserve", 8.045, 8.040, 4.0),
    ("Guma East Grazing Reserve", 8.060, 8.980, 4.5),
    ("Logo South Grazing Reserve", 7.500, 9.150, 3.5),
]
WATER_POINTS = [("Daudu Pond", 7.845, 8.760), ("Ochekwu Stream", 7.890, 8.050), ("Ugba Dam", 7.640, 9.080),
                ("Naka Borehole", 7.610, 8.160)]
# River Benue flows roughly east to west through Makurdi.
RIVER = [[9.35, 7.80], [9.05, 7.76], [8.80, 7.74], [8.54, 7.735], [8.30, 7.77], [8.05, 7.80], [7.80, 7.84]]
STOCK_ROUTES = [
    ("Route R1 (Agatu reserve to Ochekwu stream)", [[8.040, 8.045], [8.035, 7.980], [8.050, 7.900]]),
    ("Route R2 (Guma reserve to Daudu pond)", [[8.980, 8.060], [8.930, 7.990], [8.880, 7.990], [8.790, 7.880], [8.760, 7.845]]),
    ("Route R3 (Logo reserve to Ugba dam)", [[9.150, 7.500], [9.110, 7.560], [9.080, 7.640]]),
]
CROPS = ["yam", "cassava", "rice", "maize", "soybean", "sesame", "sorghum"]


def blob(lat, lon, radius_km, rng, n=12):
    ring = []
    for i in range(n):
        r = radius_km * rng.uniform(0.7, 1.15)
        la, lo = destination(lat, lon, i * 360 / n, r)
        ring.append([round(lo, 5), round(la, 5)])
    ring.append(ring[0])
    return [ring]


def feature(geom_type, coords, **props):
    return {"type": "Feature", "geometry": {"type": geom_type, "coordinates": coords}, "properties": props}


def main():
    rng = random.Random(2026)
    OUT.mkdir(exist_ok=True)
    feats = []
    for name, (s, w, n, e) in LGAS.items():
        feats.append(feature("Polygon", [[[w, s], [e, s], [e, n], [w, n], [w, s]]], kind="lga", name=name))
    for name, lga, lat, lon in COMMUNITIES:
        feats.append(feature("Point", [lon, lat], kind="community", name=name, lga=lga))
        for k in range(rng.randint(3, 5)):
            la, lo = destination(lat, lon, rng.uniform(0, 360), rng.uniform(1.2, 4.0))
            feats.append(feature("Polygon", blob(la, lo, rng.uniform(0.6, 1.4), rng), kind="farmland",
                                 name=f"{name} farm {k + 1}", lga=lga, community=name, crop=rng.choice(CROPS)))
    for name, lat, lon, r in GRAZING_RESERVES:
        feats.append(feature("Polygon", blob(lat, lon, r, rng, 16), kind="grazing_reserve", name=name))
    for name, lat, lon in WATER_POINTS:
        feats.append(feature("Point", [lon, lat], kind="water_point", name=name))
    feats.append(feature("LineString", RIVER, kind="river", name="River Benue"))
    for name, line in STOCK_ROUTES:
        feats.append(feature("LineString", line, kind="stock_route", name=name))
    (OUT / "benue_layers.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))

    # 90 days of synthetic incidents, clustered where farms meet water and routes (Guma, Agatu).
    now = datetime.now(timezone.utc)
    hotspots = [(7.86, 8.78, 0.45), (7.90, 7.97, 0.30), (7.68, 9.10, 0.15), (7.60, 8.20, 0.10)]
    types = ["crop_destruction", "crop_destruction", "cattle_rustling", "threat", "clash", "killing"]
    incidents = []
    for i in range(70):
        r = rng.random()
        acc = 0
        for lat, lon, wgt in hotspots:
            acc += wgt
            if r <= acc:
                break
        la, lo = destination(lat, lon, rng.uniform(0, 360), abs(rng.gauss(0, 4)))
        incidents.append({"id": f"H{i + 1:03d}", "lat": round(la, 5), "lon": round(lo, 5),
                          "type": rng.choice(types),
                          "ts": (now - timedelta(days=rng.uniform(1, 90))).isoformat(),
                          "source": "historical (synthetic)", "verified": True})
    (OUT / "incidents_history.json").write_text(json.dumps(incidents, indent=1))
    print(f"wrote {len(feats)} map features and {len(incidents)} historical incidents to {OUT}")


if __name__ == "__main__":
    main()
