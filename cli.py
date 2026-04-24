# =========================
# PAIOS CLI (Semantic Grouping v1)
# =========================
# Day 50 adds:
# - grouped combined summaries
# - basic semantic categories
# - cleaner knowledge synthesis
#
# This is still rule-based, not LLM-based.
# It groups meaning by detected topic words.

from scripts.core import run_query_core, extract_top_result, open_result

INDEX_PATH = "memory/index/index.json"


# =========================
# HELP
# =========================

def show_help():
    """
    Show natural-language examples.
    """
    print("""
PAIOS Natural Language Examples:

find termination
find liability
find payment terms

top termination
open termination

help
exit
""")


# =========================
# PARSER
# =========================

def parse_input(user_input):
    """
    Convert natural language into:
    - intent: search / top / open
    - query: cleaned search text
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
    ]

    query = text
    for word in remove_words:
        query = query.replace(word, "")

    return intent, " ".join(query.split())


def auto_refine(query):
    """
    Add summary refinement for multi-word queries.
    """
    if len(query.split()) >= 2:
        return "summary"
    return None


# =========================
# OUTPUT HELPERS
# =========================

def print_results(results):
    """
    Print raw ranked search results.
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
    Print only the highest-ranked result.
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
# INSIGHTS
# =========================

def generate_insights(results):
    """
    Generate simple search-level insights.
    """
    if not results:
        return

    print("\n=== INSIGHTS ===")
    print(f"- Found in {len(results)} document(s)")

    previews = [result.get("preview", "") for result in results]

    keywords = ["terminate", "termination", "liability", "payment"]
    found = set()

    for text in previews:
        for word in keywords:
            if word in text.lower():
                found.add(word)

    if found:
        print(f"- Common terms: {', '.join(sorted(found))}")

    print()


# =========================
# SEMANTIC GROUPING
# =========================

def classify_line(line):
    """
    Classify one summary line into a basic meaning group.

    Current groups:
    - Termination
    - Liability
    - Payment
    - General

    This keeps the system simple and transparent.
    """
    lower_line = line.lower()

    if "terminate" in lower_line or "termination" in lower_line:
        return "Termination"

    if "liability" in lower_line or "responsible" in lower_line or "damages" in lower_line:
        return "Liability"

    if "payment" in lower_line or "paid" in lower_line or "received" in lower_line:
        return "Payment"

    return "General"


def clean_summary_lines(results):
    """
    Load summary files, split them into lines, and remove duplicates.
    """
    seen = set()
    cleaned_lines = []

    for result in results:
        summary_path = result.get("summary_path")

        if not summary_path:
            continue

        try:
            with open(summary_path, "r", encoding="utf-8") as file:
                content = file.read()
        except Exception:
            continue

        for line in content.split("\n"):
            line = line.strip()

            if not line:
                continue

            key = line.lower()

            if key not in seen:
                seen.add(key)
                cleaned_lines.append(line)

    return cleaned_lines


def group_summary_lines(lines):
    """
    Group cleaned summary lines into semantic buckets.
    """
    groups = {
        "Termination": [],
        "Liability": [],
        "Payment": [],
        "General": [],
    }

    for line in lines:
        category = classify_line(line)
        groups[category].append(line)

    return groups


def generate_combined_summary(results):
    """
    Generate grouped combined summary from matching documents.

    This is the Day 50 upgrade:
    instead of one flat list, results are grouped by meaning.
    """
    if not results:
        return

    print("\n=== GROUPED SUMMARY ===")

    lines = clean_summary_lines(results)

    if not lines:
        print("No summary data available.\n")
        return

    groups = group_summary_lines(lines)

    for category, items in groups.items():
        if not items:
            continue

        print(f"\n[{category}]")

        for item in items:
            print(f"- {item}")

    print()


# =========================
# MAIN LOOP
# =========================

def main():
    """
    Run the natural-language CLI loop.
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
            print("Type something or 'help'.\n")
            continue

        intent, query = parse_input(user_input)

        if not query:
            print("Missing query.\n")
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
            generate_insights(results)
            generate_combined_summary(results)

        elif intent == "top":
            top = extract_top_result(results)
            print_top(top)

        elif intent == "open":
            top = extract_top_result(results)
            opened = open_result(top, mode="full")
            print_open(opened)


if __name__ == "__main__":
    main()