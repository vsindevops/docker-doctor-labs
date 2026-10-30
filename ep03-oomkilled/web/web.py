"""The clinic's website. Every request gets its own worker process."""
import http.server
import socketserver


class Server(socketserver.ForkingMixIn, http.server.HTTPServer):
    pass


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/report":
            data = b"x" * (300 * 1024 * 1024)  # this page loads a lot of data
            body = f"report ready, {len(data):,} bytes read\n"
        else:
            body = "clinic is open\n"
        self.send_response(200)
        self.end_headers()
        self.wfile.write(body.encode())


Server(("0.0.0.0", 8000), Handler).serve_forever()
