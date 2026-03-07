"""CLI entry point for docfiler."""

import os
import sys

import click

from .config import find_config, load_config
from .filing import handle_file
from .ocr import SUPPORTED_EXT, extract_text_from_file
from .triage import handle_triage

SKIP_NAMES = {
    "docfiler.yaml", "CLAUDE.md", "agents.md", "README.md",
    ".DS_Store", ".skipped", "filing-history.csv",
    "file-one.sh", "file-all.sh", "check-inbox.sh", "classify.sh",
}
SKIP_DIRS = {"agent", "Processed"}


def process_one(filepath, cfg):
    """Process a single file according to the config mode."""
    filepath = os.path.abspath(filepath)

    if not os.path.isfile(filepath):
        print(f"  File not found: {filepath}", file=sys.stderr)
        return False

    original_name = os.path.basename(filepath)
    print(f"  Reading: {original_name}")

    text, filepath = extract_text_from_file(filepath)

    if len(text) < 10:
        print(f"  Error: not enough text ({len(text)} chars)", file=sys.stderr)
        return False

    print(f"  Extracted {len(text)} chars.")

    if cfg["mode"] == "triage":
        handle_triage(filepath, text, cfg)
    else:
        handle_file(filepath, text, cfg)

    return True


@click.group()
def main():
    """AI-powered document filing."""
    pass


@main.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def process(files):
    """Process files in the current directory's inbox.

    With no arguments, processes all supported files.
    With arguments, processes only the specified files.
    """
    cwd = os.getcwd()
    config_path = find_config(cwd)
    cfg = load_config(config_path)

    if files:
        # Process specific files
        failed = []
        for i, f in enumerate(files, 1):
            print(f"[{i}/{len(files)}] {os.path.basename(f)}")
            if not process_one(f, cfg):
                failed.append(os.path.basename(f))
            print()
    else:
        # Process all supported files in inbox
        inbox = cfg["inbox_dir"]
        all_files = sorted(
            f for f in os.listdir(inbox)
            if f not in SKIP_NAMES
            and f not in SKIP_DIRS
            and not f.startswith(".")
            and os.path.splitext(f)[1].lower() in SUPPORTED_EXT
            and os.path.isfile(os.path.join(inbox, f))
        )

        if not all_files:
            print("No files to process.")
            return

        print(f"Found {len(all_files)} file(s).\n")
        failed = []

        for i, filename in enumerate(all_files, 1):
            filepath = os.path.join(inbox, filename)
            print(f"[{i}/{len(all_files)}] {filename}")
            if not process_one(filepath, cfg):
                failed.append(filename)
            print()

    if failed:
        print(f"Failed ({len(failed)}):")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("All files processed.")


@main.command()
def status():
    """Show config and inbox status for the current directory."""
    cwd = os.getcwd()
    config_path = find_config(cwd)
    cfg = load_config(config_path)

    print(f"Mode:    {cfg['mode']}")
    print(f"Context: {cfg['context']}")
    print(f"Inbox:   {cfg['inbox_dir']}")

    if cfg["mode"] == "triage":
        print(f"Routes:")
        for k, v in cfg["routes"].items():
            print(f"  {k} → {v}")
        print(f"Processed: {cfg['processed']}")
    else:
        print(f"Tree root: {cfg['tree_root']}")

    # Count files
    inbox = cfg["inbox_dir"]
    count = sum(
        1 for f in os.listdir(inbox)
        if f not in SKIP_NAMES
        and f not in SKIP_DIRS
        and not f.startswith(".")
        and os.path.splitext(f)[1].lower() in SUPPORTED_EXT
        and os.path.isfile(os.path.join(inbox, f))
    )
    print(f"\nFiles waiting: {count}")
