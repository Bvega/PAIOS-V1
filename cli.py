import sys
import os
import re
from scripts.search import search_index

INDEX_PATH = "memory/index/index.json"


def highlight(text, keyword):
    """
    Case-insensitive keyword highlighting.
    Wraps matches with [WORD]
    """
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(lambda m: f"[{m.group(0).upper()}]", text)


def run_query(query):
    results = search_index(INDEX_PATH, query)

    print("\nQuery Results:\n")

    if not results:
        print("No matches found.")
        return

    for r in results:
        file_name = r.get("file_name")
        score = r.get("score")

        print(f"File: {file_name}")
        print(f"Score: {score}")

        preview = r.get("preview")
        if preview:
            print("\nPreview:")
            print(highlight(preview, query))

        summary_path = r.get("summary_path")

        if summary_path and os.path.exists(summary_path):
            print("\nSummary:")
            with open(summary_path, "r", encoding="utf-8") as f:
                content = f.read()
                print(highlight(content, query))
        else:
            print("No summary available.")

        print("\n" + "-" * 40 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python3 cli.py "your query here"')
    else:
        query = " ".join(sys.argv[1:])
        run_query(query)