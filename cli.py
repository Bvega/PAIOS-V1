import sys
import os
import re
import json
from datetime import datetime
from scripts.search import search_index

# =========================
# PATHS
# =========================

INDEX_PATH = "memory/index/index.json"
EXPORTS_DIR = "outputs"
SESSION_FILE = "memory/session/session.json"

# =========================
# SESSION MEMORY
# =========================

QUERY_HISTORY = []
LAST_QUERY = None
LAST_RESULTS = []

# =========================
# SESSION PERSISTENCE
# =========================

def ensure_session_dir():
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)


def save_session():
    ensure_session_dir()

    data = {
        "history": QUERY_HISTORY,
        "last_query": LAST_QUERY
    }

    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_session():
    global QUERY_HISTORY, LAST_QUERY

    if not os.path.exists(SESSION_FILE):
        return

    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

            QUERY_HISTORY = data.get("history", [])
            LAST_QUERY = data.get("last_query", None)

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
# CORE ENGINE
# =========================

def run_query(query):
    global LAST_QUERY, LAST_RESULTS

    results = search_index(INDEX_PATH, query)

    QUERY_HISTORY.append(query)
    LAST_QUERY = query
    LAST_RESULTS = results

    save_session()

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

def show_history():
    if not QUERY_HISTORY:
        print("No query history yet.")
        return

    print("\nQuery History:")
    for i, q in enumerate(QUERY_HISTORY, 1):
        print(f"{i}. {q}")
    print()


def run_history_query(index):
    """
    Run a query from history by index.

    Example:
    history:
    1. test
    2. test summary

    again 2 → runs "test summary"
    """
    if index < 1 or index > len(QUERY_HISTORY):
        print("Invalid history number.\n")
        return

    query = QUERY_HISTORY[index - 1]
    print(f"\nRunning history query #{index}: {query}")
    run_query(query)


def refine_query(extra_words):
    global LAST_QUERY

    if not LAST_QUERY:
        print("No previous query.\n")
        return

    refined = f"{LAST_QUERY} {extra_words}".strip()
    print(f"\nRefined query: {refined}")
    run_query(refined)


def open_result(index):
    if not LAST_RESULTS:
        print("No results available.\n")
        return

    if index < 1 or index > len(LAST_RESULTS):
        print("Invalid result number.\n")
        return

    result = LAST_RESULTS[index - 1]
    text_path = result.get("text_path")
    summary_path = result.get("summary_path")

    print_header(f"Opening Result #{index}")

    if summary_path and os.path.exists(summary_path):
        print("[Summary]")
        with open(summary_path, "r", encoding="utf-8") as f:
            print(f.read())
        print_divider()

    if text_path and os.path.exists(text_path):
        print("[Full Content]")
        with open(text_path, "r", encoding="utf-8") as f:
            print(f.read())

    print_divider()


# =========================
# INTERACTIVE LOOP
# =========================

def interactive_mode():
    print_header("PAIOS Interactive Mode")

    print("Commands:")
    print('- query')
    print('- history')
    print('- again')
    print('- again <n>  (run query from history)')
    print('- refine <words>')
    print('- open <n>')
    print('- exit\n')

    while True:
        query = input("PAIOS> ").strip()

        if query.lower() in ["exit", "quit"]:
            print("\nExiting PAIOS.")
            break

        if query.lower() == "history":
            show_history()
            continue

        # New: run specific history query
        if query.lower().startswith("again "):
            try:
                index = int(query.split()[1])
                run_history_query(index)
            except:
                print("Usage: again <history number>\n")
            continue

        if query.lower() == "again":
            if LAST_QUERY:
                run_query(LAST_QUERY)
            else:
                print("No previous query.\n")
            continue

        if query.lower().startswith("refine "):
            refine_query(query[7:].strip())
            continue

        if query.lower().startswith("open "):
            try:
                open_result(int(query.split()[1]))
            except:
                print("Invalid open command.\n")
            continue

        if not query:
            print("Empty query.\n")
            continue

        run_query(query)


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    load_session()

    if len(sys.argv) == 1:
        interactive_mode()
    else:
        query = " ".join(sys.argv[1:])
        run_query(query)