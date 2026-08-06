"""Logger utility following AGENTS.md specification for local-bridge errors log."""
import os
import sys
import logging

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "errors.log")

def log_error(msg: str):
    """Log error line to errors.log matching ERROR:bridge:<msg> format."""
    entry = f"ERROR:bridge:{msg}\n"
    print(entry, end="", file=sys.stderr)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"Failed to write to {LOG_FILE}: {e}", file=sys.stderr)

def log_warning(msg: str):
    """Log warning line to errors.log matching WARNING:bridge:<msg> format."""
    entry = f"WARNING:bridge:{msg}\n"
    print(entry, end="", file=sys.stderr)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"Failed to write to {LOG_FILE}: {e}", file=sys.stderr)
