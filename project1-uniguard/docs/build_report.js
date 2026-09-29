// Builds UniGuard_Report.docx.  Run:  NODE_PATH=<folder with docx> node docs/build_report.js
const path = require("path");
const K = require("../../tools/reportkit");
const { P, H1, H2, H3, bullets, numbered, Figure, Tbl, Code } = K;
const img = (f) => path.join(__dirname, "img", f);

const cover = K.coverPage({
  title: "UNIGUARD: AN AUTOMATED MONITORING, BACKUP AND RECOVERY SYSTEM FOR UNIVERSITY DIGITAL INFRASTRUCTURE",
  subtitle: "Designed for the operating conditions of Nigerian universities",
  lines: [
    "A report submitted in partial fulfilment of the requirements of",
    "CMP 468: Computer Security (2 Credit Units)",
    "",
    "BY",
    "[YOUR FULL NAME]",
    "[MATRIC NUMBER]",
    "",
    "LECTURER: [LECTURER'S NAME]",
    "",
    "[MONTH, YEAR]",
  ],
});

const abstract = [
  P("Nigerian universities now run admissions, course registration, fee payment, result processing and transcripts on digital systems. The same universities work with unstable grid power, costly internet links, small ICT budgets and a known risk of insiders altering examination records. A single ransomware infection, a failed disk or a generator switch-over in the middle of a write can destroy records that took decades to build. Most institutions still depend on manual copies to external drives, with no monitoring and no tested recovery."),
  P("This project designs, builds and evaluates **UniGuard**, an open-source system that monitors university servers and services, backs data up automatically with strong encryption, detects ransomware and unauthorised changes to result files, and restores damaged data without human action. Backups are split into chunks, deduplicated, compressed and encrypted with AES-256-GCM under a key derived from a passphrase with scrypt. Each snapshot is complete on its own, so no long backup chain can break. A detector scores file activity on four signals (share of files changed, Shannon entropy, ransomware file extensions and ransom notes) and triggers an incident response that freezes backups, preserves evidence, restores every damaged file from the last clean snapshot and verifies each one with SHA-256. Result folders are protected by approval windows, and every event is written to a hash-chained audit log that exposes any later edit. The design adds features for local conditions: an emergency backup when mains power fails, night-time offsite copies with a bandwidth cap, SMS alerts through Nigerian gateways, and more frequent backups during examination periods."),
  P("The system was implemented in Python and tested with 23 automated tests, all passing. On a dataset of 2,000 files (195 MB), a full backup took 6.2 seconds, an incremental backup after 1% of files changed took 0.1 seconds, and a simulated ransomware attack on 600 files was detected and fully reversed in 2.7 seconds, with every restored file verified. The results show that a low-cost, locally maintainable tool can give a Nigerian university strong protection for the confidentiality, integrity and availability of its records."),
  P("**Keywords:** backup and recovery, ransomware detection, file integrity monitoring, AES-GCM, audit log, university information systems, Nigeria."),
];

const s = [];

// ------------------------------------------------------------------ Chapter 1
s.push(H1("Chapter One: Introduction"));
s.push(H2("1.1 Background of the Study"));
s.push(P("Security in computing rests on three goals: confidentiality, integrity and availability, often called the CIA triad (Pfleeger et al., 2015). A university needs all three. Student records and staff payroll must stay private. Examination results must stay exactly as the Senate approved them. The student portal and result processing system must be available when thousands of students register or check results in the same week."));
s.push(P("Nigerian universities have moved most of these processes online. Admission offers flow through the JAMB Central Admissions Processing System (CAPS). Fees are paid through Remita. Course registration, result computation and transcripts run on portals built in-house or by vendors. This shift brings speed, but it also concentrates risk. When a single file server holds every department's results, one incident can stop the whole institution."));
s.push(P("The local environment adds pressure. Nigeria's national grid collapsed twelve times in 2024 alone (Guardian Nigeria, 2024). Campuses switch between grid power, diesel generators and inverters several times a day, and each abrupt cut can corrupt a file being written. Internet links are slow and expensive, so copying large backups to the cloud during working hours is often not practical. ICT units work with limited staff and budgets, which rules out costly commercial backup suites. Finally, cases of examination malpractice and unauthorised grade changes mean that a threat can come from inside the institution, not only from outside."));
s.push(P("The Nigeria Data Protection Act 2023 now requires every data controller, universities included, to put in place technical measures such as encryption and the ability to restore data promptly after an incident (Section 39), and to report personal data breaches to the Nigeria Data Protection Commission within 72 hours (Section 40). Good backup and monitoring practice is therefore a legal duty as well as a technical one."));

