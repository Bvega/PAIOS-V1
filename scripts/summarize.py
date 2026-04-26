# scripts/summarize.py
# ============================================
# PAIOS Summarization Module
# ============================================
# Purpose:
# - Generate lightweight summaries from processed files
# - Improve search relevance
# - Provide better preview + ranking signals

import os
import re


# ============================================
# Config
# ============================================

SUMMARY_DIR = "memory/summaries"


# ============================================
# Ensure Directory Exists
# ============================================

def ensure_summary_dir():
    """
    Create summaries directory if it does not exist.
    """
    os.makedirs(SUMMARY_DIR, exist_ok=True)


# ============================================
# Clean Text
# ============================================

def clean_text(content):
    """
    Remove noise and normalize text.
    """
    content = content.replace("\n", " ")
    content = re.sub(r"\s+", " ", content)

    return content.strip()


# ============================================
# Extract Meaningful Lines
# ============================================

def extract_key_lines(content, max_lines=5):
    """
    Extract most meaningful lines based on length.
    """
    lines = [
        line.strip()
        for line in content.split(".")
        if len(line.strip()) > 30
    ]

    # Sort by length (longer = more informative)
    lines.sort(key=len, reverse=True)

    return lines[:max_lines]


# ============================================
# Build Summary
# ============================================

def summarize_text(content):
    """
    Generate a structured summary.
    """
    if not content:
        return "No content available."

    content = clean_text(content)

    key_lines = extract_key_lines(content)

    if not key_lines:
        return content[:200]

    summary = " | ".join(key_lines)

    return summary


# ============================================
# Process Single File
# ============================================

def summarize_file(input_path, output_path):
    """
    Generate summary file from processed text.
    """
    try:
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except:
        return False

    summary = summarize_text(content)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(summary)

    return True


# ============================================
# Batch Processing
# ============================================

def generate_summaries(processed_dir="memory/processed"):
    """
    Generate summaries for all processed files.
    """
    ensure_summary_dir()

    count = 0

    for file in os.listdir(processed_dir):
        if not file.endswith(".txt"):
            continue

        input_path = os.path.join(processed_dir, file)
        output_path = os.path.join(SUMMARY_DIR, file.replace(".txt", "_summary.txt"))

        success = summarize_file(input_path, output_path)

        if success:
            count += 1

    print(f"[SUMMARIZE] Generated {count} summaries")