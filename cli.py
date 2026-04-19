import sys
import os
from scripts.search import search_index

# Central index file used by the CLI query tool
INDEX_PATH = "memory/index/index.json"


def run_query(query):
    """
    Run a search query against the local PAIOS index and print
    clean, human-readable results.
    """
    results = search_index(INDEX_PATH, query)

    print("\nQuery Results:\n")

    if not results:
        print("No matches found.")
        return

    # Loop through each matching result and display it clearly
    for r in results:
        print(f"File: {r.get('file_name')}")
        print(f"Score: {r.get('score')}")

        summary_path = r.get("summary_path")

        # If a summary exists, print it inside the result block
        if summary_path and os.path.exists(summary_path):
            print("\nSummary:")
            with open(summary_path, "r", encoding="utf-8") as f:
                print(f.read())
        else:
            print("No summary available.")

        # Separator between results for readability
        print("\n" + "-" * 40 + "\n")


if __name__ == "__main__":
    # Require at least one query argument from the command line
    if len(sys.argv) < 2:
        print('Usage: python3 cli.py "your query here"')
    else:
        # Join all command-line words into one search query
        query = " ".join(sys.argv[1:])
        run_query(query)