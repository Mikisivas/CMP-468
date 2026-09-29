"""AgroPeace engine: ties GIS layers, risk model, tracking, reports, cases,
notifications and security together. The web server and the demo both drive it."""

import hashlib
import hmac
import json
import os
import threading
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .geo import haversine_km
from .layers import MapLayers
from .notify import Notifier, render
from .reports import TYPES, ReportStore
from .response import LEVELS, CaseBook
from .risk import RiskModel
from .security import AuditChain, AuthError, DeviceAuth, IdentityVault, RateLimiter, can, sees_lga
from .tracking import HerdTracker

REPORT_LEVEL = {  # (type, status) -> case level
    ("killing", "verified"): "critical", ("clash", "verified"): "critical",
    ("killing", "probable"): "warning", ("clash", "probable"): "warning",
    ("sighting", "verified"): "warning", ("threat", "verified"): "warning",
    ("sighting", "probable"): "advisory", ("threat", "probable"): "advisory",
    ("cattle_on_farm", "verified"): "warning", ("crop_destruction", "verified"): "warning",
    ("cattle_on_farm", "probable"): "advisory", ("crop_destruction", "probable"): "advisory",
    ("cattle_rustling", "verified"): "warning", ("cattle_rustling", "probable"): "advisory",
}


def load_config(path) -> dict:
    path = Path(path).resolve()
    cfg = json.loads(path.read_text())
    base = path.parent
    for k in ("layers", "incidents", "state_dir"):
        cfg[k] = str((base / cfg[k]).resolve())
    return cfg


def master_key_from_env(cfg) -> bytes:
    secret = os.environ.get(cfg.get("master_key_env", "AGROPEACE_MASTER_KEY"))
    if not secret or len(secret) < 16:
        raise SystemExit(f"Set {cfg.get('master_key_env', 'AGROPEACE_MASTER_KEY')} (at least 16 characters).")
    return hashlib.sha256(secret.encode()).digest()


def device_key(master: bytes, device_id: str) -> bytes:
    """Per-device key, provisioned onto each collar at registration."""
    return hmac.new(master, f"device:{device_id}".encode(), hashlib.sha256).digest()


