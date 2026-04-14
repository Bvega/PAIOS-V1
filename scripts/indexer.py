import os
import json


def build_index(processed_path, index_path):
    index = []

    for file in os.listdir(processed_path):
        if file.endswith(".txt"):
            base_name = os.path.splitext(file)[0]

            txt_path = os.path.join(processed_path, file)
            meta_path = os.path.join(processed_path, base_name + ".meta.json")

            entry = {
                "file_name": file,
                "text_path": txt_path,
                "metadata_path": meta_path if os.path.exists(meta_path) else None
            }

            index.append(entry)

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    return index