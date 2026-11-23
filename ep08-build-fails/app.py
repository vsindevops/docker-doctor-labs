"""The clinic's appointments service. It answers on port 8000."""
import http.server


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"appointments: open\n")


print("appointments: listening on port 8000", flush=True)
http.server.HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
