
import sys
import os
import re
import json
from scripts.search import search_index

# =========================
# PATHS
# =========================

INDEX_PATH = "memory/index/index.json"
SESSION_FILE = "memory/session/session.json"

# =========================
# SESSION MEMORY
# =========================

QUERY_HISTORY = []
LAST_QUERY = None
LAST_RESULTS = []
QUERY_CONTEXT = []

# New: output mode (human vs json)
OUTPUT_MODE = "human"


# =========================
# SESSION PERSISTENCE
# =========================

def ensure_session_dir():
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)


def save_session():
    ensure_session_dir()

    data = {
        "history": QUERY_HISTORY,
        "last_query": LAST_QUERY,
        "context": QUERY_CONTEXT
    }

    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_session():
    global QUERY_HISTORY, LAST_QUERY, QUERY_CONTEXT

    if not os.path.exists(SESSION_FILE):
        return

    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        QUERY_HISTORY = data.get("history", [])
        LAST_QUERY = data.get("last_query", None)
        QUERY_CONTEXT = data.get("context", [])

    except Exception:
        print("Warning: Failed to load session data.")


# =========================
# UTILITIES
# =========================

def highlight(text, keyword):
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(lambda m: f"[{m.group(0).upper()}]", text)


def print_header(title):
    print("\n" + "=" * 60)
    print(title.upper())
    print("=" * 60 + "\n")


def print_divider():
    print("\n" + "-" * 60 + "\n")


# =========================
# CONTEXT HANDLING
# =========================

def build_context_query():
    return " ".join(QUERY_CONTEXT)


def reset_context(new_query=None):
    global QUERY_CONTEXT

    if new_query:
        QUERY_CONTEXT = [new_query]
    else:
        QUERY_CONTEXT = []

    save_session()


def extend_context(extra_words):
    global QUERY_CONTEXT
    QUERY_CONTEXT.append(extra_words)
    save_session()


# =========================
# LLM OUTPUT FORMAT
# =========================

def format_results_json(query, results):
    """
    Return structured JSON output for LLM or API usage.
    """
    formatted = {
        "query": query,
        "results": []
    }

    for r in results:
        formatted["results"].append({
            "file": r.get("file_name"),
            "score": r.get("score"),
            "preview": r.get("preview"),
            "summary_path": r.get("summary_path"),
            "text_path": r.get("text_path")
        })

    return formatted


# =========================
# CORE ENGINE
# =========================

def run_query(query, use_context=True):
    global LAST_QUERY, LAST_RESULTS

    if use_context and QUERY_CONTEXT:
        query = build_context_query()

    results = search_index(INDEX_PATH, query)

    QUERY_HISTORY.append(query)
    LAST_QUERY = query
    LAST_RESULTS = results

    save_session()

    # JSON MODE (for AI integration)
    if OUTPUT_MODE == "json":
        print(json.dumps(format_results_json(query, results), indent=2))
        return

    # HUMAN MODE
    print_header(f"Query Results: {query}")

    if not results:
        print("No matches found.")
        return

    for idx, result in enumerate(results, 1):
        print(f"Result #{idx} | File: {result.get('file_name')} | Score: {result.get('score')}")

        preview = result.get("preview")
        if preview:
            print("\n[Preview]")
            print(highlight(preview, query))

        print_divider()


# =========================
# COMMANDS
# =========================

def set_output_mode(mode):
    global OUTPUT_MODE

    if mode not in ["human", "json"]:
        print("Invalid mode. Use: mode human | mode json\n")
        return

    OUTPUT_MODE = mode
    print(f"Output mode set to: {mode}\n")


def show_top_result():
    if not LAST_RESULTS:
        print("No results available.\n")
        return

    top = LAST_RESULTS[0]

    print_header("Top Result")
    print(f"File  : {top.get('file_name')}")
    print(f"Score : {top.get('score')}")

    preview = top.get("preview")
    if preview:
        print("\n[Preview]")
        print(preview)

    print_divider()


# =========================
# INTERACTIVE LOOP
# =========================

def interactive_mode():
    print_header("PAIOS Interactive Mode")

    print("Commands:")
    print('- query')
    print('- refine <words>')
    print('- top')
    print('- mode human')
    print('- mode json')
    print('- exit\n')

    while True:
        query = input("PAIOS> ").strip()

        if query.lower() in ["exit", "quit"]:
            print("\nExiting PAIOS.")
            break

        if query.lower() == "top":
            show_top_result()
            continue

        if query.lower().startswith("mode "):
            set_output_mode(query.split()[1])
            continue

        if query.lower().startswith("refine "):
            extend_context(query[7:].strip())
            run_query(build_context_query(), use_context=False)
            continue

        if not query:
            print("Empty query.\n")
            continue

        reset_context(query)
        run_query(query, use_context=False)


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    load_session()

    if len(sys.argv) == 1:
        interactive_mode()
    else:
        query = " ".join(sys.argv[1:])
        reset_context(query)
        run_query(query, use_context=False)