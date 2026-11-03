"""A clinic department. It answers every call with its name."""
import http.server
import os

NAME = os.environ.get("NAME", "department")


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"{NAME} is open\n".encode())


print(f"{NAME}: listening on port 8000", flush=True)
http.server.HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
