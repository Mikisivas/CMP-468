"""A stand-in 'Student Portal' on port 8099. Stop it (Ctrl+C) to show a service-down alert."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Portal(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"<h1>Student Portal</h1><p>Course registration is open.</p>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def make_server(port: int = 8099) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), Portal)


if __name__ == "__main__":
    print("Student Portal running on http://127.0.0.1:8099 (Ctrl+C to take it down)")
    try:
        make_server().serve_forever()
    except KeyboardInterrupt:
        pass
