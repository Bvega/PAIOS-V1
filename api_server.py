import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from scripts.search import search_index

# Path to the local search index used by PAIOS
INDEX_PATH = "memory/index/index.json"

# Local server configuration
HOST = "127.0.0.1"
PORT = 8000


def build_json_response(query: str, results: list[dict]) -> dict:
    """
    Convert raw search results into a clean JSON payload
    that can be consumed by external tools or future LLM integrations.
    """
    return {
        "query": query,
        "count": len(results),
        "results": [
            {
                "file": result.get("file_name"),
                "score": result.get("score"),
                "preview": result.get("preview"),
                "summary_path": result.get("summary_path"),
                "text_path": result.get("text_path"),
            }
            for result in results
        ],
    }


class PAIOSRequestHandler(BaseHTTPRequestHandler):
    """
    Minimal HTTP handler for exposing PAIOS search over localhost.

    Supported endpoint:
    GET /search?q=your+query
    """

    def _send_json(self, payload: dict, status_code: int = 200) -> None:
        """
        Send a JSON response with the given status code.
        """
        body = json.dumps(payload, indent=2).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        """
        Handle GET requests for the local API.
        """
        parsed_url = urlparse(self.path)

        # Health check endpoint
        if parsed_url.path == "/health":
            self._send_json({"status": "ok", "service": "PAIOS API"})
            return

        # Search endpoint
        if parsed_url.path == "/search":
            params = parse_qs(parsed_url.query)
            query = params.get("q", [""])[0].strip()

            if not query:
                self._send_json(
                    {"error": 'Missing query parameter. Use /search?q=your+query'},
                    status_code=400,
                )
                return

            results = search_index(INDEX_PATH, query)
            payload = build_json_response(query, results)
            self._send_json(payload)
            return

        # Unknown route
        self._send_json(
            {"error": "Not found. Available endpoints: /health, /search?q=..."},
            status_code=404,
        )

    def log_message(self, format: str, *args) -> None:
        """
        Silence default HTTP server logging to keep terminal output clean.
        """
        return


def run_server() -> None:
    """
    Start the local PAIOS API server.
    """
    server = HTTPServer((HOST, PORT), PAIOSRequestHandler)
    print(f"PAIOS API running at http://{HOST}:{PORT}")
    print("Endpoints:")
    print("  /health")
    print("  /search?q=your+query")
    server.serve_forever()


if __name__ == "__main__":
    run_server()