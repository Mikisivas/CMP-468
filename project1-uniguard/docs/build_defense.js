// Builds UniGuard_Defense_QA.docx: likely panel questions, model answers and a demo runbook.
const path = require("path");
const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, LevelFormat } = require("docx");

const FONT = "Calibri";
const QA = [
  ["Overview", [
    ["In one sentence, what does UniGuard do?",
      "It watches a university's servers, services and power, backs data up with encryption, detects ransomware and unauthorised result changes, and restores damaged files automatically, all with a tamper-evident log."],
    ["Why did you choose this design over just buying a commercial backup product?",
      "Cost and fit. Commercial suites charge per server or per terabyte each year and assume steady power and fast internet. UniGuard is free, runs on an old PC, reacts to power cuts, sends offsite copies at night under a data cap, and protects result files specifically."],
    ["Which part of the course outline does this cover?",
      "All ten topics. The CIA triad drives the design. The threat model covers intrusion, breaches, vulnerabilities and classes of attack. Controls cover defence methods. AES-GCM, scrypt and HKDF cover encryption and decryption. The SQLite audit log covers database security. Service checks and dashboard hardening cover network security. ISO 27001, NIST SP 800-34 and 800-61, and NDPA 2023 cover policies and standards. Table 4.5 in the report maps each one."],
  ]],
  ["Encryption and keys", [
    ["Why AES-256-GCM and not AES-CBC?",
      "GCM is authenticated encryption. It gives confidentiality and integrity in one step: if a single bit of the backup changes, decryption fails. CBC gives confidentiality only and needs a separate MAC, which people often get wrong."],
    ["What happens if a nonce repeats in GCM?",
      "Nonce reuse under the same key breaks GCM badly: it leaks the XOR of the two plaintexts and lets an attacker forge tags. UniGuard uses a fresh random 96-bit nonce for every chunk. The chance of a repeat stays negligible below about 2^32 encryptions per key, far more chunks than a university file server will hold."],
    ["Why scrypt? Why not just hash the passphrase with SHA-256?",
      "SHA-256 is fast, so an attacker with a GPU can try billions of guesses per second. Scrypt is deliberately slow and memory-hard (about 32 MiB and 100 ms per guess at N = 2^15), which makes large-scale guessing expensive."],
    ["What is HKDF doing?",
      "It splits one master key into independent keys for different jobs: one for AES-GCM encryption and one for HMAC chunk names. Using one key for two purposes is bad practice because a weakness in one use can affect the other."],
    ["Why name chunks with HMAC instead of plain SHA-256?",
      "With plain SHA-256, anyone holding the backup could hash a known file, such as last year's result sheet, and check whether that chunk exists. A keyed HMAC stops this, because only the key holder can compute the names."],
    ["What is the associated data for?",
      "The chunk's name is passed as associated data to GCM. It is authenticated but not encrypted. If an attacker swaps two encrypted chunks on disk, the name no longer matches and decryption fails. One of the tests proves this."],
    ["Where is the key stored?",
      "Nowhere on disk. The repository stores only the salt and an encrypted check value. The passphrase comes from an environment variable when UniGuard starts. In a real deployment it would be sealed in envelopes held by the Registrar and the Director of ICT."],
    ["What if the passphrase is lost?",
      "The backups cannot be read. That is the price of real encryption. I recommend dual custody of the passphrase and, as future work, splitting it with Shamir secret sharing so any two of three officers can recover it."],
  ]],
  ["Backup and recovery", [
    ["How is this incremental if every snapshot is a full backup?",
      "Every snapshot lists all chunks, so it restores on its own. But a chunk that already exists is never stored again, so each new backup only writes the changed data. In the benchmark, after 1% of files changed, the backup took 0.1 seconds and stored 224 KiB."],
    ["What are your RPO and RTO?",
      "RPO equals the backup interval: 60 minutes normally, 15 minutes in exam periods. The measured RTO for a 600-file ransomware attack was 2.7 seconds end to end."],
    ["How do you know a backup can actually be restored?",
      "Three checks. The GCM tag on every chunk. The HMAC name recomputed after decryption. The SHA-256 of each whole restored file compared with the value recorded at backup time. The verify command decrypts every chunk in the repository on demand."],
    ["How does it follow the 3-2-1 rule?",
      "Three copies: live data, primary repository, offsite copy. Two media: the backup disk and a separate machine or cloud bucket. One offsite, which only ever holds ciphertext."],
    ["What happens if power fails during a backup?",
      "Each file is written to a temporary name, flushed to disk, then renamed in one atomic step, so a half-written chunk never appears under its real name. The snapshot manifest is written last. The SQLite log uses WAL mode, which survives sudden power loss. The next backup reuses every chunk already stored."],
    ["Why does retention always keep the last clean snapshot?",
      "Ransomware can hide on a network for days before it strikes. If retention deleted older snapshots on schedule, the only clean copy could be deleted before anyone noticed. Keeping the last clean snapshot removes that risk."],
  ]],
  ["Detection", [
    ["What is Shannon entropy and why does it detect ransomware?",
      "It measures how unpredictable the bytes are, from 0 to 8 bits per byte. English text sits around 4 to 5. Encrypted data looks random, so it sits close to 8. When many files suddenly jump to near 8, something is encrypting them."],
    ["What about PDFs and Word files, which are already compressed?",
      "They are excluded from the entropy signal because they are naturally high-entropy. Mass change, ransom extensions and ransom notes still apply to them."],
    ["How do you avoid false alarms?",
      "No single signal reaches the critical score of 50. A lecturer who replaces 30 handouts triggers mass change (40 points) at most, which is a warning. Real ransomware triggers mass change plus high entropy plus extensions, which is 90 or more. A test checks that normal edits are not flagged."],
    ["Could smart ransomware evade this?",
      "Yes, if it encrypts very slowly, keeps original file names and leaves no note. That is a limitation I state in the report. The entropy signal still fires once three changed files look encrypted, and the thresholds can be lowered. Per-process monitoring on staff PCs is future work."],
    ["How does the result-tampering check work?",
      "The Registry lists protected folders and the windows when changes are allowed, such as after a Senate meeting. Any change outside a window raises a critical alert naming the files. Until it is resolved, later backups are marked SUSPECT and never used for recovery, so the approved version survives as evidence."],
    ["What if the insider has access during the approved window?",
      "The window check will not fire, but the hash-chained audit log and the snapshots still record what changed and when, so the change can be traced. Row-level auditing inside the result database is future work."],
  ]],
  ["Audit log and dashboard", [
    ["How does the hash chain prove the log was not edited?",
      "Each entry stores the SHA-256 of the previous entry plus its own content. Changing any past entry changes its hash, which no longer matches the next entry's stored link. Deleting an entry leaves a gap in the sequence numbers. The demo shows both being caught."],
    ["Couldn't an attacker rebuild the whole chain after editing?",
      "Yes, with write access to the database and enough effort. The defence is to anchor the latest chain head elsewhere: include it in the encrypted offsite snapshot, or send it in the daily SMS. Then any rebuilt chain would not match the anchor. I mention this as a hardening step."],
    ["How is the dashboard protected?",
      "Password login with constant-time comparison. Lockout for five minutes after five failed attempts from one address. HttpOnly, SameSite=Strict session cookies. Every action needs a custom CSRF header. Security headers block framing and MIME sniffing. By default it listens only on localhost; in production it should sit behind HTTPS."],
  ]],
  ["Nigerian context and deployment", [
    ["Why SMS instead of email or WhatsApp?",
      "When a server room loses power or the campus link drops, internet alerts may not arrive. SMS reaches any phone without data. Africa's Talking and Termii both serve the Nigerian market with simple HTTP APIs. Email and webhooks are also supported."],
    ["How does UniGuard know the power has gone off?",
      "It reads the UPS through Network UPS Tools, which supports common UPS brands, or through the laptop battery, or a status file written by any script. When mains power is lost it takes an emergency backup, and when the battery is low it alerts staff to shut servers down cleanly."],
    ["How does it relate to the Nigeria Data Protection Act 2023?",
      "Section 39 requires technical measures such as encryption and the ability to restore data in time after an incident. UniGuard provides both. Section 40 requires breach notification to the NDPC within 72 hours. The incident record and audit trail give the facts needed for that report."],
    ["How would you deploy it in a real university?",
      "Pilot on one faculty file server and the Registry results folder for a semester. Offsite copy to a second campus or a partner over NgREN. SMS to the ICT Director and Registrar. Approval windows written into the result calendar. Passphrase under dual custody. Monthly restore drills."],
    ["How much does it cost?",
      "No licence. The recurring costs are a second disk or offsite storage and SMS credit. It runs on an existing server or a refurbished desktop."],
  ]],
  ["Testing", [
    ["How did you test it?",
      "Twenty-three automated pytest tests, a narrated seven-scene demo, a live dashboard demo, and a benchmark on 2,000 files. All tests pass."],
    ["Your demo data is small. Does it scale?",
      "The benchmark used 2,000 files and 195 MB: full backup 6.2 s, incremental 0.1 s, full verified restore 1.7 s, ransomware recovery of 600 files 2.7 s. The work grows roughly in line with the amount of changed data, not the total, because unchanged files are skipped by size and time."],
  ]],
];

