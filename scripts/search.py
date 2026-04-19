import json
import os


def load_index(index_path):
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_file_safe(path):
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().lower()
    return ""


def search_index(index_path, query):
    index = load_index(index_path)
    results = []
    query_lower = query.lower()

    for entry in index:
        file_name = entry.get("file_name", "").lower()
        summary_path = entry.get("summary_path")

        summary_content = read_file_safe(summary_path)

        score = 0

        # filename match
        if query_lower in file_name:
            score += 2

        # summary/content match
        if query_lower in summary_content:
            score += 3

        if score > 0:
            entry["score"] = score
            results.append(entry)

    # sort by score (highest first)
    results.sort(key=lambda x: x["score"], reverse=True)

    return results