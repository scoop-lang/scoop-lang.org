"""Local HTTP fixtures for bootstrap and publication tests."""

import http.server
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def temporary(test):
    (ROOT / "tmp").mkdir(exist_ok=True)
    directory = tempfile.TemporaryDirectory(prefix="bootstrap-", dir=ROOT / "tmp")
    test.addCleanup(directory.cleanup)
    return Path(directory.name)


def server(test, root, writable=False):
    requests = []

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=root, **kwargs)

        def do_GET(self):
            requests.append(("GET", self.path))
            super().do_GET()

        def do_PUT(self):
            if not writable:
                self.send_error(405)
                return
            requests.append(("PUT", self.path))
            path = Path(self.translate_path(self.path))
            body = self.rfile.read(int(self.headers["Content-Length"]))
            if self.headers.get("If-None-Match") == "*" and path.exists():
                self.send_error(412)
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    instance = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    test.addCleanup(instance.server_close)
    test.addCleanup(instance.shutdown)
    threading.Thread(target=instance.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{instance.server_port}", requests
