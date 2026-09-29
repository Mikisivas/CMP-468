// Builds UniGuard_Presentation.pptx.  Run: NODE_PATH=<modules> node docs/build_slides.js
const path = require("path");
const pptxgen = require("pptxgenjs");
const { icon, makeTheme } = require("../../tools/deckkit");
const fa = require("react-icons/fa");

const T = makeTheme({
  primary: "0B5D3B", dark: "0A2E20", ink: "1C2733", muted: "5D6B7A", tint: "EAF4EE",
  alert: "C53030", amber: "D69E2E", white: "FFFFFF",
});
const { W, H, M } = T;
const img = (f) => path.join(__dirname, "img", f);
const FOOT = "CMP 468 · UniGuard";

(async () => {
  const I = {};
  for (const [k, c, col] of [
    ["lock", fa.FaLock], ["bolt", fa.FaBolt], ["user", fa.FaUserSecret], ["hdd", fa.FaHdd],
    ["server", fa.FaServer], ["sms", fa.FaSms], ["wifi", fa.FaWifi], ["cal", fa.FaCalendarAlt],
    ["naira", fa.FaMoneyBillWave], ["law", fa.FaBalanceScale], ["shield", fa.FaShieldAlt],
    ["bug", fa.FaBug], ["check", fa.FaCheckCircle], ["key", fa.FaKey], ["clone", fa.FaClone],
    ["search", fa.FaSearch], ["chain", fa.FaLink], ["grad", fa.FaGraduationCap],
  ]) I[k] = await icon(c, "FFFFFF");

  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = "UniGuard: Automated Monitoring, Backup and Recovery";
  let n = 0;
  const next = (bg) => { n++; const s = pres.addSlide(); s.background = { color: bg || T.white }; return s; };

  // 1. Title
  let s = next(T.dark);
  T.badge(s, I.shield, M, 1.2, 1.1, T.primary);
  s.addText("UniGuard", { x: M, y: 2.5, w: 11, h: 1.1, fontFace: T.fHead, fontSize: 60, bold: true, color: T.white, margin: 0, isTextBox: true });
  s.addText("Automated monitoring, backup and recovery for university digital infrastructure", {
    x: M, y: 3.6, w: 11, h: 0.9, fontFace: T.fBody, fontSize: 24, color: "CFE8DA", margin: 0, isTextBox: true });
  s.addText("Built for Nigerian campus conditions: unstable power, costly bandwidth, small budgets and result tampering", {
    x: M, y: 4.5, w: 11, h: 0.6, fontFace: T.fBody, fontSize: 16, italic: true, color: "9FC7B2", margin: 0, isTextBox: true });
  s.addText("[Your Name]  ·  [Matric No]  ·  CMP 468: Computer Security  ·  [Date]", {
    x: M, y: 6.3, w: 12, h: 0.4, fontFace: T.fBody, fontSize: 14, color: "CFE8DA", margin: 0, isTextBox: true });
  s.addNotes("Good morning. My project answers question one: develop an automated monitoring, backup and recovery system for university digital infrastructure. I called it UniGuard. I designed it around the real conditions of a Nigerian university, and I will show it working live.");

  // 2. Why it matters
  s = next();
  T.kicker(s, "The problem");
  T.title(s, "Campus records can vanish in minutes");
  const stats = [
    ["12", "national grid collapses in 2024 (Guardian Nigeria). Each cut can corrupt a file mid-write.", T.amber],
    ["72 hrs", "to report a personal data breach to the NDPC under the Nigeria Data Protection Act 2023, s.40", T.primary],
    ["1 drive", "is all many departments use for backup, and it sits beside the server ransomware attacks", T.alert],
  ];
  stats.forEach(([v, l, c], i) => {
    const x = M + i * 4.1;
    T.card(s, x, 1.75, 3.8, 2.9);
    T.stat(s, v, l, x + 0.35, 1.95, 3.1, c);
  });
  T.body(s, "Admissions (CAPS), fees (Remita), course registration, results and transcripts now all run on campus servers. Most have no monitoring, no tested restore, and no record of who changed what.",
    M, 5.0, W - 2 * M, 1.2, { fontSize: 18 });
  T.footer(s, FOOT, n);
  s.addNotes("Three numbers frame the problem. The grid collapsed twelve times in 2024, so power cuts are routine. The Data Protection Act gives us 72 hours to report a breach, so we must know quickly. And many departments back up to one drive kept next to the server, which ransomware encrypts along with everything else.");

  // 3. Five threats
  s = next();
  T.kicker(s, "Threat model");
  T.title(s, "Five ways a university loses its data");
  const threats = [
    [I.bug, "Ransomware", "encrypts the file server and every attached drive", T.alert],
    [I.user, "Insider tampering", "raises a grade after Senate approval", T.alert],
    [I.bolt, "Power failure", "generator switch-over corrupts a file mid-write", T.amber],
    [I.hdd, "Disk failure", "destroys data that was never copied", T.amber],
    [I.server, "Service outage", "portal down during registration, noticed hours later", T.primary],
  ];
  threats.forEach(([ic, h, d, c], i) => {
    const y = 1.6 + i * 1.0;
    T.badge(s, ic, M, y, 0.72, c);
    s.addText(h, { x: M + 1.0, y: y - 0.02, w: 3.3, h: 0.72, fontFace: T.fHead, fontSize: 20, bold: true, color: T.ink, margin: 0, isTextBox: true, valign: "middle" });
    s.addText(d, { x: M + 4.3, y: y - 0.02, w: 7.7, h: 0.72, fontFace: T.fBody, fontSize: 17, color: T.muted, margin: 0, isTextBox: true, valign: "middle" });
  });
  T.footer(s, FOOT, n);
  s.addNotes("These map to the classes of attack from our course: ransomware is interruption, grade tampering is modification, and power and disk failure threaten availability. UniGuard has a specific control for each one.");

  // 4. Objectives
  s = next();
  T.kicker(s, "Aim and objectives");
  T.title(s, "Protect the CIA triad, automatically");
  const obj = ["Encrypted, incremental backups where every snapshot restores on its own",
    "Continuous monitoring of servers, campus services and power",
    "Detection of ransomware and unauthorised result changes",
    "Automatic, verified recovery with evidence preserved",
    "Tamper-evident audit trail of every action",
    "Evaluation by tests, live demo and benchmarks"];
  obj.forEach((t, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col * 6.1, y = 1.7 + row * 1.6;
    T.card(s, x, y, 5.8, 1.35);
    s.addText(String(i + 1), { x: x + 0.25, y: y + 0.2, w: 0.9, h: 0.95, fontFace: T.fHead, fontSize: 40, bold: true, color: T.primary, margin: 0, isTextBox: true, valign: "middle" });
    s.addText(t, { x: x + 1.2, y: y + 0.15, w: 4.4, h: 1.05, fontFace: T.fBody, fontSize: 17, color: T.ink, margin: 0, isTextBox: true, valign: "middle" });
  });
  T.footer(s, FOOT, n);
  s.addNotes("Six objectives. All six were met, and I will show evidence for each one.");

  // 5. Architecture
  s = next();
  T.kicker(s, "Design");
  T.title(s, "Architecture");
  s.addImage({ path: img("architecture.png"), x: (W - 10.0) / 2, y: 1.35, w: 10.0, h: 10.0 * 1440 / 2600 });
  T.footer(s, FOOT, n);
  s.addNotes("On the left, what we protect: the file server with results, records, bursary and payroll; the student portal; the result database; and the UPS. In the middle, the engine: a monitor, an integrity monitor, a backup engine, an incident responder, the crypto layer and an alert manager, all writing to a hash-chained audit log. On the right: an encrypted primary repository, an offsite copy that only ever holds ciphertext, SMS and email alerts, and the dashboard.");

  // 6. Encryption
  s = next();
  T.kicker(s, "Encryption and decryption");
  T.title(s, "A stolen backup drive reveals nothing");
  const flow = [["Passphrase", "12+ chars, sealed with Registrar"], ["scrypt", "memory-hard: slows guessing"],
    ["HKDF", "splits into 2 independent keys"], ["AES-256-GCM", "encrypts and authenticates every chunk"]];
  flow.forEach(([h, d], i) => {
    const x = M + i * 3.1;
    T.card(s, x, 1.75, 2.75, 1.9, i === 3 ? T.primary : T.tint);
    s.addText(h, { x: x + 0.2, y: 1.9, w: 2.35, h: 0.6, fontFace: T.fHead, fontSize: 20, bold: true, color: i === 3 ? T.white : T.primary, margin: 0, isTextBox: true, align: "center" });
    s.addText(d, { x: x + 0.2, y: 2.5, w: 2.35, h: 1.0, fontFace: T.fBody, fontSize: 14, color: i === 3 ? "E6F2EB" : T.ink, margin: 0, isTextBox: true, align: "center", valign: "top" });
    if (i < 3) s.addText("→", { x: x + 2.75, y: 2.35, w: 0.35, h: 0.6, fontSize: 24, color: T.muted, margin: 0, isTextBox: true, align: "center" });
  });
  T.bullets(s, [
    "Chunk names are HMAC-SHA256 with a secret key, so an attacker cannot test whether a known file is inside",
    "Chunk name is bound as associated data: swapping two encrypted chunks is detected",
    "Fresh random 96-bit nonce for every chunk; no nonce reuse",
    "On restore: GCM tag, chunk HMAC and whole-file SHA-256 are all checked",
  ], M, 4.05, W - 2 * M, 2.6, { fontSize: 17 });
  T.footer(s, FOOT, n);
  s.addNotes("This covers encryption and decryption from our outline. The passphrase goes through scrypt, which needs lots of memory per guess, so graphics-card cracking is expensive. HKDF splits the result into an encryption key and a naming key. Every chunk is encrypted with AES-256-GCM, which also detects any change. Tests confirm that flipping one bit, swapping two chunks, or using the wrong passphrase all fail safely.");

  // 7. Smart backups
  s = next();
  T.kicker(s, "Backup engine");
  T.title(s, "Incremental speed, full-backup safety");
  T.bullets(s, [
    "Files split into 1 MiB chunks, compressed, encrypted",
    "A chunk already stored is never stored again",
    "Every snapshot is a complete list of chunks, so there is no fragile backup chain",
    "Backup files written atomically and made read-only",
    "Retention keeps daily, weekly and monthly copies, and always the last clean one",
  ], M, 1.7, 5.9, 4.6, { fontSize: 17 });
  const bx = 7.1;
  T.card(s, bx, 1.6, 5.6, 4.9);
  s.addText("Benchmark: 2,000 records, 195 MB", { x: bx + 0.35, y: 1.8, w: 4.9, h: 0.4, fontFace: T.fBody, fontSize: 14, bold: true, color: T.muted, margin: 0, isTextBox: true });
  T.stat(s, "6.2 s", "first full backup", bx + 0.35, 2.2, 2.4);
  T.stat(s, "0.1 s", "next backup after 1% of files changed (224 KiB stored)", bx + 2.95, 2.2, 2.4);
  T.stat(s, "1.7 s", "full restore, every file SHA-256 verified", bx + 0.35, 4.15, 2.4);
  T.stat(s, "23/23", "automated tests passing", bx + 2.95, 4.15, 2.4);
  T.footer(s, FOOT, n);
  s.addNotes("Classic incremental backups are fast but need the whole chain to restore. Deduplication gives us both: each backup only writes new chunks, but each snapshot still restores on its own. On 195 megabytes, the second backup took a tenth of a second.");

  // 8. Ransomware detection
  s = next();
  T.kicker(s, "Detection");
  T.title(s, "Ransomware leaves fingerprints on files");
  const sig = [["Mass change", "5+ files and 20%+ of all files modified or deleted", 40],
    ["High entropy", "3+ changed files near 8 bits/byte (random-looking)", 30],
    ["Ransom extension", ".locked, .encrypted, .lockbit and others", 20],
    ["Ransom note", "README / DECRYPT / RECOVER text files appear", 20]];
  sig.forEach(([h, d, p], i) => {
    const y = 1.65 + i * 1.02;
    s.addText(h, { x: M, y, w: 2.7, h: 0.8, fontFace: T.fHead, fontSize: 19, bold: true, color: T.ink, margin: 0, isTextBox: true, valign: "middle" });
    s.addText(d, { x: M + 2.8, y, w: 4.9, h: 0.8, fontFace: T.fBody, fontSize: 15, color: T.muted, margin: 0, isTextBox: true, valign: "middle" });
    s.addShape("rect", { x: 8.6, y: y + 0.2, w: p * 0.07, h: 0.42, fill: { color: T.alert }, line: { type: "none" } });
    s.addText(`${p} pts`, { x: 8.7 + p * 0.07, y: y + 0.15, w: 1.2, h: 0.52, fontFace: T.fBody, fontSize: 15, bold: true, color: T.alert, margin: 0, isTextBox: true, valign: "middle" });
  });
  T.card(s, M, 5.85, W - 2 * M, 0.9, T.tint);
  s.addText("50+ points = critical. No single signal is enough, so a lecturer replacing many handouts gets a warning, not a lockdown.", {
    x: M + 0.3, y: 5.9, w: W - 2 * M - 0.6, h: 0.8, fontFace: T.fBody, fontSize: 16, color: T.ink, margin: 0, isTextBox: true, valign: "middle" });
  T.footer(s, FOOT, n);
  s.addNotes("The idea comes from research on CryptoDrop by Scaife and others in 2016: ransomware makes files look random, so their Shannon entropy jumps close to 8 bits per byte. I combine four signals. It needs two or more to go critical, which keeps false alarms down. Compressed formats like PDF and DOCX are excluded from the entropy signal.");

  // 9. Automatic response
  s = next();
  T.kicker(s, "Incident response (NIST SP 800-61)");
  T.title(s, "From attack to verified recovery in seconds");
  s.addImage({ path: img("incident_flow.png"), x: M, y: 1.55, w: W - 2 * M, h: (W - 2 * M) * 560 / 2600 });
  T.stat(s, "2.7 s", "to detect, quarantine, restore and verify 600 encrypted files", M, 4.3, 3.6, T.alert);
  T.stat(s, "600/600", "files restored, every one checked with SHA-256", M + 4.1, 4.3, 3.6);
  T.stat(s, "0", "clean snapshots lost: backups freeze during the attack", M + 8.2, 4.3, 3.6);
  T.footer(s, FOOT, n);
  s.addNotes("When the score crosses 50, UniGuard locks down backups so encrypted files never overwrite good ones. It copies damaged files and moves the attacker's files into quarantine as evidence. It restores from the last clean snapshot, checks every file's hash, then sends SMS alerts and records the recovery time. In my benchmark, 600 files came back in 2.7 seconds.");

  // 10. Protecting results
  s = next();
  T.kicker(s, "Records integrity");
  T.title(s, "Catching a changed grade");
  T.card(s, M, 1.6, 5.7, 4.9, "FDF0F0");
  s.addText("The insider", { x: M + 0.35, y: 1.8, w: 5, h: 0.5, fontFace: T.fHead, fontSize: 20, bold: true, color: T.alert, margin: 0, isTextBox: true });
  s.addText([
    { text: "CMP/2022/002, CMP468", options: { bold: true, breakLine: true } },
    { text: "43 (E)  →  88 (A)", options: { fontSize: 32, bold: true, color: T.alert, breakLine: true } },
    { text: "changed after Senate approval", options: {} },
  ], { x: M + 0.35, y: 2.4, w: 5, h: 2.2, fontFace: T.fBody, fontSize: 17, color: T.ink, margin: 0, isTextBox: true, valign: "top", paraSpaceAfter: 10 });
  const steps = [[I.search, "Protected path watch", "results may only change inside Senate-approved windows"],
    [I.sms, "Instant SMS", "to Registrar and ICT Director, naming the file"],
    [I.clone, "SUSPECT backups", "later snapshots never used for recovery"],
    [I.chain, "Hash-chained audit log", "editing the log to hide it breaks the chain"]];
  steps.forEach(([ic, h, d], i) => {
    const y = 1.65 + i * 1.2;
    T.badge(s, ic, 6.8, y, 0.7);
    s.addText(h, { x: 7.7, y: y - 0.05, w: 5.0, h: 0.4, fontFace: T.fHead, fontSize: 18, bold: true, color: T.ink, margin: 0, isTextBox: true });
    s.addText(d, { x: 7.7, y: y + 0.35, w: 5.0, h: 0.75, fontFace: T.fBody, fontSize: 15, color: T.muted, margin: 0, isTextBox: true });
  });
  T.footer(s, FOOT, n);
  s.addNotes("This is the feature I think matters most for a Nigerian university. The Registry marks the results folder as protected and gives it approval windows. Any change outside a window raises a critical alert. Backups after that are marked suspect, so the approved copy stays available as evidence. And if someone edits the audit log to cover it up, the hash chain breaks at the exact row.");

  // 11. Built for Nigeria
  s = next();
  T.kicker(s, "Local adaptation");
  T.title(s, "Built for how Nigerian campuses actually run");
  const nig = [[I.bolt, "NEPA takes light", "Reads the UPS. Emergency backup the moment mains fails. Alert before the battery dies."],
    [I.wifi, "Costly bandwidth", "Only changed chunks go offsite, at night, under a data cap. Resumes after link loss."],
    [I.sms, "Internet down too", "SMS through Africa's Talking or Termii reaches phones without data."],
    [I.cal, "Exam season", "Backups every 15 minutes instead of hourly during result upload."],
    [I.naira, "Small budget", "Free software. Runs on an old PC. One command to start."],
    [I.law, "NDPA 2023", "Encryption and timely restore (s.39). Audit trail for the 72-hour report (s.40)."]];
  nig.forEach(([ic, h, d], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = M + col * 4.1, y = 1.6 + row * 2.55;
    T.card(s, x, y, 3.85, 2.35);
    T.badge(s, ic, x + 0.25, y + 0.25, 0.65);
    s.addText(h, { x: x + 1.05, y: y + 0.25, w: 2.65, h: 0.65, fontFace: T.fHead, fontSize: 18, bold: true, color: T.ink, margin: 0, isTextBox: true, valign: "middle" });
    s.addText(d, { x: x + 0.25, y: y + 1.05, w: 3.4, h: 1.2, fontFace: T.fBody, fontSize: 14, color: T.ink, margin: 0, isTextBox: true, valign: "top" });
  });
  T.footer(s, FOOT, n);
  s.addNotes("Most backup tools assume steady power and fast internet. UniGuard assumes the opposite. It knows when we are on inverter, it sends offsite copies at night under a data cap, and it alerts by SMS because the internet often fails at the same moment as the incident.");

  // 12. Dashboard
  s = next();
  T.kicker(s, "Implementation");
  T.title(s, "The ICT unit's view");
  const dh = 5.55, dw = dh * 2100 / 1838;
  s.addImage({ path: img("dashboard.png"), x: M, y: 1.45, w: dw, h: dh });
  T.bullets(s, [
    "Red banner: a result file changed outside its window",
    "Power card: running on inverter",
    "Incident: 16 files restored, 17 quarantined, 0.01 s",
    "Audit chain status on every refresh",
    "Login with lockout after 5 failures, CSRF protection, security headers",
  ], M + dw + 0.4, 1.6, W - M - (M + dw + 0.4), 5.2, { fontSize: 15 });
  T.footer(s, FOOT, n);
  s.addNotes("This is the dashboard after three staged incidents. It refreshes every three seconds. The dashboard itself is protected: login with lockout, a CSRF header on every action, and security headers against clickjacking.");

  // 13. Results chart
  s = next();
  T.kicker(s, "Evaluation");
  T.title(s, "Results on 2,000 files (195 MB)");
  s.addChart(pres.charts.BAR, [{ name: "Seconds", labels: ["Full backup", "Incremental (1% changed)", "Full verified restore", "Ransomware: detect to recovered"], values: [6.2, 0.1, 1.7, 2.7] }], {
    x: M, y: 1.5, w: 7.6, h: 5.0, barDir: "bar", chartColors: [T.primary],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 14, dataLabelColor: T.ink,
    catAxisLabelFontSize: 13, catAxisLabelColor: T.ink, valAxisLabelColor: T.muted, valAxisLabelFontSize: 11,
    valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
    showTitle: true, title: "Time in seconds", titleFontSize: 14, titleColor: T.muted, showLegend: false,
  });
  T.card(s, 8.6, 1.6, 4.1, 4.9);
  s.addText("23 of 23 tests pass", { x: 8.9, y: 1.8, w: 3.6, h: 0.5, fontFace: T.fHead, fontSize: 20, bold: true, color: T.primary, margin: 0, isTextBox: true });
  T.bullets(s, ["Tampered ciphertext rejected", "Wrong passphrase rejected", "No plaintext in repository", "Ransomware fully reversed", "Lecturer edits not flagged", "Audit log edits caught", "Dashboard lockout works"],
    8.9, 2.4, 3.6, 3.9, { fontSize: 15 });
  T.footer(s, FOOT, n);
  s.addNotes("Recovery time objective under three seconds, compared with days of manual rebuilding. The recovery point objective is the backup interval: one hour normally, fifteen minutes in exam season. The tests prove the security properties, not just that the code runs.");

  // 14. Live demo
  s = next(T.dark);
  T.kicker(s, "Live demonstration", "9FC7B2");
  T.title(s, "Let me show you", { color: T.white });
  const demo = ["NEPA takes light: power card turns amber, emergency backup, SMS",
    "Student Portal goes down: critical alert within 3 seconds",
    "Insider changes a CMP468 grade: red records banner",
    "Ransomware scrambles the file server: watch it recover itself",
    "Verify backups and check the audit chain"];
  demo.forEach((t, i) => {
    const y = 1.7 + i * 0.95;
    s.addShape("ellipse", { x: M, y, w: 0.6, h: 0.6, fill: { color: T.primary }, line: { type: "none" } });
    s.addText(String(i + 1), { x: M, y, w: 0.6, h: 0.6, fontFace: T.fHead, fontSize: 18, bold: true, color: T.white, align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(t, { x: M + 0.9, y, w: 11, h: 0.6, fontFace: T.fBody, fontSize: 20, color: T.white, valign: "middle", margin: 0, isTextBox: true });
  });
  s.addText("Backup plan if the projector laptop misbehaves:  python demo/run_demo.py", {
    x: M, y: 6.6, w: 12, h: 0.4, fontFace: T.fBody, fontSize: 13, italic: true, color: "9FC7B2", margin: 0, isTextBox: true });
  s.addNotes("Switch to the terminal and browser now. Terminal 1 runs the dashboard, terminal 2 the fake portal, terminal 3 the incident simulator. Run: simulate_incident.py power-off, then Ctrl+C the portal, then tamper, then ransomware. If anything fails, run demo/run_demo.py --fast which tells the same story in the terminal.");

  // 15. Limitations
  s = next();
  T.kicker(s, "Honest assessment");
  T.title(s, "Limitations and future work");
  T.card(s, M, 1.6, 5.9, 4.9, "FDF0F0");
  s.addText("Limitations", { x: M + 0.3, y: 1.8, w: 5.3, h: 0.5, fontFace: T.fHead, fontSize: 20, bold: true, color: T.alert, margin: 0, isTextBox: true });
  T.bullets(s, ["Work since the last clean backup is lost (RPO = backup interval)",
    "Very slow ransomware may stay under the mass-change threshold",
    "An admin-level attacker on the same server can delete local backups; the offsite copy covers this",
    "Lost passphrase = unreadable backups",
    "Watches files, not rows inside a database"], M + 0.3, 2.4, 5.3, 4.0, { fontSize: 15 });
  T.card(s, 6.83, 1.6, 5.9, 4.9);
  s.addText("Next steps", { x: 7.13, y: 1.8, w: 5.3, h: 0.5, fontFace: T.fHead, fontSize: 20, bold: true, color: T.primary, margin: 0, isTextBox: true });
  T.bullets(s, ["Row-level auditing for result databases",
    "Immutable (object-lock) offsite storage",
    "Per-process detection on staff PCs",
    "Split passphrase between Registrar and ICT Director",
    "One-semester pilot on a faculty server"], 7.13, 2.4, 5.3, 4.0, { fontSize: 15 });
  T.footer(s, FOOT, n);
  s.addNotes("I want to be clear about limits. The biggest one: changes made after the last backup are lost, so exam season uses a 15-minute interval. The offsite copy on a separate machine is the answer to an attacker who gets administrator rights on the main server.");

  // 16. Conclusion
  s = next(T.dark);
  T.badge(s, I.grad, M, 1.0, 0.9, T.primary);
  s.addText("Strong protection does not need expensive software", {
    x: M, y: 2.05, w: 12, h: 1.2, fontFace: T.fHead, fontSize: 32, bold: true, color: T.white, margin: 0, isTextBox: true });
  T.bullets(s, [
    "Encrypted, deduplicated backups that restore on their own",
    "Ransomware reversed and verified in under 3 seconds",
    "Result tampering caught, evidence preserved, log tamper-evident",
    "Designed for power cuts, thin bandwidth and small budgets",
  ], M, 3.5, 11.5, 2.3, { fontSize: 20, color: "E6F2EB" });
  s.addText("Thank you. Questions?", { x: M, y: 6.0, w: 12, h: 0.7, fontFace: T.fHead, fontSize: 28, bold: true, color: "9FC7B2", margin: 0, isTextBox: true });
  s.addNotes("To conclude: UniGuard shows that a university can protect its records against ransomware, tampering and power failure with free software on ordinary hardware. Thank you. I welcome your questions.");

  await pres.writeFile({ fileName: path.join(__dirname, "UniGuard_Presentation.pptx") });
  console.log("wrote UniGuard_Presentation.pptx,", n, "slides");
})();
