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

# Tracks progressive refinement context
QUERY_CONTEXT = []


# =========================
# SESSION PERSISTENCE
# =========================

def ensure_session_dir():
    """Ensure the session folder exists."""
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)


def save_session():
    """Save session data to disk."""
    ensure_session_dir()

    data = {
        "history": QUERY_HISTORY,
        "last_query": LAST_QUERY,
        "context": QUERY_CONTEXT
    }

    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_session():
    """Load session data from disk if available."""
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
    """Highlight keyword occurrences in a case-insensitive way."""
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(lambda m: f"[{m.group(0).upper()}]", text)


def print_header(title):
    """Print a formatted title block."""
    print("\n" + "=" * 60)
    print(title.upper())
    print("=" * 60 + "\n")


def print_divider():
    """Print a divider line."""
    print("\n" + "-" * 60 + "\n")


# =========================
# CONTEXT HANDLING
# =========================

def build_context_query():
    """
    Combine all context items into one query string.

    Example:
    ["test", "summary", "errors"]
    -> "test summary errors"
    """
    return " ".join(QUERY_CONTEXT)


def reset_context(new_query=None):
    """
    Reset context.

    - If new_query is provided, it becomes the new base context.
    - If not provided, context becomes empty.
    """
    global QUERY_CONTEXT

    if new_query:
        QUERY_CONTEXT = [new_query]
    else:
        QUERY_CONTEXT = []

    save_session()


def extend_context(extra_words):
    """Append refinement terms to the current context chain."""
    global QUERY_CONTEXT
    QUERY_CONTEXT.append(extra_words)
    save_session()


def show_context():
    """Display the current context chain and combined query."""
    if not QUERY_CONTEXT:
        print("Context is empty.\n")
        return

    print("\nCurrent context chain:")
    for i, item in enumerate(QUERY_CONTEXT, 1):
        print(f"{i}. {item}")

    print(f"\nCombined query: {build_context_query()}\n")


def undo_context():
    """
    Remove the most recent context item.

    Prevents removing the final base query item unless there is more than one item.
    """
    global QUERY_CONTEXT

    if not QUERY_CONTEXT:
        print("Context is already empty.\n")
        return

    if len(QUERY_CONTEXT) == 1:
        print("Cannot undo base query. Use 'reset' to clear context.\n")
        return

    removed = QUERY_CONTEXT.pop()
    save_session()
    print(f"Removed last context item: {removed}")
    print(f"Current context: {build_context_query()}\n")


# =========================
# CORE ENGINE
# =========================

def run_query(query, use_context=True):
    """
    Run a query against the index.

    If use_context=True and context exists, search uses the full context chain.
    """
    global LAST_QUERY, LAST_RESULTS

    if use_context and QUERY_CONTEXT:
        query = build_context_query()

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
    """Display stored query history."""
    if not QUERY_HISTORY:
        print("No query history yet.")
        return

    print("\nQuery History:")
    for i, q in enumerate(QUERY_HISTORY, 1):
        print(f"{i}. {q}")
    print()


def run_history_query(index):
    """Run a past query from history by number."""
    if index < 1 or index > len(QUERY_HISTORY):
        print("Invalid history number.\n")
        return

    query = QUERY_HISTORY[index - 1]
    print(f"\nRunning history query #{index}: {query}")

    reset_context(query)
    run_query(query, use_context=False)


def refine_query(extra_words):
    """Extend the current context chain and rerun query."""
    if not QUERY_CONTEXT:
        print("No base query. Start with a query first.\n")
        return

    extend_context(extra_words)

    refined_query = build_context_query()
    print(f"\nRefined (context): {refined_query}")

    run_query(refined_query, use_context=False)


def open_result(index):
    """Open a selected result and show summary + full content."""
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
    """Main interactive loop for PAIOS."""
    print_header("PAIOS Interactive Mode")

    print("Commands:")
    print('- query')
    print('- history')
    print('- again')
    print('- again <n>')
    print('- refine <words>')
    print('- context')
    print('- undo')
    print('- reset')
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

        if query.lower() == "context":
            show_context()
            continue

        if query.lower() == "undo":
            undo_context()
            continue

        if query.lower() == "reset":
            reset_context()
            print("Context cleared.\n")
            continue

        if query.lower().startswith("again "):
            try:
                run_history_query(int(query.split()[1]))
            except Exception:
                print("Usage: again <n>\n")
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
            except Exception:
                print("Invalid open command.\n")
            continue

        if not query:
            print("Empty query.\n")
            continue

        # Fresh query resets context chain
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