s.push(H2("1.2 Statement of the Problem"));
s.push(P("In many Nigerian universities, backup is manual and irregular. Staff copy folders to an external drive when they remember, the drive sits in the same office as the server, and nobody tests whether the copy can be restored. Monitoring is reactive: the ICT unit learns that the portal is down when students complain on social media. There is usually no record of who changed a result file and when."));
s.push(P("These gaps leave the institution exposed to five specific failures:"));
s.push(...numbered([
  "**Ransomware** encrypts the file server and any backup drive attached to it, leaving no clean copy.",
  "**Insider tampering** changes a student's grade after Senate approval, and nobody notices until a transcript is disputed.",
  "**Power failure** interrupts a write and corrupts a database or spreadsheet.",
  "**Hardware failure** of a disk destroys data that was never copied elsewhere.",
  "**Service outage** of the portal or result database goes unnoticed for hours during registration or result release.",
], "n1"));
s.push(P("No affordable tool addresses all five together in a way that suits local power, bandwidth and staffing conditions."));

s.push(H2("1.3 Aim and Objectives"));
s.push(P("The aim of this project is to develop an automated monitoring, backup and recovery system that protects the confidentiality, integrity and availability of university digital infrastructure under Nigerian operating conditions. The specific objectives are to:"));
s.push(...numbered([
  "design an encrypted, deduplicated and incremental backup system in which every snapshot can be restored on its own;",
  "monitor server health, campus services and power supply continuously and alert the right staff through SMS, email and a web dashboard;",
  "detect ransomware activity and unauthorised changes to protected records such as examination results;",
  "recover damaged data automatically, preserve evidence and verify the recovery;",
  "keep a tamper-evident audit trail of every backup, alert, login and recovery; and",
  "evaluate the system with automated tests, a live demonstration and performance measurements.",
], "n2"));

s.push(H2("1.4 Scope and Limitations"));
s.push(P("The system protects file-based data held on a university server: result sheets, student records, bursary files, admission lists, lecture materials and database backup files. It monitors services over HTTP and TCP and reads UPS status from Network UPS Tools or a status file. It does not replace endpoint antivirus, network firewalls or database-level replication, and it does not stop an attacker who steals the backup passphrase. The demonstration uses synthetic data; no real student information was used."));

s.push(H2("1.5 Significance of the Study"));
s.push(P("The project shows that a university can meet a large part of its data protection duty with free, auditable software that runs on an ordinary computer. It gives the Registry a way to prove that approved results have not changed, gives the ICT unit early warning of outages and attacks, and cuts recovery from ransomware from days of rebuilding to seconds. It also serves as a teaching tool: each module maps to a topic in the CMP 468 course outline, from encryption and decryption to security policies and standards."));

// ------------------------------------------------------------------ Chapter 2
s.push(H1("Chapter Two: Literature Review"));
s.push(H2("2.1 Characteristics of Computer Intrusion"));
s.push(P("Pfleeger et al. (2015) describe an intrusion by the method, opportunity and motive of the attacker. An attacker uses any available path, the weakest link, not the strongest defence. For a university, the weakest link is often a shared staff account on the result server or an unpatched office computer that has a mapped drive to the file share. Stallings and Brown (2018) add that intrusions pass through stages (reconnaissance, initial access, privilege escalation, action on objectives) and that detection at any stage limits the damage."));

s.push(H2("2.2 Types of Security Breaches and Classes of Attacks"));
s.push(P("Security breaches are commonly grouped by the property they violate. Interception breaks confidentiality, modification and fabrication break integrity, and interruption breaks availability (Pfleeger et al., 2015). Table 2.1 maps these classes to the threats a Nigerian university faces."));
s.push(...Tbl(["Class of attack", "University example", "Property lost"], [
  ["Interruption", "Ransomware encrypts the file server; portal DDoS during registration; grid collapse", "Availability"],
  ["Modification", "Insider raises a student's CMP 468 score after Senate approval", "Integrity"],
  ["Fabrication", "Fake admission list inserted into the CAPS upload folder", "Integrity"],
  ["Interception", "Stolen backup drive exposes payroll and student phone numbers", "Confidentiality"],
], [2000, 5026, 2000], "Table 2.1: Classes of attack and university examples"));

s.push(H2("2.3 Security Vulnerabilities in University Environments"));
s.push(P("Universities are open by design. Many staff and students share networks, bring personal devices and use weak or shared passwords. Legacy systems stay in service for years because replacing them is expensive. In Nigeria, these general weaknesses combine with unstable power, which causes unclean shutdowns, and with low investment in security testing. Backups kept on a drive that stays connected to the server are especially weak, because ransomware encrypts every drive it can reach (CISA, 2023)."));

s.push(H2("2.4 Backup Strategies"));
s.push(P("A **full backup** copies every file each time. It is simple to restore but slow and wasteful. An **incremental backup** copies only what changed since the last backup, which is fast, but a restore needs the full backup plus every increment in order; one bad link breaks the chain. A **differential backup** copies everything changed since the last full backup, trading space for a shorter chain."));
s.push(P("Content-addressed, deduplicating storage removes this trade-off. Files are split into chunks, each chunk is named by a hash of its content, and a chunk that already exists is not stored again. Every snapshot is a full list of chunks, so it restores on its own, yet it costs only the space of the changed chunks. UniGuard uses this approach."));
s.push(P("The **3-2-1 rule** recommends three copies of data, on two different media, with one copy offsite. **Grandfather-father-son (GFS)** retention keeps recent snapshots at fine intervals and older ones at coarser intervals (daily, weekly, monthly), so an institution can go back months without keeping every snapshot. NIST SP 800-34 (Swanson et al., 2010) adds two targets: the **recovery point objective (RPO)**, the most data the organisation can afford to lose, and the **recovery time objective (RTO)**, the longest it can afford to be down."));

