# =========================
# PAIOS CORE LOGIC
# =========================

from scripts.search import search_index
import os


def read_file(path):
    """
    Safely read file content.
    Returns None if file does not exist.
    """
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def build_query(base, refine):
    """
    Combine base query + refine terms.
    Example:
        base="test", refine="summary"
        → "test summary"
    """
    if not refine:
        return base
    return f"{base} {refine}".strip()


def run_query_core(index_path, q, refine=None, limit=None, min_score=None):
    """
    Shared query execution logic.

    Used by:
    - CLI
    - API

    Handles:
    - query building
    - filtering
    - limiting
    """

    # Build final query
    full_query = build_query(q, refine)

    # Run search
    results = search_index(index_path, full_query)

    # Filter by score
    if min_score is not None:
        results = [r for r in results if r.get("score", 0) >= min_score]

    # Apply limit
    if limit is not None:
        results = results[:limit]

    return full_query, results


def extract_top_result(results):
    """
    Return best result or None.
    """
    if not results:
        return None
    return results[0]


def open_result(result, mode="full"):
    """
    Extract summary/content based on mode.

    mode:
    - full → summary + content
    - summary → summary only
    - raw → content only
    """

    if not result:
        return None

    summary = read_file(result.get("summary_path"))
    content = read_file(result.get("text_path"))

    output = {
        "file": result.get("file_name"),
        "score": result.get("score"),
        "preview": result.get("preview"),
        "mode": mode,
    }

    if mode in ["full", "summary"]:
        output["summary"] = summary

    if mode in ["full", "raw"]:
        output["content"] = content

    return output