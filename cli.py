
import sys
import os
import re
from datetime import datetime
from scripts.search import search_index

# Path to the generated index file
INDEX_PATH = "memory/index/index.json"

# Directory where exported query results will be saved
EXPORTS_DIR = "outputs"

# --- Session memory ---
# Stores all queries made during the session
QUERY_HISTORY = []

# Stores the last executed query
LAST_QUERY = None

# Stores last search results (used for open/export commands)
LAST_RESULTS = []


def highlight(text, keyword):
    """
    Highlight keyword occurrences inside text.

    - Case-insensitive
    - Wraps matches in [WORD] for visibility
    """
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(lambda m: f"[{m.group(0).upper()}]", text)


def print_header(title):
    """
    Prints a formatted header block.
    """
    print("\n" + "=" * 60)
    print(title.upper())
    print("=" * 60 + "\n")


def print_divider():
    """
    Prints a separator between results or sections.
    """
    print("\n" + "-" * 60 + "\n")


def ensure_exports_dir():
    """
    Ensure the exports directory exists.
    """
    os.makedirs(EXPORTS_DIR, exist_ok=True)


def build_export_filename(prefix):
    """
    Build a timestamped export filename.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(EXPORTS_DIR, f"{prefix}_{timestamp}.txt")


# =========================
# SUGGESTION ENGINE
# =========================

def suggest_actions():
    """
    Suggest next actions based on the current result set.

    Rules:
    - No results -> suggest broadening or changing query
    - One result -> suggest opening it directly
    - Many results -> suggest refining
    - If a summary exists in first result -> suggest opening summary
    """
    print("\nSuggestions:")

    # No results: help user recover
    if not LAST_RESULTS:
        print('- try a broader query')
        print('- try fewer keywords')
        print('- try OR mode, for example: test | summary')
        print('- try exact phrase mode, for example: "line two for summary"')
        print()
        return

    first_result = LAST_RESULTS[0]
    first_summary = first_result.get("summary_path")

    # One strong result: suggest direct inspection
    if len(LAST_RESULTS) == 1:
        print('- open 1')
        if first_summary and os.path.exists(first_summary):
            print('- open summary 1')
        print('- export 1')
        print()
        return

    # Many results: suggest narrowing the search
    print('- refine summary')
    print('- refine <more keywords>')
    print('- open 1')

    if first_summary and os.path.exists(first_summary):
        print('- open summary 1')

    print('- export 1')
    print()


# =========================
# EXPORT LOGIC
# =========================

def export_last_results():
    """
    Export the most recent query results to a timestamped text file.

    Output includes:
    - query used
    - result numbering
    - file names
    - scores
    - previews
    """
    if not LAST_RESULTS or not LAST_QUERY:
        print("No results available to export.\n")
        return

    ensure_exports_dir()
    export_path = build_export_filename("query_export")

    with open(export_path, "w", encoding="utf-8") as f:
        f.write("PAIOS Query Export\n")
        f.write(f"Query: {LAST_QUERY}\n")
        f.write("=" * 60 + "\n\n")

        for idx, result in enumerate(LAST_RESULTS, 1):
            f.write(f"Result #{idx}\n")
            f.write(f"File  : {result.get('file_name')}\n")
            f.write(f"Score : {result.get('score')}\n")

            preview = result.get("preview")
            if preview:
                f.write("\n[Preview]\n")
                f.write(preview + "\n")

            f.write("\n" + "-" * 60 + "\n\n")

    print(f"Results exported to: {export_path}\n")


def export_result(index, mode="full"):
    """
    Export one selected result.

    Modes:
    - full: summary + full content
    - summary: summary only
    - raw: full content only
    """
    if not LAST_RESULTS:
        print("No results available to export.\n")
        return

    if index < 1 or index > len(LAST_RESULTS):
        print("Invalid result number.\n")
        return

    ensure_exports_dir()

    result = LAST_RESULTS[index - 1]
    file_name = result.get("file_name", f"result_{index}")
    base_name = os.path.splitext(file_name)[0]

    export_path = build_export_filename(f"{base_name}_{mode}")

    text_path = result.get("text_path")
    summary_path = result.get("summary_path")

    with open(export_path, "w", encoding="utf-8") as f:
        f.write("PAIOS Selected Result Export\n")
        f.write(f"Query: {LAST_QUERY}\n")
        f.write(f"Result #: {index}\n")
        f.write(f"File: {file_name}\n")
        f.write(f"Mode: {mode}\n")
        f.write("=" * 60 + "\n\n")

        if mode in ["summary", "full"]:
            f.write("[Summary]\n")
            if summary_path and os.path.exists(summary_path):
                with open(summary_path, "r", encoding="utf-8") as s:
                    f.write(s.read() + "\n")
            else:
                f.write("No summary available.\n")
            f.write("\n" + "-" * 60 + "\n\n")

        if mode in ["raw", "full"]:
            f.write("[Full Content]\n")
            if text_path and os.path.exists(text_path):
                with open(text_path, "r", encoding="utf-8") as t:
                    f.write(t.read() + "\n")
            else:
                f.write("File not found.\n")

    print(f"Selected result exported to: {export_path}\n")


# =========================
# CORE ENGINE
# =========================

def run_query(query):
    """
    Execute a search query and store results in session memory.

    Responsibilities:
    - Call search engine
    - Save query + results
    - Display preview of each result
    - Show context-aware suggestions
    """
    global LAST_QUERY, LAST_RESULTS

    results = search_index(INDEX_PATH, query)

    QUERY_HISTORY.append(query)
    LAST_QUERY = query
    LAST_RESULTS = results

    print_header(f"Query Results: {query}")

    if not results:
        print("No matches found.")
        suggest_actions()
        return

    for idx, result in enumerate(results, 1):
        print(f"Result #{idx} | File: {result.get('file_name')} | Score: {result.get('score')}")

        preview = result.get("preview")
        if preview:
            print("\n[Preview]")
            print(highlight(preview, query))

        print_divider()

    suggest_actions()


def open_result(index, mode="full"):
    """
    Open a selected result based on its index.

    Modes:
    - full -> show summary + full content
    - summary -> show only summary
    - raw -> show only full file content
    """
    if not LAST_RESULTS:
        print("No results available.\n")
        return

    if index < 1 or index > len(LAST_RESULTS):
        print("Invalid result number.\n")
        return

    result = LAST_RESULTS[index - 1]

    text_path = result.get("text_path")
    summary_path = result.get("summary_path")

    print_header(f"Opening Result #{index} ({mode})")

    if mode in ["summary", "full"]:
        if summary_path and os.path.exists(summary_path):
            print("[Summary]")
            with open(summary_path, "r", encoding="utf-8") as s:
                print(s.read())
            print_divider()
        else:
            print("No summary available.\n")

    if mode in ["raw", "full"]:
        if text_path and os.path.exists(text_path):
            print("[Full Content]")
            with open(text_path, "r", encoding="utf-8") as t:
                print(t.read())
        else:
            print("File not found.")

    print_divider()


def show_history():
    """
    Display all previous queries from this session.
    """
    if not QUERY_HISTORY:
        print("No query history yet.")
        return

    print("\nQuery History:")
    for i, q in enumerate(QUERY_HISTORY, 1):
        print(f"{i}. {q}")
    print()


def refine_query(extra_words):
    """
    Extend the last query with additional words.

    Example:
    LAST_QUERY = "test"
    refine summary -> "test summary"
    """
    global LAST_QUERY

    if not LAST_QUERY:
        print("No previous query.\n")
        return

    refined = f"{LAST_QUERY} {extra_words}".strip()
    print(f"\nRefined query: {refined}")
    run_query(refined)


# =========================
# INTERACTIVE LOOP
# =========================

def interactive_mode():
    """
    Main loop for interactive CLI session.

    Handles:
    - user input
    - command parsing
    - routing to appropriate functions
    """
    print_header("PAIOS Interactive Mode")

    print("Commands:")
    print('- type a query')
    print('- "history"')
    print('- "again"')
    print('- "refine <words>"')
    print('- "open <n>"')
    print('- "open summary <n>"')
    print('- "open raw <n>"')
    print('- "export"')
    print('- "export <n>"')
    print('- "export summary <n>"')
    print('- "export raw <n>"')
    print('- "exit"\n')

    while True:
        query = input("PAIOS> ").strip()

        if query.lower() in ["exit", "quit"]:
            print("\nExiting PAIOS.")
            break

        if query.lower() == "history":
            show_history()
            continue

        if query.lower() == "again":
            if LAST_QUERY:
                run_query(LAST_QUERY)
            else:
                print("No previous query.\n")
            continue

        if query.lower() == "export":
            export_last_results()
            continue

        if query.lower().startswith("export "):
            parts = query.split()
            try:
                if len(parts) == 2:
                    export_result(int(parts[1]), "full")
                elif len(parts) == 3:
                    mode = parts[1]
                    index = int(parts[2])
                    export_result(index, mode)
                else:
                    print("Invalid export command.\n")
            except Exception:
                print("Invalid export command.\n")
            continue

        if query.lower().startswith("refine "):
            refine_query(query[7:].strip())
            continue

        if query.lower().startswith("open "):
            parts = query.split()
            try:
                if len(parts) == 2:
                    open_result(int(parts[1]), "full")
                elif len(parts) == 3:
                    open_result(int(parts[2]), parts[1])
                else:
                    print("Invalid open command.\n")
            except Exception:
                print("Invalid open command.\n")
            continue

        if not query:
            print("Empty query.\n")
            continue

        run_query(query)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        query = " ".join(sys.argv[1:])
        run_query(query)