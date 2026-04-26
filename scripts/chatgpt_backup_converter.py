# =========================
# ChatGPT Backup Converter (MAPPING FORMAT SUPPORT)
# =========================

import json
import os
import re
from datetime import datetime

OUTPUT_DIR = "inbox/chatgpt"


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def safe_filename(text):
    if not text:
        return "untitled_conversation"
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:80] or "untitled_conversation"


def format_timestamp(ts):
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Unknown"


def extract_text(content):
    if not content:
        return ""
    parts = content.get("parts", [])
    return "\n".join([p for p in parts if isinstance(p, str)]).strip()


def extract_messages(conv):
    """
    Extract messages from mapping structure.
    """
    mapping = conv.get("mapping", {})

    messages = []

    for node in mapping.values():
        msg = node.get("message")

        if not msg:
            continue

        role = msg.get("author", {}).get("role", "unknown").upper()
        content = msg.get("content", {})
        text = extract_text(content)

        if not text:
            continue

        messages.append((role, text))

    return messages


def convert_conversation(conv, index):
    title = conv.get("title", "Untitled")
    created = format_timestamp(conv.get("create_time"))
    updated = format_timestamp(conv.get("update_time"))

    messages = extract_messages(conv)

    filename = f"{index:03d}_{safe_filename(title)}.txt"
    path = os.path.join(OUTPUT_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\n")
        f.write(f"Created: {created}\n")
        f.write(f"Updated: {updated}\n")
        f.write("=" * 80 + "\n\n")

        for role, text in messages:
            f.write(f"{role}:\n{text}\n\n{'-'*80}\n\n")

    return path


def convert_backup(input_path):
    ensure_output_dir()

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("Unsupported format")
        return

    count = 0

    for i, conv in enumerate(data, 1):
        convert_conversation(conv, i)
        count += 1

    print(f"Converted {count} conversations")
    print(f"Output → {OUTPUT_DIR}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 scripts/chatgpt_backup_converter.py <path>")
    else:
        convert_backup(sys.argv[1])