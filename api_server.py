import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from scripts.search import search_index

INDEX_PATH = "memory/index/index.json"

HOST = "127.0.0.1"
PORT = 8000


# =========================
# HELPERS
# =========================

def build_response(query, results):
    return {
        "query": query,
        "count": len(results),
        "results": [
            {
                "file": r.get("file_name"),
                "score": r.get("score"),
                "preview": r.get("preview"),
                "summary_path": r.get("summary_path"),
                "text_path": r.get("text_path"),
            }
            for r in results
        ],
    }


def read_file(path):
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None


# =========================
# HANDLER
# =========================

class Handler(BaseHTTPRequestHandler):

    def send_json(self, payload, status=200):
        body = json.dumps(payload, indent=2).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # -------------------------
        # /health
        # -------------------------
        if path == "/health":
            self.send_json({"status": "ok"})
            return

        # -------------------------
        # /search?q=
        # -------------------------
        if path == "/search":
            query = params.get("q", [""])[0]

            if not query:
                self.send_json({"error": "Missing ?q="}, 400)
                return

            results = search_index(INDEX_PATH, query)
            self.send_json(build_response(query, results))
            return

        # -------------------------
        # /top?q=
        # -------------------------
        if path == "/top":
            query = params.get("q", [""])[0]

            if not query:
                self.send_json({"error": "Missing ?q="}, 400)
                return

            results = search_index(INDEX_PATH, query)

            if not results:
                self.send_json({"query": query, "result": None})
                return

            top = results[0]

            self.send_json({
                "query": query,
                "result": {
                    "file": top.get("file_name"),
                    "score": top.get("score"),
                    "preview": top.get("preview"),
                }
            })
            return

        # -------------------------
        # /open?q=
        # -------------------------
        if path == "/open":
            query = params.get("q", [""])[0]

            if not query:
                self.send_json({"error": "Missing ?q="}, 400)
                return

            results = search_index(INDEX_PATH, query)

            if not results:
                self.send_json({"query": query, "result": None})
                return

            top = results[0]

            content = read_file(top.get("text_path"))
            summary = read_file(top.get("summary_path"))

            self.send_json({
                "query": query,
                "file": top.get("file_name"),
                "summary": summary,
                "content": content
            })
            return

        # -------------------------
        # fallback
        # -------------------------
        self.send_json({
            "error": "Available endpoints: /health, /search?q=, /top?q=, /open?q="
        }, 404)

    def log_message(self, format, *args):
        return


# =========================
# SERVER
# =========================

def run():
    server = HTTPServer((HOST, PORT), Handler)
    print(f"PAIOS API running at http://{HOST}:{PORT}")
    print("Endpoints:")
    print("  /health")
    print("  /search?q=...")
    print("  /top?q=...")
    print("  /open?q=...")
    server.serve_forever()


if __name__ == "__main__":
    run()