import os
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer

# The app must be told where its database is, for example:
#   DATABASE_URL=sqlite:///clinic.db
DATABASE_URL = os.environ["DATABASE_URL"]
DB_FILE = DATABASE_URL.removeprefix("sqlite:///")

db = sqlite3.connect(DB_FILE)
db.execute("CREATE TABLE IF NOT EXISTS visits (id INTEGER PRIMARY KEY)")
db.commit()


class Clinic(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_response(404)
            self.end_headers()
            return
        db.execute("INSERT INTO visits DEFAULT VALUES")
        db.commit()
        count = db.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
        page = f"<h1>Docker Doctor Clinic</h1><p>Visitors so far: {count}</p>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(page.encode())


print("Clinic is open on port 8000", flush=True)
HTTPServer(("0.0.0.0", 8000), Clinic).serve_forever()
