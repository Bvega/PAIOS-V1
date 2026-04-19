import sys
import os
from scripts.search import search_index

INDEX_PATH = "memory/index/index.json"

def run_query(query):
    results = search_index(INDEX_PATH, query)

    print("\nQuery Results:\n")

    if not results:
        print("No matches found.")
        return

    for r in results:
        print(f"File: {r.get('file_name')}")
        print(f"Score: {r.get('score')}")

        summary_path = r.get("summary_path")

        if summary_path and os.path.exists(summary_path):
            print("\nSummary:")
            with open(summary_path, "r", encoding="utf-8") as f:
                print(f.read())
        else:
            print("No summary available.")

        print("\n" + "-"*40 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 cli.py \"your query here\"")
    else:
        query = " ".join(sys.argv[1:])
        run_query(query)
        