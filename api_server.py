import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from scripts.search import search_index

HOST = "127.0.0.1"
PORT = 8000

INDEX_PATH = "memory/index/index.json"


# =========================
# HELPERS
# =========================

def read_file(path):
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def format_result(r):
    return {
        "file": r.get("file_name"),
        "score": r.get("score"),
        "preview": r.get("preview"),
        "summary_path": r.get("summary_path"),
        "text_path": r.get("text_path"),
    }


def json_response(handler, payload, status=200):
    body = json.dumps(payload, indent=2).encode("utf-8")

    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def error_response(handler, message, status=400):
    json_response(handler, {"error": message}, status)


def get_param(params, name, default=""):
    return params.get(name, [default])[0].strip()


# =========================
# HANDLER
# =========================

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # -------------------------
        # HEALTH
        # -------------------------
        if path == "/health":
            json_response(self, {
                "status": "ok",
                "service": "PAIOS API"
            })
            return

        # -------------------------
        # SEARCH
        # /search?q=test&limit=2&min_score=5
        # -------------------------
        if path == "/search":
            query = get_param(params, "q")
            limit = safe_int(get_param(params, "limit"), None)
            min_score = safe_int(get_param(params, "min_score"), None)

            if not query:
                error_response(self, "Missing ?q=")
                return

            results = search_index(INDEX_PATH, query)

            # FILTER BY SCORE
            if min_score is not None:
                results = [r for r in results if r.get("score", 0) >= min_score]

            # APPLY LIMIT
            if limit is not None:
                if limit < 1:
                    error_response(self, "Limit must be >= 1")
                    return
                results = results[:limit]

            json_response(self, {
                "query": query,
                "count": len(results),
                "min_score": min_score,
                "results": [format_result(r) for r in results]
            })
            return

        # -------------------------
        # TOP
        # -------------------------
        if path == "/top":
            query = get_param(params, "q")

            if not query:
                error_response(self, "Missing ?q=")
                return

            results = search_index(INDEX_PATH, query)

            if not results:
                json_response(self, {"query": query, "result": None})
                return

            json_response(self, {
                "query": query,
                "result": format_result(results[0])
            })
            return

        # -------------------------
        # OPEN
        # -------------------------
        if path == "/open":
            query = get_param(params, "q")
            mode = get_param(params, "mode", "full").lower()

            if not query:
                error_response(self, "Missing ?q=")
                return

            if mode not in ["full", "summary", "raw"]:
                error_response(self, "mode must be full|summary|raw")
                return

            results = search_index(INDEX_PATH, query)

            if not results:
                json_response(self, {"query": query, "result": None})
                return

            best = results[0]

            summary = read_file(best.get("summary_path"))
            content = read_file(best.get("text_path"))

            payload = {
                "query": query,
                "file": best.get("file_name"),
                "score": best.get("score"),
                "mode": mode
            }

            if mode in ["full", "summary"]:
                payload["summary"] = summary

            if mode in ["full", "raw"]:
                payload["content"] = content

            json_response(self, payload)
            return

        # -------------------------
        # FALLBACK
        # -------------------------
        error_response(self, "Invalid endpoint", 404)

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
    print("  /search?q=...&limit=...&min_score=...")
    print("  /top?q=...")
    print("  /open?q=...&mode=full|summary|raw")

    server.serve_forever()


if __name__ == "__main__":
    run()