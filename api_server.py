import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from scripts.core import run_query_core, extract_top_result, open_result

# =========================
# SERVER CONFIG
# =========================

HOST = "127.0.0.1"
PORT = 8000
INDEX_PATH = "memory/index/index.json"


# =========================
# HELPERS
# =========================

def safe_int(value, default=None):
    """
    Safely convert a value to int.
    Returns default if conversion fails.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_param(params, name, default=""):
    """
    Extract one query parameter from parsed URL params.
    """
    return params.get(name, [default])[0].strip()


def format_result(result):
    """
    Normalize one result for JSON API output.
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
    Send a JSON HTTP response.
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


# =========================
# REQUEST HANDLER
# =========================

class PAIOSRequestHandler(BaseHTTPRequestHandler):
    """
    Local API server for PAIOS.

    Endpoints:
    - /health
    - /search?q=...&refine=...&limit=...&min_score=...
    - /top?q=...&refine=...
    - /open?q=...&refine=...&mode=full|summary|raw
    """

    def do_GET(self):
        """
        Route GET requests to the correct endpoint.
        """
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        params = parse_qs(parsed_url.query)

        if path == "/health":
            json_response(
                self,
                {
                    "status": "ok",
                    "service": "PAIOS API",
                },
            )
            return

        if path == "/search":
            q = get_param(params, "q")
            refine = get_param(params, "refine")
            limit = safe_int(get_param(params, "limit"), None)
            min_score = safe_int(get_param(params, "min_score"), None)

            if not q:
                error_response(self, "Missing ?q=")
                return

            if limit is not None and limit < 1:
                error_response(self, "limit must be >= 1")
                return

            full_query, results = run_query_core(
                INDEX_PATH,
                q,
                refine=refine,
                limit=limit,
                min_score=min_score,
            )

            json_response(
                self,
                {
                    "query": q,
                    "refine": refine,
                    "full_query": full_query,
                    "count": len(results),
                    "min_score": min_score,
                    "limit": limit,
                    "results": [format_result(result) for result in results],
                },
            )
            return

        if path == "/top":
            q = get_param(params, "q")
            refine = get_param(params, "refine")

            if not q:
                error_response(self, "Missing ?q=")
                return

            full_query, results = run_query_core(INDEX_PATH, q, refine=refine)
            top = extract_top_result(results)

            json_response(
                self,
                {
                    "query": q,
                    "refine": refine,
                    "full_query": full_query,
                    "result": format_result(top) if top else None,
                },
            )
            return

        if path == "/open":
            q = get_param(params, "q")
            refine = get_param(params, "refine")
            mode = get_param(params, "mode", "full").lower()

            if not q:
                error_response(self, "Missing ?q=")
                return

            if mode not in ["full", "summary", "raw"]:
                error_response(self, "mode must be full|summary|raw")
                return

            full_query, results = run_query_core(INDEX_PATH, q, refine=refine)
            top = extract_top_result(results)
            opened = open_result(top, mode=mode)

            json_response(
                self,
                {
                    "query": q,
                    "refine": refine,
                    "full_query": full_query,
                    "result": opened,
                },
            )
            return

        error_response(self, "Invalid endpoint", status=404)

    def log_message(self, format, *args):
        """
        Disable default HTTP request logs for cleaner terminal output.
        """
        return


# =========================
# SERVER
# =========================

def run_server():
    """
    Start the local HTTP API server.
    """
    server = HTTPServer((HOST, PORT), PAIOSRequestHandler)

    print(f"PAIOS API running at http://{HOST}:{PORT}")
    print("Endpoints:")
    print("  /health")
    print("  /search?q=...&refine=...&limit=...&min_score=...")
    print("  /top?q=...&refine=...")
    print("  /open?q=...&refine=...&mode=full|summary|raw")

    server.serve_forever()


if __name__ == "__main__":
    run_server()