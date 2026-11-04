"""The clinic's records app. On every visit it does its three jobs, and shows how each one went."""
import http.server


def load_settings():
    with open("/app/settings.ini") as f:
        f.read()
    return "loaded"


def save_upload():
    with open("/app/uploads/scan.txt", "w") as f:
        f.write("x-ray scan\n")
    return "saved scan.txt"


def save_note():
    with open("/data/notes.txt", "a") as f:
        f.write("checked in\n")
    with open("/data/notes.txt") as f:
        return f"saved note {len(f.readlines())}"


JOBS = [("settings", "/app/settings.ini", load_settings),
        ("uploads", "/app/uploads", save_upload),
        ("notes", "/data", save_note)]


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        board = ""
        for name, path, job in JOBS:
            try:
                result = job()
            except OSError as error:
                result = str(error)
            board += f"{name:<9} {path:<18} {result}\n"
        self.send_response(200)
        self.end_headers()
        self.wfile.write(board.encode())


print("records: listening on port 8080", flush=True)
http.server.HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
