# CMP 468 Projects: Setup and Run Guide

_UniGuard (question 1) and AgroPeace (question 2)_

This guide takes you from a bare laptop to both projects running, tested and ready to present. Follow the parts in order the first time. Windows commands come first; macOS and Linux differences are noted where they matter.

You need about 45 minutes and an internet connection for Part A and the install steps. After that, everything runs offline.

## Part A. One-time setup

### A1. Check your computer

1. Windows 10 or 11, macOS 12 or newer, or a recent Linux. At least 4 GB RAM and 1 GB of free disk space.
2. Keep the project outside the Documents, Desktop and OneDrive folders. Windows Defender's ransomware protection can block the UniGuard ransomware simulation inside those folders. C:\CMP-468 is a good location.
### A2. Install Python

1. Go to https://www.python.org/downloads/ and download Python 3.12 (any version from 3.10 up works).
2. Run the installer. On the first screen, tick "Add python.exe to PATH" at the bottom, then click Install Now.
3. Open Command Prompt: press the Windows key, type cmd, press Enter. Check the install:

```
python --version
```

You should see Python 3.12.x (or 3.10 or newer). If Windows says python is not recognized, run the installer again and tick the PATH box, or type py instead of python in every command in this guide.

> **Note:** macOS: install from python.org, then use python3 instead of python. Linux: sudo apt install python3 python3-venv python3-pip.

### A3. Get the project files

Option 1, no Git needed:

