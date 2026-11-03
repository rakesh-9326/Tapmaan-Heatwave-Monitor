"""Small local JSON API using Python's standard library (no pip install)."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import json
from .config import CITIES, ROOT
from .service import HeatwaveService


class RequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, service, **kwargs):
        self.service = service
        super().__init__(*args, directory=str(ROOT / "frontend"), **kwargs)

    def json_response(self, data, status=200):
        content = json.dumps(data, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            return super().do_GET()
        query = parse_qs(parsed.query)
        city = query.get("city", ["dombivli"])[0]
        mode = query.get("mode", ["demo"])[0]
        try:
            if parsed.path == "/api/cities":
                return self.json_response(CITIES)
            self.service.city(city)
            if parsed.path == "/api/dashboard":
                return self.json_response(self.service.snapshot(city, mode))
            if parsed.path == "/api/readings":
                return self.json_response(self.service.database.readings(city, kind="observation"))
            self.json_response({"error": "API route not found."}, 404)
        except ValueError as error:
            self.json_response({"error": str(error)}, 400)
        except Exception:
            self.json_response({"error": "Unable to read the database."}, 500)

    def do_POST(self):
        # Restrict mutations to same-origin JSON requests to this local server.
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + self.headers.get("Host", ""):
            return self.json_response({"error": "Cross-origin request rejected."}, 403)
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.json_response({"error": "Send application/json."}, 415)
        try:
            size = int(self.headers.get("Content-Length", 0))
            if size <= 0 or size > 8192:
                raise ValueError("Invalid request size.")
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError("Request must be a JSON object.")
            route = urlparse(self.path).path
            if route == "/api/readings":
                return self.json_response(self.service.add_manual(payload), 201)
            if route == "/api/refresh":
                try:
                    data = self.service.refresh(payload.get("city", ""), payload.get("mode", ""))
                except (ValueError, KeyError) as error:
                    raise ValueError(str(error)) from error
                except Exception:
                    return self.json_response({"error": "Weather fetch failed. Check your internet connection and retry. Saved data is unchanged."}, 502)
                return self.json_response(data)
            if route == "/api/acknowledge":
                if not self.service.database.acknowledge(int(payload["id"])):
                    return self.json_response({"error": "Alert not found."}, 404)
                return self.json_response({"ok": True})
            if route == "/api/delete-reading":
                if not self.service.database.delete_manual(int(payload["id"])):
                    return self.json_response({"error": "Only existing manual readings can be deleted."}, 404)
                return self.json_response({"ok": True})
            self.json_response({"error": "API route not found."}, 404)
        except (ValueError, TypeError, KeyError) as error:
            self.json_response({"error": str(error)}, 400)
        except Exception:
            self.json_response({"error": "The database operation failed."}, 500)


def create_server(port=8000, service=None):
    handler = partial(RequestHandler, service=service or HeatwaveService())
    return ThreadingHTTPServer(("127.0.0.1", port), handler)
