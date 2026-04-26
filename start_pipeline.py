# start_pipeline.py
# ============================================
# PAIOS Master Pipeline (FIXED ORDER)
# ============================================

import os
import sys
import shutil
from datetime import datetime

# Import modules
from scripts.preprocess import process_file
from scripts.indexer import update_index
from scripts.summarize import generate_summaries


# ============================================
# Helper: Timestamp
# ============================================

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================
# Ensure directories exist
# ============================================

def ensure_dirs():
    os.makedirs("memory/processed", exist_ok=True)
    os.makedirs("memory/index", exist_ok=True)
    os.makedirs("memory/summaries", exist_ok=True)


# ============================================
# Clean mode
# ============================================

def clean_memory():
    if os.path.exists("memory/processed"):
        shutil.rmtree("memory/processed")
        print("[CLEAN] Removed memory/processed")

    if os.path.exists("memory/index"):
        shutil.rmtree("memory/index")
        print("[CLEAN] Removed memory/index")

    if os.path.exists("memory/summaries"):
        shutil.rmtree("memory/summaries")
        print("[CLEAN] Removed memory/summaries")


# ============================================
# Pipeline
# ============================================

def run_pipeline(input_path, clean=False):
    print(f"[{timestamp()}] PAIOS pipeline started")

    if clean:
        clean_memory()

    ensure_dirs()

    files = os.listdir(input_path)
    print(f"[{timestamp()}] Files detected: {len(files)}")

    processed_count = 0

    # ----------------------------------------
    # STEP 1 — PREPROCESS
    # ----------------------------------------
    for file in files:
        full_path = os.path.join(input_path, file)

        if not os.path.isfile(full_path):
            print(f"[SKIP] Non-file: {file}")
            continue

        content = process_file(full_path)

        if not content:
            print(f"[SKIP] Unsupported: {file}")
            continue

        output_path = os.path.join("memory/processed", file)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        processed_count += 1

    print(f"[{timestamp()}] Processed files: {processed_count}")

    # ----------------------------------------
    # STEP 2 — SUMMARIZE (FIXED POSITION)
    # ----------------------------------------
    generate_summaries("memory/processed")

    # ----------------------------------------
    # STEP 3 — INDEX (AFTER SUMMARIES)
    # ----------------------------------------
    update_index()

    print(f"[{timestamp()}] PAIOS pipeline finished")


# ============================================
# CLI
# ============================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 start_pipeline.py <input_path> [--clean]")
        sys.exit(1)

    input_path = sys.argv[1]
    clean_flag = "--clean" in sys.argv

    run_pipeline(input_path, clean=clean_flag)