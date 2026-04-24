# =========================
# PAIOS CLI (Natural Language Mode + Help + Insights)
# =========================
# This version adds:
# - Natural language input
# - Help system
# - Smart refine
# - Cross-document insights (NEW)

from scripts.core import run_query_core, extract_top_result, open_result

INDEX_PATH = "memory/index/index.json"


# =========================
# HELP TEXT
# =========================

def show_help():
    """
    Display usage examples so user knows what to type.
    """
    print("""
PAIOS Natural Language Examples:

Search:
  find test
  find test summary
  search contracts termination

Top result:
  top test
  best contracts termination

Open result:
  open test
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
    Detect user intent from natural language.
    """
    text = user_input.lower().strip()

    if text.startswith(("open", "show", "read")):
        intent = "open"
    elif text.startswith(("top", "best")):
        intent = "top"
    else:
        intent = "search"

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
    Auto-add 'summary' when query has multiple words.
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
    Print best result.
    """
    if not result:
        print("\nNo result found.\n")
        return

    print(f"\nTop: {result.get('file_name')} (score: {result.get('score')})")
    print(result.get("preview"))
    print("-" * 40)


def print_open(result):
    """
    Print full result content.
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
# NEW: MULTI-DOCUMENT INSIGHTS
# =========================

def generate_insights(results):
    """
    Generate simple cross-document insights.

    Current behavior:
    - Counts documents
    - Detects repeated keywords across results

    This simulates early-stage "reasoning".
    """

    if not results:
        return

    print("\n=== INSIGHTS ===")

    # Count number of documents
    print(f"- Found in {len(results)} document(s)")

    # Extract preview text from each result
    previews = [r.get("preview", "") for r in results]

    # Simple keyword detection
    keywords = ["terminate", "termination", "liability", "payment"]

    found_keywords = set()

    for text in previews:
        for word in keywords:
            if word in text.lower():
                found_keywords.add(word)

    if found_keywords:
        print(f"- Common terms: {', '.join(found_keywords)}")

    print()


# =========================
# MAIN LOOP
# =========================

def main():
    """
    Main interactive loop.
    """
    print("PAIOS Natural Language Mode")
    print("Type 'help' for examples. Type 'exit' to quit.\n")

    show_help()

    while True:
        try:
            user_input = input("PAIOS> ").strip()
        except KeyboardInterrupt:
            print("\nExiting PAIOS.")
            break

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
            print("I need a search topic. Type 'help'.\n")
            continue

        refine = auto_refine(query)

        full_query, results = run_query_core(
            INDEX_PATH,
            query,
            refine=refine
        )

        print(f"\nQuery: {full_query}")

        if intent == "search":
            print_results(results)
            generate_insights(results)  # NEW HOOK

        elif intent == "top":
            top = extract_top_result(results)
            print_top(top)

        elif intent == "open":
            top = extract_top_result(results)
            opened = open_result(top, mode="full")
            print_open(opened)


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    main()