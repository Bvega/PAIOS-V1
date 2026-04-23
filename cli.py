# =========================
# PAIOS CLI (Menu Mode)
# =========================
# This version removes command typing.
# User selects options → system asks inputs → executes using core.

from scripts.core import run_query_core, extract_top_result, open_result

# Path to index used by core engine
INDEX_PATH = "memory/index/index.json"


# =========================
# INPUT HELPERS
# =========================

def ask(prompt, optional=False):
    """
    Ask user for input.
    - If optional=True → empty input returns None
    - Otherwise returns string
    """
    value = input(prompt).strip()

    if not value and optional:
        return None

    return value


def ask_int(prompt):
    """
    Ask for integer input safely.
    - Returns int if valid
    - Returns None if empty or invalid
    """
    value = input(prompt).strip()

    if not value:
        return None

    try:
        return int(value)
    except:
        print("Invalid number. Ignored.")
        return None


# =========================
# PRINT HELPERS
# =========================

def print_results(results):
    """
    Display multiple search results.
    """
    if not results:
        print("\nNo results found.\n")
        return

    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r.get('file_name')} (score: {r.get('score')})")
        print(r.get("preview"))
        print("-" * 40)


def print_top(result):
    """
    Display best (top) result.
    """
    if not result:
        print("\nNo result found.\n")
        return

    print(f"\nTop: {result.get('file_name')} (score: {result.get('score')})")
    print(result.get("preview"))
    print("-" * 40)


def print_open(result):
    """
    Display opened result content depending on mode.
    """
    if not result:
        print("\nNo result found.\n")
        return

    print(f"\nFile: {result.get('file')}")
    print(f"Score: {result.get('score')}\n")

    # Show summary if available
    if "summary" in result:
        print("=== SUMMARY ===")
        print(result["summary"])
        print()

    # Show full content if available
    if "content" in result:
        print("=== CONTENT ===")
        print(result["content"])
        print()


# =========================
# ACTIONS (CORE OPERATIONS)
# =========================

def action_search():
    """
    Search multiple results.
    """
    q = ask("Query: ")
    refine = ask("Refine (optional): ", optional=True)
    limit = ask_int("Limit (optional): ")
    min_score = ask_int("Min score (optional): ")

    # Use shared core logic
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
    """
    Get best result only.
    """
    q = ask("Query: ")
    refine = ask("Refine (optional): ", optional=True)

    full_query, results = run_query_core(INDEX_PATH, q, refine=refine)
    top = extract_top_result(results)

    print(f"\nQuery: {full_query}")
    print_top(top)


def action_open():
    """
    Open best result with selected mode.
    """
    q = ask("Query: ")
    refine = ask("Refine (optional): ", optional=True)
    mode = ask("Mode (full/summary/raw): ", optional=True) or "full"

    full_query, results = run_query_core(INDEX_PATH, q, refine=refine)
    top = extract_top_result(results)

    # Use shared open logic
    opened = open_result(top, mode=mode)

    print(f"\nQuery: {full_query}")
    print_open(opened)


# =========================
# MENU LOOP
# =========================

def main():
    """
    Main loop:
    - shows menu
    - executes selected action
    """
    print("PAIOS Menu Mode\n")

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


# Entry point
if __name__ == "__main__":
    main()