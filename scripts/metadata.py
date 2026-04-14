import os
from datetime import datetime


def generate_metadata(file_path, file_type):
    stats = os.stat(file_path)

    metadata = {
        "file_name": os.path.basename(file_path),
        "file_type": file_type,
        "source_path": file_path,
        "size_bytes": stats.st_size,
        "created_at": datetime.fromtimestamp(stats.st_ctime).isoformat(),
        "modified_at": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        "processed_at": datetime.now().isoformat()
    }

    return metadata