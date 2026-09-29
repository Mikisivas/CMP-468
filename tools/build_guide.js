// Builds SETUP_GUIDE.docx and SETUP_GUIDE.md from one source.
//   NODE_PATH=<folder with docx> node tools/build_guide.js
const fs = require("fs");
const path = require("path");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, LevelFormat, ShadingType,
  Table, TableRow, TableCell, WidthType, BorderStyle, Footer, PageNumber } = require("docx");

// Block types: ["h1", text] ["h2", text] ["p", text] ["step", text] ["code", [lines]] ["tip", text] ["table", header, rows]
const G = [];
const h1 = (t) => G.push(["h1", t]);
const h2 = (t) => G.push(["h2", t]);
const p = (t) => G.push(["p", t]);
const step = (t) => G.push(["step", t]);
const code = (...l) => G.push(["code", l]);
const tip = (t) => G.push(["tip", t]);
const table = (h, r) => G.push(["table", h, r]);

// ---------------------------------------------------------------- content
p("This guide takes you from a bare laptop to both projects running, tested and ready to present. Follow the parts in order the first time. Windows commands come first; macOS and Linux differences are noted where they matter.");
p("You need about 45 minutes and an internet connection for Part A and the install steps. After that, everything runs offline.");

h1("Part A. One-time setup");
h2("A1. Check your computer");
step("Windows 10 or 11, macOS 12 or newer, or a recent Linux. At least 4 GB RAM and 1 GB of free disk space.");
step("Keep the project outside the Documents, Desktop and OneDrive folders. Windows Defender's ransomware protection can block the UniGuard ransomware simulation inside those folders. C:\\CMP-468 is a good location.");

h2("A2. Install Python");
step("Go to https://www.python.org/downloads/ and download Python 3.12 (any version from 3.10 up works).");
step("Run the installer. On the first screen, tick \"Add python.exe to PATH\" at the bottom, then click Install Now.");
step("Open Command Prompt: press the Windows key, type cmd, press Enter. Check the install:");
code("python --version");
p("You should see Python 3.12.x (or 3.10 or newer). If Windows says python is not recognized, run the installer again and tick the PATH box, or type py instead of python in every command in this guide.");
tip("macOS: install from python.org, then use python3 instead of python. Linux: sudo apt install python3 python3-venv python3-pip.");

h2("A3. Get the project files");
p("Option 1, no Git needed:");
step("Open https://github.com/Mikisivas/CMP-468 and sign in.");
step("Click the branch drop-down (it says main) and choose claude/zen-carson-5k0uup. If you have already merged that branch into main, stay on main.");
step("Click the green Code button, then Download ZIP.");
step("Right-click the ZIP, choose Extract All, and extract to C:\\ so you end up with a folder such as C:\\CMP-468-claude-zen-carson-5k0uup. Rename it to C:\\CMP-468.");
p("Option 2, with Git (install from https://git-scm.com first):");
code("cd C:\\", "git clone -b claude/zen-carson-5k0uup https://github.com/Mikisivas/CMP-468.git");
p("Either way, you should now have C:\\CMP-468 containing project1-uniguard, project2-agropeace and tools.");

h2("A4. Optional: a code editor");
step("Install Visual Studio Code from https://code.visualstudio.com if you want to read the code comfortably or show it to the panel. File > Open Folder > C:\\CMP-468.");

h1("Part B. Project 1: UniGuard");
h2("B1. Create its Python environment (once)");
step("Open Command Prompt and go to the project folder:");
code("cd C:\\CMP-468\\project1-uniguard");
step("Create a private Python environment for the project:");
code("python -m venv .venv");
step("Switch it on. You must do this in every new window you open for this project:");
code("Command Prompt:   .venv\\Scripts\\activate", "PowerShell:       .venv\\Scripts\\Activate.ps1", "macOS / Linux:    source .venv/bin/activate");
p("Your prompt now starts with (.venv). If PowerShell refuses to run Activate.ps1, run this once, answer Y, and try again:");
code("Set-ExecutionPolicy -Scope CurrentUser RemoteSigned");
step("Install the libraries (cryptography, psutil, Flask, pytest). Takes one to two minutes:");
code("pip install -r requirements.txt");

