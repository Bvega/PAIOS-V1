# =========================
# PAIOS CLI (Answer Engine v1 + UX FIX)
# =========================
# FIX:
# - Restores help + usability
# - Keeps narrative answer
# - Adds optional debug view (results if needed)

from scripts.core import run_query_core, extract_top_result, open_result

INDEX_PATH = "memory/index/index.json"


# =========================
# HELP
# =========================

def show_help():
    """
    Show examples so user knows what to type.
    """
    print("""
PAIOS Examples:

Search:
  find termination
  find payment terms

Top:
  top termination

Open:
  open termination

Other:
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
# SEMANTIC LOGIC
# =========================

def classify_line(line):
    l = line.lower()

    if "terminate" in l or "termination" in l:
        return "Termination"

    if "liability" in l or "damages" in l:
        return "Liability"

    if "payment" in l:
        return "Payment"

    return "General"


def clean_lines(results):
    seen = set()
    lines = []

    for r in results:
        path = r.get("summary_path")

        if not path:
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f.read().split("\n"):
                    line = line.strip()

                    if not line:
                        continue

                    key = line.lower()

                    if key not in seen:
                        seen.add(key)
                        lines.append(line)
        except:
            continue

    return lines


def group_lines(lines):
    groups = {
        "Termination": [],
        "Liability": [],
        "Payment": [],
        "General": []
    }

    for line in lines:
        groups[classify_line(line)].append(line)

    return groups


def compress_group(lines, category):
    text = " ".join(lines).lower()

    if category == "Termination":
        if "30 days" in text:
            return "may be terminated with 30 days written notice"
        return "include termination conditions"

    if category == "Liability":
        return "define liability limitations"

    if category == "Payment":
        if "14 days" in text:
            return "require payment 14 days in advance"
        return "include payment terms"

    if category == "General":
        return "include general agreement provisions"

    return None


# =========================
# ANSWER ENGINE
# =========================

def generate_narrative_answer(results):
    if not results:
        print("\nNo answer available.\n")
        return

    lines = clean_lines(results)
    groups = group_lines(lines)

    pieces = []

    for category, items in groups.items():
        if not items:
            continue

        compressed = compress_group(items, category)

        if compressed:
            pieces.append(compressed)

    if not pieces:
        print("\nNo meaningful answer.\n")
        return

    answer = "Contracts typically " + ", and ".join(pieces) + "."

    print("\n=== ANSWER ===")
    print(answer)
    print()


# =========================
# OPTIONAL DEBUG VIEW
# =========================

def print_results(results):
    """
    Optional: still available for debugging or transparency
    """
    if not results:
        return

    print("\n--- Sources ---")
    for r in results:
        print(f"{r.get('file_name')} (score: {r.get('score')})")


# =========================
# MAIN
# =========================

def main():
    print("PAIOS Answer Engine v1")
    print("Type 'help' for examples.\n")

    show_help()

    while True:
        try:
            user_input = input("PAIOS> ").strip()
        except KeyboardInterrupt:
            print("\nExiting.")
            break

        if user_input.lower() in ["exit", "quit"]:
            print("Exiting.")
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
            generate_narrative_answer(results)
            print_results(results)  # optional visibility

        elif intent == "top":
            top = extract_top_result(results)
            print(top)

        elif intent == "open":
            top = extract_top_result(results)
            print(open_result(top))


if __name__ == "__main__":
    main()