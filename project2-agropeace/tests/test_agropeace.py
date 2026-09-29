import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agropeace.engine import Engine, device_key, load_config
from agropeace.geo import (bearing_deg, destination, dist_point_polygon_km, haversine_km, point_in_polygon,
                           snap_to_grid)
from agropeace.risk import crop_factor, dry_factor, level_of
from agropeace.security import AuditChain, AuthError, DeviceAuth, IdentityVault, RateLimiter, sign_message
from agropeace.server import create_app
from simulator import plan_paths, signed_fix

ROOT = Path(__file__).resolve().parent.parent
MASTER = b"k" * 32
SQUARE = [[[8.0, 7.0], [8.1, 7.0], [8.1, 7.1], [8.0, 7.1], [8.0, 7.0]]]


# ---------------------------------------------------------------- GIS

def test_haversine_known_distance():
    # one degree of latitude is about 111.2 km
    assert abs(haversine_km(7.0, 8.5, 8.0, 8.5) - 111.2) < 0.2


def test_destination_and_bearing_roundtrip():
    lat, lon = destination(7.8, 8.6, 45, 10)
    assert abs(haversine_km(7.8, 8.6, lat, lon) - 10) < 0.01
    assert abs(bearing_deg(7.8, 8.6, lat, lon) - 45) < 0.5


def test_point_in_polygon_and_distance():
    assert point_in_polygon(7.05, 8.05, SQUARE)
    assert not point_in_polygon(7.2, 8.05, SQUARE)
    assert dist_point_polygon_km(7.05, 8.05, SQUARE) == 0
    d = dist_point_polygon_km(7.05, 8.2, SQUARE)  # 0.1 deg east of the edge
    assert 10.5 < d < 11.5


def test_polygon_hole():
    poly = SQUARE + [[[8.04, 7.04], [8.06, 7.04], [8.06, 7.06], [8.04, 7.06], [8.04, 7.04]]]
    assert not point_in_polygon(7.05, 8.05, poly)
    assert point_in_polygon(7.02, 8.02, poly)


def test_snap_to_grid_coarsens():
    lat, lon = snap_to_grid(7.8123, 8.7456, 0.05)
    assert (round(lat, 3), round(lon, 3)) == (7.825, 8.725)


# ---------------------------------------------------------------- risk model

def test_season_factors():
    assert crop_factor(9) == 1.0 and crop_factor(2) < 0.5
    assert dry_factor(1) == 1.0 and dry_factor(7) < 0.3


def test_levels():
    assert [level_of(x) for x in (0.1, 0.25, 0.4, 0.6)] == ["low", "elevated", "high", "severe"]


# ---------------------------------------------------------------- security

def test_device_signature_and_replay():
    key = b"x" * 32
    auth = DeviceAuth({"C1": key}, window_s=60)
    body = {"device_id": "C1", "lat": 7.8, "lon": 8.6, "ts": 1000.0, "nonce": "a1"}
    sig = sign_message(key, body)
    auth.verify(body, sig, now=1010)
    with pytest.raises(AuthError, match="replayed"):
        auth.verify(body, sig, now=1011)
    forged = {**body, "lat": 7.9, "nonce": "a2"}
    with pytest.raises(AuthError, match="bad signature"):
        auth.verify(forged, sig, now=1012)
    old = {**body, "nonce": "a3"}
    with pytest.raises(AuthError, match="stale"):
        auth.verify(old, sign_message(key, old), now=2000)
    with pytest.raises(AuthError, match="unknown device"):
        auth.verify({**body, "device_id": "C9"}, sig, now=1010)


def test_identity_vault():
    v = IdentityVault(MASTER)
    token = v.seal("+2348030000101")
    assert "2348030000101" not in token
    assert v.unseal(token) == "+2348030000101"
    assert v.pseudonym("+2348030000101") == v.pseudonym("+2348030000101")
    assert v.pseudonym("+2348030000101") != v.pseudonym("+2348030000102")
    bad = token[:-2] + ("00" if token[-2:] != "00" else "11")
    with pytest.raises(AuthError):
        v.unseal(bad)


def test_rate_limiter():
    rl = RateLimiter(3, 3600)
    assert [rl.allow("r", now=t) for t in (0, 1, 2, 3)] == [True, True, True, False]
    assert rl.allow("r", now=3700)


def test_audit_chain(tmp_path):
    a = AuditChain(tmp_path / "a.db")
    for i in range(4):
        a.record("u", f"act{i}")
    assert a.verify()["ok"]
    a._db.execute("UPDATE audit SET actor='someone else' WHERE seq=2")
    a._db.commit()
    assert a.verify() == {"ok": False, "broken_at": 2}


# ---------------------------------------------------------------- engine

