"""Web server: map dashboard, live event stream, tracker API, USSD and SMS webhooks."""

import hmac
import json
import os
import secrets
import threading
import time
from pathlib import Path

from flask import Flask, Response, abort, jsonify, redirect, request, send_from_directory, session
from werkzeug.security import check_password_hash

from .engine import Engine
from .security import AuthError, can, sees_lga

STATIC = Path(__file__).resolve().parent / "static"


def create_app(engine: Engine) -> Flask:
    cfg = engine.cfg
    app = Flask(__name__, static_folder=None)
    app.secret_key = secrets.token_bytes(32)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict")
    users = {u["username"]: u for u in cfg["users"]}
    failures: dict[str, list[float]] = {}
    ussd_token = os.environ.get(cfg.get("ussd_token_env", "AGROPEACE_USSD_TOKEN"), "")

    def current_user():
        u = users.get(session.get("user", ""))
        if u:
            return {"username": u["username"], "role": u["role"], "lgas": u.get("lgas", [])}
        return None

    def need(perm):
        u = current_user()
        if not can(u, perm):
            abort(403)
        if request.method == "POST" and request.headers.get("X-CSRF") != "1":
            abort(403)
        return u

    @app.after_request
    def headers(resp):
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data: https://*.tile.openstreetmap.org; "
            "style-src 'self' 'unsafe-inline'; script-src 'self'")
        return resp

    # ------------------------------------------------------------ pages
    @app.get("/")
    def index():
        return send_from_directory(STATIC, "dashboard.html")

    @app.get("/static/<path:p>")
    def static_files(p):
        return send_from_directory(STATIC, p)

    @app.post("/login")
    def login():
        ip = request.remote_addr or "?"
        recent = [t for t in failures.get(ip, []) if time.time() - t < 300]
        failures[ip] = recent
        if len(recent) >= 5:
            return jsonify({"error": "Too many attempts. Wait 5 minutes."}), 429
        data = request.get_json(silent=True) or {}
        u = users.get(data.get("username", ""))
        if u and check_password_hash(u["password_hash"], data.get("password", "")):
            session.clear()
            session["user"] = u["username"]
            engine.audit.record(u["username"], "login", {"ip": ip})
            return jsonify({"ok": True, "role": u["role"]})
        recent.append(time.time())
        engine.audit.record(data.get("username", "?")[:40], "login_failed", {"ip": ip})
        return jsonify({"error": "Wrong username or password."}), 401

    @app.post("/logout")
    def logout():
        session.clear()
        return jsonify({"ok": True})

    # ------------------------------------------------------------ data
    @app.get("/api/layers")
    def layers():
        return jsonify(engine.layers.public_geojson())

    @app.get("/api/state")
    def state():
        return jsonify(engine.snapshot(current_user()))

    @app.get("/api/stream")
    def stream():
        user = current_user()
        staff = can(user, "view_precise")
        last = int(request.args.get("after", 0))

        def gen():
            nonlocal last
            deadline = time.time() + 300
            while time.time() < deadline:
                batch = [e for e in list(engine.events) if e["id"] > last]
                for e in batch:
                    last = e["id"]
                    if e["audience"] == "public" or staff:
                        yield f"id: {e['id']}\ndata: {json.dumps({'kind': e['kind'], 'id': e['id']})}\n\n"
                if not batch:
                    yield ": keep-alive\n\n"
                time.sleep(1)
        return Response(gen(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache"})

    # ------------------------------------------------------------ devices
    @app.post("/api/tracker")
    def tracker():
        body = request.get_json(silent=True) or {}
        try:
            return jsonify(engine.ingest_position(body, request.headers.get("X-Signature", "")))
        except AuthError as exc:
            return jsonify({"error": str(exc)}), 401
        except KeyError:
            return jsonify({"error": "unknown device"}), 400

    # ------------------------------------------------------------ reports and cases
    @app.post("/api/report")
    def report():
        u = current_user()
        if request.headers.get("X-CSRF") != "1":
            abort(403)
        d = request.get_json(silent=True) or {}
        channel = "mediator" if can(u, "manage_cases") else "web_anonymous"
        phone = d.get("phone") or (f"user:{u['username']}" if u else "")
        if not phone:
            return jsonify({"error": "A phone number is needed so mediators can follow up. It is encrypted."}), 400
        try:
            rep = engine.submit_report(rtype=d.get("type", ""), channel=channel, phone=phone,
                                       community=d.get("community"), lat=d.get("lat"), lon=d.get("lon"),
                                       text=d.get("text", ""))
        except PermissionError as exc:
            return jsonify({"error": str(exc)}), 429
        except (ValueError, TypeError) as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"id": rep["id"], "status": rep["status"], "trust": rep["trust"]})

    def case_for(u, case_id):
        try:
            c = engine.cases.get(case_id)
        except StopIteration:
            abort(404)
        if not sees_lga(u, c["lga"]):
            abort(403)
        return c

    @app.post("/api/cases/<case_id>/ack")
    def ack(case_id):
        u = need("manage_cases")
        case_for(u, case_id)
        return jsonify(engine.acknowledge(case_id, u["username"]))

    @app.post("/api/cases/<case_id>/resolve")
    def resolve(case_id):
        u = need("manage_cases")
        case_for(u, case_id)
        d = request.get_json(silent=True) or {}
        try:
            return jsonify(engine.resolve(case_id, u["username"], d.get("outcome", ""), d.get("note", "")[:200]))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @app.post("/api/reports/<rid>/mark")
    def mark(rid):
        u = need("manage_cases")
        d = request.get_json(silent=True) or {}
        if d.get("outcome") not in ("confirmed", "false"):
            return jsonify({"error": "outcome must be confirmed or false"}), 400
        return jsonify({k: v for k, v in engine.mark_report(rid, d["outcome"], u).items() if k != "sealed_contact"})

    @app.post("/api/reports/<rid>/reveal")
    def reveal(rid):
        u = current_user()
        if request.headers.get("X-CSRF") != "1":
            abort(403)
        try:
            phone = engine.reveal_identity(rid, u or {"username": "anonymous", "role": "public"},
                                           (request.get_json(silent=True) or {}).get("reason", ""))
        except PermissionError as exc:
            return jsonify({"error": str(exc)}), 403
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"phone": phone})

    # ------------------------------------------------------------ USSD and SMS gateways
    def check_token(tok):
        if not ussd_token or not hmac.compare_digest(tok, ussd_token):
            abort(404)

    @app.post("/ussd/<tok>")
    def ussd(tok):
        check_token(tok)
        return Response(engine.ussd(request.form.get("phoneNumber", ""), request.form.get("text", "")),
                        mimetype="text/plain")

    @app.post("/sms/<tok>")
    def sms(tok):
        check_token(tok)
        return Response(engine.sms_inbound(request.form.get("from", ""), request.form.get("text", "")),
                        mimetype="text/plain")

    @app.post("/api/ussd-sim")
    def ussd_sim():
        """In-browser phone simulator for demonstrations (staff only)."""
        need("view_precise")
        d = request.get_json(silent=True) or {}
        return jsonify({"screen": engine.ussd(d.get("phone", "+2348099990000"), d.get("text", ""))})

    return app


def serve(engine: Engine, host: str, port: int) -> None:
    stop = threading.Event()

    def loop():
        while not stop.wait(5):
            try:
                engine.tick()
            except Exception as exc:  # keep the service alive
                engine.audit.record("system", "tick_error", {"error": str(exc)})
    threading.Thread(target=loop, daemon=True).start()
    print(f"AgroPeace dashboard: http://{host}:{port}", flush=True)
    try:
        create_app(engine).run(host=host, port=port, threaded=True, debug=False, use_reloader=False)
    finally:
        stop.set()
