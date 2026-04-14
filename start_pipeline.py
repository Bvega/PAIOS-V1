import os
import json
from datetime import datetime
from scripts.preprocess import process_file


def load_config():
    with open("config/config.json", "r") as f:
        return json.load(f)


def ensure_paths(config):
    for path in config["paths"].values():
        os.makedirs(path, exist_ok=True)


def log(message, log_file):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}\n"
    print(entry.strip())
    with open(log_file, "a") as f:
        f.write(entry)


def main():
    config = load_config()
    log_file = config["logging"]["log_file"]

    ensure_paths(config)

    log("PAIOS pipeline started", log_file)

    inbox_path = config["paths"]["inbox"]
    raw_path = config["paths"]["raw"]
    processed_path = config["paths"]["processed"]
    supported_types = config["file_types"]["supported"]

    files = os.listdir(inbox_path)

    if not files:
        log("No files found in inbox", log_file)
    else:
        log(f"Files detected: {files}", log_file)

        for file in files:
            file_path = os.path.join(inbox_path, file)

            if not os.path.isfile(file_path):
                log(f"Skipped non-file item: {file}", log_file)
                continue

            _, ext = os.path.splitext(file)

            if ext.lower() not in supported_types:
                log(f"Skipped unsupported file: {file}", log_file)
                continue

            raw_destination = os.path.join(raw_path, file)

            if os.path.exists(raw_destination):
                log(f"Duplicate file skipped: {file}", log_file)
                continue

            try:
                os.rename(file_path, raw_destination)
                log(f"Moved file to raw: {file}", log_file)
            except Exception as e:
                log(f"Error moving file {file}: {str(e)}", log_file)
                continue

            # PREPROCESSING STEP
            processed_content = process_file(raw_destination)

            if processed_content:
                output_file = os.path.splitext(file)[0] + ".txt"
                output_path = os.path.join(processed_path, output_file)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(processed_content)

                log(f"Processed file saved: {output_file}", log_file)

    log("PAIOS pipeline finished", log_file)


if __name__ == "__main__":
    main()