"""Real-time herd tracking, movement forecast and geofencing."""

from collections import deque

from .geo import bearing_deg, destination, haversine_km
from .risk import crop_factor

FORECAST_HOURS = (1, 2, 3)
NEAR_FARM_KM = 0.5
WARN_COOLDOWN_S = 2 * 3600  # do not repeat an early warning about the same farm within 2 hours


class Herd:
    def __init__(self, device_id: str, info: dict):
        self.device_id = device_id
        self.herd_id = info["herd_id"]
        self.size = info.get("size", 100)
        self.owner = info.get("owner_pseudonym", "")
        self.owner_sealed = info.get("owner_sealed", "")
        self.language = info.get("language", "ha")
        self.lat = self.lon = None
        self.ts = None
        self.speed_kmh = 0.0
        self.heading = None
        self.forecast: list[tuple[float, float, int]] = []
        self.zone = "unknown"
        self.zone_detail: dict = {}
        self.warned: dict[str, float] = {}  # farm -> time of last early warning
        self.trail: deque = deque(maxlen=30)

    def public(self, precise: bool) -> dict:
        from .geo import snap_to_grid
        lat, lon = (self.lat, self.lon) if precise else snap_to_grid(self.lat, self.lon, 0.05)
        d = {"herd_id": self.herd_id, "size": self.size, "lat": round(lat, 5), "lon": round(lon, 5),
             "zone": self.zone, "ts": self.ts}
        if precise:
            d.update({"speed_kmh": round(self.speed_kmh, 1), "heading": self.heading,
                      "forecast": [[round(a, 5), round(b, 5), h] for a, b, h in self.forecast],
                      "trail": [[round(a, 5), round(b, 5)] for a, b in self.trail], "detail": self.zone_detail})
        return d


class HerdTracker:
    def __init__(self, layers, registry: dict[str, dict]):
        self.layers = layers
        self.herds = {dev: Herd(dev, info) for dev, info in registry.items()}

    def update(self, device_id: str, lat: float, lon: float, ts: float, month: int) -> list[dict]:
        """Apply one GPS fix. Returns geofence events (only on state change)."""
        h = self.herds[device_id]
        if h.lat is not None and ts > h.ts:
            dist = haversine_km(h.lat, h.lon, lat, lon)
            hours = (ts - h.ts) / 3600
            if dist > 0.02:
                h.heading = round(bearing_deg(h.lat, h.lon, lat, lon))
            # smooth speed; cattle graze at 1 to 3 km/h and trek up to about 5 km/h
            h.speed_kmh = min(6.0, 0.5 * h.speed_kmh + 0.5 * (dist / hours if hours > 0 else 0))
        h.lat, h.lon, h.ts = lat, lon, ts
        h.trail.append((lat, lon))
        h.forecast = []
        if h.heading is not None and h.speed_kmh >= 0.3:
            h.forecast = [(*destination(lat, lon, h.heading, h.speed_kmh * t), t) for t in FORECAST_HOURS]
        return self._geofence(h, month)

    def _geofence(self, h: Herd, month: int) -> list[dict]:
        L = self.layers
        crops_in_field = crop_factor(month) >= 0.6
        farm = L.farm_at(h.lat, h.lon)
        reserve = L.in_reserve(h.lat, h.lon)
        nearest, dist = L.nearest_farm(h.lat, h.lon)
        community, _ = L.nearest_community(h.lat, h.lon)
        place = community["properties"]["name"]
        lga = community["properties"]["lga"]
        base = {"herd_id": h.herd_id, "device_id": h.device_id, "lat": h.lat, "lon": h.lon, "place": place,
                "lga": lga, "size": h.size}

        if farm:
            zone, detail = "in_farm", {"farm": farm["properties"]["name"], "crop": farm["properties"]["crop"]}
        elif reserve:
            zone, detail = "in_reserve", {"reserve": reserve["properties"]["name"]}
        elif dist <= NEAR_FARM_KM:
            zone, detail = "near_farm", {"farm": nearest["properties"]["name"], "distance_km": round(dist, 2)}
        else:
            zone, detail = "open", {}

        predicted = None
        if zone not in ("in_farm",):
            for flat, flon, hrs in h.forecast:
                f = L.farm_at(flat, flon)
                if f:
                    predicted = {"farm": f["properties"]["name"], "crop": f["properties"]["crop"], "hours": hrs}
                    break

        events = []
        prev = h.zone
        h.zone, h.zone_detail = zone, {**detail, **({"predicted": predicted} if predicted else {})}
        if zone != prev:
            if zone == "in_farm":
                events.append({**base, "event": "incursion", "crops_in_field": crops_in_field, **detail})
            elif zone == "near_farm" and crops_in_field:
                events.append({**base, "event": "approach", **detail})
            elif prev == "in_farm":
                events.append({**base, "event": "cleared", **detail})
        predicted_farm = predicted["farm"] if predicted else None
        last = h.warned.get(predicted_farm)
        if predicted_farm and crops_in_field and (last is None or h.ts - last > WARN_COOLDOWN_S):
            events.append({**base, "event": "predicted_incursion", **predicted})
            h.warned[predicted_farm] = h.ts
        return events

    def herd_dicts(self) -> list[dict]:
        return [{"herd_id": h.herd_id, "lat": h.lat, "lon": h.lon, "size": h.size,
                 "forecast": [(a, b) for a, b, _ in h.forecast]} for h in self.herds.values() if h.lat is not None]
