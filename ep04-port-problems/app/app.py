"""A small clinic service. Its name, address and port come from the environment."""
import http.server
import os

NAME = os.environ.get("NAME", "clinic")
HOST = os.environ.get("HOST", "127.0.0.1")  # the same default most dev servers use
PORT = int(os.environ.get("PORT", "8000"))


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"{NAME} is open\n".encode())


print(f"{NAME}: listening on http://{HOST}:{PORT}", flush=True)
http.server.HTTPServer((HOST, PORT), Handler).serve_forever()
