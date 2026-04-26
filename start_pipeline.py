# start_pipeline.py
# ============================================
# PAIOS Pipeline Entry Point
# ============================================

import os
import sys
import shutil
from datetime import datetime


# ============================================
# Helper: Timestamp
# ============================================

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================
# Ensure Required Structure
# ============================================

def ensure_structure():
    """
    Ensure all required runtime folders exist.
    This prevents indexer failures when folders are missing.
    """
    required_dirs = [
        "memory",
        "memory/processed",
        "memory/index",
        "outputs"
    ]

    for path in required_dirs:
        os.makedirs(path, exist_ok=True)


# ============================================
# Clean Runtime
# ============================================

def clean_runtime():
    """
    Remove runtime data for clean test runs.
    """
    for folder in ["memory", "outputs"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"[CLEAN] Removed {folder}/")


# ============================================
# File Discovery
# ============================================

def get_txt_files(input_path):
    txt_files = []

    for root, _, files in os.walk(input_path):
        for file_name in files:
            if file_name.endswith(".txt"):
                txt_files.append(os.path.join(root, file_name))

    return txt_files


# ============================================
# Preprocessing Wrapper
# ============================================

def run_preprocessing(file_path):
    """
    Safe wrapper to support evolving preprocess module.
    """
    try:
        from scripts.preprocess import preprocess_file
        return preprocess_file(file_path)

    except ImportError:
        try:
            from scripts.preprocess import process_file
            return process_file(file_path)

        except ImportError:
            # fallback safe read
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()


# ============================================
# Indexing
# ============================================

def run_indexing():
    """
    Run index builder.
    """
    try:
        from scripts.indexer import update_index
        update_index()
        print(f"[{timestamp()}] Index updated")

    except Exception as e:
        print(f"[WARNING] Index update failed: {e}")


# ============================================
# Main Pipeline
# ============================================

def run_pipeline(input_path, clean=False):
    print(f"[{timestamp()}] PAIOS pipeline started")

    if clean:
        clean_runtime()

    # CRITICAL FIX: always rebuild structure after clean
    ensure_structure()

    if not os.path.exists(input_path):
        print(f"[ERROR] Path not found: {input_path}")
        return

    files = get_txt_files(input_path)
    print(f"[{timestamp()}] Files detected: {len(files)}")

    if not files:
        print(f"[WARNING] No .txt files found")
        return

    # Process files
    for file_path in files:
        try:
            run_preprocessing(file_path)
        except Exception as e:
            print(f"[ERROR] Failed processing {file_path}: {e}")

    # Build index
    run_indexing()

    print(f"[{timestamp()}] PAIOS pipeline finished")


# ============================================
# CLI Entry
# ============================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 start_pipeline.py <input_path> [--clean]")
        sys.exit(1)

    input_path = sys.argv[1]
    clean_flag = "--clean" in sys.argv

    run_pipeline(input_path, clean=clean_flag)