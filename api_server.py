"""
PAIOS API Server

Endpoints:
- /health
- /search?q=
- /open?q=
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json

from scripts.search import search_index

HOST = "127.0.0.1"
PORT = 8000
INDEX_PATH = "memory/index/index.json"


# =========================
# Helpers
# =========================

def send_json(handler, data, status=200):
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(json.dumps(data, indent=2).encode("utf-8"))


def get_query_param(params, key):
    return params.get(key, [None])[0]


# =========================
# Handler
# =========================

class PAIOSRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        params = parse_qs(parsed_url.query)

        # -------------------------
        # HEALTH
        # -------------------------
        if path == "/health":
            send_json(self, {
                "status": "ok",
                "service": "PAIOS API",
                "index_path": INDEX_PATH
            })
            return

        # -------------------------
        # SEARCH (RAW)
        # -------------------------
        if path == "/search":
            query = get_query_param(params, "q")

            if not query:
                send_json(self, {
                    "error": "Missing query parameter"
                }, 400)
                return

            results = search_index(INDEX_PATH, query)

            send_json(self, {
                "query": query,
                "count": len(results),
                "results": results
            })
            return

        # -------------------------
        # OPEN (LLM STYLE ANSWER)
        # -------------------------
        if path == "/open":
            query = get_query_param(params, "q")

            if not query:
                send_json(self, {
                    "error": "Missing query parameter"
                }, 400)
                return

            results = search_index(INDEX_PATH, query)

            if not results:
                send_json(self, {
                    "query": query,
                    "answer": "No relevant information found.",
                    "sources": []
                })
                return

            top_results = results[:3]

            answer_parts = []
            sources = []

            for r in top_results:
                preview = r.get("preview", "")
                if preview:
                    answer_parts.append(preview.strip())

                sources.append({
                    "file": r.get("file_name"),
                    "path": r.get("text_path")
                })

            send_json(self, {
                "query": query,
                "answer": " ".join(answer_parts),
                "sources": sources
            })
            return

        # -------------------------
        # NOT FOUND
        # -------------------------
        send_json(self, {
            "error": "Endpoint not found",
            "available_endpoints": [
                "/health",
                "/search?q=project",
                "/open?q=project"
            ]
        }, 404)


# =========================
# Server
# =========================

def run_server():
    server = HTTPServer((HOST, PORT), PAIOSRequestHandler)

    print(f"PAIOS API running at http://{HOST}:{PORT}")
    print("Available endpoints:")
    print(" /health")
    print(" /search?q=project")
    print(" /search?q=project%20%7C%20song")
    print(" /open?q=project")

    server.serve_forever()


if __name__ == "__main__":
    run_server()