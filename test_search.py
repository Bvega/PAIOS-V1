from scripts.search import search_index

INDEX_PATH = "memory/index/index.json"

query = "test"

results = search_index(INDEX_PATH, query)

print("\nSearch Results:\n")

for r in results:
    print(r)