1. Open https://github.com/Mikisivas/CMP-468 and sign in.
2. Click the branch drop-down (it says main) and choose claude/zen-carson-5k0uup. If you have already merged that branch into main, stay on main.
3. Click the green Code button, then Download ZIP.
4. Right-click the ZIP, choose Extract All, and extract to C:\ so you end up with a folder such as C:\CMP-468-claude-zen-carson-5k0uup. Rename it to C:\CMP-468.
Option 2, with Git (install from https://git-scm.com first):

```
cd C:\
git clone -b claude/zen-carson-5k0uup https://github.com/Mikisivas/CMP-468.git
```

Either way, you should now have C:\CMP-468 containing project1-uniguard, project2-agropeace and tools.

### A4. Optional: a code editor

1. Install Visual Studio Code from https://code.visualstudio.com if you want to read the code comfortably or show it to the panel. File > Open Folder > C:\CMP-468.
## Part B. Project 1: UniGuard

### B1. Create its Python environment (once)

1. Open Command Prompt and go to the project folder:

```
cd C:\CMP-468\project1-uniguard
```

2. Create a private Python environment for the project:

```
python -m venv .venv
```

3. Switch it on. You must do this in every new window you open for this project:

```
Command Prompt:   .venv\Scripts\activate
PowerShell:       .venv\Scripts\Activate.ps1
macOS / Linux:    source .venv/bin/activate
```

Your prompt now starts with (.venv). If PowerShell refuses to run Activate.ps1, run this once, answer Y, and try again:

```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

4. Install the libraries (cryptography, psutil, Flask, pytest). Takes one to two minutes:

```
pip install -r requirements.txt
```

### B2. Run the tests

```
python -m pytest -q
```

Expected result: 23 passed. This proves encryption, backup, restore, ransomware recovery, tamper detection and dashboard security all work on your machine.

### B3. Narrated demo (the safe fallback)

```
python demo/run_demo.py
```

It tells the whole story in seven scenes. Press Enter between scenes. Add --fast to run without pauses. Use this if anything goes wrong with the live dashboard during your presentation.

### B4. Live dashboard demo

1. In your first window (with .venv active), start everything with one command:

```
python demo/live.py --fresh
```

This creates the sample university data, the encrypted backup repository and a stand-in Student Portal, then starts UniGuard and opens http://127.0.0.1:8080 in your browser. If Windows Firewall asks, click Allow; the demo only uses your own computer.

2. Log in to the dashboard with the password: cmp468
3. Open a second Command Prompt, go to the folder and switch the environment on:

```
cd C:\CMP-468\project1-uniguard
.venv\Scripts\activate
```

4. Stage the incidents one at a time, waiting a few seconds after each so the dashboard updates:

| Command | What to point at |
| --- | --- |
| `python demo/simulate_incident.py power-off` | Power card turns amber (ON BATTERY); a power-loss snapshot appears |
| `python demo/simulate_incident.py battery-low` | Critical alert: shut servers down cleanly |
| `python demo/simulate_incident.py power-on` | Mains power restored notice |
| `python demo/simulate_incident.py portal-down` | Student Portal row turns DOWN (HTTP 503) |
| `python demo/simulate_incident.py portal-up` | Portal back UP, with downtime in the audit trail |
| `python demo/simulate_incident.py tamper` | Red RECORDS ALERT banner: a CMP468 grade changed outside the approved window |
| `python demo/simulate_incident.py ransomware` | Incident row: files restored, files quarantined, recovery time in seconds |

5. Click Verify backups on the dashboard. It decrypts and checks every stored chunk.
6. To show the audit trail and its hash-chain check from the command line, set the demo passphrase in the second window first:

```
Command Prompt:   set UNIGUARD_PASSPHRASE=demo-passphrase-CMP468-2026
PowerShell:       $env:UNIGUARD_PASSPHRASE="demo-passphrase-CMP468-2026"
macOS / Linux:    export UNIGUARD_PASSPHRASE=demo-passphrase-CMP468-2026

python -m uniguard -c demo/demo_config.json audit
python -m uniguard -c demo/demo_config.json snapshots
```

7. Stop the demo with Ctrl+C in the first window. Next time, python demo/live.py --fresh starts clean; without --fresh it keeps the previous state.
### B5. Optional: reproduce the benchmark in the report

```
python docs/benchmark.py 2000 100
```

Creates 2,000 files (about 195 MB) in a temporary folder and prints backup, restore and ransomware-recovery times. Your numbers will differ from the report's with your hardware; mention that if the panel asks.

## Part C. Project 2: AgroPeace

### C1. Create its Python environment (once)

```
cd C:\CMP-468\project2-agropeace
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Use the PowerShell or macOS/Linux activate line from B1 if you are not in Command Prompt.

### C2. Run the tests

```
python -m pytest -q
```

Expected result: 30 passed, in about 20 seconds.

### C3. Narrated demo (the safe fallback)

```
python demo/run_demo.py
```

Six scenes: morning risk picture, herd H1 heading for Yelwata farms, escalation, SMS acknowledgement, rumour versus corroborated reports, and attacks on the system being blocked.

### C4. Live map demo

1. In your first window (with .venv active):

```
python demo/live.py --fresh
```

Your browser opens http://127.0.0.1:8090. You first see the public view: community risk levels only, with no herds and no cases. That is deliberate; say so.

2. Sign in on the right as coordinator, password peace-coord-2026. Herds, cases and the security panel appear.
3. Open a second window, go to the folder, switch the environment on, and start the GPS collars:

```
cd C:\CMP-468\project2-agropeace
.venv\Scripts\activate
python demo/simulator.py
```

The collars send a signed position every 2 seconds for about 2 minutes (add --fast for about 30 seconds). Watch herd H1: its dashed red forecast line reaches a Yelwata farm, an early-warning case opens, then H1 enters the farm and the case turns to WARNING.

4. Try the USSD phone panel: click Dial *347*468#, then send these replies one at a time: 1 (cattle on my farm), 2 (Guma), 1 (Yelwata), 1 (yes, send). Point at the new report's trust score and the reasons listed under it.
5. On a case, click Acknowledge, then pick herd_rerouted and click Resolve. Point at the audit chain status in the Security panel.
6. Show least privilege: sign out, sign in as guma_mediator / guma-mediator-2026 (sees only Guma), then as protection / protect-2026 (can reveal an informant's number, with a written reason that is logged).
7. To jump straight to the Yelwata area, open http://127.0.0.1:8090/#7.86,8.81,11.25
8. Stop with Ctrl+C in the first window. python demo/live.py --fresh clears cases and reports next time.

> **Note:** Without internet the map background is plain, because street tiles come from OpenStreetMap. Farms, reserves, routes, the river and the risk grid still draw, because the map library is bundled with the project.

## Part D. The documents

1. Open each report (project1-uniguard/docs/UniGuard_Report.docx and project2-agropeace/docs/AgroPeace_Report.docx) in Microsoft Word.
2. When Word asks to update fields, click Yes. This fills in the table of contents. If it does not ask: right-click the table of contents > Update Field > Update entire table.
3. Replace the placeholders on the cover: [UNIVERSITY NAME], [FACULTY NAME], [YOUR FULL NAME], [MATRIC NUMBER], [LECTURER'S NAME], [MONTH, YEAR].
4. If your department wants PDF: File > Save As > PDF.
5. Open each presentation in PowerPoint. Put your name and matric number on slide 1. Your talking points are in the speaker notes under each slide (View > Notes). Use Slide Show > Use Presenter View so only you see the notes.
6. Print or keep open the two Defense Q&A documents. The last pages hold the demo runbook and the numbers to remember.

> **Note:** Changing the text inside the Word and PowerPoint files directly is fine. The docs/build_*.js scripts only matter if you want to regenerate the files; that needs Node.js and is described in the main README.

## Part E. The day before you present

1. Set everything up on the laptop you will present with, not a different one. The .venv folder does not move between computers; copy the project folder and repeat B1 and C1 on the new laptop.
2. Turn off Wi-Fi and run both test suites and both live demos once. This proves they work offline.
3. Charge the laptop fully. The power-loss scenes are simulated; your laptop's real power does not matter.
4. Decide your window layout: browser on one side, the two command windows on the other. Set browser zoom to 125% so the panel can read the dashboard.
5. Keep python demo/run_demo.py --fast ready in a window as a fallback for each project.
## Part F. Troubleshooting

| Problem | Fix |
| --- | --- |
| 'python' is not recognized | Reinstall Python with "Add python.exe to PATH" ticked, or use py instead of python. |
| PowerShell: Activate.ps1 cannot be loaded | Run Set-ExecutionPolicy -Scope CurrentUser RemoteSigned, answer Y, try again. Or use Command Prompt. |
| No module named ... when running a demo | The environment is not active in that window. Run the activate command from B1 or C1 first. |
| pip install fails | Check the internet connection, run python -m pip install --upgrade pip, then repeat the install. |
| Address already in use / port busy | Another copy is still running. Press Ctrl+C in its window, or close it. You can also change "port" under "dashboard" in demo/demo_config.json. |
| The browser did not open | Type the address yourself: http://127.0.0.1:8080 for UniGuard, http://127.0.0.1:8090 for AgroPeace. |
| UniGuard: "Demo sandbox not found" | Start python demo/live.py first; it creates the sample data. |
| UniGuard: "wrong passphrase" | You set a different UNIGUARD_PASSPHRASE than the one the repository was created with. Run python demo/live.py --fresh. |
| Ransomware simulation blocked by Windows Defender | Move the project out of Documents, Desktop or OneDrive to C:\CMP-468 (Controlled Folder Access). |
| AgroPeace simulator: connection refused | Start python demo/live.py in the first window before running the simulator. |
| Map background is blank | Normal without internet. All project layers still draw. |

## Part G. Taking it beyond the demo

If your lecturer asks how a university or agency would run these for real, these are the steps.

### UniGuard on a real server

1. Use a Linux server with a second disk (or network storage) for backups, and a second site or cloud bucket for the offsite copy.
2. Copy demo/demo_config.json to /etc/uniguard/config.json and set source (the file share to protect), repository (the backup disk), offsite.path, services (the real portal and database addresses), power (source: nut for a real UPS) and protected_paths (the results folders and the Senate-approved windows).
3. Choose a long passphrase, store it in the server's environment (not in the config), and seal a paper copy with the Registrar and the Director of ICT.
4. Add SMS alerts: create an Africa's Talking or Termii account and add an alerts entry with type africastalking or termii. Put the API key in the environment and reference it as env:NAME in the config.
5. Initialise once, then run UniGuard as a service that starts on boot, behind an HTTPS reverse proxy (for example Nginx) if the dashboard is used from other machines:

```
python -m uniguard -c /etc/uniguard/config.json init
python -m uniguard -c /etc/uniguard/config.json run --dashboard
```

6. Test a restore every month: python -m uniguard -c /etc/uniguard/config.json restore latest /tmp/restore-test
### AgroPeace in the field

1. Replace data/benue_layers.geojson with surveyed farm boundaries, gazetted reserves and stock routes (the same GeoJSON format), and data/incidents_history.json with ACLED records.
2. Register real collars in the devices section, set a strong AGROPEACE_MASTER_KEY in the server environment, and load each collar's key onto the device.
3. Register responders with their phone numbers and languages. Connect a USSD code and SMS sender ID through a gateway, pointing its callback to https://your-server/ussd/<secret token> and /sms/<secret token>.
4. Replace the demo staff passwords: generate new hashes with Python (from werkzeug.security import generate_password_hash) and put them in users.
5. Pilot in one LGA for a season with herder and farmer associations, and have native speakers check all message templates before use.
