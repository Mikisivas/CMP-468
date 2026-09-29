"""Map layers and spatial queries."""

import json
from pathlib import Path

from .geo import (bearing_deg, centroid, compass, dist_point_line_km, dist_point_polygon_km, haversine_km,
                  point_in_polygon)


class MapLayers:
    def __init__(self, geojson: dict):
        self.geojson = geojson
        by = {}
        for f in geojson["features"]:
            by.setdefault(f["properties"]["kind"], []).append(f)
        self.farms = by.get("farmland", [])
        self.reserves = by.get("grazing_reserve", [])
        self.communities = by.get("community", [])
        self.water_points = by.get("water_point", [])
        self.rivers = by.get("river", [])
        self.routes = by.get("stock_route", [])
        self.lgas = by.get("lga", [])
        for f in self.farms + self.reserves:
            f["_centroid"] = centroid(f["geometry"]["coordinates"][0])

    @classmethod
    def load(cls, path) -> "MapLayers":
        return cls(json.loads(Path(path).read_text()))

    # ---------------------------------------------------------------- queries
    def farm_at(self, lat, lon):
        for f in self.farms:
            if point_in_polygon(lat, lon, f["geometry"]["coordinates"]):
                return f
        return None

    def nearest_farm(self, lat, lon):
        best = min(self.farms, key=lambda f: dist_point_polygon_km(lat, lon, f["geometry"]["coordinates"]))
        return best, dist_point_polygon_km(lat, lon, best["geometry"]["coordinates"])

    def nearest_community(self, lat, lon):
        def d(f):
            lo, la = f["geometry"]["coordinates"]
            return haversine_km(lat, lon, la, lo)
        best = min(self.communities, key=d)
        return best, d(best)

    def lga_of(self, lat, lon) -> str:
        return self.nearest_community(lat, lon)[0]["properties"]["lga"]

    def in_reserve(self, lat, lon):
        for f in self.reserves:
            if point_in_polygon(lat, lon, f["geometry"]["coordinates"]):
                return f
        return None

    def nearest_reserve(self, lat, lon):
        best = min(self.reserves, key=lambda f: dist_point_polygon_km(lat, lon, f["geometry"]["coordinates"]))
        return best, dist_point_polygon_km(lat, lon, best["geometry"]["coordinates"])

    def water_distance_km(self, lat, lon) -> float:
        d = [haversine_km(lat, lon, f["geometry"]["coordinates"][1], f["geometry"]["coordinates"][0])
             for f in self.water_points]
        d += [dist_point_line_km(lat, lon, f["geometry"]["coordinates"]) for f in self.rivers]
        return min(d) if d else 99.0

    def nearest_route(self, lat, lon):
        best = min(self.routes, key=lambda f: dist_point_line_km(lat, lon, f["geometry"]["coordinates"]))
        return best, dist_point_line_km(lat, lon, best["geometry"]["coordinates"])

    def community_by_name(self, name):
        return next((c for c in self.communities if c["properties"]["name"] == name), None)

    def communities_in_lga(self, lga):
        return [c for c in self.communities if c["properties"]["lga"] == lga]

    def reroute_advice(self, lat, lon) -> dict:
        """Where a herd should go instead: nearest grazing reserve and its stock route."""
        res, dist = self.nearest_reserve(lat, lon)
        clat, clon = res["_centroid"]
        b = bearing_deg(lat, lon, clat, clon)
        route, rdist = self.nearest_route(lat, lon)
        return {"reserve": res["properties"]["name"], "distance_km": round(dist, 1),
                "direction": compass(b), "bearing": round(b), "route": route["properties"]["name"],
                "route_distance_km": round(rdist, 1)}

    def bbox(self, pad=0.05):
        lats, lons = [], []

        def walk(c):
            if isinstance(c[0], (int, float)):
                lons.append(c[0])
                lats.append(c[1])
            else:
                for x in c:
                    walk(x)
        for f in self.geojson["features"]:
            if f["properties"]["kind"] != "lga":
                walk(f["geometry"]["coordinates"])
        return [min(lats) - pad, min(lons) - pad, max(lats) + pad, max(lons) + pad]

    def public_geojson(self) -> dict:
        return {"type": "FeatureCollection", "features": [
            {k: v for k, v in f.items() if not k.startswith("_")} for f in self.geojson["features"]]}
