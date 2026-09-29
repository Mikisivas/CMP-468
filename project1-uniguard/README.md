# UniGuard

Automated monitoring, backup and recovery for university digital infrastructure.
Built for the conditions of a Nigerian campus: unstable power, costly bandwidth,
small ICT budgets, and the risk of insiders altering results.

CMP 468 (Computer Security) project, question 1.

## What it does

| Area | Feature |
|---|---|
| Backup | Encrypted (AES-256-GCM), deduplicated, incremental snapshots. Each snapshot restores on its own. |
| Keys | Passphrase stretched with scrypt; HKDF splits it into separate encryption and naming keys. |
| Offsite | Copies only ciphertext to a second site in a night window, with a bandwidth cap. Resumes after link failure. |
| Retention | Grandfather-father-son. Always keeps the last clean snapshot and any pinned ones. |
| Recovery | Full, folder or single-file restore. Every restored file is SHA-256 verified. |
| Ransomware | Detects mass change, high entropy, ransom extensions and notes. Freezes backups, quarantines evidence, restores, verifies, and times the recovery. |
| Records integrity | Result folders may only change inside Senate-approved windows. Other changes raise a critical alert and later backups are marked SUSPECT. |
| Power | Reads UPS state (NUT, psutil or a status file). Takes an emergency backup when mains power fails. Warns before the battery dies. |
| Services | HTTP and TCP checks for the portal, result database, LMS, email. Alerts on down and on recovery with downtime. |
| Alerts | Console, SMS (Africa's Talking, Termii), email, webhook. Cooldown stops alert floods. |
| Audit | Hash-chained SQLite log. Editing or deleting any past event is detected. |
| Dashboard | Password login with lockout, CSRF protection, security headers. |

## Install

```
pip install -r requirements.txt
```

## Quick demo (one command, narrated)

```
python demo/run_demo.py          # pauses between scenes
python demo/run_demo.py --fast
```

## Live demo with the dashboard (for the presentation)

Terminal 1 (one command sets up demo data, the encrypted repository and a
stand-in Student Portal, then opens the dashboard; password `cmp468`):
```
python demo/live.py --fresh
```

Terminal 2, one incident at a time:
```
python demo/simulate_incident.py power-off      # grid fails, inverter takes over
python demo/simulate_incident.py battery-low
python demo/simulate_incident.py power-on
python demo/simulate_incident.py portal-down    # Student Portal answers HTTP 503
python demo/simulate_incident.py portal-up
python demo/simulate_incident.py tamper         # insider changes a grade
python demo/simulate_incident.py ransomware     # watch it recover in seconds
```

Full walkthrough: [../SETUP_GUIDE.md](../SETUP_GUIDE.md).

## Tests

```
python -m pytest -q
```

## Commands

```
python -m uniguard -c CONFIG init | backup | snapshots | verify | sync | audit
python -m uniguard -c CONFIG restore latest ./restore_here [registry/results]
python -m uniguard -c CONFIG diff
python -m uniguard -c CONFIG run [--dashboard]
```

## Layout

```
uniguard/crypto.py      key derivation, AES-GCM, keyed object ids
uniguard/repository.py  encrypted deduplicated store, verify, replicate
uniguard/backup.py      backup, retention, restore, diff
uniguard/monitor.py     host, services, power, integrity and ransomware detection
uniguard/alerts.py      alert channels and alert manager
uniguard/audit.py       hash-chained audit log and metrics
uniguard/engine.py      scheduler and automatic incident response
uniguard/dashboard.py   web dashboard
demo/                   sample data, incident simulator, fake portal, narrated demo
tests/                  23 automated tests
```
