import os
import json
from datetime import datetime

from scripts.preprocess import process_file
from scripts.metadata import generate_metadata
from scripts.indexer import update_index
from scripts.summarize import summarize_text


def load_config():
    with open("config/config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def read_file_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def main():
    config = load_config()

    inbox = "inbox"
    raw_dir = "memory/raw"
    processed_dir = "memory/processed"
    summaries_dir = "memory/summaries"
    supported_types = config["file_types"]["supported"]

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(summaries_dir, exist_ok=True)

    files = os.listdir(inbox)

    log("PAIOS pipeline started")

    if not files:
        log("No files found in inbox")
        update_index()
        log("Index updated")
        log("PAIOS pipeline finished")
        return

    log(f"Files detected: {files}")

    for file in files:
        source_path = os.path.join(inbox, file)

        if not os.path.isfile(source_path):
            log(f"Skipped non-file item: {file}")
            continue

        _, ext = os.path.splitext(file)

        if ext.lower() not in supported_types:
            log(f"Skipped unsupported file: {file}")
            continue

        raw_destination = os.path.join(raw_dir, file)

        if os.path.exists(raw_destination):
            log(f"Duplicate file skipped: {file}")
            continue

        os.rename(source_path, raw_destination)
        log(f"Moved file to raw: {file}")

        processed_content = process_file(raw_destination)

        if processed_content is None:
            log(f"Processing returned no content: {file}")
            continue

        processed_filename = os.path.splitext(file)[0] + ".txt"
        processed_path = os.path.join(processed_dir, processed_filename)

        with open(processed_path, "w", encoding="utf-8") as f:
            f.write(processed_content)

        log(f"Processed file saved: {processed_filename}")

        metadata = generate_metadata(raw_destination, ext)
        metadata_path = processed_path.replace(".txt", ".meta.json")

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        log(f"Metadata saved: {os.path.basename(metadata_path)}")

        content = read_file_content(processed_path)
        summary = summarize_text(content)

        summary_filename = processed_filename.replace(".txt", ".summary.txt")
        summary_path = os.path.join(summaries_dir, summary_filename)

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary)

        log(f"Summary saved: {summary_filename}")

    update_index()
    log("Index updated")
    log("PAIOS pipeline finished")


if __name__ == "__main__":
    main()