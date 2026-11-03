"""Reception calls every department, and shows what each call returned."""
import http.server
import os
import urllib.request

DEPARTMENTS = ["records", "pharmacy", "billing"]


def call(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as answer:
            return answer.read().decode().strip()
    except OSError as error:
        return str(getattr(error, "reason", error))


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        board = ""
        for name in DEPARTMENTS:
            url = os.environ[name.upper() + "_URL"]
            board += f"{name:<10} {url:<24} {call(url)}\n"
        self.send_response(200)
        self.end_headers()
        self.wfile.write(board.encode())


print("reception: listening on port 8080", flush=True)
http.server.HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
