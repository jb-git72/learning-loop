"""
csf_canonicalise_sweep.py — Replace old-form CSF disclaimer with canonical ADV-001 line.

Old form (all 18 ads): "See the general CSF risk warning + offer document."
New form (canonical):  "*Always consider the general CSF risk warning and offer document before investing."

Usage:
    python3 scripts/csf_canonicalise_sweep.py [--dry-run]
"""
import json
import re
import sys
from pathlib import Path

CANONICAL = "*Always consider the general CSF risk warning and offer document before investing."
CANONICAL_RE = re.compile(
    r"\*Always\s+consider\s+the\s+general\s+CSF\s+risk\s+warning\s+and\s+offer\s+document\s+before\s+investing"
)
# Old form variants to replace
OLD_FORM_RE = re.compile(
    r"See the general CSF risk warning \+ offer document\.?",
    re.IGNORECASE,
)
# DISC-001 banned wording — these must be stripped entirely
DISC001_RE = re.compile(
    r"(consider seeking independent financial advice|consult a financial advisor|disclosure document on Birchal)",
    re.IGNORECASE,
)

META_ADS_DIR = Path("clients/farm-thru/loop/meta-ads")
AD_IDS = [
    "BR-101", "BR-102", "BR-103", "BR-104", "BR-105",
    "BR-106", "BR-107", "BR-108", "BR-109", "BR-110",
    "CFE-101", "CFE-102", "CFE-103", "CFE-104", "CFE-105",
    "CFE-106", "CFE-107", "CFE-108",
]

dry_run = "--dry-run" in sys.argv


def process_ad(ad_id: str) -> dict:
    path = META_ADS_DIR / f"{ad_id}.json"
    ad = json.loads(path.read_text())
    result = {
        "ad_id": ad_id,
        "changed": False,
        "old_csf": None,
        "new_csf": CANONICAL,
        "disc001_stripped": False,
        "notes": [],
    }

    pt = ad.get("primary_text", "")
    original_pt = pt

    # 1. Identify and record the existing CSF/disclaimer line
    paras = pt.split("\n\n")
    last = paras[-1] if paras else ""

    if CANONICAL_RE.search(pt):
        result["notes"].append("already canonical — no change needed")
        result["old_csf"] = CANONICAL
        return result

    if OLD_FORM_RE.search(last):
        result["old_csf"] = last.strip()
    elif OLD_FORM_RE.search(pt):
        # Old form appears mid-body — note it
        result["old_csf"] = OLD_FORM_RE.search(pt).group(0)
        result["notes"].append("old form found mid-body, not as last para")
    else:
        result["old_csf"] = "(none found)"
        result["notes"].append("no CSF line detected — appending canonical")

    # 2. Strip DISC-001 banned wording anywhere in primary_text
    if DISC001_RE.search(pt):
        pt = DISC001_RE.sub("", pt)
        result["disc001_stripped"] = True
        result["notes"].append("DISC-001 banned wording stripped")

    # 3. Replace old-form CSF in last paragraph OR strip and append
    paras = pt.split("\n\n")
    last = paras[-1] if paras else ""

    if OLD_FORM_RE.search(last):
        paras[-1] = CANONICAL
    elif OLD_FORM_RE.search(pt):
        # Strip all occurrences mid-body
        pt = OLD_FORM_RE.sub("", pt).strip()
        paras = pt.split("\n\n")
        # Append canonical at end
        paras.append(CANONICAL)
    else:
        # No old form — just append canonical
        paras.append(CANONICAL)

    pt = "\n\n".join(p.strip() for p in paras if p.strip())

    if pt != original_pt:
        result["changed"] = True
        ad["primary_text"] = pt
        if not dry_run:
            path.write_text(json.dumps(ad, indent=2) + "\n")

    return result


def main():
    print(f"CSF canonicalise sweep {'(DRY RUN)' if dry_run else ''}")
    print(f"Target: {META_ADS_DIR}")
    print(f"Canonical: {CANONICAL!r}")
    print()

    results = []
    changed_count = 0
    for ad_id in AD_IDS:
        r = process_ad(ad_id)
        results.append(r)
        status = "CHANGED" if r["changed"] else ("SKIP (already canonical)" if r["old_csf"] == CANONICAL else "SKIP (no change)")
        print(f"  {ad_id}: {status}")
        if r["old_csf"] and r["old_csf"] != CANONICAL:
            print(f"    OLD: {r['old_csf']!r}")
        for note in r["notes"]:
            print(f"    NOTE: {note}")
        if r["disc001_stripped"]:
            print(f"    DISC-001: banned wording stripped")
        if r["changed"]:
            changed_count += 1

    print(f"\nSummary: {changed_count}/{len(AD_IDS)} ads updated.")
    if dry_run:
        print("DRY RUN — no files written.")


if __name__ == "__main__":
    main()