s.push(H2("2.5 Ransomware Detection"));
s.push(P("Research shows that ransomware can be caught by watching what it does to files rather than by matching known malware signatures. Scaife et al. (2016) built CryptoDrop, which flags a process when files it touches show a sharp rise in entropy, change type and lose similarity to their previous content; it stopped samples after a median of ten files lost. Kharraz et al. (2016) built UNVEIL, which detects ransomware from its file-system access patterns and its ransom-note display. Continella et al. (2016) built ShieldFS, a file system that detects ransomware behaviour and rolls back affected files from shadow copies. UniGuard borrows two ideas from this work: entropy as a sign of encryption, and automatic rollback from a protected copy. It works at the file-server level, so it needs no kernel driver and runs on any operating system."));

s.push(H2("2.6 Encryption and Decryption for Backups"));
s.push(P("Backups hold the most sensitive data an institution has, all in one place, so they must be encrypted. Authenticated encryption protects confidentiality and integrity together. AES in Galois/Counter Mode (GCM) is a NIST-approved authenticated cipher that produces a tag which fails to verify if even one bit of the ciphertext changes (Dworkin, 2007). Its main rule is that a nonce must never repeat under the same key."));
s.push(P("People remember passphrases, not 256-bit keys. A key derivation function turns a passphrase into a key and makes each guess expensive. Scrypt is memory-hard, so attackers cannot cheaply run millions of guesses on graphics cards (Percival & Josefsson, 2016). HKDF then splits one master key into several independent keys for different jobs (Krawczyk & Eronen, 2010)."));

s.push(H2("2.7 Tamper-Evident Logging"));
s.push(P("An audit log is only useful if an insider cannot quietly edit it. Schneier and Kelsey (1999) proposed logs in which each entry is linked to the one before it by a cryptographic hash, so changing or deleting any entry breaks every link after it. Crosby and Wallach (2009) extended this idea to large-scale systems. UniGuard applies the simple hash-chain form."));

s.push(H2("2.8 Security Policies and Standards"));
s.push(bullets([
  "**ISO/IEC 27001:2022**: Annex A controls 8.13 (information backup), 8.15 (logging) and 8.16 (monitoring activities).",
  "**NIST SP 800-34 Rev. 1**: contingency planning, RPO and RTO (Swanson et al., 2010).",
  "**NIST SP 800-61 Rev. 2**: incident handling lifecycle of preparation, detection and analysis, containment, eradication and recovery, and post-incident activity (Cichonski et al., 2012).",
  "**Nigeria Data Protection Act 2023**: Section 39 (security, integrity and confidentiality, including encryption and timely restoration) and Section 40 (breach notification within 72 hours).",
  "**Cybercrimes (Prohibition, Prevention, etc.) Act 2015**: makes unauthorised access to and modification of computer data offences, which gives legal weight to audit evidence.",
]));

s.push(H2("2.9 Research Gap"));
s.push(P("Existing tools cover parts of the problem. Commercial suites are costly and assume steady power and bandwidth. Open-source backup tools encrypt and deduplicate but do not monitor services or detect ransomware. Research prototypes detect ransomware but do not manage backups, retention or offsite copies. None treats examination records as a special class of data with approval windows, and none reacts to power loss. UniGuard fills this gap with one integrated, low-cost system."));

// ------------------------------------------------------------------ Chapter 3
s.push(H1("Chapter Three: System Analysis and Design"));
s.push(H2("3.1 Methodology"));
s.push(P("The project followed an iterative prototyping approach. Requirements came from the problems in Section 1.2 and the standards in Section 2.8. Each module was built, tested with automated tests, and then joined to the others. A threat model guided which controls to build."));

s.push(H2("3.2 Requirements"));
s.push(H3("Functional requirements"));
s.push(bullets([
  "Take scheduled, encrypted, incremental backups of configured folders.",
  "Restore a whole snapshot, a folder or one file, and verify each restored file.",
  "Copy backups to a second site within a time window and a bandwidth budget.",
  "Check CPU, memory, disk, campus services and UPS state at a fixed interval.",
  "Detect ransomware and changes to protected folders outside approved windows.",
  "Respond to ransomware automatically: contain, preserve evidence, restore, verify, report.",
  "Send alerts by SMS, email, webhook and console, and show status on a web dashboard.",
  "Record every event in a tamper-evident audit log.",
]));
s.push(H3("Non-functional requirements"));
s.push(bullets([
  "**Security**: backups unreadable without the passphrase; offsite site sees only ciphertext.",
  "**Reliability**: an interrupted backup must not corrupt the repository.",
  "**Low cost**: free software, runs on an ordinary PC.",
  "**Bandwidth efficiency**: send only changed data, at off-peak times.",
  "**Usability**: one command to start; clear dashboard for non-specialist staff.",
]));

