/* AgroPeace dashboard. All server text is escaped before it touches the DOM. */
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const lv = (t, cls) => `<span class="lv ${esc(cls || t)}">${esc(t)}</span>`;
const post = (url, body) => fetch(url, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF": "1" }, body: JSON.stringify(body || {}) });
const COLORS = { low: "#3f8f4f", elevated: "#d7a526", high: "#e0701e", severe: "#c0262d" };
const TYPES = { cattle_on_farm: "Cattle on farmland", crop_destruction: "Crops destroyed", threat: "Threat or rumour of attack",
  clash: "Clash in progress", killing: "Killing", cattle_rustling: "Cattle stolen", sighting: "Armed group sighted" };
const OUTCOMES = ["herd_rerouted", "dialogue_held", "compensation_agreed", "security_deployed", "false_alarm"];

const map = L.map("map", { preferCanvas: true, zoomControl: true, zoomSnap: 0.25 }).setView([7.8, 8.6], 9);
const tiles = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 16, attribution: "&copy; OpenStreetMap" });
tiles.on("tileerror", () => {}); tiles.addTo(map);
const gRisk = L.layerGroup().addTo(map), gBase = L.layerGroup().addTo(map), gHerds = L.layerGroup().addTo(map),
  gInc = L.layerGroup().addTo(map), gCases = L.layerGroup().addTo(map);
L.control.layers(null, { "Risk grid": gRisk, "Map layers": gBase, "Herds": gHerds, "Incidents (30 days)": gInc, "Cases": gCases },
  { collapsed: true }).addTo(map);
let S = null, lastEvent = 0;

async function loadLayers() {
  const gj = await (await fetch("/api/layers")).json();
  const style = (f) => ({
    farmland: { color: "#4d7c2f", weight: 1, fillColor: "#9ccc65", fillOpacity: 0.45 },
    grazing_reserve: { color: "#8a5a2b", weight: 1.5, fillColor: "#d9b77e", fillOpacity: 0.35, dashArray: "4 3" },
    stock_route: { color: "#8a5a2b", weight: 3, dashArray: "8 6" },
    river: { color: "#2f74b5", weight: 4 },
    lga: { color: "#666", weight: 1, fill: false, dashArray: "2 4" },
  }[f.properties.kind] || {});
  L.geoJSON(gj, {
    style,
    filter: (f) => f.properties.kind !== "lga",
    pointToLayer: (f, ll) => f.properties.kind === "water_point"
      ? L.circleMarker(ll, { radius: 5, color: "#2f74b5", fillColor: "#7fb3e6", fillOpacity: 1, weight: 1 })
      : L.circleMarker(ll, { radius: 4, color: "#222", fillColor: "#fff", fillOpacity: 1, weight: 1.5 })
        .bindTooltip(esc(f.properties.name), { permanent: true, direction: "right", className: "comm-label" }),
    onEachFeature: (f, l) => l.bindPopup(`<b>${esc(f.properties.name)}</b><br>${esc(f.properties.kind.replace("_", " "))}${f.properties.crop ? " &middot; " + esc(f.properties.crop) : ""}`),
  }).addTo(gBase);
  map.fitBounds(L.geoJSON(gj, { filter: (f) => f.properties.kind !== "lga" }).getBounds(), { padding: [10, 10] });
  // Optional bookmarkable view: /#7.86,8.83,11.5
  const v = location.hash.slice(1).split(",").map(Number);
  if (v.length === 3 && v.every(Number.isFinite)) map.setView([v[0], v[1]], v[2]);
  const sel = $("rComm");
  gj.features.filter((f) => f.properties.kind === "community")
    .forEach((f) => sel.insertAdjacentHTML("beforeend", `<option>${esc(f.properties.name)}</option>`));
}

