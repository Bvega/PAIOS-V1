# scripts/indexer.py
# ============================================
# PAIOS Index Builder (FIXED SUMMARY LINK)
# ============================================

import os
import json


def build_index(processed_path, index_path):
    index = []

    # Ensure summary directory exists
    summary_dir = "memory/summaries"

    for file in os.listdir(processed_path):
        if not file.endswith(".txt"):
            continue

        base_name = os.path.splitext(file)[0]

        text_path = os.path.join(processed_path, file)

        # FIX: Proper summary path mapping
        summary_file = f"{base_name}_summary.txt"
        summary_path = os.path.join(summary_dir, summary_file)

        entry = {
            "file_name": file,
            "text_path": text_path,
            "summary_path": summary_path if os.path.exists(summary_path) else None
        }

        index.append(entry)

    # Save index
    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    return index


def update_index():
    processed_path = "memory/processed"
    index_path = "memory/index/index.json"
    return build_index(processed_path, index_path)