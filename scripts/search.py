import json


def search_index(index_path, query):
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    results = []

    query_lower = query.lower()

    for entry in index:
        file_name = entry.get("file_name", "").lower()

        if query_lower in file_name:
            results.append(entry)

    return results