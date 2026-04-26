# test_query.py
# ============================================
# PAIOS Search Test Script
# ============================================
# Purpose:
# - Validate that the index has searchable content.
# - Run several simple test queries against memory/index/index.json.
# - Print clear results for debugging.
#
# Usage:
# python3 test_query.py

import json
import os


# ============================================
# Configuration
# ============================================

INDEX_PATH = "memory/index/index.json"

TEST_QUERIES = [
    "ideas",
    "project",
    "setup",
    "guide",
    "song",
]


# ============================================
# Load Index
# ============================================

def load_index():
    """
    Load the current PAIOS search index.
    """
    if not os.path.exists(INDEX_PATH):
        print(f"Index not found: {INDEX_PATH}")
        return []

    with open(INDEX_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================
# Score Result
# ============================================

def score_entry(entry, query):
    """
    Simple keyword score.

    Checks:
    - file name
    - preview content if present
    - text path content if available
    """
    query = query.lower()
    score = 0

    file_name = str(entry.get("file_name", "")).lower()
    preview = str(entry.get("preview", "")).lower()

    if query in file_name:
        score += 10

    if query in preview:
        score += 5

    text_path = entry.get("text_path")

    if text_path and os.path.exists(text_path):
        try:
            with open(text_path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read().lower()

            if query in content:
                score += content.count(query)

        except Exception:
            pass

    return score


# ============================================
# Search Index
# ============================================

def search_index(index, query):
    """
    Search index entries and return sorted matches.
    """
    results = []

    for entry in index:
        score = score_entry(entry, query)

        if score > 0:
            results.append(
                {
                    "file_name": entry.get("file_name"),
                    "score": score,
                    "preview": entry.get("preview", ""),
                    "text_path": entry.get("text_path"),
                }
            )

    results.sort(key=lambda item: item["score"], reverse=True)

    return results


# ============================================
# Print Results
# ============================================

def print_results(query, results):
    """
    Print query results in a readable format.
    """
    print("=" * 60)
    print(f"Query: {query}")
    print("=" * 60)

    if not results:
        print("No matches found.\n")
        return

    for index, result in enumerate(results[:5], 1):
        print(f"[{index}] {result.get('file_name')} (score: {result.get('score')})")

        preview = result.get("preview") or ""

        if preview:
            print(f"Preview: {preview[:200]}")

        print(f"Path: {result.get('text_path')}")
        print("-" * 60)

    print()


# ============================================
# Main
# ============================================

def main():
    """
    Run test queries against the current index.
    """
    index = load_index()

    print(f"Loaded index entries: {len(index)}\n")

    if not index:
        print("Index is empty. Run:")
        print("python3 start_pipeline.py inbox/sample --clean")
        return

    for query in TEST_QUERIES:
        results = search_index(index, query)
        print_results(query, results)


if __name__ == "__main__":
    main()