s.push(H2("3.3 Threat Model"));
s.push(...Tbl(["Threat", "Control in UniGuard"], [
  ["Ransomware on the file server", "Entropy and mass-change detection; automatic restore from last clean snapshot; backups written read-only; offsite copy out of reach"],
  ["Ransomware waits before striking (dwell time)", "Retention always keeps the last clean snapshot, however old"],
  ["Insider edits approved results", "Protected paths with approval windows; critical alert; later backups marked SUSPECT and never used for recovery"],
  ["Insider edits the audit log to hide tracks", "Hash chain breaks; dashboard shows AUDIT LOG TAMPERED"],
  ["Stolen backup drive or cloud bucket", "AES-256-GCM encryption; keyed object names reveal nothing about content"],
  ["Backup file altered or corrupted", "GCM tag and content hash checked on every read; verify command decrypts every object"],
  ["Power cut during backup", "Atomic write (temp file, fsync, rename); SQLite WAL; emergency backup when mains fails"],
  ["Dashboard password guessing", "Constant-time compare; lockout after 5 failures; CSRF header; security headers"],
], [3200, 5826], "Table 3.1: Threat model"));

s.push(H2("3.4 System Architecture"));
s.push(P("Figure 3.1 shows the architecture. On the left are the campus systems being protected. In the centre is the UniGuard engine with its modules. On the right are the storage locations and the people who receive alerts."));
s.push(...Figure(img("architecture.png"), 2600, 1440, "Figure 3.1: UniGuard architecture"));
s.push(...Tbl(["Module", "File", "Responsibility"], [
  ["Crypto", "crypto.py", "scrypt key derivation, HKDF key split, AES-256-GCM, keyed chunk names"],
  ["Repository", "repository.py", "Encrypted chunk store, snapshots, verification, garbage collection, offsite replication"],
  ["Backup engine", "backup.py", "Chunking, incremental backup, GFS retention, verified restore, diff"],
  ["Monitor", "monitor.py", "Host metrics, service checks, UPS state, integrity scan, ransomware and tamper rules"],
  ["Alert manager", "alerts.py", "Console, SMS (Africa's Talking, Termii), email, webhook; cooldown"],
  ["Audit log", "audit.py", "Hash-chained events, metrics, persistent state"],
  ["Engine", "engine.py", "Scheduler, peak periods, power response, incident response"],
  ["Dashboard", "dashboard.py", "Authenticated web interface"],
], [1800, 1700, 5526], "Table 3.2: Modules"));

s.push(H2("3.5 Cryptographic Design"));
s.push(P("At setup, the administrator chooses a passphrase of at least 12 characters. UniGuard generates a random 16-byte salt and runs scrypt (N = 2^15, r = 8, p = 1) to produce a 256-bit master key. HKDF-SHA256 derives two keys from it: an encryption key for AES-256-GCM and a separate key for HMAC-SHA256. The repository stores the salt and an encrypted check value, never the key."));
s.push(P("Each file is read in 1 MiB chunks. A chunk's name is HMAC-SHA256(key, chunk). Using a keyed hash instead of a plain SHA-256 means that someone who holds the backup cannot test whether it contains a known file. The chunk is compressed with zlib and encrypted with AES-256-GCM using a fresh random 96-bit nonce. The chunk's name is passed as associated data, so an attacker cannot swap two encrypted chunks without the swap being detected. Snapshot manifests are encrypted the same way. On restore, every chunk is decrypted, its tag is checked, its HMAC is recomputed, and finally the SHA-256 of the whole restored file is compared with the value recorded at backup time."));
s.push(...Code([
  "master  = scrypt(passphrase, salt, N=2^15, r=8, p=1)",
  "k_enc   = HKDF(master, info='uniguard-encryption')",
  "k_id    = HKDF(master, info='uniguard-object-id')",
  "id      = HMAC-SHA256(k_id, chunk)",
  "blob    = nonce(12 bytes) || AES-256-GCM(k_enc, nonce, zlib(chunk), aad=id)",
]));

