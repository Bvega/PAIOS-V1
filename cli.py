import sys
import os
import re
from scripts.search import search_index

INDEX_PATH = "memory/index/index.json"

# --- Session memory ---
QUERY_HISTORY = []
LAST_QUERY = None
LAST_RESULTS = []


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
    global LAST_QUERY, LAST_RESULTS

    results = search_index(INDEX_PATH, query)

    QUERY_HISTORY.append(query)
    LAST_QUERY = query
    LAST_RESULTS = results

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

        preview = r.get("preview")
        if preview:
            print("\n[Preview]")
            print(highlight(preview, query))

        print_divider()


def open_result(index):
    """
    Open full content of selected result
    """
    if not LAST_RESULTS:
        print("No results available. Run a query first.\n")
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
    else:
        print("File not found.")

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
    global LAST_QUERY

    if not LAST_QUERY:
        print("No previous query to refine.\n")
        return

    refined = f"{LAST_QUERY} {extra_words}".strip()
    print(f"\nRefined query: {refined}")
    run_query(refined)


def interactive_mode():
    print_header("PAIOS Interactive Mode")
    print("Commands:")
    print('- type a query')
    print('- "history" -> show past queries')
    print('- "again" -> repeat last query')
    print('- "refine <words>" -> extend last query')
    print('- "open <number>" -> open result')
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
                print("Usage: refine <words>\n")
            continue

        if query.lower().startswith("open "):
            try:
                idx = int(query.split()[1])
                open_result(idx)
            except:
                print("Usage: open <result number>\n")
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
            print('Usage: python3 cli.py "your query here"')
        else:
            run_query(query, mode, limit)