const RUNBOOK = [
  "Before the panel: open three terminals in the project1-uniguard folder and delete demo/sandbox.",
  "Terminal 1: python demo/seed_data.py, set UNIGUARD_PASSPHRASE and UNIGUARD_DASHBOARD_PASSWORD, run init, then run --dashboard.",
  "Terminal 2: python demo/fake_portal.py",
  "Browser: http://127.0.0.1:8080, log in with the dashboard password. Zoom to 125% for the projector.",
  "Scene 1: python demo/simulate_incident.py power-off. Point at the amber ON BATTERY card and the new power-loss snapshot.",
  "Scene 2: python demo/simulate_incident.py power-on. Then press Ctrl+C in terminal 2. Point at Student Portal DOWN.",
  "Scene 3: python demo/simulate_incident.py tamper. Point at the red RECORDS ALERT banner.",
  "Scene 4: python demo/simulate_incident.py ransomware. Point at the incident row: restored, quarantined, recovery time.",
  "Scene 5: click Verify backups. Then in terminal 3: python -m uniguard -c demo/demo_config.json audit",
  "If anything fails: python demo/run_demo.py --fast tells the same story in the terminal.",
];

const children = [
  new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("UniGuard: Defense Preparation")] }),
  new Paragraph({ spacing: { after: 240 }, children: [new TextRun({ text: "Likely questions from the panel, with short answers you can say in your own words. Practise out loud.", italics: true })] }),
];
let q = 0;
for (const [section, items] of QA) {
  children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(section)] }));
  for (const [question, answer] of items) {
    q++;
    children.push(new Paragraph({ spacing: { before: 160, after: 60 }, keepNext: true,
      children: [new TextRun({ text: `Q${q}. ${question}`, bold: true, color: "0B5D3B" })] }));
    children.push(new Paragraph({ spacing: { after: 120, line: 300 }, children: [new TextRun(answer)] }));
  }
}
children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun("Live Demo Runbook")] }));
RUNBOOK.forEach((t) => children.push(new Paragraph({ numbering: { reference: "steps", level: 0 }, spacing: { after: 100 }, children: [new TextRun(t)] })));
children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Numbers to Remember")] }));
[
  "23 of 23 automated tests pass",
  "195 MB, 2,000 files: full backup 6.2 s, incremental 0.1 s, verified restore 1.7 s",
  "Ransomware on 600 files: recovered and verified in 2.7 s",
  "Ransomware score: mass change 40, entropy 30, extension 20, note 20; critical at 50",
  "scrypt N = 2^15, r = 8, p = 1; AES-256-GCM with 96-bit random nonce; 1 MiB chunks",
  "12 national grid collapses in 2024; NDPA 2023 s.39 security, s.40 breach report in 72 hours",
].forEach((t) => children.push(new Paragraph({ numbering: { reference: "dots", level: 0 }, spacing: { after: 80 }, children: [new TextRun(t)] })));

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { size: 40, bold: true, color: "0A2E20", font: FONT }, paragraph: { spacing: { after: 120 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: "1C2733", font: FONT }, paragraph: { spacing: { before: 300, after: 80 }, outlineLevel: 0 } },
    ],
  },
  numbering: { config: [
    { reference: "steps", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "dots", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
  ] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1200, bottom: 1200, left: 1300, right: 1300 } } }, children }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(path.join(__dirname, "UniGuard_Defense_QA.docx"), b); console.log(`wrote defense doc with ${q} questions`); });