class Clock:
    def __init__(self):
        self.t = datetime(2026, 9, 20, 8, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.t


@pytest.fixture
def eng(tmp_path):
    if not (ROOT / "data" / "benue_layers.geojson").exists():
        import generate_data
        generate_data.main()
    cfg = load_config(ROOT / "demo" / "demo_config.json")
    cfg["state_dir"] = str(tmp_path / "state")
    clock = Clock()
    e = Engine(cfg, MASTER, clock=clock)
    e.test_clock = clock
    return e


def drive(e, device, points):
    events = []
    for lat, lon in points:
        e.test_clock.t += timedelta(minutes=10)
        body, sig = signed_fix(MASTER, device, lat, lon, e.test_clock.t.timestamp())
        events += e.ingest_position(body, sig)["events"]
    return events


def test_herd_into_farm_warns_then_opens_case(eng):
    path = plan_paths(eng.layers)["COLLAR-01"]
    events = drive(eng, "COLLAR-01", path)
    assert "predicted_incursion" in events and "incursion" in events
    assert events.index("predicted_incursion") < events.index("incursion")  # warning came first
    case = next(c for c in eng.cases.cases if c["key"] == "herd:H1")
    assert case["level"] in ("warning", "critical") and case["lga"] == "Guma"
    assert case["reroute"]["reserve"].endswith("Grazing Reserve")
    herder_sms = [m for m in eng.notifier.sent if m["to"].startswith("Herder")]
    assert any("garken ku H1" in m["text"] for m in herder_sms)  # Hausa for this herder
    assert all("+234" not in json.dumps(m) for m in eng.notifier.sent)  # outbox never stores numbers


def test_grazing_in_reserve_raises_nothing(eng):
    assert drive(eng, "COLLAR-02", plan_paths(eng.layers)["COLLAR-02"]) == []


def test_forged_position_rejected_and_audited(eng):
    body = {"device_id": "COLLAR-01", "lat": 7.9, "lon": 8.8, "ts": eng.test_clock.t.timestamp(), "nonce": "n"}
    with pytest.raises(AuthError):
        eng.ingest_position(body, sign_message(b"wrong key", body))
    assert eng.rejected == 1
    assert any(a["action"] == "position_rejected" for a in eng.audit.recent())


def test_single_anonymous_rumour_not_broadcast(eng):
    rep = eng.submit_report(rtype="threat", channel="web_anonymous", phone="+2348011110001", community="Naka")
    assert rep["status"] == "unverified"
    assert eng.cases.cases == []
    public = eng.snapshot(None)
    assert public["reports"] == [] and public["cases"] == []


def test_corroboration_upgrades_report(eng):
    r1 = eng.submit_report(rtype="threat", channel="ussd", phone="+2348011110001", community="Yelwata")
    assert r1["status"] == "unverified"
    eng.submit_report(rtype="threat", channel="ussd", phone="+2348011110002", community="Yelwata")
    assert r1["status"] == "probable"
    assert any(c["key"] == "area:Yelwata:threat" for c in eng.cases.cases)


def test_gps_corroborates_cattle_report(eng):
    path = plan_paths(eng.layers)["COLLAR-01"]
    drive(eng, "COLLAR-01", path)
    rep = eng.submit_report(rtype="cattle_on_farm", channel="ussd", phone="+2348011110003", community="Yelwata")
    assert any("GPS collar" in w for w in rep["why"])
    assert rep["status"] == "probable"


def test_false_reports_lower_reputation(eng):
    user = {"username": "coordinator", "role": "coordinator"}
    r = eng.submit_report(rtype="threat", channel="registered", phone="+2348011110004", community="Daudu")
    eng.mark_report(r["id"], "false", user)
    assert r["trust"] == 0.0
    r2 = eng.submit_report(rtype="threat", channel="registered", phone="+2348011110004", community="Abinsi")
    assert r2["trust"] < 0.55


def test_report_rate_limit(eng):
    for _ in range(3):
        eng.submit_report(rtype="sighting", channel="ussd", phone="+2348011110005", community="Ugba")
    with pytest.raises(PermissionError):
        eng.submit_report(rtype="sighting", channel="ussd", phone="+2348011110005", community="Ugba")


def test_escalation_when_nobody_acknowledges(eng):
    drive(eng, "COLLAR-01", plan_paths(eng.layers)["COLLAR-01"])
    case = next(c for c in eng.cases.cases if c["key"] == "herd:H1")
    assert case["level"] == "warning"
    eng.test_clock.t += timedelta(minutes=45)  # warning SLA is 30 minutes
    eng.tick()
    assert case["level"] == "critical" and case["escalations"] == 1
    assert any(m["to"].startswith("NSCDC Agro Rangers") for m in eng.notifier.sent)


def test_sms_ack_only_from_assigned_responder(eng):
    drive(eng, "COLLAR-01", plan_paths(eng.layers)["COLLAR-01"])
    case = next(c for c in eng.cases.cases if c["key"] == "herd:H1")
    assert "not registered" in eng.sms_inbound("+2340000000000", f"ACK {case['id']}")
    assert "acknowledged" in eng.sms_inbound("+2348060000201", f"ACK {case['id']}")
    assert case["status"] == "acknowledged"


def test_identity_reveal_is_restricted_and_audited(eng):
    r = eng.submit_report(rtype="threat", channel="ussd", phone="+2348011110006", community="Ugba")
    with pytest.raises(PermissionError):
        eng.reveal_identity(r["id"], {"username": "guma_mediator", "role": "mediator"}, "want to call them")
    phone = eng.reveal_identity(r["id"], {"username": "protection", "role": "protection_officer"},
                                "Reporter asked for protection after threats")
    assert phone == "+2348011110006"
    actions = [a["action"] for a in eng.audit.recent()]
    assert "identity_reveal_denied" in actions and "identity_revealed" in actions


def test_ussd_full_flow(eng):
    assert eng.ussd("+2348011110007", "").startswith("CON AgroPeace")
    assert "Select LGA" in eng.ussd("+2348011110007", "1")
    lgas = sorted({c["properties"]["lga"] for c in eng.layers.communities})
    g = str(lgas.index("Guma") + 1)
    assert "Yelwata" in eng.ussd("+2348011110007", f"1*{g}")
    assert "Send report" in eng.ussd("+2348011110007", f"1*{g}*1")
    end = eng.ussd("+2348011110007", f"1*{g}*1*1")
    assert end.startswith("END Report AP-")
    risk = eng.ussd("+2348011110007", f"4*{g}*1")
    assert risk.startswith("END Risk at")


def test_public_view_is_coarse(eng):
    drive(eng, "COLLAR-01", plan_paths(eng.layers)["COLLAR-01"][:4])
    pub = eng.snapshot(None)["herds"][0]
    staff = eng.snapshot({"username": "c", "role": "coordinator", "lgas": ["*"]})["herds"][0]
    assert "forecast" not in pub and "forecast" in staff
    assert (pub["lat"], pub["lon"]) != (staff["lat"], staff["lon"])


def test_mediator_sees_only_own_lga(eng):
    drive(eng, "COLLAR-01", plan_paths(eng.layers)["COLLAR-01"])  # Guma
    drive(eng, "COLLAR-04", plan_paths(eng.layers)["COLLAR-04"])  # Logo
    snap = eng.snapshot({"username": "guma_mediator", "role": "mediator", "lgas": ["Guma"]})
    assert snap["cases"] and all(c["lga"] == "Guma" for c in snap["cases"])


def test_risk_higher_near_hotspot_with_herd(eng):
    before = eng.community_risk("Yelwata")["score"]
    drive(eng, "COLLAR-01", plan_paths(eng.layers)["COLLAR-01"])
    after = eng.community_risk("Yelwata")["score"]
    quiet = eng.community_risk("Abinsi")["score"]
    assert after > before > quiet


# ---------------------------------------------------------------- web

def test_web_auth_roles_and_csrf(eng):
    c = create_app(eng).test_client()
    assert c.get("/api/state").get_json()["role"] == "public"
    assert c.post("/login", json={"username": "coordinator", "password": "nope"}).status_code == 401
    assert c.post("/login", json={"username": "coordinator", "password": "peace-coord-2026"}).status_code == 200
    assert c.get("/api/state").get_json()["role"] == "coordinator"
    drive(eng, "COLLAR-01", plan_paths(eng.layers)["COLLAR-01"])
    cid = eng.cases.cases[0]["id"]
    assert c.post(f"/api/cases/{cid}/ack").status_code == 403  # no CSRF header
    assert c.post(f"/api/cases/{cid}/ack", headers={"X-CSRF": "1"}).status_code == 200


def test_web_tracker_rejects_forgery(eng):
    c = create_app(eng).test_client()
    body = {"device_id": "COLLAR-01", "lat": 7.9, "lon": 8.8, "ts": eng.test_clock.t.timestamp(), "nonce": "q"}
    assert c.post("/api/tracker", json=body, headers={"X-Signature": "00"}).status_code == 401
    good_sig = sign_message(device_key(MASTER, "COLLAR-01"), body)
    assert c.post("/api/tracker", json=body, headers={"X-Signature": good_sig}).status_code == 200


def test_ussd_endpoint_needs_secret_token(eng, monkeypatch):
    monkeypatch.setenv("AGROPEACE_USSD_TOKEN", "secret-token-123")
    c = create_app(eng).test_client()
    assert c.post("/ussd/wrong", data={"phoneNumber": "+234", "text": ""}).status_code == 404
    r = c.post("/ussd/secret-token-123", data={"phoneNumber": "+234801", "text": ""})
    assert r.status_code == 200 and r.data.decode().startswith("CON")
