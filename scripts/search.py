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


def get_preview_snippet(path, query, window=80):
    """
    Extract a small snippet around the first match of the query.
    """
    if not path or not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content_lower = content.lower()
    query_lower = query.lower()

    idx = content_lower.find(query_lower)
    if idx == -1:
        return None

    start = max(0, idx - window)
    end = min(len(content), idx + len(query) + window)

    return content[start:end].replace("\n", " ")


def search_index(index_path, query):
    index = load_index(index_path)
    results = []
    query_lower = query.lower()

    for entry in index:
        file_name = entry.get("file_name", "").lower()
        summary_path = entry.get("summary_path")
        text_path = entry.get("text_path")

        summary_content = read_file_safe(summary_path)

        score = 0

        # filename match
        if query_lower in file_name:
            score += 2

        # summary/content match
        if query_lower in summary_content:
            score += 3

        # NEW: preview snippet from processed text
        snippet = get_preview_snippet(text_path, query)
        if snippet:
            entry["preview"] = snippet
            score += 2

        if score > 0:
            entry["score"] = score
            results.append(entry)

    results.sort(key=lambda x: x["score"], reverse=True)

    return results