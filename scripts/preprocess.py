import os


def process_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return content.strip()


def process_json(file_path):
    import json

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return json.dumps(data, indent=2)

    except Exception as e:
        return f"INVALID JSON FILE: {str(e)}"


def process_file(file_path):
    _, ext = os.path.splitext(file_path)

    if ext == ".txt":
        return process_txt(file_path)

    elif ext == ".json":
        return process_json(file_path)

    else:
        return None