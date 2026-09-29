// Builds AgroPeace_Report.docx.  Run: NODE_PATH=<folder with docx> node docs/build_report.js
const path = require("path");
const K = require("../../tools/reportkit");
const { P, H1, H2, H3, bullets, numbered, Figure, Tbl, Code } = K;
const img = (f) => path.join(__dirname, "img", f);

const cover = K.coverPage({
  title: "AGROPEACE: A GIS-BASED EARLY WARNING AND REAL-TIME RESPONSE FRAMEWORK FOR FARMER/HERDER CONFLICT RESOLUTION",
  subtitle: "With secure reporting, informant protection and a case study of Benue State, Nigeria",
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
  P("Clashes between crop farmers and cattle herders have become one of Nigeria's deadliest security problems. The International Crisis Group estimated about 2,500 deaths in 2016 alone, with the Middle Belt, and Benue State in particular, at the centre. Most incidents follow a familiar pattern: a herd enters farmland, crops are destroyed, rumours spread, and a reprisal follows before mediators or security agencies arrive. The information needed to act early often exists (herd movements, crop seasons, past incidents, community warnings) but it is scattered, unverified and slow."),
  P("This project designs and builds **AgroPeace**, a GIS-based early warning and real-time response framework. A pure-Python GIS engine combines map layers of farms, grazing reserves, stock routes and water points with live GPS positions from herd collars and reports sent from any phone through USSD. A risk model scores every 2.8 km grid cell on five explainable factors: incident history, herds near crops, crop season, dry-season water stress and trusted community reports. Herd movement is forecast up to three hours ahead, so the herder receives an SMS in Hausa, Pidgin or English with the nearest grazing reserve and stock route before the herd reaches crops. If it enters a farm, a case opens and is routed by Local Government Area to herder and farmer associations and the peace committee, then escalates to the NSCDC Agro Rangers and LGA security if nobody acknowledges it in time."),
  P("Because information itself can trigger violence, security is central to the design. Collar messages carry HMAC-SHA256 signatures with replay protection. Reporter phone numbers are encrypted with AES-256-GCM and replaced by keyed pseudonyms. Reports earn trust through independent corroboration and GPS confirmation, and unverified rumours are never broadcast. Views are filtered by role and LGA, the public never sees herd positions, and every action is written to a hash-chained audit log. The system passed 30 automated tests. It processes a signed GPS message, including geofencing, in 3.3 ms and recomputes the 2,010-cell risk grid in 0.08 s on ordinary hardware."),
  P("**Keywords:** early warning, GIS, geofencing, farmer/herder conflict, USSD, informant protection, message authentication, Benue State."),
];

const s = [];

// ------------------------------------------------------------------ Chapter 1
s.push(H1("Chapter One: Introduction"));
s.push(H2("1.1 Background of the Study"));
s.push(P("Pastoralists and crop farmers have shared land in Nigeria's savanna and Middle Belt for generations. Seasonal movement of herds, south in the dry season in search of pasture and water and north again with the rains, was historically managed through local agreements, stock routes and grazing reserves. Over recent decades that balance has broken down. Desertification in the far north, insecurity, population growth and the spread of farms onto grazing land and stock routes have pushed herds into closer contact with farms (International Crisis Group [ICG], 2017)."));
s.push(P("The results have been deadly. The ICG (2017) estimated about 2,500 deaths in 2016 and warned that the conflict had become as dangerous as the Boko Haram insurgency. Benue State, known as the Food Basket of the Nation, has been among the worst affected, with repeated attacks in Guma, Agatu and Logo Local Government Areas (LGAs). In response, Benue passed the Open Grazing Prohibition and Ranches Establishment Law in May 2017, which took effect in November 2017. The Federal Government created the NSCDC Agro Rangers to protect farms and mediate disputes, and adopted the National Livestock Transformation Plan to move herding toward ranching."));
s.push(P("A pattern appears across many incidents. A herd strays onto a farm, often at night. Crops are destroyed. The farmer's community hears a version of events, sometimes exaggerated, and a rumour of an attack spreads by phone and social media. Young men mobilise. By the time a peace committee or security patrol arrives, people have been killed. Each step in that chain happens over hours, which means there is a window to intervene, if the right people know in time."));
s.push(P("Geographic Information Systems (GIS) are well suited to this problem because every element of it is spatial: farm boundaries, stock routes, water points, herd positions and incident locations. Mobile networks now reach most rural communities, and basic phones support USSD and SMS without mobile data. Together, these make a real-time early warning system possible at low cost."));

s.push(H2("1.2 Statement of the Problem"));
s.push(P("Current responses are mostly reactive. Specific gaps are:"));
s.push(...numbered([
  "**No early warning.** Nobody is told when a herd is heading toward crops until the damage is done.",
  "**No shared picture.** Incident records, herd movements and farm boundaries sit with different agencies or nowhere at all.",
  "**Rumours travel faster than facts.** Unverified reports of attacks trigger reprisals, and there is no way to weigh a report's credibility.",
  "**Informants are exposed.** People who report threats fear being identified, so they stay silent.",
  "**Responses are slow and uncoordinated.** Alerts do not reach the peace committee, herder leaders and security agencies in a defined order, and there is no follow-up when nobody acts.",
  "**The information system itself is a target.** Fake data can be injected to provoke violence, and location data about herds could be used to target them.",
], "n1"));

s.push(H2("1.3 Aim and Objectives"));
s.push(P("The aim is to develop a GIS-based early warning and real-time framework that helps prevent and resolve farmer/herder conflict, while protecting the integrity of warnings, the confidentiality of informants and the availability of the service. The objectives are to:"));
s.push(...numbered([
  "build a GIS engine and an explainable risk model that scores conflict risk across a map in real time;",
  "track herds from signed GPS messages, forecast their movement and raise geofence alerts before they reach crops;",
  "accept community reports from any phone through USSD and the web, and score their trust;",
  "route alerts to the right responders by LGA, with escalation when nobody acknowledges;",
  "secure the system against forged data, replay, informant exposure, misuse of location data and log tampering; and",
  "evaluate the framework with automated tests, a live demonstration and performance measurements.",
], "n2"));

s.push(H2("1.4 Scope and Limitations"));
s.push(P("The framework covers four Benue LGAs (Guma, Agatu, Logo and Gwer West) and Makurdi. Town positions are approximate. All farms, grazing reserves, herds, incidents and phone numbers are synthetic, because real farm boundaries and incident records were not available and real personal data must not be used in a student project. GPS collars are simulated with the same signed message format a real device would use. The SMS gateway writes to an outbox file, with an optional live connection to Africa's Talking. The risk weights are expert-set starting values, not values fitted to real data."));

s.push(H2("1.5 Significance of the Study"));
s.push(P("The project shows how computer security principles apply outside the server room. In an early warning system, a forged message is not just bad data; it can start a reprisal. A leaked phone number can get an informant killed. A map showing a herd's exact position can guide an attack. Designing for confidentiality, integrity and availability here protects lives. For state emergency agencies, peace committees and NGOs, the project offers a low-cost design that runs on an ordinary laptop, reaches basic phones, and puts mediation before force."));

// ------------------------------------------------------------------ Chapter 2
s.push(H1("Chapter Two: Literature Review"));
s.push(H2("2.1 Drivers of Farmer/Herder Conflict"));
s.push(P("The ICG (2017) traces the conflict to the southward migration of herders, driven by desertification, insecurity in the north and the loss of grazing land to expanding farms and settlements. Its follow-up report (ICG, 2018) found the violence had spread and become more deadly, with ethnic and religious framing making it harder to resolve. Both reports stress weak early warning and slow security response as reasons small disputes become mass killings, and both recommend conflict-resolution mechanisms at local level alongside grazing reserves and better policing."));
s.push(P("Seasonality matters. In the Middle Belt, rains run roughly from April to October and harvest from September to December. Tension peaks when herds arrive while crops are still in the field or being harvested, and in the dry season when farmers and herders compete for the same rivers and ponds. AgroPeace encodes this calendar directly in its risk model."));

s.push(H2("2.2 Policy and Institutional Responses"));
s.push(bullets([
  "**Benue Open Grazing Prohibition and Ranches Establishment Law, 2017**: bans open grazing and requires ranching; enforcement has been contested and its effects are debated.",
  "**NSCDC Agro Rangers**: a unit of the Nigeria Security and Civil Defence Corps set up to guard farms and mediate farmer/herder disputes.",
  "**National Livestock Transformation Plan**: federal plan to shift livestock production toward ranches and improve grazing reserves.",
  "**Peace committees and traditional institutions**: local committees of farmers, herders, youth, women and traditional rulers remain the first line of mediation in many LGAs.",
]));
s.push(P("A technical system must fit these institutions, not replace them. AgroPeace therefore routes alerts first to herders, their associations and peace committees, and only then to security agencies."));

s.push(H2("2.3 Conflict Early Warning Systems"));
s.push(P("Regional bodies run conflict early warning systems, such as ECOWARN under ECOWAS and CEWARN under IGAD in the Horn of Africa. These collect field reports from monitors and produce analysis for decision makers, but they work at a scale of days and weeks, not the hours in which a farm dispute becomes a killing."));
s.push(P("Crowdsourced crisis mapping showed that ordinary people with basic phones can report events in real time. Ushahidi was built in a few days during Kenya's 2007/2008 post-election violence to collect and map SMS and web reports of violence (Okolloh, 2009). Its main weakness is verification: anyone can report anything. AgroPeace keeps the open reporting idea but adds trust scoring and withholds unverified reports."));
s.push(P("For historical incident data, the Armed Conflict Location and Event Data project (ACLED) codes political violence and protest events by date and exact location (Raleigh et al., 2010). ACLED is the natural source for the incident history layer in a real deployment and for calibrating the risk weights."));

s.push(H2("2.4 GIS Methods Used"));
s.push(bullets([
  "**Point-in-polygon (ray casting)**: is a GPS fix inside a farm or grazing reserve?",
  "**Great-circle distance (haversine)** and point-to-segment distance: how far is a herd from a farm edge, a river or a stock route?",
  "**Kernel density estimation**: turns scattered past incidents into a smooth hotspot surface, with each incident weighted by severity and decayed with age.",
  "**Dead reckoning**: projects a herd's position 1, 2 and 3 hours ahead from its recent speed and heading.",
  "**Geofencing**: raises an event when a tracked object enters, approaches or leaves a defined area.",
  "**Grid-based risk surfaces**: divide the map into cells (0.025 degrees, about 2.8 km) so risk can be compared and mapped.",
]));

s.push(H2("2.5 Security Threats to Early Warning Data"));
s.push(P("An early warning system is an information system, so it inherits the classic threats. Here their consequences are physical. Table 2.1 maps the classes of attack from the CMP 468 outline to this setting."));
s.push(...Tbl(["Class of attack", "Early warning example", "Possible harm"], [
  ["Fabrication", "Forged GPS message places a herd inside a farm; fake report of an attack", "False alarm triggers a reprisal against innocent herders or farmers"],
  ["Replay", "Old genuine collar message resent to make a herd appear where it was yesterday", "Wrong location, wasted or misdirected response"],
  ["Interception / disclosure", "Informant phone numbers leak from the database", "Informant targeted; reporting stops"],
  ["Location misuse", "Precise herd positions shown on a public map", "Armed groups use the map to find and attack herds"],
  ["Modification", "Insider edits the log to hide who revealed an informant", "No accountability"],
  ["Interruption / flooding", "One number floods the system with reports", "Real warnings buried; operators overwhelmed"],
], [2000, 3813, 3213], "Table 2.1: Classes of attack against an early warning system"));

s.push(H2("2.6 Research Gap"));
s.push(P("Regional early warning systems are too slow for local disputes. Crowdsourced maps are fast but cannot tell rumour from fact and do not protect reporters. GIS studies of the conflict map where it happened, not where it is about to happen. None of these combine real-time herd tracking, trust-scored community reporting, LGA-level response routing and strong security in one low-cost system that works on basic phones. AgroPeace addresses that gap."));

// ------------------------------------------------------------------ Chapter 3
s.push(H1("Chapter Three: System Analysis and Design"));
s.push(H2("3.1 Methodology"));
s.push(P("The project used iterative prototyping. The problem analysis in Chapter One and the literature in Chapter Two produced requirements and a threat model. Each module (GIS, risk, tracking, reports, response, security) was built and tested on its own, then joined through a central engine. A scenario simulator drove the whole system with realistic herd movements to test the complete flow."));

s.push(H2("3.2 Requirements"));
s.push(H3("Functional requirements"));
s.push(bullets([
  "Load map layers: LGAs, communities, farmland, grazing reserves, stock routes, rivers and water points.",
  "Compute a risk score and level for every grid cell and every community, with the main drivers named.",
  "Accept signed GPS fixes, forecast herd movement and raise geofence events.",
  "Accept reports through USSD, web and SMS, and score their trust.",
  "Open, route, escalate, acknowledge and resolve cases.",
  "Send SMS alerts in the recipient's language.",
  "Show a live, role-filtered map dashboard.",
]));
s.push(H3("Non-functional requirements"));
s.push(bullets([
  "**Integrity**: reject forged and replayed device data.",
  "**Confidentiality**: protect reporter identities and precise herd locations.",
  "**Availability**: work over basic phones without data; run on a laptop.",
  "**Accountability**: record every sensitive action in a tamper-evident log.",
  "**Explainability**: every risk score shows its drivers, so mediators can act on it and challenge it.",
]));

s.push(H2("3.3 Architecture"));
s.push(P("Figure 3.1 shows the architecture. Field inputs pass through a security gate before any module sees them. The herd tracker and report store feed the risk model and the case book. Outputs go to herders, responders and the dashboard. An audit log records every step."));
s.push(...Figure(img("architecture.png"), 2600, 1440, "Figure 3.1: AgroPeace architecture"));
s.push(...Tbl(["Module", "File", "Responsibility"], [
  ["GIS", "geo.py, layers.py", "Haversine, bearing, point-in-polygon, distances, grid, spatial queries, reroute advice"],
  ["Risk model", "risk.py", "Five-factor score per cell and community; season calendar"],
  ["Tracker", "tracking.py", "Speed and heading, 3-hour forecast, geofence state machine"],
  ["Reports", "reports.py", "Report store, trust scoring, reputation"],
  ["Response", "response.py", "Cases, responder routing, SLA escalation"],
  ["Notifications", "notify.py", "SMS templates in English, Hausa and Pidgin"],
  ["Security", "security.py", "Device authentication, identity vault, rate limiter, roles, audit chain"],
  ["Engine", "engine.py", "Orchestration, USSD menu, role-filtered views"],
  ["Web", "server.py, static/", "API, live event stream, Leaflet dashboard"],
], [1700, 2000, 5326], "Table 3.1: Modules"));

s.push(H2("3.4 Risk Model"));
s.push(P("Each cell's score is a weighted sum of five factors, each scaled from 0 to 1:"));
s.push(...Code(["risk = 0.30 H + 0.30 HP + 0.15 F + 0.10 W + 0.15 R"]));
s.push(...Tbl(["Factor", "How it is computed", "Weight"], [
  ["H  incident history", "Sum over past incidents within 12 km of exp(-d^2 / 2(3 km)^2) x exp(-age / 30 days) x severity (killing 1.6, clash 1.3, crop destruction 1.0, threat 0.8), saturated with 1 - exp(-x)", "0.30"],
  ["HP herds near crops", "Herd pressure (herd size/100 x exp(-d / 2.5 km), current and forecast positions) multiplied by crop exposure", "0.30"],
  ["F  crop exposure", "1 inside farmland, falling with distance (exp(-d / 1 km)), times the crop-season factor (1.0 from April to November, 0.3 to 0.6 in the dry months)", "0.15"],
  ["W  water stress", "Dry-season factor x exp(-distance to water / 4 km)", "0.10"],
  ["R  community reports", "Sum of trust x severity x exp(-d / 3 km) x exp(-age / 48 h) over recent reports", "0.15"],
], [2200, 5626, 1200], "Table 3.2: Risk factors"));
s.push(P("Scores map to four levels: low (below 0.20), elevated (0.20 to 0.35), high (0.35 to 0.50) and severe (0.50 and above). Herds near crops get the highest weight alongside history, because cattle next to crops in the field is the most direct trigger of clashes. The dashboard and USSD responses always name the top drivers, for example \"past incidents nearby, herds close to crops\", so a mediator knows why an area is flagged."));

s.push(H2("3.5 Herd Tracking and Geofencing"));
s.push(P("Each GPS fix updates the herd's speed (smoothed and capped at 6 km/h, the upper end of trekking pace) and heading. If the herd is moving, its position is projected 1, 2 and 3 hours ahead along the current heading. A geofence state machine then classifies the herd as in a farm, near a farm (within 500 m), in a grazing reserve or in open land, and raises an event only when that state changes, so responders are not flooded with repeats."));
s.push(...Figure(img("ap_forecast.png"), 1605, 1325, "Figure 3.2: Herd H1 (trail solid, three-hour forecast dashed red) heading into Yelwata farms"));
s.push(...Tbl(["Event", "Trigger", "Response"], [
  ["predicted_incursion", "A forecast point falls inside farmland while crops are in the field", "Herder SMS with reserve, direction and route; advisory case to herder association"],
  ["approach", "Herd within 500 m of farmland in crop season", "Advisory case"],
  ["incursion", "Herd inside farmland in crop season", "Herder SMS; warning case to peace committee and farmer and herder associations; critical if the community is already at severe risk"],
  ["cleared", "Herd leaves farmland", "Note on the open case"],
], [2000, 3500, 3526], "Table 3.3: Geofence events"));
s.push(P("The reroute advice uses the GIS layers to find the nearest grazing reserve, its distance and compass direction, and the nearest stock route, so the herder is told where to go, not only where not to be."));

s.push(H2("3.6 Community Reports and Trust"));
s.push(P("Reports arrive through a USSD menu, the web form, or from mediators. USSD matters most: it works on any phone, needs no data and no smartphone, and rural Nigerians already use it for banking. The menu asks for the type of event, the LGA and the community, so the location comes from a list rather than GPS. Each report gets a trust score:"));
s.push(...Code([
  "trust = channel base (mediator 0.85, field officer 0.80, registered 0.55, USSD/SMS 0.40, anonymous web 0.30)",
  "      + 0.15 per independent reporter within 3 km and 6 hours (maximum +0.30)",
  "      + 0.25 if a GPS collar shows a herd within 2 km (for cattle-on-farm and crop-destruction reports)",
  "      + reporter reputation (+0.10 per report confirmed on the ground, -0.20 per false report)",
]));
s.push(P("A report with trust of 0.70 or more is verified and can escalate to a critical case. From 0.45 it is probable and goes to mediators to check. Below that it is unverified: coordinators see it, but it is never broadcast, never shown to the public and never triggers security deployment. This is the main defence against rumour-driven violence. A single anonymous claim that \"they are coming tonight\" stays quiet until a second, independent person or a GPS collar supports it."));

s.push(H2("3.7 Response and Escalation"));
s.push(P("Every alert becomes a case with a level, a service-level deadline for acknowledgement, and a list of responders chosen by LGA (Figure 3.3). If nobody acknowledges before the deadline, the case climbs a rung and the new responders are alerted. Responders can acknowledge from any phone by replying \"ACK C-001\" by SMS; the system accepts the reply only from a registered number assigned to that case. Cases close with a recorded outcome: herd rerouted, dialogue held, compensation agreed, security deployed or false alarm. These outcomes build an evidence base of what works."));
s.push(...Figure(img("escalation.png"), 2600, 720, "Figure 3.3: Escalation ladder: mediation comes before force"));

s.push(H2("3.8 Security Design"));
s.push(H3("Device authentication and replay protection"));
s.push(P("Each collar holds its own key, derived as HMAC-SHA256(master key, \"device:\" + id) and loaded at registration. Every message carries the device ID, position, a timestamp and a random nonce, and is signed with HMAC-SHA256 over a canonical JSON encoding. The server rejects a message with an unknown device, a wrong signature, a timestamp more than 120 seconds from server time, or a nonce it has already seen. Signatures are compared in constant time. Every rejection is counted, shown on the dashboard and written to the audit log."));
s.push(H3("Informant protection"));
s.push(P("Reporter phone numbers are encrypted with AES-256-GCM before storage, under a key derived from the master key with HKDF. Records and logs carry only a pseudonym: HMAC-SHA256 of the number under a separate derived key. The pseudonym stays stable, so corroboration and reputation work, but it cannot be reversed. Only the protection officer role can decrypt a number, only with a written reason, and every reveal or refused attempt is audited. The SMS outbox never stores phone numbers."));
s.push(H3("Role-based access and location privacy"));
s.push(...Tbl(["Role", "Sees", "Can do"], [
  ["Public (no login)", "Community risk levels, verified reports (summary only)", "Send a report"],
  ["Mediator", "Precise herds, cases and reports in own LGA only", "Acknowledge and resolve cases; confirm or reject reports"],
  ["Coordinator", "Everything in all LGAs, including unverified reports and audit trail", "All case actions"],
  ["Protection officer", "All LGAs, audit trail", "Reveal a reporter's number with a reason (audited)"],
], [2000, 4026, 3000], "Table 3.4: Role-based access"));
s.push(P("The public never sees herd positions. A herd marked \"inside a farm\" on an open map could guide an attack on the herders, which is the reprisal the system exists to prevent. Where coarse locations are needed, a helper snaps them to a 0.05 degree grid (about 5.5 km)."));
s.push(H3("Other controls"));
s.push(bullets([
  "Rate limit of 3 reports per hour per reporter pseudonym against flooding.",
  "Hash-chained SQLite audit log: editing or deleting any entry breaks the chain.",
  "USSD and SMS webhooks sit behind a secret URL token, since gateways do not sign callbacks.",
  "Staff passwords stored as scrypt hashes; login lockout after five failures; HttpOnly, SameSite=Strict session cookie.",
  "CSRF header required on every state-changing request; Content Security Policy without inline scripts; frame and MIME-sniffing protection.",
  "All server text escaped before it reaches the page, against stored cross-site scripting through report text.",
]));

s.push(H2("3.9 Adaptation to the Nigerian Context"));
s.push(...Tbl(["Local reality", "Design response"], [
  ["Many herders and farmers use basic phones", "USSD reporting and SMS alerts; no app or data needed"],
  ["Several languages", "SMS templates in Hausa, Pidgin and English; Tiv, Idoma and Fulfulde to be added with native speakers"],
  ["LGA-based governance", "Cases routed by LGA; mediators see only their LGA"],
  ["Peace committees and traditional institutions", "First responders on the ladder before security agencies"],
  ["NSCDC Agro Rangers", "Critical rung, with LGA security council"],
  ["Middle Belt seasons", "Crop and dry-season factors in the risk model"],
  ["Rumours and disinformation", "Trust scoring; unverified reports never broadcast"],
  ["Fear of reprisal against informants", "Encrypted identities, pseudonyms, audited break-glass access"],
  ["Nigeria Data Protection Act 2023", "Data minimisation, encryption, access control and audit for personal data"],
], [3500, 5526], "Table 3.5: Local conditions and design responses"));

// ------------------------------------------------------------------ Chapter 4
s.push(H1("Chapter Four: Implementation and Testing"));
s.push(H2("4.1 Tools"));
s.push(...Tbl(["Item", "Choice", "Reason"], [
  ["Language", "Python 3.11", "Readable, widely taught, runs anywhere"],
  ["GIS", "Own pure-Python module", "No GDAL/GEOS install; accurate at state scale"],
  ["Map", "Leaflet 1.9.4 (bundled)", "Works offline; OpenStreetMap tiles when online"],
  ["Cryptography", "cryptography library", "Audited AES-GCM, HKDF; HMAC from the standard library"],
  ["Web", "Flask, Server-Sent Events", "Simple live updates without extra services"],
  ["Storage", "SQLite (WAL)", "Audit chain with no database server"],
  ["Tests", "pytest", "30 automated tests"],
], [1800, 3000, 4226], "Table 4.1: Tools"));

s.push(H2("4.2 Dashboard"));
s.push(P("Figure 4.1 shows the coordinator's view during the demonstration. The risk grid is shaded from green to red. Herd H1's trail (solid) and three-hour forecast (dashed red) run into a Yelwata farm. Rings mark open cases. The side panel lists community risk with drivers, then cases with acknowledge and resolve controls, reports with trust bars and reasons, a USSD phone simulator and the security panel."));
s.push(...Figure(img("ap_coordinator.png"), 2250, 1425, "Figure 4.1: Coordinator view during a herd incursion"));
s.push(P("Figure 4.2 shows the public view of the same moment. Risk levels are visible so communities can take care, but herd positions, cases and unverified reports are not."));
s.push(...Figure(img("ap_public.png"), 2250, 1425, "Figure 4.2: Public view: risk only, no herd positions"));

s.push(H2("4.3 Demonstration Scenario"));
s.push(P("The narrated demonstration (demo/run_demo.py) plays a morning in Guma and Logo LGAs with simulated time of ten minutes per GPS fix."));
s.push(...Tbl(["Time", "Event", "System response"], [
  ["06:00", "Morning risk picture", "Yelwata, Ochekwu, Ugba elevated from past incidents"],
  ["06:20", "H1 (140 cattle) forecast to reach a Yelwata farm in about 3 h", "Hausa SMS to herder with Guma East Grazing Reserve, direction and route R2; advisory case C-001 to herder association"],
  ["07:50", "H1 enters the farm", "Hausa SMS to herder; C-001 raised to WARNING; peace committee and farmers association alerted"],
  ["08:25", "No acknowledgement in 30 min", "C-001 escalated to CRITICAL; NSCDC Agro Rangers and LGA security alerted"],
  ["08:29", "Peace committee replies \"ACK C-001\" by SMS", "Case acknowledged; later resolved as herd rerouted"],
  ["", "Single anonymous rumour at Naka", "Unverified (trust 0.30); not broadcast"],
  ["", "USSD report plus independent second report at Ugba", "Probable (trust 0.55); advisory case"],
  ["", "Forged, replayed, identity-reveal and flooding attacks", "All rejected and audited"],
  ["", "Audit log edited", "Chain check reports the altered row"],
], [900, 3600, 4526], "Table 4.2: Demonstration timeline"));

s.push(H2("4.4 Automated Tests"));
s.push(...Tbl(["Area", "What the tests prove"], [
  ["GIS", "Distance matches one degree of latitude (111.2 km); bearing and destination round-trip; point-in-polygon with holes; distance to polygon; grid snapping"],
  ["Risk", "Season factors; level thresholds; risk rises when a herd approaches a hotspot and stays low in quiet areas"],
  ["Device security", "Valid message accepted; replay, forged signature, stale timestamp and unknown device rejected"],
  ["Identity", "Numbers encrypted and recoverable only by key; tampered ciphertext detected; pseudonyms stable and distinct; outbox holds no numbers"],
  ["Tracking", "Early warning comes before incursion; grazing inside a reserve raises nothing; Hausa SMS for a Hausa-speaking herder"],
  ["Reports", "Lone rumour stays unverified and private; corroboration upgrades; GPS confirmation counted; false reports cut reputation; rate limit"],
  ["Response", "Escalation to critical after the SLA with Agro Rangers alerted; SMS ACK accepted only from an assigned responder"],
  ["Access", "Public sees no herds or cases; mediator sees only own LGA; identity reveal restricted and audited"],
  ["Web", "Login, roles, CSRF; forged tracker message returns 401; USSD endpoint needs its secret token; full USSD flow"],
], [1800, 7226], "Table 4.3: Test coverage (30 tests, 30 passed)"));

s.push(H2("4.5 Performance"));
s.push(...Tbl(["Measurement", "Result"], [
  ["Grid size", "2,010 cells of 0.025 degrees"],
  ["Start-up including static layer analysis", "0.89 s"],
  ["Full risk recompute", "0.08 s"],
  ["Signed GPS message: verify, track, forecast, geofence", "3.3 ms"],
  ["Report submission including trust rescoring (200 reports in store)", "161 ms average"],
], [5500, 3526], "Table 4.4: Performance on a 4-core cloud machine"));
s.push(P("At 3.3 ms per message, a single laptop can handle several thousand collars reporting every ten minutes. Report rescoring compares every recent report with every other and grows with the square of the number of reports; a spatial index is listed as future work."));

s.push(H2("4.6 Mapping to the CMP 468 Course Outline"));
s.push(...Tbl(["Course topic", "Where it appears"], [
  ["Overview of security in computing", "CIA triad applied to warnings, informants and service availability"],
  ["Characteristics of computer intrusion", "Attacker motives: provoke violence, find informants, locate herds (Section 2.5)"],
  ["Types of security breaches", "Fabrication, replay, disclosure, modification, interruption (Table 2.1)"],
  ["Security vulnerability", "Unsigned devices, rumours, exposed locations, unsigned gateway callbacks"],
  ["Classes of attacks", "Spoofing, replay, flooding, insider misuse, XSS, CSRF, password guessing"],
  ["Methods of defense and controls", "Prevention (signatures, encryption, RBAC), detection (trust scoring, audit), response (escalation)"],
  ["Encryption and decryption", "AES-256-GCM identity vault; HKDF key separation; HMAC signatures and pseudonyms"],
  ["Database security", "Encrypted fields, least-privilege views, hash-chained audit table"],
  ["Network security", "Message authentication, replay window, webhook tokens, security headers, CSP"],
  ["Security policies and standards", "Role policy, break-glass procedure, NDPA 2023, Cybercrimes Act 2015"],
], [3300, 5726], "Table 4.5: Course topics covered"));

// ------------------------------------------------------------------ Chapter 5
s.push(H1("Chapter Five: Discussion"));
s.push(H2("5.1 Strengths"));
s.push(bullets([
  "Warns before damage: the herder hears about the farm ahead while there is still time to turn.",
  "Gives the herder somewhere to go: nearest reserve, direction and stock route.",
  "Reaches basic phones in local languages.",
  "Separates rumour from fact before anything is broadcast.",
  "Protects informants with encryption, pseudonyms and audited access.",
  "Keeps mediation ahead of force, and records what worked.",
]));
s.push(H2("5.2 Limitations"));
s.push(bullets([
  "Synthetic data: the model has not been tested against real incidents; weights must be calibrated with ACLED and state records.",
  "Collar adoption: herders must agree to be tracked. Without trust, they will refuse or remove collars. The system only works if herder associations co-own it.",
  "Surveillance risk: the same data that warns herders could be used against them by a hostile actor. Governance must be shared between farmer and herder bodies, and data kept to the minimum.",
  "Straight-line forecasts ignore terrain, rivers and paths; route-aware forecasting would be better.",
  "One server is a single point of failure; production needs a replica and a backup (see the UniGuard project).",
  "Trust rescoring slows as reports accumulate; a spatial index would fix this.",
  "Hausa messages need review by a native speaker, and Tiv, Idoma and Fulfulde templates are still to be written.",
]));
s.push(H2("5.3 Ethical Considerations"));
s.push(P("A conflict early warning system must follow the principle of \"do no harm\". AgroPeace applies it in three ways: unverified claims are never broadcast, herd locations are never public, and informant identities are protected by encryption and audited access. Data collection must follow the Nigeria Data Protection Act 2023, which requires a lawful basis, purpose limitation and security of personal data. Herders and farmers should give informed consent to collars and registration, and both groups should sit on the body that governs the system."));
s.push(H2("5.4 Deployment Plan"));
s.push(...numbered([
  "Form a steering group of the Benue State Emergency Management Agency, Guma LGA peace committee, farmers and herders associations, and the NSCDC.",
  "Map real farm boundaries and gazetted reserves and routes with community participation; load ACLED incidents for the state.",
  "Pilot in Guma LGA with 20 volunteer herds for one farming season.",
  "Register a USSD code and SMS sender ID through an aggregator such as Africa's Talking.",
  "Have native speakers write and check Tiv, Idoma, Hausa and Fulfulde messages.",
  "Review every case outcome monthly and recalibrate the risk weights.",
], "n3"));

// ------------------------------------------------------------------ Chapter 6
s.push(H1("Chapter Six: Conclusion and Recommendations"));
s.push(H2("6.1 Summary"));
s.push(P("This project developed AgroPeace, a GIS-based early warning and real-time response framework for farmer/herder conflict. It combines map layers, signed herd tracking, trust-scored community reports and an explainable risk model; it warns herders before they reach crops, routes cases to the right people by LGA and escalates when nobody acts; and it protects the integrity of warnings and the identity of informants. All six objectives were met and 30 automated tests pass."));
s.push(H2("6.2 Conclusion"));
s.push(P("The window between a herd straying onto a farm and a killing is often hours long. A system that sees the herd coming, tells the herder where to go, tells the peace committee what is happening, and refuses to amplify rumours can use that window. Computer security is not an add-on here. Signed messages, encrypted identities, least-privilege views and a tamper-evident log decide whether the system prevents violence or causes it."));
s.push(H2("6.3 Recommendations"));
s.push(...numbered([
  "State governments should fund community mapping of farms, reserves and stock routes as shared public infrastructure.",
  "Early warning systems should treat unverified reports as private until corroborated.",
  "Any tracking of herds should be voluntary, co-governed by herder associations, and never shown publicly.",
  "Informant data should be encrypted, pseudonymised and accessible only through audited break-glass procedures.",
  "Future work: calibrate with ACLED data, route-aware forecasts, satellite vegetation (NDVI) and rainfall layers, offline Android app for mediators, and a spatial index for reports.",
], "n4"));

// ------------------------------------------------------------------ References
s.push(H1("References"));
[
  "Federal Republic of Nigeria. (2015). _Cybercrimes (Prohibition, Prevention, etc.) Act, 2015_.",
  "Federal Republic of Nigeria. (2023). _Nigeria Data Protection Act, 2023_ (Act No. 37). Federal Government Printer.",
  "Benue State Government. (2017). _Open Grazing Prohibition and Ranches Establishment Law, 2017_. Benue State of Nigeria.",
  "International Crisis Group. (2017). _Herders against farmers: Nigeria's expanding deadly conflict_ (Africa Report No. 252). https://www.crisisgroup.org/rpt/africa/nigeria/252-herders-against-farmers-nigerias-expanding-deadly-conflict",
  "International Crisis Group. (2018). _Stopping Nigeria's spiralling farmer-herder violence_ (Africa Report No. 262). https://www.crisisgroup.org/rpt/africa/nigeria/262-stopping-nigerias-spiralling-farmer-herder-violence",
  "Krawczyk, H., & Eronen, P. (2010). _HMAC-based extract-and-expand key derivation function (HKDF)_ (RFC 5869). Internet Engineering Task Force. https://doi.org/10.17487/RFC5869",
  "Krawczyk, H., Bellare, M., & Canetti, R. (1997). _HMAC: Keyed-hashing for message authentication_ (RFC 2104). Internet Engineering Task Force. https://doi.org/10.17487/RFC2104",
  "Dworkin, M. (2007). _Recommendation for block cipher modes of operation: Galois/Counter Mode (GCM) and GMAC_ (NIST Special Publication 800-38D). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-38D",
  "Nigeria Security and Civil Defence Corps. (n.d.). _FG creates Agro Rangers Corps, set to deploy 3,000 to farms, ranches_. https://nscdc.gov.ng/fg-creates-agro-rangers-corps-set-to-deploy-3000-to-farms-ranches/",
  "Okolloh, O. (2009). Ushahidi, or 'testimony': Web 2.0 tools for crowdsourcing crisis information. _Participatory Learning and Action, 59_, 65–70. International Institute for Environment and Development.",
  "Pfleeger, C. P., Pfleeger, S. L., & Margulies, J. (2015). _Security in computing_ (5th ed.). Prentice Hall.",
  "Raleigh, C., Linke, A., Hegre, H., & Karlsen, J. (2010). Introducing ACLED: An armed conflict location and event dataset. _Journal of Peace Research, 47_(5), 651–660. https://doi.org/10.1177/0022343310378914",
  "Schneier, B., & Kelsey, J. (1999). Secure audit logs to support computer forensics. _ACM Transactions on Information and System Security, 2_(2), 159–176. https://doi.org/10.1145/317087.317089",
  "Stallings, W., & Brown, L. (2018). _Computer security: Principles and practice_ (4th ed.). Pearson.",
].sort().forEach((r) => s.push(P(r, { align: "left", para: { indent: { left: 720, hanging: 720 } } })));

// ------------------------------------------------------------------ Appendix
s.push(H1("Appendix A: Running the Demonstration"));
s.push(...Code([
  "pip install -r requirements.txt",
  "python demo/generate_data.py",
  "python -m pytest -q                       # 30 passed",
  "python demo/run_demo.py                   # narrated story",
  "",
  "# Live dashboard",
  "export AGROPEACE_MASTER_KEY=\"demo-master-key-CMP468-agropeace\"",
  "export AGROPEACE_USSD_TOKEN=\"ussd-demo-token-468\"",
  "python -m agropeace -c demo/demo_config.json run",
  "python demo/simulator.py                  # second terminal",
  "# open http://127.0.0.1:8090  (coordinator / peace-coord-2026)",
]));
s.push(H1("Appendix B: Signed Collar Message"));
s.push(...Code([
  "POST /api/tracker",
  "X-Signature: 5f1c...  (HMAC-SHA256 of the canonical JSON body under the device key)",
  "{",
  "  \"device_id\": \"COLLAR-01\",",
  "  \"lat\": 7.912345, \"lon\": 8.834567,",
  "  \"ts\": 1790661600.0,",
  "  \"nonce\": \"9f2c41d07ab3e815\"",
  "}",
]));

K.buildDoc({ cover, abstract, sections: s, out: path.join(__dirname, "AgroPeace_Report.docx"),
  headerText: "CMP 468: AgroPeace Early Warning and Response Framework" })
  .then(() => console.log("wrote AgroPeace_Report.docx"));
