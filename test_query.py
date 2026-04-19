from scripts.search import search_index
import os

INDEX_PATH = "memory/index/index.json"

query = "summary"

results = search_index(INDEX_PATH, query)

print("\nQuery Results:\n")

if not results:
    print("No matches found.")
else:
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