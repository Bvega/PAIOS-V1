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


def count_occurrences(text, term):
    """
    Count how many times one term appears in text.
    """
    return text.count(term)


def get_preview_snippet(path, query, window=80):
    """
    Extract a snippet around the first match of any query term.
    """
    if not path or not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content_lower = content.lower()
    terms = query.lower().split()

    first_idx = -1
    first_term = ""

    for term in terms:
        idx = content_lower.find(term)
        if idx != -1 and (first_idx == -1 or idx < first_idx):
            first_idx = idx
            first_term = term

    if first_idx == -1:
        return None

    start = max(0, first_idx - window)
    end = min(len(content), first_idx + len(first_term) + window)

    return content[start:end].replace("\n", " ")


def search_index(index_path, query):
    index = load_index(index_path)
    results = []
    terms = query.lower().split()

    for entry in index:
        file_name = entry.get("file_name", "").lower()
        summary_path = entry.get("summary_path")
        text_path = entry.get("text_path")

        summary_content = read_file_safe(summary_path)
        text_content = read_file_safe(text_path)

        score = 0
        matched_terms = 0

        for term in terms:
            term_matched = False

            # filename match
            if term in file_name:
                score += 2
                term_matched = True

            # summary occurrences
            summary_hits = count_occurrences(summary_content, term)
            if summary_hits > 0:
                score += summary_hits * 3
                term_matched = True

            # text occurrences
            text_hits = count_occurrences(text_content, term)
            if text_hits > 0:
                score += text_hits * 2
                term_matched = True

            if term_matched:
                matched_terms += 1

        # bonus if multiple query terms matched
        if matched_terms > 1:
            score += matched_terms * 2

        snippet = get_preview_snippet(text_path, query)
        if snippet:
            entry["preview"] = snippet

        if score > 0:
            entry["score"] = score
            entry["matched_terms"] = matched_terms
            results.append(entry)

    results.sort(key=lambda x: (x["score"], x["matched_terms"]), reverse=True)

    return results