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


def count_occurrences(text, query):
    """
    Count how many times a query appears in text.
    """
    return text.count(query)


def get_preview_snippet(path, query, window=80):
    """
    Extract a snippet around the first match.
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
        text_content = read_file_safe(text_path)

        score = 0

        # filename match
        if query_lower in file_name:
            score += 2

        # summary occurrences
        summary_hits = count_occurrences(summary_content, query_lower)
        score += summary_hits * 3

        # text occurrences (NEW)
        text_hits = count_occurrences(text_content, query_lower)
        score += text_hits * 2

        # preview snippet
        snippet = get_preview_snippet(text_path, query)
        if snippet:
            entry["preview"] = snippet

        if score > 0:
            entry["score"] = score
            results.append(entry)

    results.sort(key=lambda x: x["score"], reverse=True)

    return results