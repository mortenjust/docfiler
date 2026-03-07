"""Shared utilities: folder tree, dedup, CSV logging."""

import csv
import os
from datetime import datetime, timezone


def get_folder_tree(root, exclude_dirs=None):
    """Walk a directory tree, return sorted list of relative paths."""
    exclude = exclude_dirs or {"inbox", "agent", "Processed"}
    folders = []
    for dirpath, dirs, _ in os.walk(root):
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".")
            and d not in exclude
            and "Inbox" not in d
        ]
        rel = os.path.relpath(dirpath, root)
        if rel == ".":
            continue
        folders.append(rel)
    return "\n".join(sorted(folders))


def dedup_name(dest_dir, filename):
    """If filename exists in dest_dir, append (2), (3), etc."""
    name_base, ext = os.path.splitext(filename)
    final = filename
    counter = 2
    while os.path.exists(os.path.join(dest_dir, final)):
        final = f"{name_base} ({counter}){ext}"
        counter += 1
    return final


def log_to_csv(csv_path, original, new_name, destination):
    """Append a row to the filing history CSV."""
    write_header = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        if write_header:
            writer.writerow(["original_filename", "new_filename",
                             "destination", "filed_at"])
        writer.writerow([
            original, new_name, destination,
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        ])
