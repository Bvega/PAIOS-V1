# =========================
# PAIOS CLI (Smart Mode)
# =========================
# Adds:
# - presets (day 43)
# - smart refine auto-selection (day 44)

from scripts.core import run_query_core, extract_top_result, open_result

INDEX_PATH = "memory/index/index.json"

# =========================
# MEMORY (PRESETS)
# =========================
last_refine = None
last_limit = None
last_min_score = None


# =========================
# SMART LOGIC
# =========================

def auto_refine(query, refine):
    """
    Smart behavior:
    - If refine provided → use it
    - If not:
        short query → None
        long query → "summary"
    """
    if refine:
        return refine

    # simple heuristic
    if len(query.split()) >= 2:
        return "summary"

    return None


# =========================
# INPUT HELPERS
# =========================

def ask(prompt, optional=False, default=None):
    if default:
        value = input(f"{prompt} [{default}]: ").strip()
    else:
        value = input(prompt).strip()

    if not value:
        return default if optional else value

    return value


def ask_int(prompt, default=None):
    if default is not None:
        value = input(f"{prompt} [{default}]: ").strip()
    else:
        value = input(prompt).strip()

    if not value:
        return default

    try:
        return int(value)
    except:
        print("Invalid number. Using default.")
        return default


# =========================
# PRINT HELPERS
# =========================

def print_results(results):
    if not results:
        print("\nNo results found.\n")
        return

    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r.get('file_name')} (score: {r.get('score')})")
        print(r.get("preview"))
        print("-" * 40)


def print_top(result):
    if not result:
        print("\nNo result found.\n")
        return

    print(f"\nTop: {result.get('file_name')} (score: {result.get('score')})")
    print(result.get("preview"))
    print("-" * 40)


def print_open(result):
    if not result:
        print("\nNo result found.\n")
        return

    print(f"\nFile: {result.get('file')}")
    print(f"Score: {result.get('score')}\n")

    if "summary" in result:
        print("=== SUMMARY ===")
        print(result["summary"])
        print()

    if "content" in result:
        print("=== CONTENT ===")
        print(result["content"])
        print()


# =========================
# ACTIONS
# =========================

def action_search():
    global last_refine, last_limit, last_min_score

    q = ask("Query: ")

    refine_input = ask("Refine (optional): ", optional=True, default=last_refine)
    refine = auto_refine(q, refine_input)

    limit = ask_int("Limit (optional): ", default=last_limit)
    min_score = ask_int("Min score (optional): ", default=last_min_score)

    last_refine = refine
    last_limit = limit
    last_min_score = min_score

    full_query, results = run_query_core(
        INDEX_PATH,
        q,
        refine=refine,
        limit=limit,
        min_score=min_score,
    )

    print(f"\nQuery: {full_query}")
    print_results(results)


def action_top():
    global last_refine

    q = ask("Query: ")
    refine_input = ask("Refine (optional): ", optional=True, default=last_refine)
    refine = auto_refine(q, refine_input)

    last_refine = refine

    full_query, results = run_query_core(INDEX_PATH, q, refine=refine)
    top = extract_top_result(results)

    print(f"\nQuery: {full_query}")
    print_top(top)


def action_open():
    global last_refine

    q = ask("Query: ")
    refine_input = ask("Refine (optional): ", optional=True, default=last_refine)
    refine = auto_refine(q, refine_input)

    mode = ask("Mode (full/summary/raw): ", optional=True, default="full")

    last_refine = refine

    full_query, results = run_query_core(INDEX_PATH, q, refine=refine)
    top = extract_top_result(results)

    opened = open_result(top, mode=mode)

    print(f"\nQuery: {full_query}")
    print_open(opened)


# =========================
# MENU
# =========================

def main():
    print("PAIOS Smart Mode\n")

    while True:
        print("""
1. Search
2. Top Result
3. Open Result
4. Exit
""")

        choice = input("Select option: ").strip()

        if choice == "1":
            action_search()
        elif choice == "2":
            action_top()
        elif choice == "3":
            action_open()
        elif choice == "4":
            print("Exiting PAIOS.")
            break
        else:
            print("Invalid option.\n")


if __name__ == "__main__":
    main()