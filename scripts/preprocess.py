# scripts/preprocess.py
# ============================================
# PAIOS Preprocessing Module
# ============================================
# Purpose:
# - Read raw input files
# - Clean text content
# - Save processed .txt files into memory/processed/
#
# This is required because scripts/indexer.py builds the search index from:
# memory/processed/

import os
import json


# ============================================
# Configuration
# ============================================

PROCESSED_DIR = "memory/processed"


# ============================================
# Ensure Output Folder
# ============================================

def ensure_processed_dir():
    """
    Make sure memory/processed exists before writing files.
    """
    os.makedirs(PROCESSED_DIR, exist_ok=True)


# ============================================
# Text Cleaning
# ============================================

def clean_text(content):
    """
    Basic text cleanup.

    Current behavior:
    - strips leading/trailing whitespace
    - normalizes line endings
    - removes excessive blank lines
    """
    if not content:
        return ""

    content = content.replace("\r\n", "\n").replace("\r", "\n")

    lines = [line.rstrip() for line in content.split("\n")]

    cleaned_lines = []
    previous_blank = False

    for line in lines:
        is_blank = line.strip() == ""

        # Avoid repeated blank lines
        if is_blank and previous_blank:
            continue

        cleaned_lines.append(line)
        previous_blank = is_blank

    return "\n".join(cleaned_lines).strip()


# ============================================
# File Name Handling
# ============================================

def output_filename(file_path):
    """
    Keep original filename but force .txt output.
    """
    base_name = os.path.basename(file_path)
    name_without_ext, _ = os.path.splitext(base_name)
    return f"{name_without_ext}.txt"


# ============================================
# TXT Processing
# ============================================

def process_txt(file_path):
    """
    Process a normal .txt file and save it to memory/processed.
    """
    ensure_processed_dir()

    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        content = file.read()

    cleaned = clean_text(content)

    output_path = os.path.join(PROCESSED_DIR, output_filename(file_path))

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(cleaned)

    return output_path


# ============================================
# JSON Processing
# ============================================

def process_json(file_path):
    """
    Process a .json file by converting it into readable formatted text.

    This keeps JSON support available for future use.
    """
    ensure_processed_dir()

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            data = json.load(file)

        content = json.dumps(data, indent=2, ensure_ascii=False)

    except Exception as error:
        content = f"INVALID JSON FILE: {str(error)}"

    cleaned = clean_text(content)

    output_path = os.path.join(PROCESSED_DIR, output_filename(file_path))

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(cleaned)

    return output_path


# ============================================
# Main Processor
# ============================================

def process_file(file_path):
    """
    Route file processing based on extension.

    Supported:
    - .txt
    - .json
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == ".txt":
        return process_txt(file_path)

    if ext == ".json":
        return process_json(file_path)

    return None


# ============================================
# Compatibility Alias
# ============================================

def preprocess_file(file_path):
    """
    Compatibility wrapper.

    Some pipeline versions call preprocess_file().
    Others call process_file().
    Both now work.
    """
    return process_file(file_path)