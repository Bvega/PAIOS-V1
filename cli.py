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
    Used for sections like results and open views.
    """
    print("\n" + "=" * 60)
    print(title.upper())
    print("=" * 60 + "\n")


def print_divider():
    """
    Prints a separator between results or sections.
    Improves readability in CLI output.
    """
    print("\n" + "-" * 60 + "\n")


def ensure_exports_dir():
    """
    Ensure the exports directory exists before saving files.
    """
    os.makedirs(EXPORTS_DIR, exist_ok=True)


def build_export_filename(prefix):
    """
    Build a timestamped export filename.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(EXPORTS_DIR, f"{prefix}_{timestamp}.txt")


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

        # Write summary when requested
        if mode in ["summary", "full"]:
            f.write("[Summary]\n")
            if summary_path and os.path.exists(summary_path):
                with open(summary_path, "r", encoding="utf-8") as summary_file:
                    f.write(summary_file.read() + "\n")
            else:
                f.write("No summary available.\n")
            f.write("\n" + "-" * 60 + "\n\n")

        # Write raw/full content when requested
        if mode in ["raw", "full"]:
            f.write("[Full Content]\n")
            if text_path and os.path.exists(text_path):
                with open(text_path, "r", encoding="utf-8") as text_file:
                    f.write(text_file.read() + "\n")
            else:
                f.write("File not found.\n")

    print(f"Selected result exported to: {export_path}\n")


def run_query(query):
    """
    Executes a search query and stores results in session memory.

    Responsibilities:
    - Calls search engine
    - Saves query + results
    - Displays preview of each result
    """
    global LAST_QUERY, LAST_RESULTS

    results = search_index(INDEX_PATH, query)

    # Save query history
    QUERY_HISTORY.append(query)
    LAST_QUERY = query
    LAST_RESULTS = results

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


def open_result(index, mode="full"):
    """
    Opens a selected result based on its index.

    Modes:
    - full → show summary + full content
    - summary → show only summary
    - raw → show only full file content

    Uses LAST_RESULTS from previous query.
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

    # Show summary if requested
    if mode in ["summary", "full"]:
        if summary_path and os.path.exists(summary_path):
            print("[Summary]")
            with open(summary_path, "r", encoding="utf-8") as summary_file:
                print(summary_file.read())
            print_divider()
        else:
            print("No summary available.\n")

    # Show raw content if requested
    if mode in ["raw", "full"]:
        if text_path and os.path.exists(text_path):
            print("[Full Content]")
            with open(text_path, "r", encoding="utf-8") as text_file:
                print(text_file.read())
        else:
            print("File not found.")

    print_divider()


def show_history():
    """
    Displays all previous queries from this session.
    """
    if not QUERY_HISTORY:
        print("No query history yet.")
        return

    print("\nQuery History:")
    for i, query in enumerate(QUERY_HISTORY, 1):
        print(f"{i}. {query}")
    print()


def refine_query(extra_words):
    """
    Extends the last query with additional words.

    Example:
    LAST_QUERY = "test"
    refine summary → "test summary"
    """
    global LAST_QUERY

    if not LAST_QUERY:
        print("No previous query.\n")
        return

    refined = f"{LAST_QUERY} {extra_words}".strip()
    print(f"\nRefined query: {refined}")
    run_query(refined)


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
    print('- "history" -> show past queries')
    print('- "again" -> repeat last query')
    print('- "refine <words>" -> extend last query')
    print('- "open <n>" -> open full result')
    print('- "open summary <n>" -> summary only')
    print('- "open raw <n>" -> raw content only')
    print('- "export" -> save last result set to outputs/')
    print('- "export <n>" -> export one full result')
    print('- "export summary <n>" -> export summary only')
    print('- "export raw <n>" -> export full content only')
    print('- "exit" -> quit\n')

    while True:
        query = input("PAIOS> ").strip()

        # Exit command
        if query.lower() in ["exit", "quit"]:
            print("\nExiting PAIOS.")
            break

        # Show history
        if query.lower() == "history":
            show_history()
            continue

        # Repeat last query
        if query.lower() == "again":
            if LAST_QUERY:
                run_query(LAST_QUERY)
            else:
                print("No previous query.\n")
            continue

        # Export last results
        if query.lower() == "export":
            export_last_results()
            continue

        # Export selected result
        if query.lower().startswith("export "):
            parts = query.split()

            try:
                if len(parts) == 2:
                    export_result(int(parts[1]), "full")
                elif len(parts) == 3:
                    mode = parts[1]
                    index = int(parts[2])

                    if mode in ["summary", "raw"]:
                        export_result(index, mode)
                    else:
                        print("Invalid export mode.\n")
                else:
                    print("Usage: export <n> | export summary <n> | export raw <n>\n")
            except Exception:
                print("Invalid export command format.\n")

            continue

        # Refine query
        if query.lower().startswith("refine "):
            extra_words = query[7:].strip()
            refine_query(extra_words)
            continue

        # Open commands
        if query.lower().startswith("open "):
            parts = query.split()

            try:
                if len(parts) == 2:
                    open_result(int(parts[1]), "full")
                elif len(parts) == 3:
                    mode = parts[1]
                    index = int(parts[2])

                    if mode in ["summary", "raw"]:
                        open_result(index, mode)
                    else:
                        print("Invalid open mode.\n")
                else:
                    print("Usage: open <n> | open summary <n> | open raw <n>\n")
            except Exception:
                print("Invalid command format.\n")

            continue

        # Empty input
        if not query:
            print("Empty query.\n")
            continue

        # Default: run query
        run_query(query)


if __name__ == "__main__":
    # If no arguments → interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        query = " ".join(sys.argv[1:])
        if not query:
            print('Usage: python3 cli.py "your query here"')
        else:
            run_query(query)