s.push(H2("3.6 Detection Design"));
s.push(H3("Ransomware scoring"));
s.push(P("The integrity monitor compares the live file tree with the last clean snapshot. Files whose size and modification time are unchanged are skipped, so a scan is cheap. For changed files it computes Shannon entropy over the first 64 KiB. Plain text scores about 4 to 5 bits per byte; encrypted data scores close to 8. File types that are already compressed (PDF, DOCX, JPEG, ZIP) are excluded from the entropy signal to avoid false alarms. Table 3.3 shows the scoring."));
s.push(...Tbl(["Signal", "Condition", "Points"], [
  ["Mass change", "At least 5 files and 20% of all files modified or deleted", "40"],
  ["High entropy", "At least 3 changed files with entropy of 7.2 bits per byte or more", "30"],
  ["Ransomware extension", "New files ending in .locked, .encrypted, .lockbit and similar", "20"],
  ["Ransom note", "New text or HTML file with names like README, DECRYPT, RECOVER", "20"],
], [2200, 5226, 1600], "Table 3.3: Ransomware scoring (50 or more = critical, 20 to 49 = warning)"));
s.push(P("No single signal reaches the critical level alone. A lecturer who replaces many files at once gets at most a warning, while real ransomware, which changes many files and makes them look random, crosses 50 quickly."));
s.push(H3("Protected records"));
s.push(P("The Registry lists folders such as registry/results as protected and gives each one approved windows, for example the period between a Senate meeting and result publication. A change outside every window raises a critical alert naming the files. While that alert stays open, new backups are marked SUSPECT, and the recovery process ignores them. This keeps the last approved copy of the results available as evidence and for restoration."));

s.push(H2("3.7 Incident Response Design"));
s.push(P("The response follows the NIST SP 800-61 lifecycle (Cichonski et al., 2012), shown in Figure 3.2."));
s.push(...Figure(img("incident_flow.png"), 2600, 560, "Figure 3.2: Automatic ransomware response"));
s.push(...numbered([
  "**Detect**: the score reaches 50.",
  "**Contain**: lockdown mode stops new backups and retention, so encrypted files never replace good ones and no clean snapshot is deleted.",
  "**Preserve**: damaged files are copied, and files the attacker dropped are moved, into a quarantine folder named after the incident for forensic study.",
  "**Recover**: every modified or deleted file is restored from the last clean snapshot.",
  "**Verify**: each file's SHA-256 is checked, and the tree is scanned again.",
  "**Report**: SMS alerts go out, the recovery time is recorded, lockdown ends and a post-recovery snapshot is taken.",
], "n3"));

s.push(H2("3.8 Adaptation to Nigerian Conditions"));
s.push(...Tbl(["Local condition", "Design response"], [
  ["Frequent grid collapse and generator switch-over", "Reads UPS state; emergency backup when mains fails; critical alert when battery is low; atomic writes and SQLite WAL survive sudden cuts"],
  ["Costly, unreliable bandwidth", "Deduplication and compression; offsite copy in a night window; per-run byte cap; resumes after link loss; snapshots copied only after all their chunks"],
  ["Internet down during incidents", "SMS alerts through Africa's Talking or Termii reach phones without data"],
  ["Examination and registration peaks", "Peak periods in the config shorten the backup interval (for example hourly to every 15 minutes)"],
  ["Result tampering risk", "Protected paths, approval windows, SUSPECT snapshots, hash-chained audit log"],
  ["Small budget and staff", "Free software, Python only, runs on an old PC; one command to start; web dashboard"],
  ["NDPA 2023 duties", "Encryption and timely restoration (s.39); audit trail and incident record support 72-hour breach report (s.40)"],
], [3000, 6026], "Table 3.4: Local conditions and design responses"));

// ------------------------------------------------------------------ Chapter 4
s.push(H1("Chapter Four: Implementation and Testing"));
s.push(H2("4.1 Tools and Environment"));
s.push(...Tbl(["Item", "Choice", "Reason"], [
  ["Language", "Python 3.11", "Widely taught in Nigerian universities; runs on Windows and Linux"],
  ["Cryptography", "cryptography library (OpenSSL backend)", "Audited implementations of AES-GCM, scrypt, HKDF"],
  ["Database", "SQLite", "No server to manage; WAL mode survives power loss"],
  ["Web", "Flask", "Small and simple for a dashboard"],
  ["System metrics", "psutil", "CPU, memory and battery on all platforms"],
  ["Testing", "pytest", "Automated regression tests"],
], [1800, 3200, 4026], "Table 4.1: Tools"));

s.push(H2("4.2 Using the System"));
s.push(P("An administrator writes a JSON configuration naming the folder to protect, the backup location, the offsite location, the services to check and the protected paths. The passphrase and dashboard password are read from environment variables so they never sit in a file. The main commands are:"));
s.push(...Code([
  "python -m uniguard -c config.json init          # create encrypted repository",
  "python -m uniguard -c config.json run --dashboard",
  "python -m uniguard -c config.json snapshots     # list backups",
  "python -m uniguard -c config.json restore latest ./restore registry/results",
  "python -m uniguard -c config.json verify        # decrypt and check every chunk",
  "python -m uniguard -c config.json audit         # show log and check the chain",
]));

s.push(H2("4.3 The Dashboard"));
s.push(P("Figure 4.1 shows the dashboard after three staged incidents: mains power loss, a ransomware attack that was recovered automatically, and a grade change in the results folder, which is still open and shown in the red banner."));
s.push(...Figure(img("dashboard.png"), 2100, 1838, "Figure 4.1: UniGuard dashboard during a records alert"));

