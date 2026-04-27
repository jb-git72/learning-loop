"""Backfill is_test=True on the 4 historical stragglers identified in Phase 3c.

These are real Firestore docs whose email matches an internal/test pattern but
were created BEFORE PR #231 shipped, so they have no is_test field. This is the
"deferred follow-up" the prior agent left in their audit (item 1 under "What's
NOT done in this PR"). Fixing here.

Acceptance:
- Before: 124 public, 3 is_test=True
- After:  120 public, 7 is_test=True
- LP signupCount drops 124 -> 120

Counter doc unchanged (still represents DB total = 127).
Sheet1 not modified (admin/historical record).
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROJECT = "launcher-lab-proposals"
SLUG = "fmth-ecb582"
LP_URL = "https://join.farmthru.com.au/campaigns/fmth-ecb582/"

# Same patterns as campaign_store
_TEST_EMAIL_PATTERNS = (
    re.compile(r"@(test|example|sheettest|email|ref)\.com$", re.IGNORECASE),
    re.compile(
        r"^(e2e|firestore-test|verify|count-check|flow-demo|test-diagnosis|"
        r"aest-test|jb-demo|sheets-test|live-sheets-test|webhook|slack|"
        r"noslack|slackvar|vipslack|markvip|vipemail|welcome)[-_]?",
        re.IGNORECASE,
    ),
    re.compile(r"@launcherlab\.com\.au$", re.IGNORECASE),
    re.compile(r"\+(test|qa|verify|claude|staging|e2e)@", re.IGNORECASE),
)


def is_test_email(email: str) -> bool:
    e = (email or "").strip().lower()
    if not e:
        return False
    return any(p.search(e) for p in _TEST_EMAIL_PATTERNS)


STRAGGLERS = [
    "jeremy+viptest1@launcherlab.com.au",
    "jeremy+test1@launcherlab.com.au",
    "test+20260425@example.com",
    "jeremy+fmth-test@launcherlab.com.au",
]


def fetch_lp_count() -> int | None:
    req = urllib.request.Request(LP_URL, headers={"User-Agent": "verify/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    matches = re.findall(r"signupCount[\"']?\s*[:=]\s*(\d+)", html)
    return int(matches[0]) if matches else None


def main():
    from google.cloud import firestore  # type: ignore
    db = firestore.Client(project=PROJECT)
    coll = db.collection("campaigns").document(SLUG).collection("signups")

    # Pre-state
    docs_before = list(coll.stream())
    fs_total_before = len(docs_before)
    public_before = sum(1 for d in docs_before if not (d.to_dict() or {}).get("is_test"))
    is_test_before = sum(1 for d in docs_before if (d.to_dict() or {}).get("is_test") is True)
    lp_before = fetch_lp_count()
    print(f"Pre-state:  total={fs_total_before}  public={public_before}  is_test=True={is_test_before}  LP={lp_before}")

    # SAFETY: confirm regex flags every straggler
    not_flagged = [e for e in STRAGGLERS if not is_test_email(e)]
    if not_flagged:
        sys.exit(f"[ABORT] regex does not flag {not_flagged}")

    # Find docs by email
    found = []
    for e in STRAGGLERS:
        matches = [d for d in docs_before if (d.to_dict() or {}).get("email", "").strip().lower() == e.lower()]
        if not matches:
            print(f"  [WARN] {e} not found in DB (skipping)")
            continue
        if len(matches) > 1:
            print(f"  [WARN] {e} matches {len(matches)} docs — taking the first")
        found.append((e, matches[0]))

    print(f"\n[Update] {len(found)} docs to update")
    if not found:
        print("Nothing to do.")
        return

    # SAFETY: never touch more than 10 docs
    if len(found) > 10:
        sys.exit(f"[ABORT] {len(found)} stragglers > safety cap of 10")

    batch = db.batch()
    backfilled_at = datetime.now(timezone.utc).isoformat()
    for email, doc in found:
        batch.update(doc.reference, {
            "is_test": True,
            "is_test_backfilled_at": backfilled_at,
            "is_test_backfill_reason": "PR#231 prevention filter retroactive backfill (Phase 3c)",
        })
        print(f"  set is_test=True on {email}  (doc_id={doc.id})")
    batch.commit()
    print("[Update] committed")

    # Post-state
    docs_after = list(coll.stream())
    fs_total_after = len(docs_after)
    public_after = sum(1 for d in docs_after if not (d.to_dict() or {}).get("is_test"))
    is_test_after = sum(1 for d in docs_after if (d.to_dict() or {}).get("is_test") is True)
    lp_after = fetch_lp_count()
    print(f"\nPost-state: total={fs_total_after}  public={public_after}  is_test=True={is_test_after}  LP={lp_after}")
    print(f"\nDelta: public {public_before} -> {public_after} (Δ {public_after - public_before})")
    print(f"       is_test {is_test_before} -> {is_test_after} (Δ {is_test_after - is_test_before})")
    print(f"       LP {lp_before} -> {lp_after} (Δ {(lp_after or 0) - (lp_before or 0)})")

    out = Path("/Users/jb/Documents/GitHub/learning-loop/clients/farm-thru/data-snapshots/verify-stragglers-backfill.json")
    out.write_text(json.dumps({
        "stamp_utc": backfilled_at,
        "stragglers": STRAGGLERS,
        "updated_count": len(found),
        "before": {"total": fs_total_before, "public": public_before, "is_test": is_test_before, "lp": lp_before},
        "after": {"total": fs_total_after, "public": public_after, "is_test": is_test_after, "lp": lp_after},
    }, indent=2))
    print(f"\n[Done] -> {out}")


if __name__ == "__main__":
    main()
