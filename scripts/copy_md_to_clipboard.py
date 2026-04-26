#!/usr/bin/env python3
"""Copy a markdown file to the macOS clipboard as RTF (rich text).

Pastes into Google Docs / Pages / Word / Slack / email with headings, bold,
lists, and tables preserved.

Usage: python3 scripts/copy_md_to_clipboard.py path/to/file.md
"""
import subprocess
import sys
from pathlib import Path

import markdown


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-markdown-file>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    md_text = path.read_text()
    html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

    rtf = subprocess.check_output(
        ["textutil", "-stdin", "-stdout", "-format", "html", "-convert", "rtf"],
        input=html.encode(),
    )
    subprocess.run(["pbcopy"], input=rtf, check=True)

    print(f"Copied {path.name} as rich text ({len(rtf)} RTF bytes) to clipboard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
