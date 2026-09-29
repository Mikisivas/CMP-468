"""Conflict-resolution workflow: cases, responder routing and escalation.

Escalation ladder (each rung adds responders; nobody is dropped):

  advisory  herder, herder association          (prevent: turn the herd early)
  warning   + peace committee, farmer association  (mediate on the spot)
  critical  + NSCDC Agro Rangers, LGA security   (protect lives)

If nobody acknowledges within the SLA, the case climbs one rung and the new
responders are alerted. Mediation comes before force by design.
"""

from datetime import datetime, timedelta

LEVELS = ["advisory", "warning", "critical"]
SLA_MIN = {"advisory": 60, "warning": 30, "critical": 10}
RUNG_ROLES = {
    "advisory": ["herder_association"],
    "warning": ["herder_association", "peace_committee", "farmer_association"],
    "critical": ["herder_association", "peace_committee", "farmer_association", "agro_rangers", "lga_security"],
}
OUTCOMES = ["herd_rerouted", "dialogue_held", "compensation_agreed", "security_deployed", "false_alarm"]


class CaseBook:
    def __init__(self, responders: list[dict]):
        self.responders = responders
        self.cases: list[dict] = []
        self._n = 0

    def responders_for(self, level: str, lga: str) -> list[dict]:
        roles = RUNG_ROLES[level]
        return [r for r in self.responders if r["role"] in roles and (r.get("lga") in (lga, "*"))]

    def open_or_update(self, *, key: str, level: str, title: str, lat, lon, lga, place, now: datetime,
                       source: dict) -> tuple[dict, bool]:
        """Create a case, or raise the level of an open case with the same key. Returns (case, is_new_or_raised)."""
        for c in self.cases:
            if c["key"] == key and c["status"] not in ("resolved",):
                if LEVELS.index(level) > LEVELS.index(c["level"]):
                    c["level"] = level
                    c["due"] = (now + timedelta(minutes=SLA_MIN[level])).isoformat()
                    c["timeline"].append({"ts": now.isoformat(), "event": f"raised to {level}: {title}"})
                    c["title"] = title
                    return c, True
                c["timeline"].append({"ts": now.isoformat(), "event": f"update: {title}"})
                return c, False
        self._n += 1
        c = {"id": f"C-{self._n:03d}", "key": key, "level": level, "title": title, "lat": lat, "lon": lon,
             "lga": lga, "place": place, "status": "open", "created": now.isoformat(),
             "due": (now + timedelta(minutes=SLA_MIN[level])).isoformat(), "acknowledged_by": None,
             "outcome": None, "notified": [], "source": source,
             "timeline": [{"ts": now.isoformat(), "event": f"opened as {level}: {title}"}]}
        self.cases.append(c)
        return c, True

    def acknowledge(self, case_id: str, who: str, now: datetime) -> dict:
        c = self.get(case_id)
        if c["status"] == "open":
            c["status"] = "acknowledged"
            c["acknowledged_by"] = who
            mins = (now - datetime.fromisoformat(c["created"])).total_seconds() / 60
            c["response_min"] = round(mins, 1)
            c["timeline"].append({"ts": now.isoformat(), "event": f"acknowledged by {who} after {mins:.0f} min"})
        return c

    def resolve(self, case_id: str, who: str, outcome: str, note: str, now: datetime) -> dict:
        if outcome not in OUTCOMES:
            raise ValueError(f"outcome must be one of {OUTCOMES}")
        c = self.get(case_id)
        c["status"], c["outcome"] = "resolved", outcome
        c["timeline"].append({"ts": now.isoformat(), "event": f"resolved by {who}: {outcome}. {note}".strip()})
        return c

    def overdue(self, now: datetime) -> list[dict]:
        """Open cases past their SLA. Each is raised one rung (critical stays critical but re-alerts)."""
        out = []
        for c in self.cases:
            if c["status"] == "open" and now > datetime.fromisoformat(c["due"]):
                i = LEVELS.index(c["level"])
                new = LEVELS[min(i + 1, len(LEVELS) - 1)]
                c["timeline"].append({"ts": now.isoformat(),
                                      "event": f"no acknowledgement within {SLA_MIN[c['level']]} min: escalated to {new}"})
                c["level"] = new
                c["due"] = (now + timedelta(minutes=SLA_MIN[new])).isoformat()
                c["escalations"] = c.get("escalations", 0) + 1
                out.append(c)
        return out

    def get(self, case_id: str) -> dict:
        return next(c for c in self.cases if c["id"] == case_id)