h2("B2. Run the tests");
code("python -m pytest -q");
p("Expected result: 23 passed. This proves encryption, backup, restore, ransomware recovery, tamper detection and dashboard security all work on your machine.");

h2("B3. Narrated demo (the safe fallback)");
code("python demo/run_demo.py");
p("It tells the whole story in seven scenes. Press Enter between scenes. Add --fast to run without pauses. Use this if anything goes wrong with the live dashboard during your presentation.");

h2("B4. Live dashboard demo");
step("In your first window (with .venv active), start everything with one command:");
code("python demo/live.py --fresh");
p("This creates the sample university data, the encrypted backup repository and a stand-in Student Portal, then starts UniGuard and opens http://127.0.0.1:8080 in your browser. If Windows Firewall asks, click Allow; the demo only uses your own computer.");
step("Log in to the dashboard with the password: cmp468");
step("Open a second Command Prompt, go to the folder and switch the environment on:");
code("cd C:\\CMP-468\\project1-uniguard", ".venv\\Scripts\\activate");
step("Stage the incidents one at a time, waiting a few seconds after each so the dashboard updates:");
table(["Command", "What to point at"], [
  ["python demo/simulate_incident.py power-off", "Power card turns amber (ON BATTERY); a power-loss snapshot appears"],
  ["python demo/simulate_incident.py battery-low", "Critical alert: shut servers down cleanly"],
  ["python demo/simulate_incident.py power-on", "Mains power restored notice"],
  ["python demo/simulate_incident.py portal-down", "Student Portal row turns DOWN (HTTP 503)"],
  ["python demo/simulate_incident.py portal-up", "Portal back UP, with downtime in the audit trail"],
  ["python demo/simulate_incident.py tamper", "Red RECORDS ALERT banner: a CMP468 grade changed outside the approved window"],
  ["python demo/simulate_incident.py ransomware", "Incident row: files restored, files quarantined, recovery time in seconds"],
]);
step("Click Verify backups on the dashboard. It decrypts and checks every stored chunk.");
step("To show the audit trail and its hash-chain check from the command line, set the demo passphrase in the second window first:");
code("Command Prompt:   set UNIGUARD_PASSPHRASE=demo-passphrase-CMP468-2026", "PowerShell:       $env:UNIGUARD_PASSPHRASE=\"demo-passphrase-CMP468-2026\"", "macOS / Linux:    export UNIGUARD_PASSPHRASE=demo-passphrase-CMP468-2026", "", "python -m uniguard -c demo/demo_config.json audit", "python -m uniguard -c demo/demo_config.json snapshots");
step("Stop the demo with Ctrl+C in the first window. Next time, python demo/live.py --fresh starts clean; without --fresh it keeps the previous state.");

h2("B5. Optional: reproduce the benchmark in the report");
code("python docs/benchmark.py 2000 100");
p("Creates 2,000 files (about 195 MB) in a temporary folder and prints backup, restore and ransomware-recovery times. Your numbers will differ from the report's with your hardware; mention that if the panel asks.");

h1("Part C. Project 2: AgroPeace");
h2("C1. Create its Python environment (once)");
code("cd C:\\CMP-468\\project2-agropeace", "python -m venv .venv", ".venv\\Scripts\\activate", "pip install -r requirements.txt");
p("Use the PowerShell or macOS/Linux activate line from B1 if you are not in Command Prompt.");

h2("C2. Run the tests");
code("python -m pytest -q");
p("Expected result: 30 passed, in about 20 seconds.");

