import sys
import os
import re
from scripts.search import search_index

# Path to the generated index file
INDEX_PATH = "memory/index/index.json"

# --- Session memory ---
# Stores all queries made during the session
QUERY_HISTORY = []

# Stores the last executed query
LAST_QUERY = None

# Stores last search results (used for open commands)
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

    for idx, r in enumerate(results, 1):
        print(f"Result #{idx} | File: {r.get('file_name')} | Score: {r.get('score')}")

        preview = r.get("preview")
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
            with open(summary_path, "r", encoding="utf-8") as f:
                print(f.read())
            print_divider()
        else:
            print("No summary available.\n")

    # Show raw content if requested
    if mode in ["raw", "full"]:
        if text_path and os.path.exists(text_path):
            print("[Full Content]")
            with open(text_path, "r", encoding="utf-8") as f:
                print(f.read())
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
    for i, q in enumerate(QUERY_HISTORY, 1):
        print(f"{i}. {q}")
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