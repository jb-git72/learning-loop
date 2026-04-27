#!/usr/bin/env python3
"""Check and auto-trim learnings files.

Prevents the recurring bug where learnings grow past the attention window
and the LLM stops following rules. Run after modifying any learnings file.

Usage:
  python3 scripts/check_learnings.py [client-slug]         # check only
  python3 scripts/check_learnings.py [client-slug] --trim   # check + auto-trim files over budget
"""

import json
import os
import sys
from pathlib import Path

root = Path(__file__).parent.parent

# Load .env for API key (needed for --trim)
env_path = root / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

# Thresholds
MAX_COMMON_CHARS = 2000    # learnings.md — universal rules, must be tight
MAX_TYPE_CHARS = 2000      # learnings-{type}.md — type-specific patterns
WARN_COMBINED_CHARS = 3500 # combined common + type should stay under this
TRIM_THRESHOLD = 0.85      # auto-trim when file exceeds 85% of limit

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


def _trim_with_llm(text: str, max_chars: int, file_name: str) -> str:
    """Use LLM to compress learnings while preserving all rules and meaning."""
    try:
        import anthropic
    except ImportError:
        print(f"  [SKIP] anthropic package not installed, can't auto-trim")
        return text

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(f"  [SKIP] ANTHROPIC_API_KEY not set, can't auto-trim")
        return text

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Compress this learnings file to under {max_chars} characters while preserving EVERY rule and pattern.

Rules for compression:
- Keep every NEVER/ALWAYS/MUST rule — these are non-negotiable
- Merge similar points into single bullets
- Remove examples if the rule is clear without them
- Use shorter phrasing: "No em dashes" not "NEVER use em dashes (—) or en dashes (–) in ANY content"
- Remove markdown formatting that doesn't add meaning (bold, headers are OK)
- Keep section structure (## headings)
- Numbers and specific data points must be preserved exactly
- If two rules say the same thing differently, keep the shorter one

Current file ({len(text)} chars, need under {max_chars}):

{text}

Output ONLY the compressed text, nothing else."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    trimmed = response.content[0].text.strip()

    # Validate: must be shorter and preserve critical content
    if len(trimmed) >= len(text):
        print(f"  [WARN] LLM output not shorter ({len(trimmed)} >= {len(text)}), keeping original")
        return text

    # Accept if meaningfully shorter, even if above aggressive target
    if len(trimmed) >= len(text) * 0.95:
        print(f"  [WARN] LLM only trimmed {len(text)-len(trimmed)} chars, keeping original")
        return text

    return trimmed


def check_client(client_slug: str, auto_trim: bool = False) -> int:
    client_dir = root / "clients" / client_slug
    if not client_dir.exists():
        print(f"Client {client_slug} not found")
        return 1

    errors = 0
    warnings = 0
    trimmed_files = []

    # Check common learnings
    common = client_dir / "learnings.md"
    if common.exists():
        text = common.read_text()
        size = len(text)
        limit = MAX_COMMON_CHARS
        pct = size / limit

        if size > limit:
            print(f"[FAIL] learnings.md: {size} chars (max {limit})")
            if auto_trim:
                print(f"  Trimming...")
                trimmed = _trim_with_llm(text, limit, "learnings.md")
                common.write_text(trimmed)
                print(f"  {size} -> {len(trimmed)} chars ({len(trimmed)/limit*100:.0f}%)")
                trimmed_files.append("learnings.md")
            else:
                print(f"  Run with --trim to auto-compress, or manually trim.")
                errors += 1
        elif pct > TRIM_THRESHOLD and auto_trim:
            print(f"[TRIM] learnings.md: {size} chars ({pct*100:.0f}% of {limit} — approaching limit)")
            trimmed = _trim_with_llm(text, int(limit * 0.75), "learnings.md")
            common.write_text(trimmed)
            print(f"  {size} -> {len(trimmed)} chars ({len(trimmed)/limit*100:.0f}%)")
            trimmed_files.append("learnings.md")
        else:
            print(f"[OK]   learnings.md: {size} chars ({pct*100:.0f}% of {limit})")

        # Check critical rules present
        final_text = common.read_text().lower()
        missing = [r for r in CRITICAL_RULES if r.lower() not in final_text]
        if missing:
            print(f"[WARN] learnings.md missing critical rules: {', '.join(missing)}")
            warnings += 1
    else:
        print(f"[FAIL] learnings.md not found")
        errors += 1

    # Check type-specific files
    for ct in ["meta-ad", "landing-page", "email", "sms"]:
        f = client_dir / f"learnings-{ct}.md"
        if not f.exists():
            print(f"[INFO] learnings-{ct}.md not found (optional)")
            continue

        text = f.read_text()
        size = len(text)
        limit = MAX_TYPE_CHARS
        pct = size / limit

        if size > limit:
            print(f"[FAIL] learnings-{ct}.md: {size} chars (max {limit})")
            if auto_trim:
                print(f"  Trimming...")
                trimmed = _trim_with_llm(text, limit, f"learnings-{ct}.md")
                f.write_text(trimmed)
                print(f"  {size} -> {len(trimmed)} chars ({len(trimmed)/limit*100:.0f}%)")
                trimmed_files.append(f"learnings-{ct}.md")
            else:
                print(f"  Run with --trim to auto-compress, or manually trim.")
                errors += 1
        elif pct > TRIM_THRESHOLD and auto_trim:
            print(f"[TRIM] learnings-{ct}.md: {size} chars ({pct*100:.0f}% — approaching limit)")
            trimmed = _trim_with_llm(text, int(limit * 0.75), f"learnings-{ct}.md")
            f.write_text(trimmed)
            print(f"  {size} -> {len(trimmed)} chars ({len(trimmed)/limit*100:.0f}%)")
            trimmed_files.append(f"learnings-{ct}.md")
        else:
            print(f"[OK]   learnings-{ct}.md: {size} chars ({pct*100:.0f}% of {limit})")

        # Check combined size
        if common.exists():
            combined = len(common.read_text()) + len(f.read_text())
            if combined > WARN_COMBINED_CHARS:
                print(f"[WARN] common + {ct} combined: {combined} chars (target <{WARN_COMBINED_CHARS})")
                warnings += 1

    print()
    if trimmed_files:
        print(f"Trimmed {len(trimmed_files)} file(s): {', '.join(trimmed_files)}")
        # Re-check critical rules after trim
        if common.exists():
            final_text = common.read_text().lower()
            lost = [r for r in CRITICAL_RULES if r.lower() not in final_text]
            if lost:
                print(f"[WARN] Trim may have lost critical rules: {', '.join(lost)}")
                print(f"  Review the trimmed file and restore any lost rules manually.")
                warnings += 1
        print()

    if errors:
        print(f"FAIL: {errors} error(s), {warnings} warning(s)")
    elif warnings:
        print(f"PASS with {warnings} warning(s)")
    else:
        print("PASS: all learnings within budget")

    return 1 if errors else 0


if __name__ == "__main__":
    slug = sys.argv[1] if len(sys.argv) > 1 else "farm-thru"
    auto_trim = "--trim" in sys.argv
    sys.exit(check_client(slug, auto_trim=auto_trim))
