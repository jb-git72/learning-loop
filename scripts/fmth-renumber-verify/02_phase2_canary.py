"""Phase 2 — Canary signup test (live).

Steps:
1. Snapshot DB state (counter, public count) immediately before POST
2. POST canary signup with email canary-overnight-<ts>@test.com
3. Read response (HTTP code, redirect URL, body)
4. Query Firestore for the new doc — verify is_test=True, position increment
5. Confirm public count NOT incremented (canary excluded)
6. Confirm Sheet1 NOT updated (test row skipped)
7. Confirm LP signupCount NOT changed
8. Detect any concurrent organic signups during the test window
9. Cleanup: delete canary doc from Firestore (counter NOT decremented — feature)
10. Verify cleanup: doc gone, counter unchanged
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
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
LP_BASE = "https://join.farmthru.com.au/campaigns/fmth-ecb582"
LP_URL = LP_BASE + "/"
LP_SIGNUP_URL = LP_BASE + "/signup"
SNAPSHOT_DIR = Path("/Users/jb/Documents/GitHub/learning-loop/clients/farm-thru/data-snapshots")


def fetch_lp_count():
    req = urllib.request.Request(LP_URL, headers={"User-Agent": "verify-overnight/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    matches = re.findall(r"signupCount[\"']?\s*[:=]\s*(\d+)", html)
    return int(matches[0]) if matches else None


def db_state(db):
    """Return (total_docs, public_count, counter_value) from Firestore."""
    coll = db.collection("campaigns").document(SLUG).collection("signups")
    docs = list(coll.stream())
    parsed = [{"_doc_id": d.id, **(d.to_dict() or {})} for d in docs]
    public = [r for r in parsed if r.get("is_test") is not True]
    counter_ref = (db.collection("campaigns").document(SLUG)
                   .collection("meta").document("counters"))
    counter_val = (counter_ref.get().to_dict() or {}).get("signup_count")
    return len(parsed), len(public), counter_val, parsed


def main():
    from google.cloud import firestore  # type: ignore
    import gspread  # type: ignore
    from google.oauth2 import service_account as sa  # type: ignore

    out = {"started_at": datetime.now(timezone.utc).isoformat()}
    canary_email = f"canary-overnight-{int(time.time())}@test.com"
    canary_name = "Overnight Canary"
    out["canary_email"] = canary_email

    print(f"\n{'=' * 70}")
    print(f"PHASE 2 — Canary signup test")
    print(f"{'=' * 70}\n")
    print(f"Canary email: {canary_email}")

    # ---------- DB pre-snapshot ----------
    db = firestore.Client(project=PROJECT)
    pre_total, pre_public, pre_counter, pre_parsed = db_state(db)
    pre_emails = {(r.get("email") or "").lower() for r in pre_parsed}
    pre_lp_count = fetch_lp_count()

    print(f"\nPRE-canary state:")
    print(f"  DB total: {pre_total}")
    print(f"  DB public: {pre_public}")
    print(f"  Counter: {pre_counter}")
    print(f"  LP signupCount: {pre_lp_count}")
    out["pre_state"] = {"db_total": pre_total, "db_public": pre_public,
                        "counter": pre_counter, "lp_signup_count": pre_lp_count}

    # ---------- Sheet1 pre-snapshot (just row count) ----------
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = sa.Credentials.from_service_account_file(KEY_FILE, scopes=scopes).with_subject(IMPERSONATE)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    target_ws = sh.worksheet(TARGET_TAB)
    pre_sheet_values = target_ws.get_all_values()
    pre_sheet_data = [r for r in pre_sheet_values[1:] if any(c.strip() for c in r)]
    pre_sheet_rows = len(pre_sheet_data)
    pre_sheet_emails = {(r[1] or "").lower() for r in pre_sheet_data}
    print(f"  Sheet1 data rows: {pre_sheet_rows}")
    out["pre_state"]["sheet1_rows"] = pre_sheet_rows

    # ---------- POST canary ----------
    form_data = urllib.parse.urlencode({
        "email": canary_email,
        "name": canary_name,
        "phone": "0400000000",
        "variant": "a",
        "utm_source": "verify_overnight_canary",
        "utm_medium": "test",
        "utm_campaign": "renumber_verification",
    }).encode()

    req = urllib.request.Request(
        LP_SIGNUP_URL, data=form_data, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "User-Agent": "verify-overnight/1.0",
                 "Accept": "application/json"},
    )
    posted_at = datetime.now(timezone.utc).isoformat()
    print(f"\nPOSTing canary @ {posted_at}...")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            response_code = resp.status
            response_body = resp.read().decode("utf-8", errors="replace")
            response_url = resp.geturl()
        print(f"  HTTP {response_code}")
        print(f"  URL: {response_url}")
        print(f"  Body (first 500): {response_body[:500]}")
    except urllib.error.HTTPError as e:
        response_code = e.code
        response_body = e.read().decode("utf-8", errors="replace")
        response_url = None
        print(f"  HTTP ERROR {response_code}: {response_body[:500]}")

    out["canary_post"] = {
        "posted_at": posted_at,
        "http_code": response_code,
        "response_body_first_500": response_body[:500],
        "response_url": response_url,
    }

    # Try to extract claimed position from response
    claimed_position = None
    try:
        body_json = json.loads(response_body)
        claimed_position = body_json.get("position")
    except Exception:
        # Try regex on HTML
        m = re.search(r"#?(\d{1,4})\s*of", response_body)
        if m:
            claimed_position = int(m.group(1))
    print(f"  Claimed position from response: {claimed_position}")
    out["canary_post"]["claimed_position"] = claimed_position

    # Wait briefly for Firestore consistency
    time.sleep(2)

    # ---------- DB post-snapshot ----------
    post_total, post_public, post_counter, post_parsed = db_state(db)
    post_lp_count = fetch_lp_count()

    canary_docs = [r for r in post_parsed if (r.get("email") or "").lower() == canary_email]
    canary_doc = canary_docs[0] if canary_docs else None

    print(f"\nPOST-canary state:")
    print(f"  DB total: {post_total} (was {pre_total}, delta {post_total - pre_total})")
    print(f"  DB public: {post_public} (was {pre_public}, delta {post_public - pre_public})")
    print(f"  Counter: {post_counter} (was {pre_counter}, delta {post_counter - pre_counter})")
    print(f"  LP signupCount: {post_lp_count} (was {pre_lp_count}, delta {post_lp_count - pre_lp_count})")

    if canary_doc:
        print(f"\nCanary doc found:")
        print(f"  doc_id:     {canary_doc.get('_doc_id')}")
        print(f"  email:      {canary_doc.get('email')}")
        print(f"  position:   {canary_doc.get('position')}")
        print(f"  is_test:    {canary_doc.get('is_test')}")
        print(f"  signed_up_at: {canary_doc.get('signed_up_at')}")
    else:
        print(f"\nERROR: canary doc NOT found in Firestore!")
    out["post_state"] = {
        "db_total": post_total, "db_public": post_public,
        "counter": post_counter, "lp_signup_count": post_lp_count,
        "canary_doc_id": canary_doc.get("_doc_id") if canary_doc else None,
        "canary_position": canary_doc.get("position") if canary_doc else None,
        "canary_is_test": canary_doc.get("is_test") if canary_doc else None,
        "canary_signed_up_at": canary_doc.get("signed_up_at") if canary_doc else None,
    }

    # ---------- Sheet1 post-check ----------
    post_sheet_values = target_ws.get_all_values()
    post_sheet_data = [r for r in post_sheet_values[1:] if any(c.strip() for c in r)]
    post_sheet_rows = len(post_sheet_data)
    post_sheet_emails = {(r[1] or "").lower() for r in post_sheet_data}
    canary_in_sheet = canary_email in post_sheet_emails
    print(f"  Sheet1 data rows: {post_sheet_rows} (was {pre_sheet_rows}, delta {post_sheet_rows - pre_sheet_rows})")
    print(f"  Canary in Sheet1: {canary_in_sheet}")
    out["post_state"]["sheet1_rows"] = post_sheet_rows
    out["post_state"]["canary_in_sheet"] = canary_in_sheet

    # ---------- Detect organic signups during the canary window ----------
    post_emails = {(r.get("email") or "").lower() for r in post_parsed}
    new_emails = post_emails - pre_emails - {canary_email}
    new_organics = []
    for r in post_parsed:
        e = (r.get("email") or "").lower()
        if e in new_emails:
            new_organics.append({
                "email": e,
                "position": r.get("position"),
                "is_test": r.get("is_test"),
                "signed_up_at": r.get("signed_up_at"),
            })
    if new_organics:
        print(f"\n  CONCURRENT ORGANIC SIGNUPS during canary window: {len(new_organics)}")
        for r in sorted(new_organics, key=lambda x: x.get("signed_up_at") or ""):
            print(f"    pos={r['position']:>4}  is_test={r['is_test']}  {r['email']}  @ {r['signed_up_at'][:25] if r['signed_up_at'] else 'NONE'}")
    else:
        print(f"\n  No concurrent organic signups during canary window.")
    out["organic_signups_during_window"] = new_organics

    # ---------- Verify expected behavior ----------
    expected_canary_position = pre_counter + 1
    # NOTE: if there were N concurrent organic signups before us, the canary
    # might have landed at pre_counter + 1 + N. Account for that.
    n_organics_before_canary = sum(
        1 for r in new_organics
        if r["signed_up_at"] and canary_doc and r["signed_up_at"] < canary_doc.get("signed_up_at", "9")
    )
    expected_canary_position_adj = expected_canary_position + n_organics_before_canary

    canary_position_ok = (canary_doc is not None and
                          canary_doc.get("position") == expected_canary_position_adj)
    canary_is_test_true = (canary_doc is not None and canary_doc.get("is_test") is True)

    # Public count delta should == count of NEW non-test arrivals
    public_organics = [r for r in new_organics if r.get("is_test") is not True]
    expected_public_delta = len(public_organics)
    public_delta_ok = (post_public - pre_public) == expected_public_delta

    # LP count delta should == public_organics count (NOT including canary)
    lp_delta_ok = (post_lp_count - pre_lp_count) == expected_public_delta

    # Sheet1 delta should == public_organics count (NOT including canary)
    sheet_delta_ok = (post_sheet_rows - pre_sheet_rows) == expected_public_delta

    # Counter delta should == 1 + total new arrivals (incl canary)
    expected_counter_delta = 1 + len(new_organics)
    counter_delta_ok = (post_counter - pre_counter) == expected_counter_delta

    print(f"\nVERIFY canary semantics:")
    print(f"  Canary doc exists:                      {canary_doc is not None}")
    print(f"  Canary is_test=True (excluded):         {'PASS' if canary_is_test_true else 'FAIL'}")
    print(f"  Canary position == expected ({expected_canary_position_adj}): {'PASS' if canary_position_ok else f'FAIL (got {canary_doc.get(chr(34) + chr(112) + chr(111) + chr(115) + chr(105) + chr(116) + chr(105) + chr(111) + chr(110) + chr(34)) if canary_doc else None})'}")
    print(f"  Canary NOT in Sheet1:                   {'PASS' if not canary_in_sheet else 'FAIL'}")
    print(f"  Public count delta == organics ({expected_public_delta}):  {'PASS' if public_delta_ok else f'FAIL (got {post_public - pre_public})'}")
    print(f"  LP count delta == organics ({expected_public_delta}):       {'PASS' if lp_delta_ok else f'FAIL (got {post_lp_count - pre_lp_count})'}")
    print(f"  Sheet1 delta == organics ({expected_public_delta}):         {'PASS' if sheet_delta_ok else f'FAIL (got {post_sheet_rows - pre_sheet_rows})'}")
    print(f"  Counter delta == 1+organics ({expected_counter_delta}):     {'PASS' if counter_delta_ok else f'FAIL (got {post_counter - pre_counter})'}")

    out["verify"] = {
        "canary_exists": canary_doc is not None,
        "canary_is_test_true": canary_is_test_true,
        "canary_position_ok": canary_position_ok,
        "expected_canary_position_adj": expected_canary_position_adj,
        "actual_canary_position": canary_doc.get("position") if canary_doc else None,
        "canary_excluded_from_sheet": not canary_in_sheet,
        "n_organics_before_canary": n_organics_before_canary,
        "n_public_organics": len(public_organics),
        "public_delta_ok": public_delta_ok,
        "lp_delta_ok": lp_delta_ok,
        "sheet_delta_ok": sheet_delta_ok,
        "counter_delta_ok": counter_delta_ok,
    }

    # ---------- Cleanup ----------
    if canary_doc and canary_doc.get("_doc_id"):
        canary_ref = (db.collection("campaigns").document(SLUG)
                      .collection("signups").document(canary_doc["_doc_id"]))
        canary_ref.delete()
        time.sleep(1)
        # Verify gone
        post_delete = canary_ref.get()
        deleted_ok = not post_delete.exists
        # Counter should NOT be decremented
        counter_post_delete = (db.collection("campaigns").document(SLUG)
                               .collection("meta").document("counters")
                               .get().to_dict() or {}).get("signup_count")
        counter_unchanged = (counter_post_delete == post_counter)
        print(f"\nCLEANUP:")
        print(f"  Canary doc deleted from Firestore:  {'PASS' if deleted_ok else 'FAIL'}")
        print(f"  Counter unchanged ({counter_post_delete} vs {post_counter}): {'PASS' if counter_unchanged else 'FAIL'}")
        out["cleanup"] = {
            "deleted": deleted_ok,
            "counter_post_delete": counter_post_delete,
            "counter_unchanged": counter_unchanged,
        }

    all_pass = (canary_doc is not None and canary_is_test_true and canary_position_ok
                and not canary_in_sheet and public_delta_ok and lp_delta_ok
                and sheet_delta_ok and counter_delta_ok)
    out["overall_pass"] = all_pass
    print(f"\n  OVERALL: {'PASS' if all_pass else 'FAIL'}")

    out_path = SNAPSHOT_DIR / "verify-phase2-canary.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n[Phase 2] DONE -> {out_path}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
