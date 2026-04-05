#!/usr/bin/env python3
"""Check learnings files for bloat and missing critical rules.

Prevents the recurring bug where learnings grow past the attention window
and the LLM stops following rules. Run after modifying any learnings file.

Usage: python3 scripts/check_learnings.py [client-slug]
"""

import sys
from pathlib import Path

root = Path(__file__).parent.parent

# Thresholds
MAX_COMMON_CHARS = 2000    # learnings.md — universal rules, must be tight
MAX_TYPE_CHARS = 2000      # learnings-{type}.md — type-specific patterns
WARN_COMBINED_CHARS = 3500 # combined common + type should stay under this

# Critical rules that MUST appear in common learnings
CRITICAL_RULES = [
    "em dash",
    "sentence",
    "doubt",
    "regenerative",
    "fabricat",
    "competitor",
    "Title Case",
    "delivered to your door",
]


def check_client(client_slug: str) -> int:
    client_dir = root / "clients" / client_slug
    if not client_dir.exists():
        print(f"Client {client_slug} not found")
        return 1

    errors = 0
    warnings = 0

    # Check common learnings
    common = client_dir / "learnings.md"
    if common.exists():
        text = common.read_text()
        size = len(text)
        if size > MAX_COMMON_CHARS:
            print(f"[FAIL] learnings.md: {size} chars (max {MAX_COMMON_CHARS})")
            print(f"       Trim or move content-type-specific patterns to split files.")
            errors += 1
        else:
            pct = size / MAX_COMMON_CHARS * 100
            print(f"[OK]   learnings.md: {size} chars ({pct:.0f}% of {MAX_COMMON_CHARS} limit)")

        # Check critical rules present
        text_lower = text.lower()
        missing = [r for r in CRITICAL_RULES if r.lower() not in text_lower]
        if missing:
            print(f"[WARN] learnings.md missing critical rules: {', '.join(missing)}")
            warnings += 1
    else:
        print(f"[FAIL] learnings.md not found")
        errors += 1

    # Check type-specific files
    for ct in ["meta-ad", "landing-page", "email"]:
        f = client_dir / f"learnings-{ct}.md"
        if f.exists():
            size = len(f.read_text())
            if size > MAX_TYPE_CHARS:
                print(f"[FAIL] learnings-{ct}.md: {size} chars (max {MAX_TYPE_CHARS})")
                errors += 1
            else:
                pct = size / MAX_TYPE_CHARS * 100
                print(f"[OK]   learnings-{ct}.md: {size} chars ({pct:.0f}% of {MAX_TYPE_CHARS} limit)")

            # Check combined size
            if common.exists():
                combined = len(common.read_text()) + size
                if combined > WARN_COMBINED_CHARS:
                    print(f"[WARN] common + {ct} combined: {combined} chars (target <{WARN_COMBINED_CHARS})")
                    warnings += 1
        else:
            print(f"[INFO] learnings-{ct}.md not found (optional)")

    print()
    if errors:
        print(f"FAIL: {errors} error(s), {warnings} warning(s)")
        print("Action: trim learnings files. Compress verbose rules into tighter phrasing.")
        print("Every extra word dilutes the LLM's attention on critical rules.")
    elif warnings:
        print(f"PASS with {warnings} warning(s)")
    else:
        print("PASS: all learnings within budget")

    return 1 if errors else 0


if __name__ == "__main__":
    slug = sys.argv[1] if len(sys.argv) > 1 else "farm-thru"
    sys.exit(check_client(slug))
