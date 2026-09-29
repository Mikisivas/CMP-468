"""One-command narrated demo. Use it as a rehearsal, or as a backup plan if the
live dashboard demo misbehaves in front of the panel.

    python demo/run_demo.py            # full story, pauses between scenes
    python demo/run_demo.py --fast     # no pauses
"""

import os
import shutil
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import fake_portal  # noqa: E402
import seed_data  # noqa: E402
import simulate_incident  # noqa: E402
from uniguard.config import load_config  # noqa: E402
from uniguard.engine import UniGuard  # noqa: E402
from uniguard.repository import Repository  # noqa: E402

FAST = "--fast" in sys.argv
BOLD, END = ("\033[1m", "\033[0m") if sys.stdout.isatty() else ("", "")


def scene(title: str) -> None:
    print(f"\n{BOLD}{'=' * 70}\n{title}\n{'=' * 70}{END}")
    if not FAST:
        input("Press Enter to continue...")


def main() -> None:
    os.environ.setdefault("UNIGUARD_PASSPHRASE", "demo-passphrase-CMP468-2026")
    if (HERE / "sandbox").exists():
        shutil.rmtree(HERE / "sandbox", onerror=lambda f, p, e: (os.chmod(p, 0o700), f(p)))

    scene("1. A university file server with results, records, fees and payroll")
    seed_data.main()
    cfg = load_config(HERE / "demo_config.json")
    Repository.init(cfg["repository"], os.environ["UNIGUARD_PASSPHRASE"])
    portal = fake_portal.make_server()
    threading.Thread(target=portal.serve_forever, daemon=True).start()

    eng = UniGuard(cfg, os.environ["UNIGUARD_PASSPHRASE"])
    m = eng.run_backup(tag="initial")
    print(f"First backup: {m['stats']['files']} files, encrypted with AES-256-GCM, in {m['stats']['duration_s']}s")
    eng.monitor_tick()
    print("Services:", ", ".join(f"{s['name']}={'UP' if s['up'] else 'DOWN'}" for s in eng.services.values()))

    scene("2. Incremental backup: only changed data is stored (saves disk and bandwidth)")
    notes = cfg["source"] + "/departments/computer_science/lecture_notes/CMP468_week10.md"
    Path(notes).write_text("# Week 10: Revision\n")
    m = eng.run_backup(tag="scheduled")
    s = m["stats"]
    print(f"Second backup: {s['files_new']} new file, {s['files_unchanged']} unchanged, "
          f"only {s['bytes_stored']} bytes written")
    res = eng.run_replication(force=True)
    print(f"Offsite copy to partner campus: {res['files_copied']} encrypted files, {res['bytes_sent'] / 1024:.0f} KiB")

    scene("3. NEPA takes light: the server falls back to the inverter")
    simulate_incident.power("BATTERY 78")
    eng.monitor_tick()
    simulate_incident.power("BATTERY 20")
    eng.monitor_tick()
    simulate_incident.power("MAINS 100")
    eng.monitor_tick()

    scene("4. The Student Portal goes down during course registration")
    portal.shutdown()
    portal.server_close()
    eng.monitor_tick()

    scene("5. An insider changes a student's CMP468 grade after Senate approval")
    simulate_incident.tamper()
    eng.monitor_tick()
    for rel in list(eng.integrity.scan()["modified"]):
        pass
    eng.run_backup(tag="scheduled")
    print("Backup taken while tampering is open is marked SUSPECT, so recovery never uses it.")
    base = eng.repo.latest_snapshot(clean_only=True)
    from uniguard.backup import restore_snapshot
    r = restore_snapshot(eng.repo, base["id"], cfg["source"], ["registry/results"])
    print(f"Registrar restores the approved results from the last clean snapshot: {r['restored']} files verified.")
    eng.open_tamper.clear()

    scene("6. Ransomware hits the file server")
    simulate_incident.ransomware()
    t0 = time.monotonic()
    eng.monitor_tick()
    inc = eng.incidents[-1]
    print(f"\nIncident {inc['id']}: {inc['status'].upper()}")
    print(f"  files restored and SHA-256 verified : {inc['files_restored']}")
    print(f"  malicious files quarantined         : {inc['files_quarantined']}")
    print(f"  time from detection to recovery     : {inc['rto_seconds']} s (end-to-end {time.monotonic() - t0:.1f} s)")
    print(f"  evidence kept in                    : {inc['quarantine']}")

    scene("7. Proof: backups verify, and the audit trail catches log tampering")
    v = eng.repo.verify()
    print(f"Backup verification: {'OK' if v['ok'] else 'FAILED'} ({v['objects_checked']} objects decrypted)")
    print("Audit chain:", eng.audit.verify_chain())
    eng.audit._db.execute("UPDATE events SET message='nothing happened' WHERE kind='alert.tamper'")
    eng.audit._db.commit()
    print("After an insider edits the log:", eng.audit.verify_chain())
    print(f"\nSMS alerts that would have gone to the ICT Director: {HERE / 'sandbox' / 'sms_outbox.jsonl'}")
    for line in open(HERE / "sandbox" / "sms_outbox.jsonl"):
        import json
        print("  SMS:", json.loads(line)["sms"])


if __name__ == "__main__":
    main()
