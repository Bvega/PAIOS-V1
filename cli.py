# =========================
# PAIOS CLI (Natural Language Mode + Help)
# =========================
# User can type natural phrases like:
# - find test summary
# - top test summary
# - open test summary
# The CLI detects intent automatically and explains usage.

from scripts.core import run_query_core, extract_top_result, open_result

INDEX_PATH = "memory/index/index.json"


# =========================
# HELP TEXT
# =========================

def show_help():
    """
    Show examples so users know what to ask.
    """
    print("""
PAIOS Natural Language Examples:

Search:
  find test
  find test summary
  search contracts termination

Top result:
  top test
  top test summary
  best contracts termination

Open result:
  open test
  open test summary
  open contracts termination

Other:
  help
  exit
""")


# =========================
# INTENT PARSER
# =========================

def parse_input(user_input):
    """
    Detect user intent from simple natural language.

    Supported intents:
    - search
    - top
    - open
    """
    text = user_input.lower().strip()

    if text.startswith(("open", "show", "read")):
        intent = "open"
    elif text.startswith(("top", "best")):
        intent = "top"
    else:
        intent = "search"

    # Remove command-like words to leave only query terms.
    remove_words = [
        "open", "show", "read",
        "top", "best",
        "find", "search",
        "about", "for",
        "result", "results",
    ]

    query = text
    for word in remove_words:
        query = query.replace(word, "")

    query = " ".join(query.split())

    return intent, query


def auto_refine(query):
    """
    Automatically refine longer queries.

    If query has two or more words, add 'summary'
    as a simple refinement heuristic.
    """
    if len(query.split()) >= 2:
        return "summary"
    return None


# =========================
# OUTPUT HELPERS
# =========================

def print_results(results):
    """
    Print search results.
    """
    if not results:
        print("\nNo results found.\n")
        return

    for i, result in enumerate(results, 1):
        print(f"\n[{i}] {result.get('file_name')} (score: {result.get('score')})")
        print(result.get("preview"))
        print("-" * 40)


def print_top(result):
    """
    Print only the best result.
    """
    if not result:
        print("\nNo result found.\n")
        return

    print(f"\nTop: {result.get('file_name')} (score: {result.get('score')})")
    print(result.get("preview"))
    print("-" * 40)


def print_open(result):
    """
    Print opened result content.
    """
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
# MAIN LOOP
# =========================

def main():
    """
    Start natural-language CLI loop.
    """
    print("PAIOS Natural Language Mode")
    print("Type 'help' for examples. Type 'exit' to quit.\n")

    show_help()

    while True:
        user_input = input("PAIOS> ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("Exiting PAIOS.")
            break

        if user_input.lower() == "help":
            show_help()
            continue

        if not user_input:
            print("Type a request or 'help'.\n")
            continue

        intent, query = parse_input(user_input)

        if not query:
            print("I need a search topic. Type 'help' for examples.\n")
            continue

        refine = auto_refine(query)

        full_query, results = run_query_core(
            INDEX_PATH,
            query,
            refine=refine,
        )

        print(f"\nQuery: {full_query}")

        if intent == "search":
            print_results(results)

        elif intent == "top":
            top = extract_top_result(results)
            print_top(top)

        elif intent == "open":
            top = extract_top_result(results)
            opened = open_result(top, mode="full")
            print_open(opened)


if __name__ == "__main__":
    main()
    