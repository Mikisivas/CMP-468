// Builds AgroPeace_Presentation.pptx.  Run: NODE_PATH=<modules> node docs/build_slides.js
const path = require("path");
const pptxgen = require("pptxgenjs");
const { icon, makeTheme } = require("../../tools/deckkit");
const fa = require("react-icons/fa");
const gi = require("react-icons/gi");

const T = makeTheme({
  primary: "7A4A1F", dark: "2B1D12", ink: "22201C", muted: "6B645A", tint: "F4EEE4",
  green: "3F7F45", alert: "C0262D", amber: "D7A526", orange: "E0701E", white: "FFFFFF",
});
const { W, H, M } = T;
const img = (f) => path.join(__dirname, "img", f);
const FOOT = "CMP 468 · AgroPeace";

(async () => {
  const I = {};
  for (const [k, c] of [["cow", gi.GiCow], ["wheat", gi.GiWheat], ["map", fa.FaMapMarkedAlt], ["sat", fa.FaSatelliteDish],
    ["phone", fa.FaMobileAlt], ["users", fa.FaUsers], ["shield", fa.FaShieldAlt], ["lock", fa.FaLock], ["eye", fa.FaEyeSlash],
    ["sig", fa.FaSignature], ["redo", fa.FaRedo], ["filter", fa.FaFilter], ["chain", fa.FaLink], ["comment", fa.FaCommentDots],
    ["fire", fa.FaFire], ["bullhorn", fa.FaBullhorn], ["dove", fa.FaDove], ["check", fa.FaCheck]]) I[k] = await icon(c, "FFFFFF");

  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = "AgroPeace: GIS early warning for farmer/herder conflict";
  let n = 0;
  const next = (bg) => { n++; const s = pres.addSlide(); s.background = { color: bg || T.white }; return s; };
  const txt = (s, t, x, y, w, h, o = {}) => s.addText(t, { x, y, w, h, fontFace: T.fBody, fontSize: 16, color: T.ink, margin: 0, isTextBox: true, valign: "top", ...o });

  // 1 Title
  let s = next(T.dark);
  T.badge(s, I.dove, M, 1.1, 1.1, T.green);
  txt(s, "AgroPeace", M, 2.4, 11, 1.1, { fontFace: T.fHead, fontSize: 60, bold: true, color: T.white });
  txt(s, "A GIS-based early warning and real-time response framework for farmer/herder conflict resolution", M, 3.5, 11.5, 1.0, { fontSize: 24, color: "EADBC8" });
  txt(s, "Case study: Guma, Agatu, Logo and Gwer West LGAs, Benue State", M, 4.55, 11, 0.5, { fontSize: 16, italic: true, color: "C9B59C" });
  txt(s, "[Your Name]  ·  [Matric No]  ·  CMP 468: Computer Security  ·  [Date]", M, 6.3, 12, 0.4, { fontSize: 14, color: "EADBC8" });
  s.addNotes("Good morning. My second project answers the question: develop a GIS-based early warning and real-time framework for farmer/herder conflict resolution. I built AgroPeace and used Benue State as the case study, because Benue has suffered some of the worst of this conflict.");

  // 2 Problem
  s = next();
  T.kicker(s, "The problem");
  T.title(s, "Hours separate a stray herd from a killing");
  const st = [["47", "incidents around Gbajimba, Guma LGA, in 2015 to 2018, the highest in Guma and Logo (Musa et al., 2024)", T.alert],
    ["2017", "Benue bans open grazing; the conflict escalated rather than calmed (Nwankwo, 2024a)", T.primary],
    ["Hours", "between crops being destroyed and a reprisal: long enough to act, if the right people know", T.green]];
  st.forEach(([v, l, c], i) => { const x = M + i * 4.1; T.card(s, x, 1.75, 3.8, 3.0); T.stat(s, v, l, x + 0.35, 1.95, 3.1, c); });
  txt(s, "The information to act early exists: herd movements, crop seasons, past incidents, community warnings. It is scattered, unverified and slow.", M, 5.1, W - 2 * M, 1.0, { fontSize: 18 });
  T.footer(s, FOOT, n);
  s.addNotes("Mapping of ACLED records by Musa and colleagues in 2024 found 47 incidents around Gbajimba in Guma LGA between 2015 and 2018, the highest in Guma and Logo. Benue banned open grazing in 2017, but Nwankwo's 2024 study found the conflict escalated rather than calmed. My key observation: most incidents take hours to escalate. That gap is the opportunity.");

  // 3 Chain
  s = next();
  T.kicker(s, "How a dispute becomes a massacre");
  T.title(s, "Break the chain early");
  const chain = [[I.cow, "Herd heads\nfor farms", T.primary], [I.wheat, "Crops\ndestroyed", T.amber], [I.comment, "Rumour\nspreads", T.orange],
    [I.users, "Youths\nmobilise", T.orange], [I.fire, "Reprisal", T.alert]];
  chain.forEach(([ic, t, c], i) => {
    const x = M + 0.2 + i * 2.5;
    T.badge(s, ic, x + 0.45, 1.9, 1.1, c);
    txt(s, t, x, 3.15, 2.0, 0.9, { fontSize: 17, bold: true, align: "center" });
    if (i < 4) txt(s, "→", x + 1.85, 2.15, 0.6, 0.6, { fontSize: 30, color: T.muted, align: "center" });
  });
  const fix = [["Forecast + SMS to herder", 0], ["Case to peace committee", 1], ["Trust scoring holds rumours", 2], ["Escalate to Agro Rangers", 3]];
  fix.forEach(([t, i]) => {
    const x = M + 0.2 + i * 2.5;
    T.card(s, x - 0.1, 4.35, 2.2, 1.3, "E8F1E6");
    txt(s, t, x, 4.45, 2.0, 1.1, { fontSize: 14, color: T.green, bold: true, align: "center", valign: "middle" });
  });
  txt(s, "AgroPeace steps in at four points", M, 6.0, 8, 0.5, { fontSize: 15, italic: true, color: T.muted });
  T.footer(s, FOOT, n);
  s.addNotes("This is the chain. AgroPeace intervenes at four points: it warns the herder before the herd reaches the farm, it opens a case for the peace committee when damage starts, it holds back unverified rumours, and it escalates to the Agro Rangers when nobody acts.");

  // 4 Objectives
  s = next();
  T.kicker(s, "Aim and objectives");
  T.title(s, "Warn early, verify, respond, protect");
  ["GIS engine and explainable risk model", "Signed herd tracking with forecast and geofences", "USSD and web reporting with trust scoring",
    "LGA-based routing and escalation", "Security against forgery, replay, exposure and tampering", "Evaluation by tests, demo and benchmarks"]
    .forEach((t, i) => {
      const x = M + (i % 2) * 6.1, y = 1.7 + Math.floor(i / 2) * 1.6;
      T.card(s, x, y, 5.8, 1.35);
      txt(s, String(i + 1), x + 0.25, y + 0.2, 0.9, 0.95, { fontFace: T.fHead, fontSize: 40, bold: true, color: T.primary, valign: "middle" });
      txt(s, t, x + 1.2, y + 0.15, 4.4, 1.05, { fontSize: 17, valign: "middle" });
    });
  T.footer(s, FOOT, n);
  s.addNotes("Six objectives, all met.");

  // 5 Architecture
  s = next();
  T.kicker(s, "Design");
  T.title(s, "Architecture");
  s.addImage({ path: img("architecture.png"), x: (W - 10) / 2, y: 1.35, w: 10, h: 10 * 1440 / 2600 });
  T.footer(s, FOOT, n);
  s.addNotes("Field inputs on the left: signed GPS collars, USSD from any phone, web reports and map layers. Everything passes a security gate first. The tracker and report store feed the risk model and case book. Outputs go to herders by SMS, to peace committees and associations, to the Agro Rangers, and to a role-filtered dashboard. Every step is written to a hash-chained audit log.");

  // 6 Risk model
  s = next();
  T.kicker(s, "GIS risk model");
  T.title(s, "Five factors every mediator can understand");
  s.addChart(pres.charts.BAR, [{ name: "Weight", labels: ["Past incidents (kernel density)", "Herds near crops (live + forecast)", "Crops in the field (season)", "Community reports (by trust)", "Dry-season water competition"], values: [0.30, 0.30, 0.15, 0.15, 0.10] }], {
    x: M, y: 1.5, w: 7.3, h: 4.8, barDir: "bar", chartColors: [T.primary], showValue: true, dataLabelPosition: "outEnd",
    dataLabelFontSize: 14, dataLabelColor: T.ink, dataLabelFormatCode: "0.00", catAxisLabelFontSize: 13, catAxisLabelColor: T.ink,
    valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
    showTitle: true, title: "Weight in risk score", titleFontSize: 13, titleColor: T.muted, catAxisOrientation: "maxMin",
  });
  T.card(s, 8.3, 1.6, 4.4, 4.8);
  txt(s, "2,010 cells of 2.8 km", 8.6, 1.8, 3.9, 0.5, { fontFace: T.fHead, fontSize: 20, bold: true, color: T.primary });
  T.bullets(s, ["Low < 0.20 · elevated · high · severe ≥ 0.50", "Seasons built in: rains April to October, harvest to December, dry-season water stress",
    "Every score names its drivers, e.g. \"past incidents nearby, herds close to crops\"", "Weights to be calibrated with ACLED data"],
    8.6, 2.45, 3.9, 3.8, { fontSize: 15 });
  T.footer(s, FOOT, n);
  s.addNotes("Each grid cell gets a score from five factors. The two biggest are past incidents, using kernel density with age decay, and herds close to crops. Explainability matters: a peace committee will not act on a black box, so every score names its drivers. The weights are starting values; a real deployment would calibrate them with ACLED conflict data.");

  // 7 Tracking
  s = next();
  T.kicker(s, "Real time");
  T.title(s, "See the herd coming, three hours ahead");
  s.addImage({ path: img("ap_forecast.png"), x: M, y: 1.4, w: 5.3 * 1605 / 1325, h: 5.3 });
  const ev = [["Forecast", "position at +1, +2, +3 h from speed and heading"], ["Early warning", "forecast enters a farm: SMS to herder with safe route"],
    ["Incursion", "herd inside farm: case to peace committee"], ["No repeats", "events fire only when the zone changes"]];
  ev.forEach(([h, d], i) => {
    const y = 1.55 + i * 1.2;
    T.badge(s, [I.sat, I.bullhorn, I.cow, I.filter][i], 8.3, y, 0.65);
    txt(s, h, 9.15, y - 0.05, 3.6, 0.4, { fontFace: T.fHead, fontSize: 18, bold: true });
    txt(s, d, 9.15, y + 0.35, 3.6, 0.7, { fontSize: 14, color: T.muted });
  });
  T.footer(s, FOOT, n);
  s.addNotes("Each signed GPS fix updates the herd's speed and heading. The dashed red line is the three-hour forecast. When a forecast point falls inside a farm during crop season, the herder is warned while there is still time to turn. The state machine only raises an event when the herd's zone changes, so responders are not spammed.");

  // 8 SMS example
  s = next();
  T.kicker(s, "Early warning to the herder");
  T.title(s, "Tell them where to go, in their language");
  s.addShape("roundRect", { x: M + 0.4, y: 1.5, w: 4.2, h: 5.2, rectRadius: 0.35, fill: { color: "1B1B1B" }, line: { type: "none" } });
  s.addShape("roundRect", { x: M + 0.65, y: 1.95, w: 3.7, h: 4.3, rectRadius: 0.1, fill: { color: "F2EFE8" }, line: { type: "none" } });
  txt(s, "AgroPeace", M + 0.85, 2.1, 3.3, 0.35, { fontSize: 13, bold: true, color: T.primary });
  s.addShape("roundRect", { x: M + 0.8, y: 2.5, w: 3.4, h: 2.7, rectRadius: 0.12, fill: { color: T.white }, line: { color: "D8D2C6", width: 1 } });
  txt(s, "AgroPeace gargadi: garken ku H1 zai kai gonaki kusa da Yelwata cikin awa 3. Ku juya zuwa Guma East Grazing Reserve (NE) ta hanyar Route R2.", M + 0.95, 2.6, 3.1, 2.5, { fontSize: 14 });
  T.card(s, 6.0, 1.6, 6.7, 2.1);
  txt(s, "English meaning", 6.3, 1.75, 6, 0.4, { fontFace: T.fHead, fontSize: 18, bold: true, color: T.primary });
  txt(s, "Warning: your herd H1 will reach farms near Yelwata in about 3 hours. Turn toward Guma East Grazing Reserve (north-east) along Route R2.", 6.3, 2.2, 6.1, 1.4, { fontSize: 15 });
  T.bullets(s, ["Hausa, Nigerian Pidgin and English templates; Tiv, Idoma and Fulfulde to add with native speakers",
    "Nearest reserve, compass direction and stock route come from the GIS layers",
    "Plain SMS: works on any phone, no data", "Outbox never stores phone numbers"], 6.0, 4.0, 6.7, 2.7, { fontSize: 15 });
  T.footer(s, FOOT, n);
  s.addNotes("This is the actual message the system sent in my demo. It is in Hausa because the herder registered Hausa. It does not just say 'stay away'; it tells the herder where to go and which route to take. The Hausa must be checked by a native speaker before field use, and I say so in the report.");

  // 9 USSD + trust
  s = next();
  T.kicker(s, "Community reporting");
  T.title(s, "Every phone can report, rumours stay put");
  s.addShape("roundRect", { x: M + 0.4, y: 1.5, w: 4.2, h: 5.2, rectRadius: 0.35, fill: { color: "1B1B1B" }, line: { type: "none" } });
  s.addShape("rect", { x: M + 0.65, y: 1.95, w: 3.7, h: 3.4, fill: { color: "0E2415" }, line: { type: "none" } });
  txt(s, "*347*468#\n\nAgroPeace (Benue)\n1. Cattle on my farm\n2. Threat or attack\n3. Cattle stolen\n4. Check risk in my area", M + 0.85, 2.1, 3.3, 3.1, { fontFace: "Courier New", fontSize: 14, color: "B7F5C6" });
  txt(s, "Type, LGA, community, confirm", M + 0.65, 5.55, 3.7, 0.8, { fontSize: 13, color: "CFE8D5", align: "center" });
  const tr = [["Channel base", "mediator 0.85 · USSD 0.40 · anonymous web 0.30"], ["+ independent reporters", "+0.15 each within 3 km and 6 h (max +0.30)"],
    ["+ GPS confirmation", "+0.25 if a collar shows a herd within 2 km"], ["± reputation", "+0.10 per confirmed report, -0.20 per false one"]];
  tr.forEach(([h, d], i) => {
    const y = 1.55 + i * 0.95;
    txt(s, h, 6.0, y, 2.8, 0.8, { fontFace: T.fHead, fontSize: 17, bold: true, valign: "middle" });
    txt(s, d, 8.8, y, 3.9, 0.8, { fontSize: 14, color: T.muted, valign: "middle" });
  });
  T.card(s, 6.0, 5.45, 6.7, 1.25, "FBEDEE");
  txt(s, "Below 0.45 = unverified: never broadcast, never public, never triggers security. A lone \"they are coming tonight\" stays quiet until someone else confirms it.", 6.25, 5.5, 6.25, 1.15, { fontSize: 15, valign: "middle" });
  T.footer(s, FOOT, n);
  s.addNotes("USSD works on the cheapest phone without data, and rural Nigerians already use it for banking. Crowdsourced reporting is fast, but anyone can report anything, and a 2026 Bauchi study found WhatsApp and Facebook were the main channels for farmer-herder misinformation. So every report gets a trust score. The key rule: unverified reports are never broadcast. That is how the system avoids becoming a rumour amplifier.");

  // 10 Escalation
  s = next();
  T.kicker(s, "Conflict resolution workflow");
  T.title(s, "Mediation first, force last");
  s.addImage({ path: img("escalation.png"), x: M, y: 1.5, w: W - 2 * M, h: (W - 2 * M) * 720 / 2600 });
  T.bullets(s, ["Responders chosen by LGA from the directory", "Reply \"ACK C-001\" by SMS from a registered number to acknowledge",
    "No acknowledgement before the deadline: the case climbs a rung automatically",
    "Cases close with an outcome: herd rerouted, dialogue held, compensation agreed, security deployed, false alarm"],
    M, 5.0, W - 2 * M, 1.9, { fontSize: 16 });
  T.footer(s, FOOT, n);
  s.addNotes("The ladder puts herders and associations first, then peace committees and farmers, and only then the Agro Rangers and LGA security. Responders acknowledge by plain SMS. If nobody acknowledges in time, the case escalates by itself. Recorded outcomes build evidence of what works.");

  // 11 Security
  s = next();
  T.kicker(s, "Computer security");
  T.title(s, "Here, bad data can get people killed");
  const sec = [[I.sig, "Forged GPS", "HMAC-SHA256 per-device signature"], [I.redo, "Replayed message", "120 s window + nonce cache"],
    [I.lock, "Informant exposure", "AES-256-GCM phone numbers, keyed pseudonyms"], [I.eye, "Herds targeted", "public never sees herd positions"],
    [I.filter, "Rumour flooding", "trust scoring + 3 reports/hour limit"], [I.chain, "Covering tracks", "hash-chained audit log"]];
  sec.forEach(([ic, h, d], i) => {
    const x = M + (i % 3) * 4.1, y = 1.6 + Math.floor(i / 3) * 2.55;
    T.card(s, x, y, 3.85, 2.3);
    T.badge(s, ic, x + 0.25, y + 0.25, 0.65, T.alert);
    txt(s, h, x + 1.05, y + 0.25, 2.65, 0.65, { fontFace: T.fHead, fontSize: 18, bold: true, valign: "middle" });
    txt(s, d, x + 0.25, y + 1.1, 3.4, 1.0, { fontSize: 15 });
  });
  T.footer(s, FOOT, n);
  s.addNotes("This is where the course comes in. A forged GPS message could place a herd in a farm and start a reprisal, so every collar signs its messages. Old messages are rejected by timestamp and nonce. Phone numbers of informants are encrypted; records carry only a keyed pseudonym. The public never sees herd positions. Trust scoring and rate limits stop flooding. And every action is in a hash-chained log.");

  // 12 Roles
  s = next();
  T.kicker(s, "Least privilege");
  T.title(s, "Each role sees only what it needs");
  const roles = [["Public", "Community risk levels only. No herds, no cases, no unverified reports.", "8A8378"],
    ["Mediator", "Precise herds, cases and reports in their own LGA. Acknowledge, resolve, confirm or reject reports.", T.green],
    ["Coordinator", "All LGAs, unverified reports and audit trail. All case actions.", T.primary],
    ["Protection officer", "Can reveal an informant's number only with a written reason. Every attempt is audited.", T.alert]];
  roles.forEach(([h, d, c], i) => {
    const y = 1.6 + i * 1.25;
    s.addShape("roundRect", { x: M, y, w: 2.9, h: 1.05, rectRadius: 0.1, fill: { color: c }, line: { type: "none" } });
    txt(s, h, M + 0.2, y, 2.5, 1.05, { fontFace: T.fHead, fontSize: 18, bold: true, color: T.white, valign: "middle" });
    txt(s, d, M + 3.2, y, 8.9, 1.05, { fontSize: 16, valign: "middle" });
  });
  T.footer(s, FOOT, n);
  s.addNotes("Least privilege, applied. A Guma mediator cannot see Logo cases. Even the coordinator cannot unmask an informant; only the protection officer can, with a reason, and it is logged.");

  // 13 Dashboard
  s = next();
  T.kicker(s, "Implementation");
  T.title(s, "The coordinator's live map");
  s.addImage({ path: img("ap_coordinator.png"), x: M, y: 1.4, w: 8.9, h: 8.9 * 1425 / 2250 });
  T.bullets(s, ["Risk grid green to red", "Herd trails and dashed 3-hour forecasts", "Rings mark open cases",
    "Case controls: acknowledge, resolve", "USSD phone simulator for the demo", "Leaflet bundled: works offline"],
    M + 9.2, 1.6, W - M - (M + 9.2), 5.2, { fontSize: 15 });
  T.footer(s, FOOT, n);
  s.addNotes("Built with Leaflet, bundled locally so it works without internet during this presentation. It updates live through server-sent events.");

  // 14 Results
  s = next();
  T.kicker(s, "Evaluation");
  T.title(s, "Results");
  const res = [["30/30", "automated tests pass", T.green], ["3.3 ms", "per signed GPS message incl. geofencing", T.primary],
    ["0.08 s", "to recompute 2,010 risk cells", T.primary], ["4/4", "attacks blocked in demo: forgery, replay, unmasking, flooding", T.alert]];
  res.forEach(([v, l, c], i) => { const x = M + i * 3.07; T.card(s, x, 1.7, 2.85, 2.6); T.stat(s, v, l, x + 0.25, 1.85, 2.4, c); });
  T.bullets(s, ["Early warning reached the herder 90 minutes before the herd entered the farm",
    "A lone anonymous rumour stayed unverified (trust 0.30) and was never broadcast",
    "No acknowledgement in 30 minutes: case escalated to NSCDC Agro Rangers automatically",
    "Editing one audit row was detected at the exact row"], M, 4.65, W - 2 * M, 2.2, { fontSize: 16 });
  T.footer(s, FOOT, n);
  s.addNotes("The tests prove the security properties, not only that the code runs. In the demo, the herder got the warning 90 minutes before the herd reached the farm.");

  // 15 Live demo
  s = next(T.dark);
  T.kicker(s, "Live demonstration", "C9B59C");
  T.title(s, "Let me show you", { color: T.white });
  ["Public view: risk only, no herds", "Sign in as coordinator: herds, forecasts, cases appear", "Start the collar simulator: H1 gets an early warning, then enters a farm",
    "USSD phone: report cattle on a farm at Yelwata; watch the trust score", "Acknowledge and resolve the case; show the audit chain"].forEach((t, i) => {
    const y = 1.7 + i * 0.95;
    s.addShape("ellipse", { x: M, y, w: 0.6, h: 0.6, fill: { color: T.primary }, line: { type: "none" } });
    txt(s, String(i + 1), M, y, 0.6, 0.6, { fontFace: T.fHead, fontSize: 18, bold: true, color: T.white, align: "center", valign: "middle" });
    txt(s, t, M + 0.9, y, 11, 0.6, { fontSize: 20, color: T.white, valign: "middle" });
  });
  txt(s, "Backup plan if the laptop misbehaves:  python demo/run_demo.py", M, 6.6, 12, 0.4, { fontSize: 13, italic: true, color: "C9B59C" });
  s.addNotes("Window 1: python demo/live.py --fresh opens the dashboard at 127.0.0.1:8090. Show the public view, then sign in as coordinator. Window 2: python demo/simulator.py. Use the USSD panel: dial, 1, 2 for Guma, 1 for Yelwata, 1 to send. If anything fails, run demo/run_demo.py --fast.");

  // 16 Limitations
  s = next();
  T.kicker(s, "Honest assessment");
  T.title(s, "Limitations and ethics");
  T.card(s, M, 1.6, 5.9, 4.9, "FBEDEE");
  txt(s, "Limitations", M + 0.3, 1.8, 5.3, 0.5, { fontFace: T.fHead, fontSize: 20, bold: true, color: T.alert });
  T.bullets(s, ["Synthetic data; weights not yet calibrated", "Herders must agree to collars", "Straight-line forecasts ignore terrain",
    "One server is a single point of failure", "Hausa text needs native review"], M + 0.3, 2.4, 5.3, 4.0, { fontSize: 15 });
  T.card(s, 6.83, 1.6, 5.9, 4.9, "E8F1E6");
  txt(s, "Do no harm", 7.13, 1.8, 5.3, 0.5, { fontFace: T.fHead, fontSize: 20, bold: true, color: T.green });
  T.bullets(s, ["Never broadcast unverified claims", "Never show herd positions publicly", "Protect informants by design",
    "Farmer and herder bodies co-govern the data", "Follow the Nigeria Data Protection Act 2023"], 7.13, 2.4, 5.3, 4.0, { fontSize: 15 });
  T.footer(s, FOOT, n);
  s.addNotes("The biggest risk is misuse: the same data that warns a herder could be used to find one. That is why governance must be shared and why the public never sees herds.");

  // 17 Conclusion
  s = next(T.dark);
  T.badge(s, I.dove, M, 1.0, 0.9, T.green);
  txt(s, "Use the hours before violence", M, 2.05, 12, 1.1, { fontFace: T.fHead, fontSize: 36, bold: true, color: T.white });
  T.bullets(s, ["GIS sees the herd coming and tells the herder where to go", "Trust scoring stops rumours from spreading",
    "Cases reach the right people, and escalate if nobody acts", "Security keeps warnings true and informants safe"],
    M, 3.4, 11.5, 2.3, { fontSize: 20, color: "EADBC8" });
  txt(s, "Thank you. Questions?", M, 6.0, 12, 0.7, { fontFace: T.fHead, fontSize: 28, bold: true, color: "C9B59C" });
  s.addNotes("To conclude: the time between a stray herd and a killing is often hours. AgroPeace uses those hours. Thank you. I welcome your questions.");

  await pres.writeFile({ fileName: path.join(__dirname, "AgroPeace_Presentation.pptx") });
  console.log("wrote AgroPeace_Presentation.pptx,", n, "slides");
})();
