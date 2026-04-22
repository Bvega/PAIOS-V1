import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from scripts.search import search_index

# =========================
# SERVER CONFIG
# =========================

HOST = "127.0.0.1"
PORT = 8000

# Main index used by the API server
INDEX_PATH = "memory/index/index.json"


# =========================
# HELPERS
# =========================

def read_file(path):
    """
    Read and return file content if the path exists.
    Return None when the file is missing.
    """
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    return None


def safe_int(value, default=None):
    """
    Safely convert a value to int.
    Return default if conversion fails.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def format_result(result):
    """
    Normalize one search result into a clean JSON-friendly shape.
    """
    return {
        "file": result.get("file_name"),
        "score": result.get("score"),
        "preview": result.get("preview"),
        "summary_path": result.get("summary_path"),
        "text_path": result.get("text_path"),
    }


def json_response(handler, payload, status=200):
    """
    Send a JSON response with a consistent content type and status code.
    """
    body = json.dumps(payload, indent=2).encode("utf-8")

    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def error_response(handler, message, status=400):
    """
    Send a standardized JSON error response.
    """
    json_response(handler, {"error": message}, status=status)


def get_query_param(params, name, default=""):
    """
    Get a single query-string value from parse_qs output.
    """
    return params.get(name, [default])[0].strip()


# =========================
# REQUEST HANDLER
# =========================

class PAIOSRequestHandler(BaseHTTPRequestHandler):
    """
    Local HTTP API for PAIOS.

    Supported endpoints:
    - /health
    - /search?q=...&limit=...
    - /top?q=...
    - /open?q=...&mode=full|summary|raw
    """

    def do_GET(self):
        """
        Route incoming GET requests to the proper endpoint.
        """
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        params = parse_qs(parsed_url.query)

        # -------------------------
        # HEALTH CHECK
        # -------------------------
        if path == "/health":
            json_response(
                self,
                {
                    "status": "ok",
                    "service": "PAIOS API",
                    "host": HOST,
                    "port": PORT,
                },
            )
            return

        # -------------------------
        # SEARCH
        # /search?q=test&limit=2
        # -------------------------
        if path == "/search":
            query = get_query_param(params, "q")
            limit = safe_int(get_query_param(params, "limit"), default=None)

            if not query:
                error_response(self, 'Missing query parameter. Use /search?q=your+query')
                return

            if limit is not None and limit < 1:
                error_response(self, "Limit must be 1 or greater.")
                return

            results = search_index(INDEX_PATH, query)

            if limit is not None:
                results = results[:limit]

            payload = {
                "query": query,
                "count": len(results),
                "results": [format_result(result) for result in results],
            }
            json_response(self, payload)
            return

        # -------------------------
        # TOP RESULT
        # /top?q=test
        # -------------------------
        if path == "/top":
            query = get_query_param(params, "q")

            if not query:
                error_response(self, 'Missing query parameter. Use /top?q=your+query')
                return

            results = search_index(INDEX_PATH, query)

            if not results:
                json_response(
                    self,
                    {
                        "query": query,
                        "result": None,
                        "message": "No matches found.",
                    },
                )
                return

            top_result = format_result(results[0])

            json_response(
                self,
                {
                    "query": query,
                    "result": top_result,
                },
            )
            return

        # -------------------------
        # OPEN BEST RESULT
        # /open?q=test&mode=full|summary|raw
        # -------------------------
        if path == "/open":
            query = get_query_param(params, "q")
            mode = get_query_param(params, "mode", default="full").lower()

            if not query:
                error_response(self, 'Missing query parameter. Use /open?q=your+query')
                return

            if mode not in ["full", "summary", "raw"]:
                error_response(self, "Mode must be one of: full, summary, raw.")
                return

            results = search_index(INDEX_PATH, query)

            if not results:
                json_response(
                    self,
                    {
                        "query": query,
                        "result": None,
                        "message": "No matches found.",
                    },
                )
                return

            best_result = results[0]

            summary_content = read_file(best_result.get("summary_path"))
            full_content = read_file(best_result.get("text_path"))

            payload = {
                "query": query,
                "file": best_result.get("file_name"),
                "score": best_result.get("score"),
                "preview": best_result.get("preview"),
                "mode": mode,
            }

            if mode in ["full", "summary"]:
                payload["summary"] = summary_content

            if mode in ["full", "raw"]:
                payload["content"] = full_content

            json_response(self, payload)
            return

        # -------------------------
        # UNKNOWN ROUTE
        # -------------------------
        error_response(
            self,
            "Not found. Available endpoints: /health, /search?q=..., /top?q=..., /open?q=...&mode=...",
            status=404,
        )

    def log_message(self, format, *args):
        """
        Silence default HTTP logging so the terminal stays clean.
        """
        return


# =========================
# SERVER START
# =========================

def run_server():
    """
    Start the local PAIOS API server.
    """
    server = HTTPServer((HOST, PORT), PAIOSRequestHandler)

    print(f"PAIOS API running at http://{HOST}:{PORT}")
    print("Endpoints:")
    print("  /health")
    print("  /search?q=...&limit=...")
    print("  /top?q=...")
    print("  /open?q=...&mode=full|summary|raw")

    server.serve_forever()


if __name__ == "__main__":
    run_server()