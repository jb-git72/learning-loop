"""
Fix objection_preemption scoring signals in FarmThru landing pages.

The scorer checks 5 regex patterns across all text fields:
  1. refundable               (when deposit mentioned)
  2. not financial advice | disclosure document
  3. don't know | most startups | can't promise | no guarantee   (risk ack)
  4. no (warehouse|wholesaler|middlem)                           (supply chain)
  5. sydney | central coast | wollongong | deliver               (delivery area)

This script reads each LP JSON, checks which signals are present,
and adds missing signals to appropriate sections.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LP_DIR = Path(__file__).resolve().parent.parent / "clients" / "farm-thru" / "loop" / "landing-pages"

SIGNALS = {
    1: re.compile(r"refundable", re.IGNORECASE),
    2: re.compile(r"not\s+financial\s+advice|disclosure\s+document", re.IGNORECASE),
    3: re.compile(r"don't\s+know|most\s+startups|can't\s+promise|no\s+guarantee", re.IGNORECASE),
    4: re.compile(r"no\s+(?:warehouse|wholesaler|middlem)", re.IGNORECASE),
    5: re.compile(r"sydney|central\s+coast|wollongong|deliver", re.IGNORECASE),
}

HERO_MAX = 500
BODY_MAX = 1000


def collect_all_text(lp: dict) -> str:
    """Gather all text fields into one string for signal checking."""
    parts = [
        lp.get("headline", ""),
        lp.get("subhead", ""),
        lp.get("hero_copy", ""),
    ]
    for sec in lp.get("sections", []):
        parts.append(sec.get("heading", ""))
        parts.append(sec.get("body", ""))
    return "\n".join(parts)


def check_signals(text: str) -> dict[int, bool]:
    """Return dict of signal_id -> present."""
    return {sid: bool(pat.search(text)) for sid, pat in SIGNALS.items()}


def has_investment_content(lp: dict) -> bool:
    """Check if the page discusses investment (for signal 3 relevance)."""
    text = collect_all_text(lp).lower()
    return "invest" in text or "equity crowdfunding" in text or "birchal" in text


def find_section_index(lp: dict, keywords: list[str]) -> int | None:
    """Find first non-Compliance section whose heading contains any keyword."""
    for i, sec in enumerate(lp.get("sections", [])):
        heading = sec.get("heading", "").lower()
        if heading == "compliance":
            continue
        if any(kw in heading for kw in keywords):
            return i
    return None


def find_investment_section(lp: dict) -> int | None:
    """Find the investment/opportunity section index."""
    return find_section_index(lp, ["invest", "term", "part of", "comes next", "opening", "vip"])


def find_how_it_works_section(lp: dict) -> int | None:
    """Find the how-it-works / hub / model section index."""
    return find_section_index(lp, ["hub", "model", "how", "supply", "order", "paddock", "built"])


def append_to_body(lp: dict, section_idx: int, sentence: str) -> bool:
    """Append sentence to section body if within char limit. Return success."""
    body = lp["sections"][section_idx]["body"]
    new_body = body.rstrip() + " " + sentence
    if len(new_body) > BODY_MAX:
        print(f"  WARNING: would exceed body limit ({len(new_body)}/{BODY_MAX}), skipping")
        return False
    lp["sections"][section_idx]["body"] = new_body
    return True


def prepend_to_hero(lp: dict, sentence: str) -> bool:
    """Append sentence to hero_copy if within char limit."""
    hero = lp.get("hero_copy", "")
    new_hero = hero.rstrip() + "\n\n" + sentence
    if len(new_hero) > HERO_MAX:
        print(f"  WARNING: would exceed hero_copy limit ({len(new_hero)}/{HERO_MAX}), skipping")
        return False
    lp["hero_copy"] = new_hero
    return True


def fix_lp(lp: dict) -> list[str]:
    """Fix missing signals in one LP. Returns list of changes made."""
    page_id = lp.get("page_id", "unknown")
    all_text = collect_all_text(lp)
    present = check_signals(all_text)
    changes = []

    print(f"\n{page_id}:")
    for sid, found in present.items():
        status = "FOUND" if found else "MISSING"
        print(f"  Signal {sid}: {status}")

    # Signal 4: no middlemen
    if not present[4]:
        # Try hero_copy first, then first non-Compliance section body
        how_idx = find_how_it_works_section(lp)
        if how_idx is not None:
            if append_to_body(lp, how_idx, "No middlemen. No wholesalers."):
                changes.append("Added signal 4 (no middlemen) to section: " + lp["sections"][how_idx]["heading"])
        else:
            # Fall back to hero_copy
            if prepend_to_hero(lp, "No middlemen. No wholesalers."):
                changes.append("Added signal 4 (no middlemen) to hero_copy")

    # Signal 5: delivery area / Sydney
    if not present[5]:
        how_idx = find_how_it_works_section(lp)
        if how_idx is not None:
            if append_to_body(lp, how_idx, "Sydney families collect from the Brookvale hub."):
                changes.append("Added signal 5 (delivery area) to section: " + lp["sections"][how_idx]["heading"])
        else:
            # Try investment section or first non-compliance section
            for i, sec in enumerate(lp.get("sections", [])):
                if sec.get("heading", "").lower() != "compliance":
                    if append_to_body(lp, i, "Sydney families collect from the Brookvale hub."):
                        changes.append("Added signal 5 (delivery area) to section: " + sec["heading"])
                    break

    # Signal 3: risk acknowledgment (only if investment content)
    if not present[3] and has_investment_content(lp):
        inv_idx = find_investment_section(lp)
        if inv_idx is not None:
            if append_to_body(lp, inv_idx, "We can't promise returns — early-stage investing carries real risk."):
                changes.append("Added signal 3 (risk acknowledgment) to section: " + lp["sections"][inv_idx]["heading"])
        else:
            # Last resort: hero_copy
            if prepend_to_hero(lp, "We can't promise returns — early-stage investing carries real risk."):
                changes.append("Added signal 3 (risk acknowledgment) to hero_copy")

    if not changes:
        print("  No changes needed.")
    else:
        for c in changes:
            print(f"  FIXED: {c}")

    return changes


def validate_limits(lp: dict) -> list[str]:
    """Check character limits. Returns list of violations."""
    violations = []
    page_id = lp.get("page_id", "unknown")
    hero_len = len(lp.get("hero_copy", ""))
    if hero_len > HERO_MAX:
        violations.append(f"{page_id}: hero_copy {hero_len}/{HERO_MAX}")
    for sec in lp.get("sections", []):
        body_len = len(sec.get("body", ""))
        if body_len > BODY_MAX:
            violations.append(f"{page_id}: section '{sec.get('heading', '')}' body {body_len}/{BODY_MAX}")
    return violations


def main():
    lp_files = sorted(LP_DIR.glob("LP-*.json"))
    if not lp_files:
        print(f"No LP files found in {LP_DIR}")
        sys.exit(1)

    print(f"Found {len(lp_files)} landing pages in {LP_DIR}")

    all_changes = {}
    all_violations = []

    for fp in lp_files:
        lp = json.loads(fp.read_text())
        changes = fix_lp(lp)
        all_changes[fp.name] = changes

        violations = validate_limits(lp)
        all_violations.extend(violations)

        if changes:
            fp.write_text(json.dumps(lp, indent=2) + "\n")
            print(f"  Written: {fp.name}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total = sum(len(c) for c in all_changes.values())
    print(f"Total changes: {total}")
    for fname, changes in all_changes.items():
        if changes:
            print(f"  {fname}: {len(changes)} change(s)")

    if all_violations:
        print("\nCHARACTER LIMIT VIOLATIONS:")
        for v in all_violations:
            print(f"  {v}")
        sys.exit(1)
    else:
        print("\nAll character limits OK.")

    # Re-verify all signals are now present
    print("\nPOST-FIX VERIFICATION:")
    all_pass = True
    for fp in lp_files:
        lp = json.loads(fp.read_text())
        text = collect_all_text(lp)
        present = check_signals(text)
        missing = [sid for sid, found in present.items() if not found]
        # Signal 3 only matters if investment content
        if 3 in missing and not has_investment_content(lp):
            missing.remove(3)
        status = "PASS" if not missing else f"MISSING signals: {missing}"
        print(f"  {fp.name}: {status}")
        if missing:
            all_pass = False

    if not all_pass:
        print("\nSome signals still missing!")
        sys.exit(1)
    else:
        print("\nAll signals present. Done.")


if __name__ == "__main__":
    main()
