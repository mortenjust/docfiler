"""File mode: read folder tree and move document to the correct subfolder."""

import os
import shutil
import sys

from .ai import ask_ai
from .utils import dedup_name, get_folder_tree, log_to_csv


def handle_file(filepath, text, cfg):
    """Pick the right folder from the tree, rename, and move."""
    original_name = os.path.basename(filepath)
    ext = os.path.splitext(filepath)[1]

    tree_root = cfg["tree_root"]
    tree = get_folder_tree(tree_root)

    print("  Classifying...")
    response = ask_ai(
        f"You are filing a document into a {cfg['context']}.\n\n"
        f"First page text:\n{text}\n\n"
        f"Original filename: {original_name}\n\n"
        f"Available folders:\n{tree}\n\n"
        f"Respond with exactly two lines, nothing else:\n"
        f"Line 1: the destination folder path (from the list above)\n"
        f"Line 2: a filename following this convention: "
        f"{cfg['naming']}{ext}\n\n"
        f"Filename examples:\n"
        f"  2026-02-15 - Paddle - Monthly Payout Statement.pdf\n"
        f"  2026-01-01 - AHV - Annual Contribution Notice.pdf\n"
        f"  2026-03-05 - John Doe - Invoice Web Development.pdf\n\n"
        f"DATE RULE: Use the document's own date, NOT today's date. "
        f"If no date found, use 0000-00-00.\n"
        f"TOPIC RULE: Always in English (translate if needed).\n"
        f"Under 80 chars, keep the original file extension.",
        cwd=cfg["inbox_dir"],
    )

    lines = [l.strip() for l in response.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        print(f"  Error: unexpected AI response:\n{response}", file=sys.stderr)
        sys.exit(1)

    destination = lines[0]
    new_name = lines[1]
    ext_lower = ext.lower()
    if not new_name.lower().endswith(ext_lower):
        new_name += ext

    # Validate / create destination
    dest_dir = os.path.join(tree_root, destination)
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
        print(f"  Created folder: {destination}")

    # Dedup and move
    new_name = dedup_name(dest_dir, new_name)
    shutil.move(filepath, os.path.join(dest_dir, new_name))
    print(f"  Filed → {destination}/{new_name}")

    # Log
    csv_path = os.path.join(cfg["inbox_dir"], "filing-history.csv")
    log_to_csv(csv_path, original_name, new_name, destination)

    return new_name
