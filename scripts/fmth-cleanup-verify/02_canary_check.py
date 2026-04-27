"""Phase 5 — verify canary signup landed with is_test=True, public count unchanged, sheet unchanged.

Then delete the canary doc so it doesn't pollute prod.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

PROJECT = "launcher-lab-proposals"
SLUG = "fmth-ecb582"
SHEET_ID = "1ooyw7zCCP039ml_4cZfPbhrxtFKuQsFa5VSfsyq6NhA"
KEY_FILE = "/Users/jb/Documents/GitHub/sales-skill/.gdocs-sync-key.json"
IMPERSONATE = "jeremy@launcherlab.com.au"
LP_URL = "https://join.farmthru.com.au/campaigns/fmth-ecb582/"

CANARY_EMAIL = sys.argv[1] if len(sys.argv) > 1 else None
if not CANARY_EMAIL:
    sys.exit("Usage: 02_canary_check.py <canary_email>")


def fetch_lp_count() -> int | None:
    req = urllib.request.Request(LP_URL, headers={"User-Agent": "verify/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    matches = re.findall(r"signupCount[\"']?\s*[:=]\s*(\d+)", html)
    return int(matches[0]) if matches else None


def main():
    print(f"Canary email: {CANARY_EMAIL}")

    from google.cloud import firestore  # type: ignore
    db = firestore.Client(project=PROJECT)
    coll = db.collection("campaigns").document(SLUG).collection("signups")

    # Step 1: locate the canary doc
    docs = list(coll.where("email", "==", CANARY_EMAIL).stream())
    print(f"\nStep 1: locate canary doc")
    print(f"  matching docs: {len(docs)} (expected 1)")
    if not docs:
        sys.exit("[FAIL] canary doc not found in Firestore")
    canary_doc = docs[0]
    canary_data = canary_doc.to_dict() or {}
    print(f"  doc_id: {canary_doc.id}")
    print(f"  email: {canary_data.get('email')}")
    print(f"  is_test: {canary_data.get('is_test')}")
    print(f"  position: {canary_data.get('position')}")

    if canary_data.get("is_test") is not True:
        print(f"[FAIL] is_test field is {canary_data.get('is_test')!r} (expected True)")
        # Don't exit — we still want to clean up
        result_status = "FAIL"
    else:
        print("[OK] is_test=True — prevention filter tagged the canary")
        result_status = "PASS"

    # Step 2: total docs (incl canary), public count (should exclude canary)
    all_docs = list(coll.stream())
    fs_total = len(all_docs)
    public_count = sum(1 for d in all_docs if not (d.to_dict() or {}).get("is_test"))
    print(f"\nStep 2: post-canary counts")
    print(f"  DB total: {fs_total}")
    print(f"  DB public (is_test != True): {public_count}")

    # Step 3: LP signup count (should be public_count, not fs_total)
    lp_count = fetch_lp_count()
    print(f"\nStep 3: LP signupCount = {lp_count}  (expected = public_count = {public_count})")
    if lp_count != public_count:
        print(f"[FAIL] LP count {lp_count} != public count {public_count}")
        result_status = "FAIL"
    else:
        print("[OK] LP excludes canary correctly")

    # Step 4: Sheet1 row count and absence of canary
    import gspread  # type: ignore
    from google.oauth2 import service_account as sa  # type: ignore

    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = sa.Credentials.from_service_account_file(KEY_FILE, scopes=scopes).with_subject(IMPERSONATE)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet("Sheet1")
    rows = ws.get_all_values()
    sheet1_data_count = len(rows) - 1
    sheet1_emails = {(r[1] or "").strip().lower() for r in rows[1:] if len(r) >= 2}
    canary_in_sheet = CANARY_EMAIL.lower() in sheet1_emails
    print(f"\nStep 4: Sheet1 data rows = {sheet1_data_count} (expected {public_count})")
    print(f"  Canary in Sheet1: {canary_in_sheet} (expected False)")
    if canary_in_sheet or sheet1_data_count != public_count:
        print(f"[FAIL] Sheet1 has canary or row count mismatch")
        result_status = "FAIL"
    else:
        print("[OK] Sheet1 unchanged by canary")

    # Step 5: Cleanup the canary
    print(f"\nStep 5: Cleanup canary doc {canary_doc.id}")
    canary_doc.reference.delete()
    print(f"  deleted")

    # Counter doc should be set to current real count.
    # Atomic counter incremented on canary insert (now reads fs_total).
    # After delete, no auto-decrement, so manually correct.
    counter_ref = db.collection("campaigns").document(SLUG).collection("meta").document("counters")
    new_total = fs_total - 1
    counter_ref.set({"signup_count": new_total}, merge=True)
    print(f"  counter doc -> {new_total}")

    # Re-verify
    docs_after = list(coll.stream())
    print(f"\n  Post-cleanup DB total: {len(docs_after)} (expected {fs_total - 1})")

    out = Path("/Users/jb/Documents/GitHub/learning-loop/clients/farm-thru/data-snapshots/verify-canary-result.json")
    out.write_text(json.dumps({
        "canary_email": CANARY_EMAIL,
        "is_test_field": canary_data.get("is_test"),
        "post_canary_db_total": fs_total,
        "post_canary_public": public_count,
        "post_canary_lp_count": lp_count,
        "post_canary_sheet1_rows": sheet1_data_count,
        "canary_in_sheet": canary_in_sheet,
        "post_cleanup_db_total": len(docs_after),
        "verdict": result_status,
    }, indent=2))
    print(f"\n[Result] verdict={result_status}  written to {out}")


if __name__ == "__main__":
    main()
