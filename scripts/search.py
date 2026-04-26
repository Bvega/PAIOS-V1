# scripts/search.py
# ============================================
# PAIOS Search Engine
# ============================================
# Features:
# - Normal multi-term search
# - OR search using |
# - Exact phrase search using quotes
# - Filename, summary, and text scoring
# - Highlighted preview snippets
# - Explainable relevance reasons

import json
import os
import re


def load_index(index_path):
    """
    Load index.json safely.
    """
    if not os.path.exists(index_path):
        return []

    with open(index_path, "r", encoding="utf-8") as file:
        return json.load(file)


def read_file_safe(path):
    """
    Safely read file content as lowercase text.
    """
    if not path or not os.path.exists(path):
        return ""

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            return file.read().lower()
    except Exception:
        return ""


def normalize_text(text):
    """
    Normalize text for matching.
    Keeps letters, numbers, accents, underscores, hyphens, and spaces.
    """
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^a-z0-9áéíóúñü\s_-]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def parse_query(query):
    """
    Parse query into mode and terms.

    Supported:
    - Exact phrase: "xampp setup"
    - OR search: api | song
    - Normal search: api project
    """
    raw_query = query.strip()
    normalized_query = normalize_text(raw_query)

    exact_phrase = False
    or_mode = False

    if raw_query.startswith('"') and raw_query.endswith('"') and len(raw_query) > 2:
        exact_phrase = True
        phrase = normalize_text(raw_query[1:-1])
        terms = [phrase]

    elif "|" in raw_query:
        or_mode = True
        terms = [
            normalize_text(part)
            for part in raw_query.split("|")
            if normalize_text(part)
        ]
        phrase = " ".join(terms)

    else:
        terms = [
            term
            for term in normalized_query.split()
            if term
        ]
        phrase = normalized_query

    return {
        "raw_query": raw_query,
        "phrase": phrase,
        "terms": terms,
        "exact_phrase": exact_phrase,
        "or_mode": or_mode,
    }


def count_occurrences(text, term):
    """
    Count term occurrences.
    """
    if not text or not term:
        return 0

    return text.count(term)


def highlight_terms(snippet, terms):
    """
    Highlight matched terms in preview using markdown-style **term**.
    """
    if not snippet:
        return ""

    for term in terms:
        if not term:
            continue

        pattern = re.compile(re.escape(term), re.IGNORECASE)
        snippet = pattern.sub(lambda match: f"**{match.group(0)}**", snippet)

    return snippet


def get_preview_snippet(path, parsed_query, window=120):
    """
    Return a preview snippet around the first relevant match.
    """
    if not path or not os.path.exists(path):
        return ""

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
    except Exception:
        return ""

    content_lower = content.lower()
    search_targets = []

    if parsed_query["exact_phrase"]:
        search_targets.append(parsed_query["phrase"])
    else:
        search_targets.extend(parsed_query["terms"])

    match_index = -1
    match_length = 0

    for target in search_targets:
        idx = content_lower.find(target.lower())
        if idx != -1:
            match_index = idx
            match_length = len(target)
            break

    if match_index == -1:
        snippet = content[:240]
    else:
        start = max(0, match_index - window)
        end = min(len(content), match_index + match_length + window)
        snippet = content[start:end]

    snippet = snippet.replace("\n", " ")
    snippet = re.sub(r"\s+", " ", snippet).strip()

    return highlight_terms(snippet, parsed_query["terms"])


def score_exact_phrase(file_name, summary_content, text_content, phrase):
    """
    Score exact phrase searches.
    """
    score = 0
    reasons = []

    if phrase in file_name:
        score += 25
        reasons.append(f"exact phrase in filename: '{phrase}' (+25)")

    summary_hits = count_occurrences(summary_content, phrase)
    if summary_hits:
        value = summary_hits * 12
        score += value
        reasons.append(f"exact phrase in summary: '{phrase}' x{summary_hits} (+{value})")

    text_hits = count_occurrences(text_content, phrase)
    if text_hits:
        value = text_hits * 6
        score += value
        reasons.append(f"exact phrase in text: '{phrase}' x{text_hits} (+{value})")

    return score, reasons


def score_terms(file_name, summary_content, text_content, parsed_query):
    """
    Score normal and OR searches.
    """
    score = 0
    reasons = []
    matched_terms = 0

    for term in parsed_query["terms"]:
        term_matched = False

        if term in file_name:
            score += 8
            reasons.append(f"filename match: '{term}' (+8)")
            term_matched = True

        summary_hits = count_occurrences(summary_content, term)
        if summary_hits:
            value = summary_hits * 6
            score += value
            reasons.append(f"summary match: '{term}' x{summary_hits} (+{value})")
            term_matched = True

        text_hits = count_occurrences(text_content, term)
        if text_hits:
            value = text_hits * 2
            score += value
            reasons.append(f"text match: '{term}' x{text_hits} (+{value})")
            term_matched = True

        if term_matched:
            matched_terms += 1

    # Normal mode bonus: rewards documents matching multiple query terms.
    # OR mode does not receive this bonus because OR is intentionally broad.
    if matched_terms > 1 and not parsed_query["or_mode"]:
        value = matched_terms * 4
        score += value
        reasons.append(f"multi-term bonus (+{value})")

    # Phrase boost for normal mode only.
    phrase = parsed_query["phrase"]

    if phrase and not parsed_query["or_mode"]:
        if phrase in summary_content:
            score += 15
            reasons.append("phrase boost in summary (+15)")

        if phrase in text_content:
            score += 10
            reasons.append("phrase boost in text (+10)")

    return score, reasons, matched_terms


def search_index(index_path, query):
    """
    Search index and return ranked results.
    """
    index = load_index(index_path)
    parsed_query = parse_query(query)

    results = []

    for entry in index:
        file_name = normalize_text(entry.get("file_name", ""))
        text_path = entry.get("text_path")
        summary_path = entry.get("summary_path")

        text_content = normalize_text(read_file_safe(text_path))
        summary_content = normalize_text(read_file_safe(summary_path))

        if parsed_query["exact_phrase"]:
            score, reasons = score_exact_phrase(
                file_name,
                summary_content,
                text_content,
                parsed_query["phrase"],
            )
            matched_terms = 1 if score > 0 else 0
        else:
            score, reasons, matched_terms = score_terms(
                file_name,
                summary_content,
                text_content,
                parsed_query,
            )

        if score <= 0:
            continue

        preview = get_preview_snippet(text_path, parsed_query)

        results.append({
            "file_name": entry.get("file_name"),
            "text_path": text_path,
            "summary_path": summary_path,
            "score": score,
            "matched_terms": matched_terms,
            "preview": preview,
            "reasons": reasons,
            "mode": (
                "exact_phrase"
                if parsed_query["exact_phrase"]
                else "or"
                if parsed_query["or_mode"]
                else "normal"
            ),
        })

    results.sort(
        key=lambda item: (item["score"], item["matched_terms"]),
        reverse=True,
    )

    return results