# =========================
# PAIOS API SERVER
# =========================
# Day 55 corrected:
# - Keeps existing http.server architecture
# - Keeps port 8000
# - Preserves existing endpoints:
#   /health
#   /search
#   /top
#   /open
# - Adds new endpoint:
#   /ask?q=...&mode=short|detailed|sources

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from scripts.core import run_query_core, extract_top_result, open_result


# =========================
# CONFIG
# =========================

HOST = "127.0.0.1"
PORT = 8000
INDEX_PATH = "memory/index/index.json"


# =========================
# BASIC HELPERS
# =========================

def safe_int(value, default=None):
    """
    Safely convert string to integer.
    Returns default if conversion fails.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_param(params, name, default=""):
    """
    Extract one query parameter value from parsed URL params.
    """
    return params.get(name, [default])[0].strip()


def json_response(handler, payload, status=200):
    """
    Send JSON response to client.
    """
    body = json.dumps(payload, indent=2).encode("utf-8")

    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def error_response(handler, message, status=400):
    """
    Send standardized error response.
    """
    json_response(handler, {"error": message}, status=status)


def format_result(result):
    """
    Normalize one search result for API output.
    """
    if not result:
        return None

    return {
        "file": result.get("file_name"),
        "score": result.get("score"),
        "preview": result.get("preview"),
        "summary_path": result.get("summary_path"),
        "text_path": result.get("text_path"),
    }


# =========================
# ANSWER ENGINE HELPERS
# =========================

def auto_refine(query):
    """
    Automatically add summary refinement for multi-word queries.
    """
    if len(query.split()) >= 2:
        return "summary"
    return None


def classify_line(line):
    """
    Classify one summary line into a rule-based semantic category.
    """
    lower_line = line.lower()

    if "terminate" in lower_line or "termination" in lower_line:
        return "Termination"

    if "liability" in lower_line or "damages" in lower_line:
        return "Liability"

    if "payment" in lower_line:
        return "Payment"

    return "General"


def clean_lines(results):
    """
    Load summary lines from result files and deduplicate them.
    """
    seen = set()
    lines = []

    for result in results:
        summary_path = result.get("summary_path")

        if not summary_path:
            continue

        try:
            with open(summary_path, "r", encoding="utf-8") as file:
                for line in file.read().split("\n"):
                    line = line.strip()

                    if not line:
                        continue

                    key = line.lower()

                    if key not in seen:
                        seen.add(key)
                        lines.append(line)
        except Exception:
            continue

    return lines


def group_lines(lines):
    """
    Group clean summary lines into semantic categories.
    """
    groups = {
        "Termination": [],
        "Liability": [],
        "Payment": [],
        "General": [],
    }

    for line in lines:
        category = classify_line(line)
        groups[category].append(line)

    return groups


def compress_group(lines, category):
    """
    Compress a category group into one concise rule-based statement.
    """
    text = " ".join(lines).lower()

    if category == "Termination":
        if "30 days" in text:
            return "may be terminated with 30 days written notice"
        return "include termination conditions"

    if category == "Liability":
        return "define liability limitations"

    if category == "Payment":
        if "14 days" in text:
            return "require payment 14 days in advance"
        return "include payment terms"

    return None


def build_answer(pieces):
    """
    Build final human-readable answer sentence.
    """
    if not pieces:
        return "No clear answer found."

    if len(pieces) == 1:
        return f"Contracts {pieces[0]}."

    return "Contracts " + ", and ".join(pieces) + "."


def build_ask_response(query, results, mode):
    """
    Build /ask response with selected answer mode.
    """
    lines = clean_lines(results)
    groups = group_lines(lines)

    pieces = []

    for category, items in groups.items():
        if not items:
            continue

        compressed = compress_group(items, category)

        if compressed:
            pieces.append(compressed)

    answer = build_answer(pieces)

    payload = {
        "query": query,
        "mode": mode,
        "documents": len(results),
        "answer": answer,
    }

    if mode == "detailed":
        payload["details"] = {
            "categories_detected": [
                category for category, items in groups.items() if items
            ]
        }

    if mode == "sources":
        payload["sources"] = [
            {
                "file": result.get("file_name"),
                "score": result.get("score"),
            }
            for result in results
        ]

    return payload


# =========================
# REQUEST HANDLER
# =========================

class PAIOSRequestHandler(BaseHTTPRequestHandler):
    """
    Local PAIOS HTTP API.

    Endpoints:
    - /health
    - /search?q=...&refine=...&limit=...&min_score=...
    - /top?q=...&refine=...
    - /open?q=...&refine=...&mode=full|summary|raw
    - /ask?q=...&mode=short|detailed|sources
    """

    def do_GET(self):
        """
        Route GET requests.
        """
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        params = parse_qs(parsed_url.query)

        # -------------------------
        # HEALTH
        # -------------------------
        if path == "/health":
            json_response(
                self,
                {
                    "status": "ok",
                    "service": "PAIOS API",
                },
            )
            return

        # -------------------------
        # SEARCH
        # -------------------------
        if path == "/search":
            query = get_param(params, "q")
            refine = get_param(params, "refine")
            limit = safe_int(get_param(params, "limit"), None)
            min_score = safe_int(get_param(params, "min_score"), None)

            if not query:
                error_response(self, "Missing ?q=")
                return

            if limit is not None and limit < 1:
                error_response(self, "limit must be >= 1")
                return

            full_query, results = run_query_core(
                INDEX_PATH,
                query,
                refine=refine,
                limit=limit,
                min_score=min_score,
            )

            json_response(
                self,
                {
                    "query": query,
                    "refine": refine,
                    "full_query": full_query,
                    "count": len(results),
                    "min_score": min_score,
                    "limit": limit,
                    "results": [format_result(result) for result in results],
                },
            )
            return

        # -------------------------
        # TOP
        # -------------------------
        if path == "/top":
            query = get_param(params, "q")
            refine = get_param(params, "refine")

            if not query:
                error_response(self, "Missing ?q=")
                return

            full_query, results = run_query_core(
                INDEX_PATH,
                query,
                refine=refine,
            )

            top = extract_top_result(results)

            json_response(
                self,
                {
                    "query": query,
                    "refine": refine,
                    "full_query": full_query,
                    "result": format_result(top),
                },
            )
            return

        # -------------------------
        # OPEN
        # -------------------------
        if path == "/open":
            query = get_param(params, "q")
            refine = get_param(params, "refine")
            mode = get_param(params, "mode", "full").lower()

            if not query:
                error_response(self, "Missing ?q=")
                return

            if mode not in ["full", "summary", "raw"]:
                error_response(self, "mode must be full|summary|raw")
                return

            full_query, results = run_query_core(
                INDEX_PATH,
                query,
                refine=refine,
            )

            top = extract_top_result(results)
            opened = open_result(top, mode=mode)

            json_response(
                self,
                {
                    "query": query,
                    "refine": refine,
                    "full_query": full_query,
                    "result": opened,
                },
            )
            return

        # -------------------------
        # ASK
        # -------------------------
        if path == "/ask":
            query = get_param(params, "q")
            mode = get_param(params, "mode", "detailed").lower()

            if not query:
                error_response(self, "Missing ?q=")
                return

            if mode not in ["short", "detailed", "sources"]:
                error_response(self, "mode must be short|detailed|sources")
                return

            refine = auto_refine(query)

            full_query, results = run_query_core(
                INDEX_PATH,
                query,
                refine=refine,
            )

            payload = build_ask_response(full_query, results, mode)

            json_response(self, payload)
            return

        # -------------------------
        # FALLBACK
        # -------------------------
        error_response(
            self,
            "Invalid endpoint. Available: /health, /search, /top, /open, /ask",
            status=404,
        )

    def log_message(self, format, *args):
        """
        Keep terminal output clean by disabling default request logs.
        """
        return


# =========================
# SERVER
# =========================

def run_server():
    """
    Start local API server.
    """
    server = HTTPServer((HOST, PORT), PAIOSRequestHandler)

    print(f"PAIOS API running at http://{HOST}:{PORT}")
    print("Endpoints:")
    print("  /health")
    print("  /search?q=...&refine=...&limit=...&min_score=...")
    print("  /top?q=...&refine=...")
    print("  /open?q=...&refine=...&mode=full|summary|raw")
    print("  /ask?q=...&mode=short|detailed|sources")

    server.serve_forever()


if __name__ == "__main__":
    run_server()