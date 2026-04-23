# =========================
# PAIOS CLI (Core-aligned)
# =========================

import sys
from scripts.core import run_query_core, extract_top_result, open_result

INDEX_PATH = "memory/index/index.json"


def print_results(results):
    """
    Print search results in CLI format.
    """
    if not results:
        print("No results found.\n")
        return

    for i, r in enumerate(results, 1):
        print(f"[{i}] {r.get('file_name')} (score: {r.get('score')})")
        print(r.get("preview"))
        print("-" * 40)


def print_top(result):
    """
    Print top result preview.
    """
    if not result:
        print("No result found.\n")
        return

    print(f"Top: {result.get('file_name')} (score: {result.get('score')})")
    print(result.get("preview"))
    print("-" * 40)


def print_open(result):
    """
    Print opened result content.
    """
    if not result:
        print("No result found.\n")
        return

    print(f"File: {result.get('file')}")
    print(f"Score: {result.get('score')}")
    print()

    if "summary" in result:
        print("=== SUMMARY ===")
        print(result["summary"])
        print()

    if "content" in result:
        print("=== CONTENT ===")
        print(result["content"])
        print()


def parse_args(args):
    """
    Parse CLI arguments.
    Supported:
    - search q refine= limit= min_score=
    - top q refine=
    - open q refine= mode=
    """

    if len(args) < 2:
        return None, {}

    command = args[1]
    params = {
        "q": None,
        "refine": None,
        "limit": None,
        "min_score": None,
        "mode": "full",
    }

    for arg in args[2:]:
        if "=" in arg:
            key, value = arg.split("=", 1)
            params[key] = value
        else:
            params["q"] = arg

    return command, params


def main():
    command, params = parse_args(sys.argv)

    if not command:
        print("Usage:")
        print("  search <q> refine=... limit=... min_score=...")
        print("  top <q> refine=...")
        print("  open <q> refine=... mode=full|summary|raw")
        return

    q = params.get("q")
    refine = params.get("refine")
    limit = params.get("limit")
    min_score = params.get("min_score")
    mode = params.get("mode")

    # Convert numeric params
    if limit:
        limit = int(limit)

    if min_score:
        min_score = int(min_score)

    if not q:
        print("Missing query.")
        return

    # =========================
    # SEARCH
    # =========================
    if command == "search":
        full_query, results = run_query_core(
            INDEX_PATH,
            q,
            refine=refine,
            limit=limit,
            min_score=min_score,
        )
        print(f"Query: {full_query}\n")
        print_results(results)
        return

    # =========================
    # TOP
    # =========================
    if command == "top":
        full_query, results = run_query_core(INDEX_PATH, q, refine=refine)
        top = extract_top_result(results)
        print(f"Query: {full_query}\n")
        print_top(top)
        return

    # =========================
    # OPEN
    # =========================
    if command == "open":
        full_query, results = run_query_core(INDEX_PATH, q, refine=refine)
        top = extract_top_result(results)
        opened = open_result(top, mode=mode)
        print(f"Query: {full_query}\n")
        print_open(opened)
        return

    print("Unknown command.")


if __name__ == "__main__":
    main()