class Engine:
    def __init__(self, cfg: dict, master: bytes, clock=None):
        self.cfg = cfg
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        state = Path(cfg["state_dir"])
        state.mkdir(parents=True, exist_ok=True)
        self.layers = MapLayers.load(cfg["layers"])
        self.history = json.loads(Path(cfg["incidents"]).read_text())
        self.risk = RiskModel(self.layers, cfg.get("cell_deg", 0.025))
        self.vault = IdentityVault(master)
        self.audit = AuditChain(state / "audit.db")
        self.notifier = Notifier(state / "sms_outbox.jsonl", cfg.get("africastalking"))
        self.report_limiter = RateLimiter(cfg.get("reports_per_hour", 3), 3600)
        registry = {}
        for dev, info in cfg["devices"].items():
            registry[dev] = {**info, "owner_pseudonym": self.vault.pseudonym(info["owner_phone"]),
                             "owner_sealed": self.vault.seal(info["owner_phone"])}
        self.tracker = HerdTracker(self.layers, registry)
        self.auth = DeviceAuth({dev: device_key(master, dev) for dev in cfg["devices"]}, cfg.get("replay_window_s", 120))
        self.reports = ReportStore()
        self.cases = CaseBook(cfg["responders"])
        self.lock = threading.RLock()
        self.events: deque = deque(maxlen=300)
        self._event_id = 0
        self.rejected = 0
        self.grid: list[dict] = []
        self.community: list[dict] = []
        self.recompute_risk()

    # ---------------------------------------------------------------- helpers
    def month(self) -> int:
        return self.cfg.get("season_month") or self.clock().month

    def _now_for_risk(self):
        now = self.clock()
        if self.cfg.get("season_month"):
            now = now.replace(month=self.cfg["season_month"])
        return now

    def publish(self, kind: str, data: dict, audience: str = "staff") -> None:
        self._event_id += 1
        self.events.append({"id": self._event_id, "kind": kind, "audience": audience,
                            "ts": self.clock().isoformat(), "data": data})

    def all_incidents(self) -> list[dict]:
        live = [{"lat": r["lat"], "lon": r["lon"], "type": r["type"], "ts": r["ts"]}
                for r in self.reports.reports if r["status"] == "verified" and r["type"] in ("clash", "killing", "crop_destruction", "cattle_rustling")]
        return self.history + live

    def recompute_risk(self) -> None:
        with self.lock:
            now = self._now_for_risk()
            herds = self.tracker.herd_dicts()
            reps = self.reports.for_risk()
            self.grid = self.risk.compute(self.all_incidents(), herds, reps, now)
            self.community = self.risk.community_risk(self.all_incidents(), herds, reps, now)

    def community_risk(self, name) -> dict | None:
        return next((c for c in self.community if c["community"] == name), None)

    def _notify_case(self, case: dict) -> None:
        for r in self.cases.responders_for(case["level"], case["lga"]):
            if r["id"] in case["notified"] and case["level"] != "critical":
                continue
            text = render("responder_case", r.get("language", "en"), level=case["level"].upper(), case=case["id"],
                          title=case["title"], place=case["place"], lga=case["lga"])
            self.notifier.send(r["name"], r.get("phone", ""), text, {"case": case["id"], "level": case["level"]})
            if r["id"] not in case["notified"]:
                case["notified"].append(r["id"])
        self.publish("case", case)

    def _herder_sms(self, herd, template, **kw) -> None:
        text = render(template, herd.language, herd=herd.herd_id, **kw)
        phone = self.vault.unseal(herd.owner_sealed)
        self.notifier.send(f"Herder {herd.owner} ({herd.herd_id})", phone, text, {"herd": herd.herd_id})

    # ---------------------------------------------------------------- tracker input
    def ingest_position(self, body: dict, signature: str) -> dict:
        with self.lock:
            try:
                self.auth.verify(body, signature, now=self.clock().timestamp())
            except AuthError as exc:
                self.rejected += 1
                self.audit.record(body.get("device_id", "?"), "position_rejected", {"reason": str(exc)})
                self.publish("security", {"message": f"Rejected tracker message: {exc}"})
                raise
            events = self.tracker.update(body["device_id"], float(body["lat"]), float(body["lon"]),
                                         float(body["ts"]), self.month())
            herd = self.tracker.herds[body["device_id"]]
            for ev in events:
                self._handle_geofence(herd, ev)
            self.publish("herd", herd.public(precise=True))
            return {"ok": True, "events": [e["event"] for e in events]}

    def _handle_geofence(self, herd, ev) -> None:
        now = self.clock()
        adv = self.layers.reroute_advice(herd.lat, herd.lon)
        key = f"herd:{herd.herd_id}"
        if ev["event"] == "predicted_incursion":
            self._herder_sms(herd, "herder_predicted", place=ev["place"], hours=ev["hours"], reserve=adv["reserve"],
                             dir=adv["direction"], route=adv["route"])
            case, changed = self.cases.open_or_update(
                key=key, level="advisory", title=f"Herd {herd.herd_id} ({herd.size} cattle) heading for {ev['farm']} ({ev['crop']}), ~{ev['hours']} h",
                lat=herd.lat, lon=herd.lon, lga=ev["lga"], place=ev["place"], now=now, source=ev)
        elif ev["event"] in ("approach", "incursion"):
            if ev["event"] == "incursion" and not ev.get("crops_in_field"):
                return
            if ev["event"] == "incursion":
                self._herder_sms(herd, "herder_incursion", farm=ev["farm"], crop=ev["crop"], place=ev["place"],
                                 reserve=adv["reserve"], dist=adv["distance_km"], dir=adv["direction"], route=adv["route"])
            cr = self.community_risk(ev["place"]) or {"level": "low"}
            level = "critical" if ev["event"] == "incursion" and cr["level"] == "severe" else (
                "warning" if ev["event"] == "incursion" else "advisory")
            what = f"inside {ev['farm']} ({ev['crop']})" if ev["event"] == "incursion" else f"{ev['distance_km']} km from {ev['farm']}"
            case, changed = self.cases.open_or_update(
                key=key, level=level, title=f"Herd {herd.herd_id} ({herd.size} cattle) {what}",
                lat=herd.lat, lon=herd.lon, lga=ev["lga"], place=ev["place"], now=now, source=ev)
            case["reroute"] = adv
        elif ev["event"] == "cleared":
            for c in self.cases.cases:
                if c["key"] == key and c["status"] != "resolved":
                    c["timeline"].append({"ts": now.isoformat(), "event": f"GPS: herd left {ev.get('farm', 'farmland')}"})
                    self.publish("case", c)
            self.audit.record("system", "herd_cleared", {"herd": herd.herd_id})
            return
        else:
            return
        self.audit.record("system", f"geofence_{ev['event']}", {"herd": herd.herd_id, "case": case["id"], "level": case["level"]})
        if changed:
            self._notify_case(case)
        self.recompute_risk()

    # ---------------------------------------------------------------- community reports
    def submit_report(self, *, rtype: str, channel: str, phone: str, community: str | None = None,
                      lat=None, lon=None, text: str = "") -> dict:
        with self.lock:
            pseud = self.vault.pseudonym(phone)
            if not self.report_limiter.allow(pseud):
                self.audit.record(pseud, "report_rate_limited", {})
                raise PermissionError("Too many reports from this number. Try again later.")
            if community:
                c = self.layers.community_by_name(community)
                if not c:
                    raise ValueError("unknown community")
                lon, lat = c["geometry"]["coordinates"]
            lat, lon = float(lat), float(lon)
            near, _ = self.layers.nearest_community(lat, lon)
            rep = self.reports.add(rtype=rtype, lat=lat, lon=lon, channel=channel, pseudonym=pseud,
                                   sealed_contact=self.vault.seal(phone), community=near["properties"]["name"],
                                   lga=near["properties"]["lga"], text=text, ts=self.clock())
            self.audit.record(pseud, "report_submitted", {"report": rep["id"], "type": rtype, "channel": channel})
            self._rescore_reports()
            self.publish("report", self._report_view(rep, None))
            return rep

    def _rescore_reports(self) -> None:
        upgraded = self.reports.rescore(self.tracker.herd_dicts(), self.clock())
        for r in upgraded:
            level = REPORT_LEVEL.get((r["type"], r["status"]))
            if not level:
                continue
            case, changed = self.cases.open_or_update(
                key=f"area:{r['community']}:{r['type']}", level=level,
                title=f"{r['label']} reported at {r['community']} ({r['status']}, trust {r['trust']:.2f})",
                lat=r["lat"], lon=r["lon"], lga=r["lga"], place=r["community"], now=self.clock(),
                source={"report": r["id"]})
            self.audit.record("system", "report_escalated", {"report": r["id"], "status": r["status"], "case": case["id"]})
            if changed:
                self._notify_case(case)
        if upgraded:
            self.recompute_risk()

    def mark_report(self, report_id: str, outcome: str, user: dict) -> dict:
        with self.lock:
            r = self.reports.mark(report_id, outcome)
            self.audit.record(user["username"], "report_marked", {"report": report_id, "outcome": outcome})
            self._rescore_reports()
            self.recompute_risk()
            return r

    def reveal_identity(self, report_id: str, user: dict, reason: str) -> str:
        """Break-glass access to an informant's number, for protection only. Always audited."""
        if not can(user, "reveal_identity"):
            self.audit.record(user.get("username", "?"), "identity_reveal_denied", {"report": report_id})
            raise PermissionError("Only the protection officer can reveal a reporter's identity.")
        if len(reason.strip()) < 10:
            raise ValueError("A written reason is required.")
        r = next(x for x in self.reports.reports if x["id"] == report_id)
        self.audit.record(user["username"], "identity_revealed", {"report": report_id, "reason": reason})
        return self.vault.unseal(r["sealed_contact"])

    # ---------------------------------------------------------------- case actions
    def acknowledge(self, case_id: str, who: str) -> dict:
        with self.lock:
            c = self.cases.acknowledge(case_id, who, self.clock())
            self.audit.record(who, "case_acknowledged", {"case": case_id})
            self.publish("case", c)
            return c

    def resolve(self, case_id: str, who: str, outcome: str, note: str = "") -> dict:
        with self.lock:
            c = self.cases.resolve(case_id, who, outcome, note, self.clock())
            self.audit.record(who, "case_resolved", {"case": case_id, "outcome": outcome})
            self.publish("case", c)
            return c

    def sms_inbound(self, phone: str, text: str) -> str:
        """Field responders reply 'ACK C-001' from any phone, no internet needed."""
        parts = text.strip().upper().split()
        if len(parts) != 2 or parts[0] != "ACK":
            return "Send: ACK <case id>"
        r = next((x for x in self.cfg["responders"] if hmac.compare_digest(x.get("phone", ""), phone)), None)
        if not r:
            self.audit.record(self.vault.pseudonym(phone), "sms_ack_rejected", {"text": text[:40]})
            return "Number not registered as a responder."
        try:
            c = self.cases.get(parts[1])
        except StopIteration:
            return f"No case {parts[1]}."
        if r["id"] not in c["notified"]:
            return f"You were not assigned to {parts[1]}."
        self.acknowledge(parts[1], r["name"])
        return f"Thanks. {parts[1]} marked acknowledged by {r['name']}."

    # ---------------------------------------------------------------- periodic work
    def tick(self) -> None:
        with self.lock:
            for c in self.cases.overdue(self.clock()):
                self.audit.record("system", "case_escalated", {"case": c["id"], "level": c["level"]})
                self._notify_case(c)
            self._rescore_reports()
            self.recompute_risk()
            self.publish("risk", {"communities": self.community[:10]}, audience="public")

    # ---------------------------------------------------------------- USSD (Africa's Talking style)
    def ussd(self, phone: str, text: str) -> str:
        steps = [s for s in text.split("*")] if text else []
        lgas = sorted({c["properties"]["lga"] for c in self.layers.communities})
        main = "CON AgroPeace (Benue)\n1. Cattle on my farm\n2. Threat or attack\n3. Cattle stolen\n4. Check risk in my area"
        if not steps:
            return main
        first = steps[0]
        if first not in ("1", "2", "3", "4"):
            return "END Invalid choice."
        rest = steps[1:]
        rtype = {"1": "cattle_on_farm", "3": "cattle_rustling"}.get(first)
        if first == "2":
            if not rest:
                return "CON What is happening?\n1. Threat or rumour\n2. Clash now\n3. Armed men seen"
            rtype = {"1": "threat", "2": "clash", "3": "sighting"}.get(rest[0])
            if not rtype:
                return "END Invalid choice."
            rest = rest[1:]
        if not rest:
            return "CON Select LGA\n" + "\n".join(f"{i + 1}. {n}" for i, n in enumerate(lgas))
        try:
            lga = lgas[int(rest[0]) - 1]
        except (ValueError, IndexError):
            return "END Invalid LGA."
        comms = [c["properties"]["name"] for c in self.layers.communities_in_lga(lga)]
        if len(rest) == 1:
            return "CON Select community\n" + "\n".join(f"{i + 1}. {n}" for i, n in enumerate(comms))
        try:
            comm = comms[int(rest[1]) - 1]
        except (ValueError, IndexError):
            return "END Invalid community."
        if first == "4":
            cr = self.community_risk(comm)
            causes = ", ".join(cr["drivers"]) or "no major factors"
            return (f"END Risk at {comm}: {cr['level'].upper()}. Herds within 5 km: {cr['herds_within_5km']}. "
                    f"Main causes: {causes}.")
        if len(rest) == 2:
            return f"CON Send report: {TYPES[rtype]} at {comm}?\n1. Yes, send\n2. Cancel"
        if rest[2] != "1":
            return "END Cancelled."
        try:
            rep = self.submit_report(rtype=rtype, channel="ussd", phone=phone, community=comm)
        except PermissionError as exc:
            return f"END {exc}"
        return f"END Report {rep['id']} received. Your identity is protected. Peace committee is being informed."

    # ---------------------------------------------------------------- views
    def _report_view(self, r: dict, user) -> dict:
        v = {k: v for k, v in r.items() if k not in ("sealed_contact",)}
        return v

    def snapshot(self, user: dict | None) -> dict:
        """Role-filtered state for the dashboard. The public sees coarse, verified information only."""
        with self.lock:
            precise = can(user, "view_precise")
            # The public never sees herds: a herd marked "inside a farm" on a public map invites reprisals.
            herds = [h.public(precise) for h in self.tracker.herds.values() if h.lat is not None] if precise else []
            if precise and not can(user, "view_all_lgas"):
                herds = [h for h in herds if sees_lga(user, self.layers.lga_of(h["lat"], h["lon"]))]
            reports = [self._report_view(r, user) for r in self.reports.reports
                       if r["status"] != "unverified" or can(user, "view_unverified")]
            if not precise:
                reports = [{"id": r["id"], "label": r["label"], "community": r["community"], "status": r["status"],
                            "ts": r["ts"]} for r in reports if r["status"] == "verified"]
            elif not can(user, "view_all_lgas"):
                reports = [r for r in reports if sees_lga(user, r["lga"])]
            cases = [c for c in self.cases.cases if precise and sees_lga(user, c["lga"])]
            cutoff = self.clock() - timedelta(days=30)
            history = [i for i in self.history if datetime.fromisoformat(i["ts"]) >= cutoff] if precise else []
            return {
                "role": (user or {}).get("role", "public"), "user": (user or {}).get("username"),
                "month": self.month(),
                "grid": [{"b": g["bounds"], "s": g["score"], "l": g["level"]} for g in self.grid if g["score"] >= 0.1],
                "communities": self.community,
                "herds": herds, "reports": reports[-50:], "cases": list(reversed(cases))[:30],
                "incidents_30d": history,
                "security": {"rejected_messages": self.rejected, "audit": self.audit.verify()} if precise else None,
                "audit_recent": self.audit.recent(15) if can(user, "view_audit") else None,
                "levels": LEVELS,
            }
