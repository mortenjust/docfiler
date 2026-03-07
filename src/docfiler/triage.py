"""Triage mode: classify a document and route to the correct inbox."""

import os
import shutil
import sys

from .ai import ask_ai
from .utils import dedup_name, log_to_csv


def handle_triage(filepath, text, cfg):
    """Classify as one of the route keys, copy to that inbox, archive original."""
    original_name = os.path.basename(filepath)
    ext = os.path.splitext(filepath)[1]

    route_keys = list(cfg["routes"].keys())
    routes_str = " or ".join(route_keys)
    routes_desc = "\n".join(
        f"{k} = {cfg['routes'][k]}" for k in route_keys
    )

    print("  Classifying...")
    response = ask_ai(
        f"You are sorting a scanned document for a {cfg['context']}.\n\n"
        f"First page text:\n{text}\n\n"
        f"Original filename: {original_name}\n\n"
        f"Respond with exactly two lines, nothing else:\n"
        f"Line 1: {routes_str}\n"
        f"Line 2: a filename following this convention: "
        f"{cfg['naming']}{ext}\n\n"
        f"Examples:\n"
        f"  2026-01-01 - AHV - Annual Contribution Notice.pdf\n"
        f"  2026-02-10 - Doctor Name - Medical Bill.pdf\n"
        f"  2026-03-05 - Paddle - Monthly Payout Statement.pdf\n\n"
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

    category = lines[0]
    name_part = lines[1]

    if category not in cfg["routes"]:
        print(f"  Error: expected {routes_str}, got: {category}", file=sys.stderr)
        sys.exit(1)

    new_name = f"{category} - {name_part}"
    ext_lower = ext.lower()
    if not new_name.lower().endswith(ext_lower):
        new_name += ext

    # Copy to the right inbox
    dest_inbox = cfg["routes"][category]
    os.makedirs(dest_inbox, exist_ok=True)

    copy_name = dedup_name(dest_inbox, new_name)
    shutil.copy2(filepath, os.path.join(dest_inbox, copy_name))
    print(f"  Copied → {category} inbox/{copy_name}")

    # Move original to Processed
    processed = cfg["processed"]
    os.makedirs(processed, exist_ok=True)
    processed_name = dedup_name(processed, new_name)
    shutil.move(filepath, os.path.join(processed, processed_name))
    print(f"  Archived → Processed/{processed_name}")

    # Log
    csv_path = os.path.join(cfg["inbox_dir"], "filing-history.csv")
    log_to_csv(csv_path, original_name, copy_name, f"{category} inbox")

    return copy_name
