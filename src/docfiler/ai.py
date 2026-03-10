"""Claude CLI wrapper."""

import subprocess
import sys


def ask_ai(prompt, cwd=None):
    """Send a prompt to Claude CLI and return the response."""
    # Some PDFs contain null bytes in extracted text which causes
    # subprocess to fail with "ValueError: embedded null byte"
    prompt = prompt.replace("\x00", "")
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, cwd=cwd,
    )
    if result.returncode != 0:
        print(f"  claude error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()
