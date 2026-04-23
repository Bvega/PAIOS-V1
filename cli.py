# =========================
# PAIOS CLI (Interactive Mode)
# =========================

from scripts.core import run_query_core, extract_top_result, open_result

INDEX_PATH = "memory/index/index.json"


# =========================
# PRINT HELPERS
# =========================

def print_results(results):
    if not results:
        print("No results found.\n")
        return

    for i, r in enumerate(results, 1):
        print(f"[{i}] {r.get('file_name')} (score: {r.get('score')})")
        print(r.get("preview"))
        print("-" * 40)


def print_top(result):
    if not result:
        print("No result found.\n")
        return

    print(f"Top: {result.get('file_name')} (score: {result.get('score')})")
    print(result.get("preview"))
    print("-" * 40)


def print_open(result):
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


# =========================
# COMMAND HANDLER
# =========================

def handle_command(line):
    """
    Parse and execute user command.
    """
    parts = line.strip().split()

    if not parts:
        return

    command = parts[0]
    args = parts[1:]

    params = {
        "q": None,
        "refine": None,
        "limit": None,
        "min_score": None,
        "mode": "full",
    }

    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            params[key] = value
        else:
            params["q"] = arg

    q = params.get("q")
    refine = params.get("refine")
    limit = params.get("limit")
    min_score = params.get("min_score")
    mode = params.get("mode")

    if limit:
        limit = int(limit)

    if min_score:
        min_score = int(min_score)

    if command == "help":
        print("""
Commands:
  search <q> refine=... limit=... min_score=...
  top <q> refine=...
  open <q> refine=... mode=full|summary|raw
  exit
""")
        return

    if command == "exit":
        print("Exiting PAIOS.")
        exit()

    if not q:
        print("Missing query.\n")
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
        print(f"\nQuery: {full_query}\n")
        print_results(results)
        return

    # =========================
    # TOP
    # =========================
    if command == "top":
        full_query, results = run_query_core(INDEX_PATH, q, refine=refine)
        top = extract_top_result(results)
        print(f"\nQuery: {full_query}\n")
        print_top(top)
        return

    # =========================
    # OPEN
    # =========================
    if command == "open":
        full_query, results = run_query_core(INDEX_PATH, q, refine=refine)
        top = extract_top_result(results)
        opened = open_result(top, mode=mode)
        print(f"\nQuery: {full_query}\n")
        print_open(opened)
        return

    print("Unknown command. Type 'help'.")


# =========================
# INTERACTIVE LOOP
# =========================

def main():
    print("PAIOS Interactive Mode")
    print("Type 'help' for commands.\n")

    while True:
        try:
            line = input("PAIOS> ")
            handle_command(line)
        except KeyboardInterrupt:
            print("\nExiting PAIOS.")
            break


if __name__ == "__main__":
    main()