# =========================
# PAIOS CLI (Smart Aggregation v2)
# =========================
# New in Day 49:
# - Deduplication
# - Line compression
# - Cleaner combined summaries

from scripts.core import run_query_core, extract_top_result, open_result

INDEX_PATH = "memory/index/index.json"


# =========================
# HELP
# =========================

def show_help():
    print("""
PAIOS Natural Language Examples:

find termination
top termination
open termination

help
exit
""")


# =========================
# PARSER
# =========================

def parse_input(user_input):
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
    if len(query.split()) >= 2:
        return "summary"
    return None


# =========================
# OUTPUT
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
# INSIGHTS
# =========================

def generate_insights(results):
    if not results:
        return

    print("\n=== INSIGHTS ===")
    print(f"- Found in {len(results)} document(s)")

    previews = [r.get("preview", "") for r in results]

    keywords = ["terminate", "termination", "liability", "payment"]
    found = set()

    for text in previews:
        for word in keywords:
            if word in text.lower():
                found.add(word)

    if found:
        print(f"- Common terms: {', '.join(found)}")

    print()


# =========================
# NEW: SMART MERGING
# =========================

def clean_and_merge(lines):
    """
    Deduplicate and clean summary lines.
    """
    seen = set()
    cleaned = []

    for line in lines:
        line = line.strip()

        # skip empty lines
        if not line:
            continue

        # normalize for dedup
        key = line.lower()

        if key not in seen:
            seen.add(key)
            cleaned.append(line)

    return cleaned


def generate_combined_summary(results):
    """
    Smart merged summary:
    - loads summaries
    - splits into lines
    - deduplicates
    """

    if not results:
        return

    print("\n=== COMBINED SUMMARY ===")

    all_lines = []

    for r in results:
        summary_path = r.get("summary_path")

        if summary_path:
            try:
                with open(summary_path, "r") as f:
                    content = f.read()
                    lines = content.split("\n")
                    all_lines.extend(lines)
            except:
                continue

    merged = clean_and_merge(all_lines)

    if merged:
        for line in merged:
            print(f"- {line}")
    else:
        print("No summary data available.")

    print()


# =========================
# MAIN
# =========================

def main():
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
            continue

        intent, query = parse_input(user_input)

        if not query:
            print("Missing query.\n")
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