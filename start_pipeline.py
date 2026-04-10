import os
import json
from datetime import datetime


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

            destination = os.path.join(raw_path, file)

            if os.path.exists(destination):
                log(f"Duplicate file skipped: {file}", log_file)
                continue

            try:
                os.rename(file_path, destination)
                log(f"Moved file to raw: {file}", log_file)
            except Exception as e:
                log(f"Error moving file {file}: {str(e)}", log_file)

    log("PAIOS pipeline finished", log_file)


if __name__ == "__main__":
    main()