function drawMap(s) {
  gRisk.clearLayers(); gHerds.clearLayers(); gInc.clearLayers(); gCases.clearLayers();
  s.grid.forEach((g) => L.rectangle([[g.b[0], g.b[1]], [g.b[2], g.b[3]]],
    { stroke: false, fillColor: COLORS[g.l], fillOpacity: g.l === "low" ? 0.18 : Math.min(0.75, 0.3 + g.s * 0.7), interactive: false }).addTo(gRisk));
  s.incidents_30d.forEach((i) => L.circleMarker([i.lat, i.lon], { radius: 3, color: "#7a1f1f", weight: 1, fillColor: "#c0262d", fillOpacity: 0.7 })
    .bindTooltip(esc(i.type.replace("_", " "))).addTo(gInc));
  s.herds.forEach((h) => {
    if (h.trail) L.polyline(h.trail, { color: "#8a5a2b", weight: 2, opacity: 0.6 }).addTo(gHerds);
    if (h.forecast && h.forecast.length) {
      L.polyline([[h.lat, h.lon], ...h.forecast.map((f) => [f[0], f[1]])], { color: "#c0262d", weight: 2, dashArray: "5 5" }).addTo(gHerds);
      h.forecast.forEach((f) => L.circleMarker([f[0], f[1]], { radius: 3, color: "#c0262d", fillOpacity: 0 }).bindTooltip(`+${f[2]} h`).addTo(gHerds));
    }
    const danger = h.zone === "in_farm" ? "#c0262d" : h.zone === "near_farm" ? "#e0701e" : "#8a5a2b";
    L.circleMarker([h.lat, h.lon], { radius: 8, color: "#fff", weight: 2, fillColor: danger, fillOpacity: 1 })
      .bindTooltip(`${esc(h.herd_id)} &middot; ${h.size}`, { permanent: true, direction: "top", className: "herd-label", offset: [0, -6] })
      .bindPopup(`<b>Herd ${esc(h.herd_id)}</b> (${h.size} cattle)<br>Zone: ${esc(h.zone.replace("_", " "))}${h.speed_kmh != null ? `<br>${h.speed_kmh} km/h heading ${h.heading ?? "-"}&deg;` : "<br><i>Location coarsened for public view</i>"}`)
      .addTo(gHerds);
  });
  s.cases.filter((c) => c.status !== "resolved").forEach((c) => L.circleMarker([c.lat, c.lon],
    { radius: 16, color: COLORS[{ advisory: "elevated", warning: "high", critical: "severe" }[c.level]], weight: 3, fillOpacity: 0.08 })
    .bindTooltip(esc(c.id)).addTo(gCases));
}

function drawPanel(s) {
  const staff = s.role !== "public";
  document.querySelectorAll(".staff").forEach((e) => (e.style.display = staff ? "" : "none"));
  $("loginBox").style.display = staff ? "none" : "";
  $("who").innerHTML = staff ? `${esc(s.user)} ${lv(s.role.replace("_", " "), "verified")} <button class="ghost small" id="out" style="color:#fff;border-color:#fff8">Sign out</button>` : lv("public view", "unverified");
  if (staff) $("out").onclick = async () => { await post("/logout"); refresh(); };
  $("rPhone").style.display = staff ? "none" : "";

  $("comm").innerHTML = s.communities.slice(0, 6).map((c) => `<tr><td><b>${esc(c.community)}</b><br><span class="muted">${esc(c.lga)}${c.drivers.length ? " &middot; " + esc(c.drivers.join(", ")) : ""}</span></td><td style="text-align:right">${lv(c.level)}<br><span class="muted">${c.score.toFixed(2)}${staff ? ` &middot; ${c.herds_within_5km} herds &le;5 km` : ""}</span></td></tr>`).join("");

  $("cases").innerHTML = s.cases.length ? s.cases.map((c) => {
    const due = new Date(c.due), mins = Math.round((due - Date.now()) / 60000);
    const open = c.status !== "resolved";
    return `<div class="case" data-id="${esc(c.id)}">
      ${lv(c.level)} ${lv(c.status)} <b>${esc(c.id)}</b> <span class="muted">${esc(c.place)}, ${esc(c.lga)}</span>
      <div class="t">${esc(c.title)}</div>
      ${c.reroute ? `<div class="muted">Reroute: ${esc(c.reroute.reserve)}, ${c.reroute.distance_km} km ${esc(c.reroute.direction)} via ${esc(c.reroute.route)}</div>` : ""}
      <ul>${c.timeline.slice(-3).map((t) => `<li>${new Date(t.ts).toLocaleTimeString()} ${esc(t.event)}</li>`).join("")}</ul>
      <div class="muted">Notified: ${c.notified.length} &middot; ${c.status === "open" ? (mins >= 0 ? `ack due in ${mins} min` : "OVERDUE") : esc(c.acknowledged_by || "")}</div>
      ${open ? `<div class="row" style="margin-top:6px">${c.status === "open" ? `<button class="small" data-ack="${esc(c.id)}">Acknowledge</button>` : ""}
        <select data-out="${esc(c.id)}">${OUTCOMES.map((o) => `<option>${o}</option>`).join("")}</select>
        <button class="small ghost" data-res="${esc(c.id)}">Resolve</button></div>` : `<div class="muted">Outcome: ${esc(c.outcome)}</div>`}
    </div>`;
  }).join("") : '<p class="muted">No cases.</p>';

  $("reports").innerHTML = s.reports.length ? s.reports.slice().reverse().map((r) => `<div class="case">
      ${lv(r.status)} <b>${esc(r.id)}</b> ${esc(r.label)} <span class="muted">&middot; ${esc(r.community)}</span>
      ${r.trust != null ? `<div class="bar"><i style="width:${Math.round(r.trust * 100)}%"></i></div>
      <div class="muted">trust ${r.trust.toFixed(2)} &middot; ${esc(r.channel)} &middot; reporter ${esc(r.reporter)}<br>${esc((r.why || []).join("; "))}</div>
      ${r.text ? `<div>"${esc(r.text)}"</div>` : ""}
      <div class="row" style="margin-top:6px">${s.role === "coordinator" || s.role === "mediator" ? `<button class="small" data-mark="${esc(r.id)}" data-o="confirmed">Confirm on ground</button><button class="small ghost" data-mark="${esc(r.id)}" data-o="false">Mark false</button>` : ""}
      ${s.role === "protection_officer" ? `<button class="small ghost" data-reveal="${esc(r.id)}">Reveal reporter</button>` : ""}</div>` : ""}
    </div>`).join("") : '<p class="muted">No verified reports.</p>';

  if (s.security) {
    const a = s.security.audit;
    $("sec").innerHTML = `${a.ok ? lv(`audit chain intact (${a.entries})`, "verified") : lv("AUDIT TAMPERED at #" + a.broken_at, "severe")}
      <p class="muted">Forged or replayed tracker messages rejected: <b>${s.security.rejected_messages}</b></p>`;
    $("audit").innerHTML = s.audit_recent ? `<table>${s.audit_recent.map((e) => `<tr><td class="muted">${new Date(e.ts).toLocaleTimeString()}</td><td>${esc(e.actor)}</td><td>${esc(e.action)}</td></tr>`).join("")}</table>` : "";
  }
}