h2("C3. Narrated demo (the safe fallback)");
code("python demo/run_demo.py");
p("Six scenes: morning risk picture, herd H1 heading for Yelwata farms, escalation, SMS acknowledgement, rumour versus corroborated reports, and attacks on the system being blocked.");

h2("C4. Live map demo");
step("In your first window (with .venv active):");
code("python demo/live.py --fresh");
p("Your browser opens http://127.0.0.1:8090. You first see the public view: community risk levels only, with no herds and no cases. That is deliberate; say so.");
step("Sign in on the right as coordinator, password peace-coord-2026. Herds, cases and the security panel appear.");
step("Open a second window, go to the folder, switch the environment on, and start the GPS collars:");
code("cd C:\\CMP-468\\project2-agropeace", ".venv\\Scripts\\activate", "python demo/simulator.py");
p("The collars send a signed position every 2 seconds for about 2 minutes (add --fast for about 30 seconds). Watch herd H1: its dashed red forecast line reaches a Yelwata farm, an early-warning case opens, then H1 enters the farm and the case turns to WARNING.");
step("Try the USSD phone panel: click Dial *347*468#, then send these replies one at a time: 1 (cattle on my farm), 2 (Guma), 1 (Yelwata), 1 (yes, send). Point at the new report's trust score and the reasons listed under it.");
step("On a case, click Acknowledge, then pick herd_rerouted and click Resolve. Point at the audit chain status in the Security panel.");
step("Show least privilege: sign out, sign in as guma_mediator / guma-mediator-2026 (sees only Guma), then as protection / protect-2026 (can reveal an informant's number, with a written reason that is logged).");
step("To jump straight to the Yelwata area, open http://127.0.0.1:8090/#7.86,8.81,11.25");
step("Stop with Ctrl+C in the first window. python demo/live.py --fresh clears cases and reports next time.");
tip("Without internet the map background is plain, because street tiles come from OpenStreetMap. Farms, reserves, routes, the river and the risk grid still draw, because the map library is bundled with the project.");

h1("Part D. The documents");
step("Open each report (project1-uniguard/docs/UniGuard_Report.docx and project2-agropeace/docs/AgroPeace_Report.docx) in Microsoft Word.");
step("When Word asks to update fields, click Yes. This fills in the table of contents. If it does not ask: right-click the table of contents > Update Field > Update entire table.");
step("Replace the placeholders on the cover: [UNIVERSITY NAME], [FACULTY NAME], [YOUR FULL NAME], [MATRIC NUMBER], [LECTURER'S NAME], [MONTH, YEAR].");
step("If your department wants PDF: File > Save As > PDF.");
step("Open each presentation in PowerPoint. Put your name and matric number on slide 1. Your talking points are in the speaker notes under each slide (View > Notes). Use Slide Show > Use Presenter View so only you see the notes.");
step("Print or keep open the two Defense Q&A documents. The last pages hold the demo runbook and the numbers to remember.");
tip("Changing the text inside the Word and PowerPoint files directly is fine. The docs/build_*.js scripts only matter if you want to regenerate the files; that needs Node.js and is described in the main README.");

h1("Part E. The day before you present");
step("Set everything up on the laptop you will present with, not a different one. The .venv folder does not move between computers; copy the project folder and repeat B1 and C1 on the new laptop.");
step("Turn off Wi-Fi and run both test suites and both live demos once. This proves they work offline.");
step("Charge the laptop fully. The power-loss scenes are simulated; your laptop's real power does not matter.");
step("Decide your window layout: browser on one side, the two command windows on the other. Set browser zoom to 125% so the panel can read the dashboard.");
step("Keep python demo/run_demo.py --fast ready in a window as a fallback for each project.");

