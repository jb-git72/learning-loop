#!/usr/bin/env python3
"""Mark PLAT-005 (64% market-share) DOM ads + headlines as citation-pending.

PLAT-005 is JB-authorised but its `source_status` is OPEN: ASIC RG 234 needs
a documented public citation on file before any DOM ad runs on Meta. The
V5c bodies are `phase: waitlist`, so in the approval sheet they fall under
the green "READY to ship" band. That band is phase-based and would visually
imply the DOM ads are ship-ready, which they are not until the citation is
attached.

This makes the gate impossible to miss in JB's review surface:
  - DOM body files: prefix `_source_label` with "[64% CITATION PENDING] "
  - headlines file: set `status: "citation-pending"` on every PLAT-005 entry
    (the V5 headlines tab renders a Status column from this field).

Idempotent: re-running does not double-prefix or change anything already set.

Run:
    python3 scripts/mark_v5c_citation_pending.py            # default V5c set
    python3 scripts/mark_v5c_citation_pending.py --dry-run
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VARIANTS = REPO / "clients" / "birchal" / "loop" / "birchal-ad-variants"

PREFIX = "[64% CITATION PENDING] "
DOM_BODIES = [VARIANTS / f"BIRCHAL-V5C-DOM{i}.json" for i in (1, 2, 3, 4)]
HEADLINES = VARIANTS / "birchal-headlines-v5c.json"
PLAT005_MARKER = "PLAT-005"  # appears in the DOM angle string


def mark(dry_run: bool = False) -> list[str]:
    changed: list[str] = []

    for p in DOM_BODIES:
        ad = json.loads(p.read_text())
        label = ad.get("_source_label", "")
        if not label.startswith(PREFIX):
            ad["_source_label"] = PREFIX + label
            if not dry_run:
                p.write_text(json.dumps(ad, indent=2) + "\n")
            changed.append(f"{p.name}: _source_label -> {ad['_source_label']!r}")

    hl = json.loads(HEADLINES.read_text())
    n_hl = 0
    for h in hl.get("headlines", []):
        if PLAT005_MARKER in h.get("angle", "") and h.get("status") != "citation-pending":
            h["status"] = "citation-pending"
            n_hl += 1
    if n_hl and not dry_run:
        HEADLINES.write_text(json.dumps(hl, indent=2) + "\n")
    if n_hl:
        changed.append(f"{HEADLINES.name}: status=citation-pending on {n_hl} PLAT-005 headlines")

    return changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    changes = mark(dry_run=args.dry_run)
    if not changes:
        print("Nothing to do (already marked).")
        return
    head = "[dry-run] would change:" if args.dry_run else "Changed:"
    print(head)
    for c in changes:
        print(f"  - {c}")


if __name__ == "__main__":
    main()
