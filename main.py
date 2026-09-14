"""
Main Entry Point for PDF to DOCX Converter
Automatically launches GUI if no CLI arguments are supplied.
"""

import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure package directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
ROOT_DIR = os.path.dirname(PARENT_DIR)

for p in (ROOT_DIR, PARENT_DIR, BASE_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from tool.pdf_to_docx_converter.cli import run_cli

if __name__ == "__main__":
    sys.exit(run_cli())
