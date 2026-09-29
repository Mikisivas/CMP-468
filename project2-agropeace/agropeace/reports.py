"""Community reports and trust scoring.

Rumours drive reprisals. A report is only broadcast once it is credible:

  trust = channel base
        + 0.15 for each independent reporter nearby (3 km, 6 h), max 0.30
        + 0.25 if a GPS collar confirms a herd within 2 km
        + reporter reputation (confirmed reports up, false reports down)

  verified >= 0.70   broadcast and escalate
  probable >= 0.45   send to mediators to check
  unverified         coordinators only, never broadcast
"""

from datetime import datetime

from .geo import haversine_km

CHANNEL_TRUST = {"mediator": 0.85, "field_officer": 0.80, "registered": 0.55, "ussd": 0.40, "sms": 0.40,
                 "web_anonymous": 0.30}
TYPES = {"cattle_on_farm": "Cattle on farmland", "crop_destruction": "Crops destroyed",
         "threat": "Threat or rumour of attack", "clash": "Clash in progress", "killing": "Killing",
         "cattle_rustling": "Cattle stolen", "sighting": "Armed group sighted"}
HERD_CONFIRMABLE = {"cattle_on_farm", "crop_destruction"}


def status_of(trust: float) -> str:
    return "verified" if trust >= 0.70 else "probable" if trust >= 0.45 else "unverified"


class ReportStore:
    def __init__(self):
        self.reports: list[dict] = []
        self.reputation: dict[str, float] = {}
        self._n = 0

    def add(self, *, rtype, lat, lon, channel, pseudonym, sealed_contact, community, lga, text, ts: datetime) -> dict:
        if rtype not in TYPES:
            raise ValueError(f"unknown report type {rtype}")
        self._n += 1
        rep = {"id": f"AP-{self._n:04d}", "type": rtype, "label": TYPES[rtype], "lat": lat, "lon": lon,
               "channel": channel, "reporter": pseudonym, "sealed_contact": sealed_contact,
               "community": community, "lga": lga, "text": text[:280], "ts": ts.isoformat(),
               "trust": 0.0, "status": "unverified", "why": [], "outcome": None}
        self.reports.append(rep)
        return rep

    def rescore(self, herds: list[dict], now: datetime) -> list[dict]:
        """Recompute trust for recent reports. Returns reports whose status went up."""
        upgraded = []
        recent = [r for r in self.reports
                  if (now - datetime.fromisoformat(r["ts"])).total_seconds() < 72 * 3600]
        for r in recent:
            why = [f"{r['channel']} channel {CHANNEL_TRUST.get(r['channel'], 0.3):.2f}"]
            t = CHANNEL_TRUST.get(r["channel"], 0.3)
            rts = datetime.fromisoformat(r["ts"])
            others = {o["reporter"] for o in recent
                      if o is not r and o["reporter"] != r["reporter"]
                      and haversine_km(r["lat"], r["lon"], o["lat"], o["lon"]) <= 3
                      and abs((datetime.fromisoformat(o["ts"]) - rts).total_seconds()) <= 6 * 3600}
            if others:
                bonus = min(0.30, 0.15 * len(others))
                t += bonus
                why.append(f"{len(others)} independent reporter(s) nearby +{bonus:.2f}")
            if r["type"] in HERD_CONFIRMABLE and any(
                    haversine_km(r["lat"], r["lon"], h["lat"], h["lon"]) <= 2 for h in herds):
                t += 0.25
                why.append("GPS collar confirms herd within 2 km +0.25")
            rep = self.reputation.get(r["reporter"], 0.0)
            if rep:
                t += rep
                why.append(f"reporter reputation {rep:+.2f}")
            if r["outcome"] == "confirmed":
                t = max(t, 0.95)
            elif r["outcome"] == "false":
                t = 0.0
            t = round(max(0.0, min(1.0, t)), 2)
            old = r["status"]
            r["trust"], r["why"], r["status"] = t, why, status_of(t)
            if ["unverified", "probable", "verified"].index(r["status"]) > ["unverified", "probable", "verified"].index(old):
                upgraded.append(r)
        return upgraded

    def mark(self, report_id: str, outcome: str) -> dict:
        """A mediator confirms a report on the ground or finds it false."""
        r = next(x for x in self.reports if x["id"] == report_id)
        r["outcome"] = outcome
        delta = 0.10 if outcome == "confirmed" else -0.20
        self.reputation[r["reporter"]] = max(-0.4, min(0.2, self.reputation.get(r["reporter"], 0.0) + delta))
        return r

    def for_risk(self) -> list[dict]:
        return [{"lat": r["lat"], "lon": r["lon"], "type": r["type"], "ts": r["ts"], "trust": r["trust"]}
                for r in self.reports if r["status"] != "unverified" or r["trust"] >= 0.3]