document.addEventListener("click", async (e) => {
  const t = e.target;
  if (t.dataset.ack) { await post(`/api/cases/${t.dataset.ack}/ack`); refresh(); }
  if (t.dataset.res) { await post(`/api/cases/${t.dataset.res}/resolve`, { outcome: document.querySelector(`[data-out="${t.dataset.res}"]`).value }); refresh(); }
  if (t.dataset.mark) { await post(`/api/reports/${t.dataset.mark}/mark`, { outcome: t.dataset.o }); refresh(); }
  if (t.dataset.reveal) {
    const reason = prompt("Reason for revealing this reporter (recorded in the audit log):");
    if (!reason) return;
    const j = await (await post(`/api/reports/${t.dataset.reveal}/reveal`, { reason })).json();
    alert(j.phone ? `Reporter contact: ${j.phone}` : j.error);
    refresh();
  }
});

$("loginBtn").onclick = async () => {
  const r = await post("/login", { username: $("u").value, password: $("p").value });
  const j = await r.json();
  $("loginErr").textContent = j.error || ""; $("p").value = "";
  refresh();
};
Object.entries(TYPES).forEach(([k, v]) => $("rType").insertAdjacentHTML("beforeend", `<option value="${k}">${esc(v)}</option>`));
$("rSend").onclick = async () => {
  const r = await post("/api/report", { type: $("rType").value, community: $("rComm").value, phone: $("rPhone").value, text: $("rText").value });
  const j = await r.json();
  $("rMsg").textContent = j.error || `Report ${j.id} received: ${j.status} (trust ${j.trust.toFixed(2)}).`;
  $("rText").value = ""; refresh();
};

let ussdText = null;
async function ussdStep(input) {
  ussdText = ussdText === null ? "" : (ussdText === "" ? input : `${ussdText}*${input}`);
  const j = await (await post("/api/ussd-sim", { text: ussdText, phone: "+2348099990001" })).json();
  const scr = j.screen || j.error || "";
  $("screen").textContent = scr.replace(/^(CON|END) /, "");
  if (scr.startsWith("END")) ussdText = null;
  refresh();
}
$("ussdDial").onclick = () => { ussdText = null; ussdStep(""); };
$("ussdSend").onclick = () => { if (ussdText !== null) { ussdStep($("ussdIn").value.trim()); $("ussdIn").value = ""; } };
$("ussdIn").addEventListener("keydown", (e) => { if (e.key === "Enter") $("ussdSend").click(); });
$("ussdEnd").onclick = () => { ussdText = null; $("screen").textContent = "Session ended"; };

let busy = false;
async function refresh() {
  if (busy) return; busy = true;
  try { S = await (await fetch("/api/state")).json(); drawMap(S); drawPanel(S); } finally { busy = false; }
}
function listen() {
  const es = new EventSource(`/api/stream?after=${lastEvent}`);
  es.onmessage = (m) => { lastEvent = Math.max(lastEvent, JSON.parse(m.data).id); refresh(); };
  es.onerror = () => { es.close(); setTimeout(listen, 3000); };
}
loadLayers().then(refresh).then(listen);
setInterval(refresh, 15000);
