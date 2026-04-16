import os
import json


def build_index(processed_path, index_path):
    index = []

    for file in os.listdir(processed_path):
        if file.endswith(".txt"):
            base_name = os.path.splitext(file)[0]

            txt_path = os.path.join(processed_path, file)
            meta_path = os.path.join(processed_path, base_name + ".meta.json")
            summary_path = os.path.join("memory/summaries", base_name + ".summary.txt")

            entry = {
                "file_name": file,
                "text_path": txt_path,
                "metadata_path": meta_path if os.path.exists(meta_path) else None,
                "summary_path": summary_path if os.path.exists(summary_path) else None
            }

            index.append(entry)

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    return index


def update_index():
    processed_path = "memory/processed"
    index_path = "memory/index/index.json"
    return build_index(processed_path, index_path)