h1("Part F. Troubleshooting");
table(["Problem", "Fix"], [
  ["'python' is not recognized", "Reinstall Python with \"Add python.exe to PATH\" ticked, or use py instead of python."],
  ["PowerShell: Activate.ps1 cannot be loaded", "Run Set-ExecutionPolicy -Scope CurrentUser RemoteSigned, answer Y, try again. Or use Command Prompt."],
  ["No module named ... when running a demo", "The environment is not active in that window. Run the activate command from B1 or C1 first."],
  ["pip install fails", "Check the internet connection, run python -m pip install --upgrade pip, then repeat the install."],
  ["Address already in use / port busy", "Another copy is still running. Press Ctrl+C in its window, or close it. You can also change \"port\" under \"dashboard\" in demo/demo_config.json."],
  ["The browser did not open", "Type the address yourself: http://127.0.0.1:8080 for UniGuard, http://127.0.0.1:8090 for AgroPeace."],
  ["UniGuard: \"Demo sandbox not found\"", "Start python demo/live.py first; it creates the sample data."],
  ["UniGuard: \"wrong passphrase\"", "You set a different UNIGUARD_PASSPHRASE than the one the repository was created with. Run python demo/live.py --fresh."],
  ["Ransomware simulation blocked by Windows Defender", "Move the project out of Documents, Desktop or OneDrive to C:\\CMP-468 (Controlled Folder Access)."],
  ["AgroPeace simulator: connection refused", "Start python demo/live.py in the first window before running the simulator."],
  ["Map background is blank", "Normal without internet. All project layers still draw."],
]);

h1("Part G. Taking it beyond the demo");
p("If your lecturer asks how a university or agency would run these for real, these are the steps.");
h2("UniGuard on a real server");
step("Use a Linux server with a second disk (or network storage) for backups, and a second site or cloud bucket for the offsite copy.");
step("Copy demo/demo_config.json to /etc/uniguard/config.json and set source (the file share to protect), repository (the backup disk), offsite.path, services (the real portal and database addresses), power (source: nut for a real UPS) and protected_paths (the results folders and the Senate-approved windows).");
step("Choose a long passphrase, store it in the server's environment (not in the config), and seal a paper copy with the Registrar and the Director of ICT.");
step("Add SMS alerts: create an Africa's Talking or Termii account and add an alerts entry with type africastalking or termii. Put the API key in the environment and reference it as env:NAME in the config.");
step("Initialise once, then run UniGuard as a service that starts on boot, behind an HTTPS reverse proxy (for example Nginx) if the dashboard is used from other machines:");
code("python -m uniguard -c /etc/uniguard/config.json init", "python -m uniguard -c /etc/uniguard/config.json run --dashboard");
step("Test a restore every month: python -m uniguard -c /etc/uniguard/config.json restore latest /tmp/restore-test");
h2("AgroPeace in the field");
step("Replace data/benue_layers.geojson with surveyed farm boundaries, gazetted reserves and stock routes (the same GeoJSON format), and data/incidents_history.json with ACLED records.");
step("Register real collars in the devices section, set a strong AGROPEACE_MASTER_KEY in the server environment, and load each collar's key onto the device.");
step("Register responders with their phone numbers and languages. Connect a USSD code and SMS sender ID through a gateway, pointing its callback to https://your-server/ussd/<secret token> and /sms/<secret token>.");
step("Replace the demo staff passwords: generate new hashes with Python (from werkzeug.security import generate_password_hash) and put them in users.");
step("Pilot in one LGA for a season with herder and farmer associations, and have native speakers check all message templates before use.");