s.push(H2("4.4 Automated Tests"));
s.push(P("Twenty-three automated tests check the security properties of the system. All 23 pass."));
s.push(...Tbl(["Area", "What the tests prove"], [
  ["Encryption", "Round trip works; one flipped bit is detected; swapping ciphertexts between names is detected; same plaintext encrypts differently each time; wrong and short passphrases are rejected; no plaintext appears anywhere in the repository"],
  ["Backup and restore", "Restored files match byte for byte; second backup stores only the change; files over 1 MiB are chunked; corrupted chunks fail verification; selective restore and diff work"],
  ["Retention", "Pinned and last clean snapshots survive pruning; repository still verifies after garbage collection"],
  ["Offsite copy", "Byte budget is respected; no snapshot is copied before its chunks; the offsite copy opens and verifies"],
  ["Detection", "Entropy values are correct; ransomware is flagged critical; normal lecturer edits are not; protected paths alert outside the window and stay quiet inside it"],
  ["Audit log", "Editing a row and deleting a row are both detected"],
  ["Engine", "Ransomware is fully reversed and quarantined; power loss triggers an emergency backup; tampering marks later backups SUSPECT; service outage raises an alert"],
  ["Dashboard", "Login required; wrong password rejected; CSRF header required; lockout after 5 failures"],
], [2000, 7026], "Table 4.2: Test coverage (23 tests, 23 passed)"));

s.push(H2("4.5 Demonstration Scenario Results"));
s.push(P("The narrated demonstration (demo/run_demo.py) runs seven scenes on synthetic data for a Nigerian university: 120 students, results for five 400-level courses, fee payments, a CAPS admission list, lecture notes and a staff payroll database."));
s.push(...Tbl(["Scene", "Event", "UniGuard response"], [
  ["1", "First backup of 24 files", "Encrypted snapshot in 0.02 s"],
  ["2", "One lecture note added", "Second backup stores 56 bytes; offsite copy sent"],
  ["3", "Grid power fails; battery falls to 20%; power returns", "Warning SMS and emergency backup; critical SMS at 20%; restoration notice"],
  ["4", "Student Portal stops", "Critical SMS within one monitoring cycle"],
  ["5", "Insider changes a CMP468 score from 43 (E) to 88 (A)", "Critical SMS naming the file; next backup marked SUSPECT; Registrar restores approved results"],
  ["6", "Ransomware scrambles 16 of 24 files and drops a note", "Detected with score 110; 16 files restored and verified; 17 malicious files quarantined"],
  ["7", "Insider edits the audit log", "Chain check reports the exact row altered"],
], [900, 3800, 4326], "Table 4.3: Demonstration results"));

s.push(H2("4.6 Performance"));
s.push(P("To test beyond the small demo, the benchmark script (docs/benchmark.py) generated 2,000 CSV records of 100 KiB each (195 MB) on a 4-core cloud machine. Table 4.4 shows the results."));
s.push(...Tbl(["Measurement", "Result"], [
  ["Full first backup (195 MB)", "6.2 s"],
  ["Repository size after first backup", "22.3 MB (the synthetic text compresses well; real data compresses less)"],
  ["Incremental backup after 1% of files changed", "0.1 s, 224 KiB stored"],
  ["Full restore with SHA-256 check of every file", "1.7 s"],
  ["Ransomware on 600 files (30%): detection to full recovery", "2.7 s end to end; 1.5 s from detection to verified recovery"],
], [5000, 4026], "Table 4.4: Performance on 2,000 files"));
s.push(P("In NIST terms, the achieved RTO for this attack is under three seconds, compared with days for manual rebuilding. The RPO equals the backup interval: 60 minutes in normal periods and 15 minutes during examination periods in the recommended configuration."));

s.push(H2("4.7 Mapping to the CMP 468 Course Outline"));
s.push(...Tbl(["Course topic", "Where it appears in UniGuard"], [
  ["Overview of security in computing", "CIA triad drives the design (Section 1.1)"],
  ["Characteristics of computer intrusion", "Threat model; ransomware and insider behaviour (Sections 2.1, 3.3)"],
  ["Types of security breaches", "Interruption, modification, fabrication, interception (Table 2.1)"],
  ["Security vulnerability", "Attached backup drives, shared accounts, power cuts (Section 2.3)"],
  ["Classes of attacks", "Ransomware, insider tampering, log tampering, password guessing"],
  ["Methods of defense and controls", "Prevention (encryption, read-only backups), detection (scoring, integrity), recovery (automatic restore)"],
  ["Encryption and decryption", "scrypt, HKDF, AES-256-GCM, HMAC (Section 3.5)"],
  ["Database security", "SQLite audit log with hash chain; payroll database backed up and verified"],
  ["Network security", "Service monitoring; dashboard login, lockout, CSRF, security headers; ciphertext-only offsite link"],
  ["Security policies and standards", "ISO/IEC 27001, NIST SP 800-34 and 800-61, NDPA 2023, Cybercrimes Act 2015"],
], [3300, 5726], "Table 4.5: Course topics covered"));

