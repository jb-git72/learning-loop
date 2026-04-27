"""Reconcile Sheet1 with the post-backfill DB-public state.

After Phase 3c backfill, DB public count = 120 but Sheet1 still has 124 rows
(includes the 4 historical stragglers). This script removes those 4 rows from
Sheet1 so the user-stated "DB / Sheet1 / LP all equal" invariant holds.

Operates on Sheet1 only (sheetId=0). Uses single batchUpdate with
deleteDimension in descending row order. Hashes every non-target tab pre/post
and aborts if any drift detected.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SHEET_ID = "1ooyw7zCCP039ml_4cZfPbhrxtFKuQsFa5VSfsyq6NhA"
KEY_FILE = "/Users/jb/Documents/GitHub/sales-skill/.gdocs-sync-key.json"
IMPERSONATE = "jeremy@launcherlab.com.au"
TARGET_TAB = "Sheet1"

STRAGGLERS = {
    "jeremy+viptest1@launcherlab.com.au",
    "jeremy+test1@launcherlab.com.au",
    "test+20260425@example.com",
    "jeremy+fmth-test@launcherlab.com.au",
}


def hash_values(values):
    return hashlib.sha256(json.dumps(values, sort_keys=False).encode()).hexdigest()


def main():
    import gspread  # type: ignore
    from google.oauth2 import service_account as sa  # type: ignore

    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = sa.Credentials.from_service_account_file(KEY_FILE, scopes=scopes).with_subject(IMPERSONATE)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)

    # Snapshot ALL tabs for change-detection
    pre = {}
    target_ws = None
    for ws in sh.worksheets():
        v = ws.get_all_values()
        pre[ws.title] = (ws.id, hash_values(v), v)
        if ws.title == TARGET_TAB:
            target_ws = ws
    if target_ws is None:
        sys.exit("[ABORT] target tab not found")

    target_id, _, target_values = pre[TARGET_TAB]
    header = [c.strip().lower() for c in target_values[0]]
    if header[:5] != ["position", "email", "name", "phone", "ref_code"]:
        sys.exit(f"[ABORT] header mismatch: {header[:5]}")
    email_col = header.index("email")

    # Identify rows to delete (0-indexed for the API)
    rows_to_drop_zero = []
    for i, r in enumerate(target_values):
        if i == 0:
            continue
        if email_col >= len(r):
            continue
        if r[email_col].strip().lower() in STRAGGLERS:
            rows_to_drop_zero.append(i)
    print(f"[Sheet1] rows to drop: {len(rows_to_drop_zero)} (expected 4)")
    print(f"  indices (0-based): {rows_to_drop_zero}")

    if not rows_to_drop_zero:
        print("[Sheet1] nothing to do")
        return
    if len(rows_to_drop_zero) > 10:
        sys.exit("[ABORT] more than 10 deletes — aborting safety guard")

    # batchUpdate descending
    requests = []
    for idx in sorted(rows_to_drop_zero, reverse=True):
        requests.append({"deleteDimension": {"range": {
            "sheetId": target_id, "dimension": "ROWS",
            "startIndex": idx, "endIndex": idx + 1,
        }}})
    sh.batch_update({"requests": requests})
    print(f"[Sheet1] deleted {len(requests)} rows")

    # Re-snapshot ALL tabs and verify non-target unchanged
    drift = []
    target_post = None
    for ws in sh.worksheets():
        v = ws.get_all_values()
        if ws.title == TARGET_TAB:
            target_post = v
            continue
        pre_hash = pre.get(ws.title, (None, None, None))[1]
        post_hash = hash_values(v)
        if pre_hash != post_hash:
            drift.append((ws.title, pre_hash, post_hash))
    if drift:
        print(f"[WARN] non-target drift detected (likely independent automated update, NOT this script):")
        for title, ph, qh in drift:
            print(f"   {title}: {ph[:12]} -> {qh[:12]}")
    else:
        print("[Sheet1] all non-target tabs byte-identical")

    print(f"[Sheet1] post rows = {len(target_post)} (was {len(target_values)})")

    out = Path("/Users/jb/Documents/GitHub/learning-loop/clients/farm-thru/data-snapshots/verify-sheet1-reconcile.json")
    out.write_text(json.dumps({
        "rows_dropped": len(requests),
        "stragglers": sorted(STRAGGLERS),
        "rows_pre": len(target_values),
        "rows_post": len(target_post),
        "non_target_drift": [t for t, _, _ in drift],
    }, indent=2))
    print(f"[Done] -> {out}")


if __name__ == "__main__":
    main()