// ---------------------------------------------------------------- Word output
const FONT = "Calibri";
const border = { style: BorderStyle.SINGLE, size: 4, color: "B8C2CC" };
const borders = { top: border, bottom: border, left: border, right: border };
const kids = [
  new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("CMP 468 Projects: Setup and Run Guide")] }),
  new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "UniGuard (question 1) and AgroPeace (question 2)", italics: true, color: "5D6B7A" })] }),
];
let inst = 0; // a new numbering instance per section, so steps restart at 1
for (const b of G) {
  const [type] = b;
  if (type === "h1") { inst++; kids.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(b[1])] })); }
  else if (type === "h2") { inst++; kids.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(b[1])] })); }
  else if (type === "p") kids.push(new Paragraph({ spacing: { after: 120, line: 290 }, children: [new TextRun(b[1])] }));
  else if (type === "step") {
    kids.push(new Paragraph({ numbering: { reference: "steps", level: 0, instance: inst }, spacing: { after: 100, line: 290 }, children: [new TextRun(b[1])] }));
  } else if (type === "tip") kids.push(new Paragraph({ spacing: { before: 60, after: 140 }, shading: { fill: "EEF6F1", type: ShadingType.CLEAR, color: "auto" },
    children: [new TextRun({ text: "Note: ", bold: true, color: "0B5D3B" }), new TextRun(b[1])] }));
  else if (type === "code") {
    b[1].forEach((l, i) => kids.push(new Paragraph({ indent: { left: 360 }, spacing: { after: i === b[1].length - 1 ? 140 : 0 },
      shading: { fill: "F1F3F5", type: ShadingType.CLEAR, color: "auto" }, children: [new TextRun({ text: l || " ", font: "Consolas", size: 19 })] })));
  } else if (type === "table") {
    const widths = [4200, 5200];
    const cell = (t, head, w) => new TableCell({ borders, width: { size: w, type: WidthType.DXA },
      shading: head ? { fill: "1C2733", type: ShadingType.CLEAR, color: "auto" } : undefined,
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({ children: [new TextRun({ text: t, size: 19, bold: head, color: head ? "FFFFFF" : undefined,
        font: !head && t.startsWith("python ") ? "Consolas" : FONT })] })] });
    kids.push(new Table({ width: { size: 9400, type: WidthType.DXA }, columnWidths: widths,
      rows: [new TableRow({ tableHeader: true, children: b[1].map((h, i) => cell(h, true, widths[i])) }),
        ...b[2].map((r) => new TableRow({ children: r.map((c, i) => cell(c, false, widths[i])) }))] }));
    kids.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
  }
}
const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { size: 40, bold: true, color: "1C2733", font: FONT }, paragraph: { spacing: { after: 60 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, color: "0B5D3B", font: FONT }, paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 25, bold: true, color: "1C2733", font: FONT }, paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 1, keepNext: true } },
    ],
  },
  numbering: { config: [{ reference: "steps", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1247, right: 1247 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] }) },
    children: kids,
  }],
});

// ---------------------------------------------------------------- Markdown output
const md = ["# CMP 468 Projects: Setup and Run Guide", "", "_UniGuard (question 1) and AgroPeace (question 2)_", ""];
let n = 0;
for (const b of G) {
  const [type] = b;
  if (type === "h1") { n = 0; md.push(`## ${b[1]}`, ""); }
  else if (type === "h2") { n = 0; md.push(`### ${b[1]}`, ""); }
  else if (type === "p") md.push(b[1], "");
  else if (type === "step") { n++; md.push(`${n}. ${b[1]}`); }
  else if (type === "tip") md.push("", `> **Note:** ${b[1]}`, "");
  else if (type === "code") md.push("", "```", ...b[1], "```", "");
  else if (type === "table") {
    md.push("", `| ${b[1].join(" | ")} |`, `| ${b[1].map(() => "---").join(" | ")} |`,
      ...b[2].map((r) => `| ${r.map((c) => c.startsWith("python ") ? "`" + c + "`" : c.replace(/\|/g, "\\|")).join(" | ")} |`), "");
  }
}
const root = path.join(__dirname, "..");
fs.writeFileSync(path.join(root, "SETUP_GUIDE.md"), md.join("\n").replace(/\n{3,}/g, "\n\n") + "\n");
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(path.join(root, "SETUP_GUIDE.docx"), buf); console.log("wrote SETUP_GUIDE.docx and SETUP_GUIDE.md"); });
