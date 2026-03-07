"""Load and validate docfiler.yaml configuration."""

import os
import sys

import yaml

CONFIG_FILENAME = "docfiler.yaml"


def find_config(start_dir):
    """Find docfiler.yaml in start_dir. Returns (config_dict, config_dir)."""
    path = os.path.join(start_dir, CONFIG_FILENAME)
    if not os.path.isfile(path):
        print(f"No {CONFIG_FILENAME} found in {start_dir}", file=sys.stderr)
        sys.exit(1)
    return path


def load_config(config_path):
    """Load and validate the config file."""
    config_dir = os.path.dirname(os.path.abspath(config_path))

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    if not cfg or "mode" not in cfg:
        print(f"Invalid config: 'mode' is required", file=sys.stderr)
        sys.exit(1)

    mode = cfg["mode"]
    if mode not in ("triage", "file"):
        print(f"Invalid mode: {mode} (expected 'triage' or 'file')", file=sys.stderr)
        sys.exit(1)

    # Resolve paths relative to config dir
    if mode == "triage":
        if "routes" not in cfg:
            print("Triage mode requires 'routes'", file=sys.stderr)
            sys.exit(1)
        cfg["routes"] = {
            k: os.path.expanduser(os.path.join(config_dir, v))
            if not os.path.isabs(os.path.expanduser(v))
            else os.path.expanduser(v)
            for k, v in cfg["routes"].items()
        }
        processed = cfg.get("processed", "Processed")
        cfg["processed"] = os.path.join(config_dir, processed)

    if mode == "file":
        tree_root = cfg.get("tree_root", "..")
        cfg["tree_root"] = os.path.abspath(os.path.join(config_dir, tree_root))

    cfg["inbox_dir"] = config_dir
    cfg["context"] = cfg.get("context", "")
    cfg["naming"] = cfg.get("naming", "YYYY-MM-DD - Sender - Topic in English")

    return cfg
