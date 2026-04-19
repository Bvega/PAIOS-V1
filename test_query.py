from scripts.search import search_index

INDEX_PATH = "memory/index/index.json"

query = "summary"

results = search_index(INDEX_PATH, query)

print("\nQuery Results:\n")

if not results:
    print("No matches found.")
else:
    for r in results:
        print(r)