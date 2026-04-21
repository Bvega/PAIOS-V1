import sys
import os
import re
from scripts.search import search_index

INDEX_PATH = "memory/index/index.json"


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
    """
    Parses CLI arguments for:
    --compact
    --full (default)
    --limit=N
    """
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
            except:
                pass
        else:
            query_parts.append(arg)

    query = " ".join(query_parts)
    return query, mode, limit


def run_query(query, mode="full", limit=None):
    results = search_index(INDEX_PATH, query)

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

        # FULL MODE
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


if __name__ == "__main__":
    query, mode, limit = parse_args()

    if not query:
        print('Usage: python3 cli.py "your query here" [--compact] [--limit=N]')
    else:
        run_query(query, mode, limit)