import sys
import os
import re
from scripts.search import search_index

INDEX_PATH = "memory/index/index.json"

# --- Session memory ---
QUERY_HISTORY = []
LAST_QUERY = None


def highlight(text, keyword):
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(lambda m: f"[{m.group(0).upper()}]", text)


def print_header(title):
    print("\n" + "=" * 60)
    print(title.upper())
    print("=" * 60 + "\n")


def print_divider():
    print("\n" + "-" * 60 + "\n")


def parse_args():
    args = sys.argv[1:]
    query_parts = []
    mode = "full"
    limit = None

    for arg in args:
        if arg == "--compact":
            mode = "compact"
        elif arg == "--full":
            mode = "full"
        elif arg.startswith("--limit="):
            try:
                limit = int(arg.split("=")[1])
            except Exception:
                pass
        else:
            query_parts.append(arg)

    query = " ".join(query_parts)
    return query, mode, limit


def run_query(query, mode="full", limit=None):
    global LAST_QUERY

    results = search_index(INDEX_PATH, query)

    # Save query to session memory
    QUERY_HISTORY.append(query)
    LAST_QUERY = query

    print_header(f"Query Results: {query}")

    if not results:
        print("No matches found.")
        return

    if limit:
        results = results[:limit]

    for idx, r in enumerate(results, 1):
        file_name = r.get("file_name")
        score = r.get("score")

        print(f"Result #{idx} | File: {file_name} | Score: {score}")

        if mode == "compact":
            preview = r.get("preview")
            if preview:
                print(highlight(preview[:120], query))
            print_divider()
            continue

        preview = r.get("preview")
        if preview:
            print("\n[Preview]")
            print(highlight(preview, query))

        summary_path = r.get("summary_path")
        if summary_path and os.path.exists(summary_path):
            print("\n[Summary]")
            with open(summary_path, "r", encoding="utf-8") as f:
                content = f.read()
                print(highlight(content, query))
        else:
            print("\n[Summary]")
            print("No summary available.")

        print_divider()


def show_history():
    if not QUERY_HISTORY:
        print("No query history yet.")
        return

    print("\nQuery History:")
    for i, q in enumerate(QUERY_HISTORY, 1):
        print(f"{i}. {q}")
    print()


def refine_query(extra_words):
    """
    Combine the last query with new refinement terms.
    Example:
    last query = "test"
    refine summary
    new query = "test summary"
    """
    global LAST_QUERY

    if not LAST_QUERY:
        print("No previous query to refine.\n")
        return

    refined = f"{LAST_QUERY} {extra_words}".strip()
    print(f"\nRefined query: {refined}")
    run_query(refined)


def interactive_mode():
    global LAST_QUERY

    print_header("PAIOS Interactive Mode")
    print("Commands:")
    print('- type a query')
    print('- "history" -> show past queries')
    print('- "again" -> repeat last query')
    print('- "refine <extra words>" -> extend last query')
    print('- "exit" -> quit\n')

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

        if query.lower().startswith("refine "):
            extra_words = query[7:].strip()
            if extra_words:
                refine_query(extra_words)
            else:
                print("Usage: refine <extra words>\n")
            continue

        if not query:
            print("Empty query.\n")
            continue

        run_query(query)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        query, mode, limit = parse_args()

        if not query:
            print('Usage: python3 cli.py "your query here" [--compact] [--limit=N]')
        else:
            run_query(query, mode, limit)