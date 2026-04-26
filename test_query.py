# test_query.py
# ============================================
# PAIOS Search Test Script
# ============================================
# Purpose:
# - Test the current search index.
# - Print ranked search results.
# - Show preview snippets.
# - Show relevance reasons for each result.
#
# Usage:
# python3 test_query.py

import os
from scripts.search import search_index


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
# Result Printer
# ============================================

def print_results(query, results):
    """
    Print search results in a readable debug format.
    """
    print("=" * 60)
    print(f"Query: {query}")
    print("=" * 60)

    if not results:
        print("No matches found.\n")
        return

    for index, result in enumerate(results[:5], 1):
        file_name = result.get("file_name", "Unknown file")
        score = result.get("score", 0)
        path = result.get("text_path", "")
        preview = result.get("preview", "")
        reasons = result.get("reasons", [])

        print(f"[{index}] {file_name} (score: {score})")
        print(f"Path: {path}")

        if reasons:
            print("Reasons:")
            for reason in reasons:
                print(f"- {reason}")

        if preview:
            print(f"Preview: {preview[:300]}")

        print("-" * 60)

    print()


# ============================================
# Main
# ============================================

def main():
    """
    Run all test queries against the indexed sample data.
    """
    if not os.path.exists(INDEX_PATH):
        print("Index not found.")
        print("Run this first:")
        print("python3 start_pipeline.py inbox/sample --clean")
        return

    print("PAIOS Search Quality Test")
    print(f"Index path: {INDEX_PATH}\n")

    for query in TEST_QUERIES:
        results = search_index(INDEX_PATH, query)
        print_results(query, results)


if __name__ == "__main__":
    main()