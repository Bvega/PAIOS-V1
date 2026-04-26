# scripts/search.py
# ============================================
# PAIOS Search Module (WITH HIGHLIGHTING)
# ============================================

import json
import os
import re


# ============================================
# Load Index
# ============================================

def load_index(index_path):
    if not os.path.exists(index_path):
        return []

    with open(index_path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================
# Safe File Reader
# ============================================

def read_file_safe(path):
    if not path or not os.path.exists(path):
        return ""

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            return file.read().lower()
    except:
        return ""


# ============================================
# Normalize Text
# ============================================

def normalize_text(text):
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^a-z0-9áéíóúñü\s_-]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def split_terms(query):
    return [term for term in normalize_text(query).split() if term]


# ============================================
# Highlight Matches
# ============================================

def highlight_terms(snippet, query):
    """
    Highlight matching terms inside snippet using **term**
    """
    if not snippet:
        return ""

    terms = split_terms(query)

    for term in terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        snippet = pattern.sub(lambda m: f"**{m.group(0)}**", snippet)

    return snippet


# ============================================
# Occurrence Counter
# ============================================

def count_occurrences(text, term):
    return text.count(term) if text and term else 0


# ============================================
# Preview Snippet
# ============================================

def get_preview_snippet(path, query, window=120):
    if not path or not os.path.exists(path):
        return ""

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
    except:
        return ""

    content_lower = content.lower()
    query_lower = query.lower().strip()

    idx = content_lower.find(query_lower)
    match_length = len(query_lower)

    if idx == -1:
        terms = split_terms(query)
        for term in terms:
            idx = content_lower.find(term)
            if idx != -1:
                match_length = len(term)
                break

    if idx == -1:
        snippet = content[:240]
    else:
        start = max(0, idx - window)
        end = min(len(content), idx + match_length + window)
        snippet = content[start:end]

    snippet = snippet.replace("\n", " ")
    snippet = re.sub(r"\s+", " ", snippet)

    return snippet.strip()


# ============================================
# Query Parser
# ============================================

def parse_query(query):
    query = query.strip()

    exact_phrase = False
    or_mode = False

    if len(query) >= 2 and query.startswith('"') and query.endswith('"'):
        exact_phrase = True
        clean_query = query[1:-1].strip()
        terms = [normalize_text(clean_query)]

    elif "|" in query:
        or_mode = True
        terms = [normalize_text(p) for p in query.split("|") if normalize_text(p)]
        clean_query = " ".join(terms)

    else:
        clean_query = normalize_text(query)
        terms = split_terms(query)

    return {
        "clean_query": clean_query,
        "terms": terms,
        "exact_phrase": exact_phrase,
        "or_mode": or_mode,
    }


# ============================================
# Score Entry
# ============================================

def score_entry(entry, parsed_query):
    file_name = normalize_text(entry.get("file_name", ""))
    summary_path = entry.get("summary_path")
    text_path = entry.get("text_path")

    summary_content = normalize_text(read_file_safe(summary_path))
    text_content = normalize_text(read_file_safe(text_path))

    terms = parsed_query["terms"]
    clean_query = parsed_query["clean_query"]
    exact_phrase = parsed_query["exact_phrase"]
    or_mode = parsed_query["or_mode"]

    score = 0
    matched_terms = 0

    if exact_phrase:
        if clean_query in file_name:
            score += 20
            matched_terms += 1

        summary_hits = count_occurrences(summary_content, clean_query)
        text_hits = count_occurrences(text_content, clean_query)

        score += summary_hits * 10
        score += text_hits * 6

        if summary_hits or text_hits:
            matched_terms += 1

    else:
        for term in terms:
            term_matched = False

            if term in file_name:
                score += 8
                term_matched = True

            summary_hits = count_occurrences(summary_content, term)
            text_hits = count_occurrences(text_content, term)

            if summary_hits:
                score += summary_hits * 5
                term_matched = True

            if text_hits:
                score += text_hits * 2
                term_matched = True

            if term_matched:
                matched_terms += 1

        if matched_terms > 1 and not or_mode:
            score += matched_terms * 4

        if clean_query and clean_query in text_content:
            score += 10

        if clean_query and clean_query in summary_content:
            score += 15

    return score, matched_terms


# ============================================
# Search Index
# ============================================

def search_index(index_path, query):
    index = load_index(index_path)
    parsed_query = parse_query(query)

    results = []

    for entry in index:
        score, matched_terms = score_entry(entry, parsed_query)

        if score <= 0:
            continue

        text_path = entry.get("text_path")

        snippet = get_preview_snippet(text_path, parsed_query["clean_query"])
        snippet = highlight_terms(snippet, query)

        results.append({
            "file_name": entry.get("file_name"),
            "text_path": text_path,
            "score": score,
            "matched_terms": matched_terms,
            "preview": snippet,
        })

    results.sort(
        key=lambda x: (x["score"], x["matched_terms"]),
        reverse=True
    )

    return results