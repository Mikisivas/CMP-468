"""Stage incidents against the DEMO sandbox so you can show UniGuard reacting.

It only runs on a folder created by seed_data.py (it checks for the sandbox
marker file) and it never touches anything else.

    python demo/simulate_incident.py ransomware   # scramble files, drop a note
    python demo/simulate_incident.py tamper       # change one student's grade
    python demo/simulate_incident.py power-off    # grid goes off, inverter takes over
    python demo/simulate_incident.py battery-low  # inverter battery nearly flat
    python demo/simulate_incident.py power-on     # grid restored
"""

import csv
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SANDBOX = HERE / "sandbox"
DATA = SANDBOX / "university_data"
MARKER = ".uniguard-demo-sandbox"


def require_sandbox() -> None:
    if not (DATA / MARKER).exists():
        raise SystemExit("Demo sandbox not found. Run: python demo/seed_data.py")


def ransomware() -> None:
    """Simulated ransomware: overwrite files with random bytes and rename them.

    No real cipher and no key: the originals are gone unless UniGuard restores them.
    """
    require_sandbox()
    victims = [p for p in DATA.rglob("*") if p.is_file() and p.name != MARKER]
    for p in victims[: int(len(victims) * 0.7)]:
        size = max(p.stat().st_size, 256)
        p.write_bytes(os.urandom(size))
        p.rename(p.with_name(p.name + ".locked"))
    (DATA / "HOW_TO_RECOVER_YOUR_FILES.txt").write_text(
        "SIMULATION. Your files are encrypted. Pay 2 BTC to recover them.\n")
    print(f"[simulation] scrambled {int(len(victims) * 0.7)} of {len(victims)} files and dropped a ransom note")


def tamper() -> None:
    """An insider quietly upgrades one student's CMP468 score after Senate approval."""
    require_sandbox()
    path = DATA / "registry" / "results" / "CMP468_2025_2026_second_semester.csv"
    rows = list(csv.reader(open(path, newline="")))
    row = next(r for r in rows[1:] if r[5] in ("F", "E", "D"))
    before = f"{row[4]} ({row[5]})"
    row[2], row[3], row[4], row[5], row[6] = "28", "60", "88", "A", "5"
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"[simulation] {row[0]}: CMP468 score changed from {before} to 88 (A)")


def power(state: str) -> None:
    (SANDBOX / "ups_status.txt").write_text(state + "\n")
    print(f"[simulation] UPS status now: {state}")


ACTIONS = {
    "ransomware": ransomware,
    "tamper": tamper,
    "power-off": lambda: power("BATTERY 78"),
    "battery-low": lambda: power("BATTERY 20"),
    "power-on": lambda: power("MAINS 100"),
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ACTIONS:
        raise SystemExit(__doc__)
    ACTIONS[sys.argv[1]]()
