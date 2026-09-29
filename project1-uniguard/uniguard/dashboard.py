"""Web dashboard for the ICT/MIS unit (Flask).

Security controls:
  * password login, compared in constant time; 5 failed attempts per IP locks
    login for 5 minutes
  * session cookie is HttpOnly and SameSite=Strict
  * every state-changing call needs the X-UniGuard-CSRF header (blocks CSRF)
  * binds to 127.0.0.1 by default; expose it only behind HTTPS
"""

import hmac
import os
import secrets
import threading
import time

from flask import Flask, abort, jsonify, redirect, request, session

from .engine import UniGuard

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>UniGuard Dashboard</title>
<style>
:root{--bg:#f4f6f8;--card:#fff;--ink:#1c2733;--muted:#5d6b7a;--ok:#1a7f4b;--warn:#b7791f;--bad:#c53030;--line:#dde3ea;--accent:#0b5d3b}
@media (prefers-color-scheme:dark){:root{--bg:#0f1419;--card:#18212b;--ink:#e6edf3;--muted:#93a1b0;--line:#2a3643;--ok:#3fb67a;--warn:#e0a84a;--bad:#f06c6c;--accent:#3fb67a}}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}
header{background:var(--accent);color:#fff;padding:14px 20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
header h1{margin:0;font-size:18px}header small{opacity:.85}
main{padding:16px;display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));max-width:1400px;margin:auto}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.card h2{margin:0 0 10px;font-size:14px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.wide{grid-column:1/-1}.big{font-size:26px;font-weight:700}
.pill{display:inline-block;padding:2px 8px;border-radius:99px;font-size:12px;font-weight:600;color:#fff}
.ok{background:var(--ok)}.warning{background:var(--warn)}.critical,.bad{background:var(--bad)}.info{background:#3b6ea5}
table{width:100%;border-collapse:collapse}td,th{padding:5px 6px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:12px}
button{background:var(--accent);color:#fff;border:0;border-radius:6px;padding:8px 12px;font-weight:600;cursor:pointer;margin:0 6px 6px 0}
#banner{display:none;background:var(--bad);color:#fff;padding:12px 20px;font-weight:700}
.muted{color:var(--muted)}.scroll{max-height:420px;overflow:auto}
</style></head><body>
<div id="banner"></div>
<header><div><h1>UniGuard &middot; <span id="inst"></span></h1><small>Monitoring, backup &amp; recovery</small></div>
<small id="updated"></small></header>
<main>
 <div class="card"><h2>Protection status</h2><div id="prot" class="big"></div><div id="protd" class="muted"></div></div>
 <div class="card"><h2>Power</h2><div id="power" class="big"></div><div id="powerd" class="muted"></div></div>
 <div class="card"><h2>Server</h2><div id="host"></div></div>
 <div class="card"><h2>Actions</h2>
  <button onclick="act('backup')">Back up now</button><button onclick="act('verify')">Verify backups</button>
  <button onclick="act('sync')">Sync offsite now</button><div id="actres" class="muted"></div></div>
 <div class="card wide"><h2>Campus services</h2><table id="svc"></table></div>
 <div class="card wide"><h2>Incidents</h2><table id="inc"></table></div>
 <div class="card"><h2>Snapshots</h2><div class="scroll"><table id="snaps"></table></div></div>
 <div class="card"><h2>Audit trail</h2><div id="chain"></div><div class="scroll"><table id="events"></table></div></div>
</main>
<script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pill=(t,c)=>`<span class="pill ${c}">${esc(t)}</span>`;
const t=s=>s?new Date(s).toLocaleString():'';
async function act(a){document.getElementById('actres').textContent='Working...';
 const r=await fetch('/api/'+a,{method:'POST',headers:{'X-UniGuard-CSRF':'1'}});const j=await r.json();
 document.getElementById('actres').textContent=j.message||JSON.stringify(j);load();}
async function load(){
 const r=await fetch('/api/status');if(r.status==401){location='/login';return}
 const s=await r.json();
 inst.textContent=s.institution;updated.textContent='Updated '+new Date().toLocaleTimeString();
 const openInc=s.incidents.find(i=>i.status!=='recovered');
 banner.style.display=s.lockdown||openInc?'block':'none';
 banner.textContent=s.lockdown?'LOCKDOWN: ransomware response in progress. Backups frozen.':(openInc?'Incident '+openInc.id+' needs attention':'');
 const age=s.latest_backup_age_h;
 prot.innerHTML=s.lockdown?pill('LOCKDOWN','bad'):pill('PROTECTED','ok');
 protd.innerHTML=`${s.snapshot_count} snapshots &middot; last ${age==null?'never':(age*60).toFixed(1)+' min ago'}<br>
  Backup every ${Math.round(s.backup_interval_s/60)} min ${s.peak_period?'('+esc(s.peak_period)+')':''}<br>
  Repository ${s.repo_size_mb} MB &middot; Offsite: ${s.offsite?esc(s.offsite.at)+' '+(s.offsite.complete?'complete':'partial'):'pending'}`;
 const p=s.power;power.innerHTML=p.on_mains==null?pill('UNKNOWN','info'):(p.on_mains?pill('MAINS','ok'):pill('ON BATTERY','warning'));
 powerd.textContent=p.battery_percent!=null?`Battery ${p.battery_percent}% (source: ${p.source})`:'No UPS data';
 const h=s.host;host.innerHTML=Object.entries(h).map(([k,v])=>`${esc(k)}: <b>${v}%</b>`).join('<br>');
 svc.innerHTML='<tr><th>Service</th><th>Status</th><th>Latency</th><th>Detail</th></tr>'+s.services.map(x=>
  `<tr><td>${esc(x.name)}</td><td>${x.up?pill('UP','ok'):pill('DOWN','bad')}</td><td>${x.up?x.latency_ms+' ms':'-'}</td><td class="muted">${esc(x.detail)}</td></tr>`).join('');
 inc.innerHTML='<tr><th>ID</th><th>Status</th><th>Restored</th><th>Quarantined</th><th>Recovery time</th><th>Why</th></tr>'+(s.incidents.length?s.incidents.map(i=>
  `<tr><td>${esc(i.id)}</td><td>${pill(i.status,i.status==='recovered'?'ok':'bad')}</td><td>${i.files_restored??'-'}</td><td>${i.files_quarantined??'-'}</td><td>${i.rto_seconds!=null?i.rto_seconds+' s':'-'}</td><td class="muted">${esc((i.reasons||[]).join('; '))}</td></tr>`).join(''):'<tr><td colspan=6 class="muted">No incidents</td></tr>');
 snaps.innerHTML='<tr><th>Time</th><th>Tag</th><th>Files</th><th>Stored</th></tr>'+s.snapshots.map(x=>
  `<tr><td>${t(x.created)}</td><td>${pill(x.tag,x.clean?'ok':'warning')}</td><td>${x.stats.files}</td><td>${(x.stats.bytes_stored/1024).toFixed(1)} KiB</td></tr>`).join('');
 chain.innerHTML=s.audit_chain.ok?pill('Audit chain intact ('+s.audit_chain.events+' events)','ok'):pill('AUDIT LOG TAMPERED at #'+s.audit_chain.broken_at,'bad');
 events.innerHTML=s.events.map(e=>`<tr><td class="muted">${new Date(e.ts).toLocaleTimeString()}</td><td>${pill(e.severity,e.severity)}</td><td>${esc(e.message)}</td></tr>`).join('');
}
load();setInterval(load,3000);
</script></body></html>"""

LOGIN = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>UniGuard Login</title><style>body{font:15px system-ui;background:#0b5d3b;display:grid;place-items:center;height:100vh;margin:0}
form{background:#fff;padding:28px;border-radius:10px;width:min(340px,90vw)}input,button{width:100%;padding:10px;margin-top:10px;font-size:15px}
button{background:#0b5d3b;color:#fff;border:0;border-radius:6px}.e{color:#c53030}</style></head><body>
<form method="post"><h2>UniGuard</h2><div class="e">{err}</div><input type="password" name="password" placeholder="Dashboard password" autofocus>
<button>Sign in</button></form></body></html>"""


def create_app(engine: UniGuard, password: str) -> Flask:
    app = Flask(__name__)
    app.secret_key = secrets.token_bytes(32)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict")
    failures: dict[str, list[float]] = {}

    def authed():
        return session.get("ok") is True

    @app.after_request
    def headers(resp):
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'unsafe-inline' 'self'; style-src 'unsafe-inline'"
        return resp

    @app.route("/login", methods=["GET", "POST"])
    def login():
        ip = request.remote_addr or "?"
        recent = [t for t in failures.get(ip, []) if time.time() - t < 300]
        failures[ip] = recent
        if request.method == "POST":
            if len(recent) >= 5:
                return LOGIN.replace("{err}", "Too many attempts. Wait 5 minutes."), 429
            if hmac.compare_digest(request.form.get("password", "").encode(), password.encode()):
                session.clear()
                session["ok"] = True
                engine.audit.record("dashboard.login", f"Dashboard login from {ip}", "info")
                return redirect("/")
            recent.append(time.time())
            engine.audit.record("dashboard.login_failed", f"Failed dashboard login from {ip}", "warning")
            return LOGIN.replace("{err}", "Wrong password."), 401
        return LOGIN.replace("{err}", "")

    @app.route("/")
    def index():
        return PAGE if authed() else redirect("/login")

    @app.route("/api/status")
    def status():
        if not authed():
            abort(401)
        return jsonify(engine.status())

    def guarded(fn):
        def wrapper():
            if not authed():
                abort(401)
            if request.headers.get("X-UniGuard-CSRF") != "1":
                abort(403)
            return fn()
        wrapper.__name__ = fn.__name__
        return wrapper

    @app.post("/api/backup")
    @guarded
    def backup_now():
        m = engine.run_backup(tag="manual", reason="dashboard")
        return jsonify({"message": f"Snapshot {m['id']} created" if m else "Backup skipped (see audit trail)"})

    @app.post("/api/verify")
    @guarded
    def verify():
        res = engine.repo.verify(full=True)
        engine.audit.record("backup.verify", f"Verification: {'OK' if res['ok'] else 'FAILED'}, "
                            f"{res['objects_checked']} objects", "info" if res["ok"] else "critical", res)
        return jsonify({"message": f"{'All good' if res['ok'] else 'PROBLEMS FOUND'}: "
                                   f"{res['objects_checked']} objects decrypted and checked", **res})

    @app.post("/api/sync")
    @guarded
    def sync():
        res = engine.run_replication(force=True)
        return jsonify({"message": f"Sent {res['files_copied']} files offsite" if res else "No offsite configured"})

    return app


def serve(engine: UniGuard, host: str, port: int, password: str) -> None:
    stop = threading.Event()
    worker = threading.Thread(target=engine.run_forever, args=(stop,), daemon=True)
    worker.start()
    print(f"Dashboard: http://{host}:{port}  (Ctrl+C to stop)", flush=True)
    try:
        create_app(engine, password).run(host=host, port=port, debug=False, use_reloader=False)
    finally:
        stop.set()
        worker.join(timeout=5)