// ------------------------------------------------------------------ Chapter 5
s.push(H1("Chapter Five: Discussion"));
s.push(H2("5.1 Strengths"));
s.push(bullets([
  "One system covers backup, monitoring, detection, recovery and audit, which small ICT units can run.",
  "Every snapshot restores on its own, so there is no fragile incremental chain.",
  "Recovery is automatic and verified, which removes the delay of waiting for staff.",
  "The design treats examination records as a special asset, which matches a real Nigerian risk.",
  "Offsite storage never sees plaintext, so a cheap cloud bucket or a partner university's server can hold the copy.",
]));
s.push(H2("5.2 Limitations"));
s.push(bullets([
  "Changes made after the last clean backup are lost in a ransomware attack. A shorter interval reduces this window.",
  "Ransomware that encrypts files slowly, a few at a time, may stay below the mass-change threshold. The entropy and extension signals still apply, and thresholds can be tuned.",
  "The read-only permission on backup files stops ordinary malware but not an attacker with administrator rights on the same server. The offsite copy on a separate machine answers that case; an immutable object store would be stronger.",
  "Losing the passphrase makes every backup unreadable. The passphrase must be split or sealed and stored under dual control.",
  "Protected-path rules watch files, not database rows. Result systems that store grades only inside a database need database-level auditing as well.",
]));
s.push(H2("5.3 Cost"));
s.push(P("UniGuard needs no licence. A university can run it on an existing server or a refurbished desktop with a second disk. The main recurring costs are an external or partner-site disk for the offsite copy and SMS credit for alerts. Commercial backup suites typically charge per server or per terabyte each year, which puts them out of reach for many departmental servers."));
s.push(H2("5.4 Deployment Plan for a Nigerian University"));
s.push(...numbered([
  "Pilot on one faculty file server and the Registry result folder for one semester.",
  "Set the offsite copy to a server at a second campus, a partner university over NgREN, or a cloud bucket hosted in Nigeria to support data sovereignty.",
  "Register the ICT Director, Registrar and Deputy Registrar (Academic) for SMS alerts.",
  "Write the protected-path windows into the Senate-approved result processing calendar.",
  "Seal the passphrase in two envelopes held by the Registrar and the Director of ICT.",
  "Run a restore drill every month and record the time taken.",
  "Extend to the bursary, admissions and library servers after the pilot review.",
], "n4"));

// ------------------------------------------------------------------ Chapter 6
s.push(H1("Chapter Six: Conclusion and Recommendations"));
s.push(H2("6.1 Summary"));
s.push(P("This project set out to protect university digital infrastructure under Nigerian conditions. It produced UniGuard, a working system that encrypts, deduplicates and schedules backups, copies them offsite over a limited link, monitors servers, services and power, detects ransomware and unauthorised changes to results, recovers automatically with verification, and records every event in a tamper-evident log. All six objectives in Section 1.3 were met, and 23 automated tests confirm the security properties."));
s.push(H2("6.2 Conclusion"));
s.push(P("Strong data protection does not require expensive software. Sound cryptography, content-addressed storage, simple behaviour-based detection and careful attention to local conditions give a university real protection against the threats it faces most: ransomware, insider tampering, power failure and service outages. The measured recovery time of under three seconds for a 600-file attack shows what automation makes possible."));
s.push(H2("6.3 Recommendations"));
s.push(...numbered([
  "Universities should adopt the 3-2-1 rule with at least one offsite, encrypted copy, and test restores monthly.",
  "The Registry should define result approval windows formally and monitor result folders against them.",
  "ICT units should take backup media off the network, or use a pull-based offsite copy, so ransomware cannot reach every copy.",
  "Management should include backup and restoration in the institution's NDPA 2023 compliance plan and its 72-hour breach response procedure.",
  "Future work: database row-level auditing for result systems, immutable object storage, per-process detection on staff PCs, and a mobile app for alerts.",
], "n5"));

