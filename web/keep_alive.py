from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")


def run_server():
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
