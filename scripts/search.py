import json
import os

def search_index(index_path, query):
    if not os.path.exists(index_path):
        return []

    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    results = []
    query_lower = query.lower()

    for entry in index:
        file_name = entry.get("file_name", "").lower()
        text_path = entry.get("text_path")

        match_score = 0

        # Match in filename
        if query_lower in file_name:
            match_score += 2

        # Match in file content
        if text_path and os.path.exists(text_path):
            try:
                with open(text_path, "r", encoding="utf-8") as f:
                    content = f.read().lower()
                    if query_lower in content:
                        match_score += 3
            except:
                pass

        if match_score > 0:
            entry["score"] = match_score
            results.append(entry)

    # Sort by relevance
    results.sort(key=lambda x: x.get("score", 0), reverse=True)

    return results