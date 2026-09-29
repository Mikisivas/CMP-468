"""Conflict risk model.

Each grid cell (default 0.025 deg, about 2.8 km) gets a score from 0 to 1 built
from five explainable factors:

  H  incident history    Gaussian kernel density of past incidents,
                         weighted by severity and decayed with age
  HP herd x farm         live and forecast herd pressure, multiplied by crop
                         exposure: cattle next to crops in the field is the
                         single strongest trigger of clashes
  F  crop exposure       farmland in or near the cell, scaled by crop season
  W  water stress        closeness to water in the dry season, when herds and
                         farmers compete for the same rivers and ponds
  R  community reports   recent reports (threats, sightings), weighted by trust

risk = 0.30 H + 0.30 HP + 0.15 F + 0.10 W + 0.15 R

The weights are expert-set starting values. A real deployment would calibrate
them against ACLED event data for the state.
"""

import math
from datetime import datetime, timezone

from .geo import dist_point_polygon_km, grid_cells, haversine_km

WEIGHTS = {"H": 0.30, "HP": 0.30, "F": 0.15, "W": 0.10, "R": 0.15}
LEVELS = [(0.50, "severe"), (0.35, "high"), (0.20, "elevated"), (0.0, "low")]
SEVERITY = {"killing": 1.6, "clash": 1.3, "crop_destruction": 1.0, "cattle_rustling": 1.0, "threat": 0.8,
            "cattle_on_farm": 0.6, "sighting": 0.4}
FACTOR_NAMES = {"H": "past incidents nearby", "HP": "herds close to crops", "F": "crops in the field",
                "W": "dry-season water competition", "R": "recent community reports"}


# Middle Belt calendar: rains April to October; main harvest September to December;
# herds move south in the dry season (November to March) and back north with the rains.
def crop_factor(month: int) -> float:
    return {12: 0.6, 1: 0.35, 2: 0.3, 3: 0.4}.get(month, 1.0)


def dry_factor(month: int) -> float:
    return {11: 0.8, 12: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 0.7, 10: 0.4}.get(month, 0.15)


def level_of(score: float) -> str:
    return next(name for cut, name in LEVELS if score >= cut)


def _sat(x: float) -> float:
    return 1 - math.exp(-x)


class RiskModel:
    def __init__(self, layers, cell_deg: float = 0.025, bbox=None):
        self.layers = layers
        self.cell_deg = cell_deg
        self.bbox = bbox or layers.bbox()
        self.cells = []
        for r, c, lat, lon, bounds in grid_cells(self.bbox, cell_deg):
            farm_d = min(dist_point_polygon_km(lat, lon, f["geometry"]["coordinates"]) for f in layers.farms)
            self.cells.append({"r": r, "c": c, "lat": lat, "lon": lon, "bounds": bounds,
                               "farm_exposure": 1.0 if farm_d == 0 else math.exp(-farm_d / 1.0),
                               "water_km": layers.water_distance_km(lat, lon)})

    def score_point(self, lat, lon, farm_exposure, water_km, incidents, herds, reports, now) -> dict:
        m = now.month
        h = 0.0
        for inc in incidents:
            d = haversine_km(lat, lon, inc["lat"], inc["lon"])
            if d > 12:
                continue
            age = (now - datetime.fromisoformat(inc["ts"])).total_seconds() / 86400
            h += math.exp(-d * d / (2 * 3.0 ** 2)) * math.exp(-max(age, 0) / 30) * SEVERITY.get(inc["type"], 1.0)
        H = _sat(h)

        p = 0.0
        for hd in herds:
            for (hlat, hlon), w in [((hd["lat"], hd["lon"]), 1.0)] + [((f[0], f[1]), 0.6) for f in hd.get("forecast", [])]:
                d = haversine_km(lat, lon, hlat, hlon)
                if d < 15:
                    p += w * hd.get("size", 100) / 100 * math.exp(-d / 2.5)
        F = crop_factor(m) * farm_exposure
        HP = _sat(p) * min(1.0, F * 1.4)

        W = dry_factor(m) * math.exp(-water_km / 4.0)

        rr = 0.0
        for rep in reports:
            d = haversine_km(lat, lon, rep["lat"], rep["lon"])
            if d > 10:
                continue
            age_h = (now - datetime.fromisoformat(rep["ts"])).total_seconds() / 3600
            rr += rep.get("trust", 0.5) * SEVERITY.get(rep["type"], 1.0) * math.exp(-d / 3) * math.exp(-max(age_h, 0) / 48)
        R = _sat(rr)

        parts = {"H": H, "HP": HP, "F": F, "W": W, "R": R}
        score = sum(WEIGHTS[k] * v for k, v in parts.items())
        drivers = sorted(((WEIGHTS[k] * v, k) for k, v in parts.items()), reverse=True)
        return {"score": round(score, 3), "level": level_of(score),
                "factors": {k: round(v, 3) for k, v in parts.items()},
                "drivers": [FACTOR_NAMES[k] for c, k in drivers if c >= 0.05][:3]}

    def compute(self, incidents, herds, reports, now=None) -> list[dict]:
        now = now or datetime.now(timezone.utc)
        out = []
        for cell in self.cells:
            res = self.score_point(cell["lat"], cell["lon"], cell["farm_exposure"], cell["water_km"],
                                   incidents, herds, reports, now)
            out.append({**res, "lat": cell["lat"], "lon": cell["lon"], "bounds": cell["bounds"]})
        return out

    def community_risk(self, incidents, herds, reports, now=None) -> list[dict]:
        now = now or datetime.now(timezone.utc)
        out = []
        for c in self.layers.communities:
            lon, lat = c["geometry"]["coordinates"]
            farm_d = min(dist_point_polygon_km(lat, lon, f["geometry"]["coordinates"]) for f in self.layers.farms)
            res = self.score_point(lat, lon, 1.0 if farm_d == 0 else math.exp(-farm_d / 1.0),
                                   self.layers.water_distance_km(lat, lon), incidents, herds, reports, now)
            near = [h for h in herds if haversine_km(lat, lon, h["lat"], h["lon"]) <= 5]
            out.append({"community": c["properties"]["name"], "lga": c["properties"]["lga"], "lat": lat, "lon": lon,
                        "herds_within_5km": len(near), **res})
        return sorted(out, key=lambda x: -x["score"])