// ------------------------------------------------------------------ References
s.push(H1("References"));
[
  "Cichonski, P., Millar, T., Grance, T., & Scarfone, K. (2012). _Computer security incident handling guide_ (NIST Special Publication 800-61 Rev. 2). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-61r2",
  "CISA & MS-ISAC. (2023). _#StopRansomware guide_. Cybersecurity and Infrastructure Security Agency. https://www.cisa.gov/stopransomware/ransomware-guide",
  "Continella, A., Guagnelli, A., Zingaro, G., De Pasquale, G., Barenghi, A., Zanero, S., & Maggi, F. (2016). ShieldFS: A self-healing, ransomware-aware filesystem. In _Proceedings of the 32nd Annual Computer Security Applications Conference_ (pp. 336–347). ACM. https://doi.org/10.1145/2991079.2991110",
  "Crosby, S. A., & Wallach, D. S. (2009). Efficient data structures for tamper-evident logging. In _Proceedings of the 18th USENIX Security Symposium_ (pp. 317–334). USENIX Association.",
  "Dworkin, M. (2007). _Recommendation for block cipher modes of operation: Galois/Counter Mode (GCM) and GMAC_ (NIST Special Publication 800-38D). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-38D",
  "Federal Republic of Nigeria. (2015). _Cybercrimes (Prohibition, Prevention, etc.) Act, 2015_.",
  "Federal Republic of Nigeria. (2023). _Nigeria Data Protection Act, 2023_ (Act No. 37). Federal Government Printer.",
  "Guardian Nigeria. (2024, December). Timeline: The 12 times national grid collapsed in 2024. _The Guardian (Nigeria)_. https://guardian.ng/news/timeline-the-12-times-national-grid-collapsed-in-2024/",
  "International Organization for Standardization. (2022). _ISO/IEC 27001:2022 Information security, cybersecurity and privacy protection: Information security management systems: Requirements_. ISO.",
  "Kharraz, A., Arshad, S., Mulliner, C., Robertson, W., & Kirda, E. (2016). UNVEIL: A large-scale, automated approach to detecting ransomware. In _Proceedings of the 25th USENIX Security Symposium_ (pp. 757–772). USENIX Association.",
  "Krawczyk, H., & Eronen, P. (2010). _HMAC-based extract-and-expand key derivation function (HKDF)_ (RFC 5869). Internet Engineering Task Force. https://doi.org/10.17487/RFC5869",
  "Percival, C., & Josefsson, S. (2016). _The scrypt password-based key derivation function_ (RFC 7914). Internet Engineering Task Force. https://doi.org/10.17487/RFC7914",
  "Pfleeger, C. P., Pfleeger, S. L., & Margulies, J. (2015). _Security in computing_ (5th ed.). Prentice Hall.",
  "Scaife, N., Carter, H., Traynor, P., & Butler, K. R. B. (2016). CryptoLock (and drop it): Stopping ransomware attacks on user data. In _2016 IEEE 36th International Conference on Distributed Computing Systems_ (pp. 303–312). IEEE. https://doi.org/10.1109/ICDCS.2016.46",
  "Schneier, B., & Kelsey, J. (1999). Secure audit logs to support computer forensics. _ACM Transactions on Information and System Security, 2_(2), 159–176. https://doi.org/10.1145/317087.317089",
  "Stallings, W., & Brown, L. (2018). _Computer security: Principles and practice_ (4th ed.). Pearson.",
  "Swanson, M., Bowen, P., Phillips, A. W., Gallup, D., & Lynes, D. (2010). _Contingency planning guide for federal information systems_ (NIST Special Publication 800-34 Rev. 1). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-34r1",
].forEach((r) => s.push(P(r, { align: "left", para: { indent: { left: 720, hanging: 720 } } })));

// ------------------------------------------------------------------ Appendix
s.push(H1("Appendix A: Running the Demonstration"));
s.push(...Code([
  "pip install -r requirements.txt",
  "python -m pytest -q                      # 23 passed",
  "python demo/run_demo.py                  # narrated, seven scenes",
  "",
  "# Live dashboard",
  "python demo/seed_data.py",
  "export UNIGUARD_PASSPHRASE=\"demo-passphrase-CMP468-2026\"",
  "export UNIGUARD_DASHBOARD_PASSWORD=\"cmp468\"",
  "python -m uniguard -c demo/demo_config.json init",
  "python -m uniguard -c demo/demo_config.json run --dashboard",
  "python demo/fake_portal.py               # second terminal",
  "python demo/simulate_incident.py power-off | tamper | ransomware",
]));
s.push(H1("Appendix B: Sample Configuration (extract)"));
s.push(...Code([
  "{",
  "  \"institution\": \"Federal University of Technology\",",
  "  \"source\": \"/srv/fileshare\",",
  "  \"repository\": \"/mnt/backup_disk/uniguard\",",
  "  \"offsite\": {\"path\": \"/mnt/partner_campus\", \"window\": {\"start\": \"22:00\", \"end\": \"05:00\"},",
  "              \"max_mb_per_run\": 2000},",
  "  \"intervals\": {\"monitor_s\": 30, \"backup_s\": 3600, \"peak_backup_s\": 900},",
  "  \"peak_periods\": [{\"label\": \"Exams\", \"start\": \"2026-07-01T00:00\", \"end\": \"2026-08-15T23:59\"}],",
  "  \"services\": [{\"name\": \"Student Portal\", \"type\": \"http\", \"target\": \"https://portal.example.edu.ng\"}],",
  "  \"power\": {\"source\": \"nut\", \"ups\": \"ups@localhost\"},",
  "  \"protected_paths\": [{\"path\": \"registry/results\", \"allowed_windows\": [...]}],",
  "  \"alerts\": [{\"type\": \"termii\", \"api_key\": \"env:TERMII_KEY\", \"recipients\": [\"23480...\"]}]",
  "}",
]));

K.buildDoc({ cover, abstract, sections: s, out: path.join(__dirname, "UniGuard_Report.docx"),
  headerText: "CMP 468: UniGuard Monitoring, Backup and Recovery System" })
  .then(() => console.log("wrote UniGuard_Report.docx"));
