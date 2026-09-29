"""A stand-in 'Student Portal' on port 8099.

To show a service-down alert without closing any window:
    python demo/simulate_incident.py portal-down     (portal answers HTTP 503)
    python demo/simulate_incident.py portal-up
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DOWN_FLAG = Path(__file__).resolve().parent / "sandbox" / "portal_down"


class Portal(BaseHTTPRequestHandler):
    def do_GET(self):
        if DOWN_FLAG.exists():
            body, code = b"<h1>Student Portal</h1><p>Service unavailable.</p>", 503
        else:
            body, code = b"<h1>Student Portal</h1><p>Course registration is open.</p>", 200
        self.send_response(code)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def make_server(port: int = 8099) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), Portal)


if __name__ == "__main__":
    print("Student Portal running on http://127.0.0.1:8099 (Ctrl+C to stop)")
    try:
        make_server().serve_forever()
    except KeyboardInterrupt:
        pass
