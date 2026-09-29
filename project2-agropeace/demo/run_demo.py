"""Narrated, self-contained demonstration (no browser needed). Simulated time
runs ten minutes per GPS fix so a whole morning plays out in seconds.

    python demo/run_demo.py          # pauses between scenes
    python demo/run_demo.py --fast
"""

import os
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import generate_data  # noqa: E402
from agropeace.engine import Engine, load_config  # noqa: E402
from agropeace.security import AuthError, sign_message  # noqa: E402
from simulator import plan_paths, signed_fix  # noqa: E402

FAST = "--fast" in sys.argv
B, E = ("\033[1m", "\033[0m") if sys.stdout.isatty() else ("", "")
MASTER = b"demo-master-key-for-narrated-run!"


class Clock:
    t = datetime(2026, 9, 29, 6, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.t


def scene(title):
    print(f"\n{B}{'=' * 72}\n{title}\n{'=' * 72}{E}")
    if not FAST:
        input("Press Enter to continue...")


def show_sms(eng, since):
    for m in eng.notifier.sent[since:]:
        print(f"  SMS to {m['to']}:\n     {m['text']}")
    return len(eng.notifier.sent)


def main():
    if not (HERE.parent / "data" / "benue_layers.geojson").exists():
        generate_data.main()
    cfg = load_config(HERE / "demo_config.json")
    cfg["state_dir"] = str(HERE / "sandbox" / "narrated")
    shutil.rmtree(cfg["state_dir"], ignore_errors=True)
    clock = Clock()
    eng = Engine(cfg, MASTER, clock=clock)
    paths = plan_paths(eng.layers)
    sent = 0

    scene("1. Morning risk picture for Benue (harvest season, crops in the field)")
    for c in eng.community[:5]:
        print(f"  {c['community']:<20}{c['lga']:<10}{c['level'].upper():<10}{c['score']:.2f}  {', '.join(c['drivers'])}")

    scene("2. Herd H1 (140 cattle) treks toward Yelwata farms. GPS collars report every 10 minutes")
    h1 = paths["COLLAR-01"]
    entered = False
    for i, (lat, lon) in enumerate(h1):
        if entered:
            break
        clock.t += timedelta(minutes=10)
        for dev in ("COLLAR-01", "COLLAR-02"):
            p = paths[dev][min(i, len(paths[dev]) - 1)] if dev != "COLLAR-01" else (lat, lon)
            body, sig = signed_fix(MASTER, dev, *p, clock.t.timestamp())
            r = eng.ingest_position(body, sig)
            if r["events"]:
                h = eng.tracker.herds[dev]
                print(f"  {clock.t:%H:%M} {h.herd_id}: {', '.join(r['events'])} "
                      f"(speed {h.speed_kmh:.1f} km/h, zone {h.zone})")
                sent = show_sms(eng, sent)
                entered = entered or "incursion" in r["events"]
    case = next(c for c in eng.cases.cases if c["key"] == "herd:H1")
    print(f"\n  Case {case['id']} [{case['level'].upper()}] {case['title']}")
    print(f"  Reroute: {case['reroute']['reserve']}, {case['reroute']['distance_km']} km {case['reroute']['direction']}")

    scene("3. Nobody acknowledges within 30 minutes: automatic escalation")
    clock.t += timedelta(minutes=35)
    eng.tick()
    print(f"  {clock.t:%H:%M} case {case['id']} is now {case['level'].upper()}")
    sent = show_sms(eng, sent)

    scene("4. Guma Peace Committee replies 'ACK' by plain SMS, then resolves the case")
    clock.t += timedelta(minutes=4)
    print(f"  {clock.t:%H:%M} reply:", eng.sms_inbound("+2348060000201", f"ACK {case['id']}"))
    clock.t += timedelta(minutes=50)
    eng.resolve(case["id"], "guma_mediator", "herd_rerouted", "Herd moved back to route R2 with youth leaders present")
    print(f"  {case['id']} resolved: {case['outcome']}; acknowledged {case['response_min']:.0f} min after "
          f"the first early warning")

    scene("5. A single anonymous rumour vs corroborated reports")
    r1 = eng.submit_report(rtype="threat", channel="web_anonymous", phone="+2348011110001", community="Naka",
                           text="They are coming tonight")
    print(f"  {r1['id']} rumour at Naka: {r1['status'].upper()} (trust {r1['trust']}). Not broadcast.")
    a = eng.ussd("+2348011110002", "")
    print("  USSD screen:\n    " + a.replace("\n", "\n    "))
    lgas = sorted({c['properties']['lga'] for c in eng.layers.communities})
    g = str(lgas.index("Logo") + 1)
    out = eng.ussd("+2348011110002", f"1*{g}*1*1")
    print("  USSD result:", out)
    eng.submit_report(rtype="cattle_on_farm", channel="ussd", phone="+2348011110003", community="Ugba")
    r = eng.reports.reports[-2]
    print(f"  {r['id']} after a second, independent report: {r['status'].upper()} (trust {r['trust']})")
    print("  Why:", "; ".join(r["why"]))

    scene("6. Attacks on the system itself")
    body = {"device_id": "COLLAR-01", "lat": 7.9, "lon": 8.8, "ts": clock.t.timestamp(), "nonce": "fake"}
    for label, sig in [("forged signature", sign_message(b"attacker key", body))]:
        try:
            eng.ingest_position(body, sig)
        except AuthError as exc:
            print(f"  {label}: REJECTED ({exc})")
    good, gsig = signed_fix(MASTER, "COLLAR-02", *paths["COLLAR-02"][0], clock.t.timestamp())
    eng.ingest_position(good, gsig)
    try:
        eng.ingest_position(good, gsig)
    except AuthError as exc:
        print(f"  replayed genuine message: REJECTED ({exc})")
    try:
        eng.reveal_identity(r1["id"], {"username": "guma_mediator", "role": "mediator"}, "curious who sent it")
    except PermissionError as exc:
        print(f"  mediator tries to unmask an informant: DENIED ({exc})")
    for _ in range(3):
        try:
            eng.submit_report(rtype="sighting", channel="ussd", phone="+2348019999999", community="Ugba")
        except PermissionError:
            pass
    try:
        eng.submit_report(rtype="sighting", channel="ussd", phone="+2348019999999", community="Ugba")
    except PermissionError as exc:
        print(f"  one number floods reports: BLOCKED ({exc})")
    print("  Audit chain:", eng.audit.verify())
    eng.audit._db.execute("UPDATE audit SET actor='nobody' WHERE action='identity_reveal_denied'")
    eng.audit._db.commit()
    print("  After someone edits the audit log:", eng.audit.verify())


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    main()
