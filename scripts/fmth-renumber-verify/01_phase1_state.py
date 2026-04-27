"""Phase 1 — Re-verify post-renumber state (read-only).

Independently derives:
- DB total signups
- DB public count (is_test != True)
- DB is_test=True count
- Sheet1 row count (excluding header)
- LP signupCount (curl join.farmthru.com.au)
- Counter doc value

Then verifies:
- DB public == Sheet1 == LP signupCount
- Counter doc == DB public
- Position contiguity 1..N (no gaps, no duplicates, no positions > N)
- Position-vs-time order: N-th in time-order has position == N

Outputs JSON to clients/farm-thru/data-snapshots/verify-phase1-state.json.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")

PROJECT = "launcher-lab-proposals"
SLUG = "fmth-ecb582"
SHEET_ID = "1ooyw7zCCP039ml_4cZfPbhrxtFKuQsFa5VSfsyq6NhA"
KEY_FILE = "/Users/jb/Documents/GitHub/sales-skill/.gdocs-sync-key.json"
IMPERSONATE = "jeremy@launcherlab.com.au"
TARGET_TAB = "Sheet1"
LP_URL = "https://join.farmthru.com.au/campaigns/fmth-ecb582/"
SNAPSHOT_DIR = Path("/Users/jb/Documents/GitHub/learning-loop/clients/farm-thru/data-snapshots")


def fetch_lp_count():
    req = urllib.request.Request(LP_URL, headers={"User-Agent": "verify-overnight/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    matches = re.findall(r"signupCount[\"']?\s*[:=]\s*(\d+)", html)
    return int(matches[0]) if matches else None


def main():
    from google.cloud import firestore  # type: ignore
    import gspread  # type: ignore
    from google.oauth2 import service_account as sa  # type: ignore

    out = {"started_at": datetime.now(timezone.utc).isoformat()}

    # ---------- Firestore ----------
    db = firestore.Client(project=PROJECT)
    coll = db.collection("campaigns").document(SLUG).collection("signups")
    docs = list(coll.stream())
    parsed = [{"_doc_id": d.id, **(d.to_dict() or {})} for d in docs]
    db_total = len(parsed)
    public = [r for r in parsed if r.get("is_test") is not True]
    db_public = len(public)
    db_is_test_true = sum(1 for r in parsed if r.get("is_test") is True)
    db_is_test_none = sum(1 for r in parsed if r.get("is_test") is None)
    db_is_test_false = sum(1 for r in parsed if r.get("is_test") is False)

    counter_ref = (db.collection("campaigns").document(SLUG)
                   .collection("meta").document("counters"))
    counter_val = (counter_ref.get().to_dict() or {}).get("signup_count")

    # ---------- Position contiguity ----------
    public_positions = sorted(r.get("position") for r in public if r.get("position") is not None)
    expected_positions = list(range(1, db_public + 1))
    pos_contiguous = public_positions == expected_positions
    pos_gaps = sorted(set(expected_positions) - set(public_positions))
    pos_duplicates = sorted([p for p in public_positions if public_positions.count(p) > 1])
    pos_above_n = sorted([p for p in public_positions if p > db_public])

    # ---------- Position-vs-time order ----------
    # Sort public by signed_up_at, check N-th in time has position == N
    by_time = sorted(public, key=lambda r: r.get("signed_up_at") or "")
    time_order_mismatches = []
    for i, r in enumerate(by_time, start=1):
        if r.get("position") != i:
            time_order_mismatches.append({
                "expected_position": i,
                "actual_position": r.get("position"),
                "email": r.get("email"),
                "signed_up_at": r.get("signed_up_at"),
            })

    # ---------- Sheet1 ----------
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = sa.Credentials.from_service_account_file(KEY_FILE, scopes=scopes).with_subject(IMPERSONATE)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    target_ws = sh.worksheet(TARGET_TAB)
    sheet_values = target_ws.get_all_values()
    sheet_data = [r for r in sheet_values[1:] if any(c.strip() for c in r)]
    sheet_rows = len(sheet_data)
    sheet_positions = [r[0] for r in sheet_data]
    sheet_pos_contiguous = sheet_positions == [str(i) for i in range(1, sheet_rows + 1)]

    # ---------- LP ----------
    lp_count = fetch_lp_count()

    # ---------- Verification ----------
    triple_match = (db_public == sheet_rows == lp_count)
    counter_eq_public = (counter_val == db_public)
    next_position_will_be = counter_val + 1 if counter_val is not None else None

    out["counts"] = {
        "db_total": db_total,
        "db_public": db_public,
        "db_is_test_true": db_is_test_true,
        "db_is_test_false": db_is_test_false,
        "db_is_test_none": db_is_test_none,
        "sheet1_rows": sheet_rows,
        "lp_signup_count": lp_count,
        "counter_signup_count": counter_val,
        "next_position_will_be": next_position_will_be,
    }
    out["checks"] = {
        "triple_match_db_sheet_lp": triple_match,
        "counter_eq_public": counter_eq_public,
        "db_pos_contiguous_1_to_N": pos_contiguous,
        "sheet_pos_contiguous_1_to_N": sheet_pos_contiguous,
        "time_order_matches_position": len(time_order_mismatches) == 0,
    }
    out["details"] = {
        "expected_positions_count": len(expected_positions),
        "actual_positions_count": len(public_positions),
        "pos_gaps": pos_gaps,
        "pos_duplicates": pos_duplicates,
        "pos_above_N": pos_above_n,
        "time_order_mismatches": time_order_mismatches[:10],
        "time_order_mismatch_count": len(time_order_mismatches),
    }

    # ---------- Print summary ----------
    print(f"\n{'=' * 70}")
    print(f"PHASE 1 — Post-renumber state verification")
    print(f"{'=' * 70}\n")

    print(f"COUNTS:")
    print(f"  DB total signups          = {db_total}")
    print(f"  DB public (is_test!=True) = {db_public}")
    print(f"  DB is_test=True           = {db_is_test_true}")
    print(f"  DB is_test=False          = {db_is_test_false}")
    print(f"  DB is_test=None           = {db_is_test_none}")
    print(f"  Sheet1 data rows          = {sheet_rows}")
    print(f"  LP signupCount            = {lp_count}")
    print(f"  Counter signup_count      = {counter_val}")
    print(f"  Next signup will get pos  = {next_position_will_be}")

    print(f"\nCHECKS:")
    print(f"  Triple match (DB={db_public} == Sheet1={sheet_rows} == LP={lp_count}): {'PASS' if triple_match else 'FAIL'}")
    print(f"  Counter ({counter_val}) == DB public ({db_public}): {'PASS' if counter_eq_public else 'FAIL'}")
    print(f"  DB positions contiguous 1..{db_public}: {'PASS' if pos_contiguous else 'FAIL'}")
    print(f"  Sheet1 positions contiguous 1..{sheet_rows}: {'PASS' if sheet_pos_contiguous else 'FAIL'}")
    print(f"  Time-order matches position field: {'PASS' if len(time_order_mismatches) == 0 else 'FAIL'}")

    if pos_gaps:
        print(f"\n  POSITION GAPS: {pos_gaps[:20]}{'...' if len(pos_gaps) > 20 else ''}")
    if pos_duplicates:
        print(f"\n  POSITION DUPLICATES: {pos_duplicates[:20]}{'...' if len(pos_duplicates) > 20 else ''}")
    if pos_above_n:
        print(f"\n  POSITIONS > N: {pos_above_n[:20]}{'...' if len(pos_above_n) > 20 else ''}")
    if time_order_mismatches:
        print(f"\n  TIME-ORDER MISMATCHES (first 10):")
        for m in time_order_mismatches[:10]:
            print(f"    expected pos {m['expected_position']}, actual {m['actual_position']}: {m['email']} @ {m['signed_up_at'][:25] if m['signed_up_at'] else 'NONE'}")

    all_pass = (triple_match and counter_eq_public and pos_contiguous
                and sheet_pos_contiguous and len(time_order_mismatches) == 0)
    out["overall_pass"] = all_pass

    print(f"\n  OVERALL: {'PASS' if all_pass else 'FAIL'}")

    out_path = SNAPSHOT_DIR / "verify-phase1-state.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n[Phase 1] DONE -> {out_path}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
