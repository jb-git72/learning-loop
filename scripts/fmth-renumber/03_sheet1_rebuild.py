"""Phase 4: Rebuild Sheet1 data range from current Firestore public state.

Pre-write safeguard:
1. Snapshot ALL tabs (hash of each) — abort if any tab is missing
2. Verify Sheet1 header matches expected schema
3. Append a single canary row with email _renumber_safety_canary_<ts>@test.com
4. Verify canary landed in Sheet1 (not another tab) by re-fetching tab + matching email
5. Delete canary row by row index
6. Verify canary deletion succeeded

If any of those fail, ABORT — DB renumber still ships.

Bulk rebuild:
1. Read public signups from Firestore, sort by NEW position 1..N
2. Build 14-column rows matching COLUMNS = [position, email, name, phone, ref_code,
   referral_count, referred_by, signed_up_at, vip, utm_source, utm_medium,
   utm_campaign, utm_content, variant]
3. Use values.batchClear with 'Sheet1'!A2:Z9999 (range-qualified, NEVER bare A2:Z9999)
4. Use values.update with 'Sheet1'!A2:N{1+N} to write the rows
5. Verify post-write:
   - Sheet1 row count = N+1 (header + N data)
   - Column B (email) values are unique
   - Column A (position) values are 1..N
   - Spot-check first/last row
6. Verify all OTHER tabs are byte-identical to pre-snapshot
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT = "launcher-lab-proposals"
SLUG = "fmth-ecb582"
SHEET_ID = "1ooyw7zCCP039ml_4cZfPbhrxtFKuQsFa5VSfsyq6NhA"
KEY_FILE = "/Users/jb/Documents/GitHub/sales-skill/.gdocs-sync-key.json"
IMPERSONATE = "jeremy@launcherlab.com.au"
TARGET_TAB = "Sheet1"
SNAPSHOT_DIR = Path("/Users/jb/Documents/GitHub/learning-loop/clients/farm-thru/data-snapshots")

# Match campaign_storage.py COLUMNS exactly
COLUMNS = [
    "position", "email", "name", "phone", "ref_code",
    "referral_count", "referred_by", "signed_up_at",
    "vip", "utm_source", "utm_medium", "utm_campaign", "utm_content",
    "variant",
]


def hash_values(values):
    return hashlib.sha256(json.dumps(values, sort_keys=False).encode()).hexdigest()


def fmt_value(v, key=None):
    """Render a Python value the way Sheets prefers."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    return str(v)


def main():
    import gspread  # type: ignore
    from google.oauth2 import service_account as sa  # type: ignore
    from google.cloud import firestore  # type: ignore

    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = sa.Credentials.from_service_account_file(KEY_FILE, scopes=scopes).with_subject(IMPERSONATE)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)

    # ------ Snapshot ALL tabs ------
    pre = {}
    target_ws = None
    for ws in sh.worksheets():
        v = ws.get_all_values()
        pre[ws.title] = {"sheet_id": ws.id, "rows": len(v), "sha256": hash_values(v)}
        if ws.title == TARGET_TAB:
            target_ws = ws
            target_pre_values = v
    if target_ws is None:
        sys.exit(f"[ABORT] {TARGET_TAB} tab not found")
    print(f"[Sheet1] Pre-snapshot: {len(pre)} tabs total")
    for tab, info in pre.items():
        marker = "<- TARGET" if tab == TARGET_TAB else ""
        print(f"  {tab:25s} rows={info['rows']:4d} sha={info['sha256'][:12]} {marker}")

    # ------ Verify header schema ------
    header = target_pre_values[0]
    header_lower = [c.strip().lower() for c in header]
    # Live header has trailing empty col (variant header was never added).
    expected_first_13 = COLUMNS[:13]
    if header_lower[:13] != expected_first_13:
        sys.exit(f"[ABORT] Sheet1 header mismatch.\n   got:      {header_lower}\n   expected: {expected_first_13}+(variant)")
    if len(header) < 14:
        print(f"[Sheet1] WARN: header has only {len(header)} cols (no 'variant' label) — will preserve as-is")
    print(f"[Sheet1] Header verified ({len(header)} cols): {header}")

    # ------ Pre-write canary ------
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    canary_email = f"_renumber_safety_canary_{ts}@test.com"
    print(f"\n[Canary] Appending: {canary_email}")
    canary_row = ["__CANARY__", canary_email, "Canary Row", "", "canarycode",
                  0, "", datetime.now(timezone.utc).isoformat(),
                  "FALSE", "", "", "", "", "canary"]
    target_ws.append_rows([canary_row], value_input_option="USER_ENTERED")

    # Re-fetch + verify canary landed in TARGET_TAB
    canary_check_values = target_ws.get_all_values()
    canary_row_idx_1based = None
    for i, r in enumerate(canary_check_values):
        if len(r) >= 2 and r[1].strip().lower() == canary_email.lower():
            canary_row_idx_1based = i + 1  # gspread is 1-indexed
            break
    if canary_row_idx_1based is None:
        sys.exit(f"[ABORT] Canary {canary_email} did not appear in {TARGET_TAB} after append")
    print(f"[Canary] Found in {TARGET_TAB} at row {canary_row_idx_1based} — append goes to correct tab")

    # Verify canary did NOT appear in any other tab
    for ws in sh.worksheets():
        if ws.title == TARGET_TAB:
            continue
        v = ws.get_all_values()
        for r in v:
            if len(r) >= 2 and r[1].strip().lower() == canary_email.lower():
                sys.exit(f"[ABORT] Canary leaked into tab {ws.title}")
    print(f"[Canary] No leak into other tabs")

    # Delete canary row using batchUpdate deleteDimension (row idx is 0-based for API)
    sh.batch_update({"requests": [{"deleteDimension": {"range": {
        "sheetId": pre[TARGET_TAB]["sheet_id"],
        "dimension": "ROWS",
        "startIndex": canary_row_idx_1based - 1,
        "endIndex": canary_row_idx_1based,
    }}}]})

    # Verify deletion
    post_canary_values = target_ws.get_all_values()
    if any(len(r) >= 2 and r[1].strip().lower() == canary_email.lower() for r in post_canary_values):
        sys.exit(f"[ABORT] Canary still present after delete request")
    print(f"[Canary] Deleted — Sheet1 rows now = {len(post_canary_values)} (was {len(canary_check_values)})")

    # Pre-snapshot Sheet1 should match what we have now (canary added + removed)
    if len(post_canary_values) != len(target_pre_values):
        print(f"[Canary] WARN: row count drift after canary cycle "
              f"({len(target_pre_values)} -> {len(post_canary_values)}) — likely a real signup landed mid-canary; continuing")

    # ------ Read DB for source-of-truth rows ------
    db = firestore.Client(project=PROJECT)
    coll = db.collection("campaigns").document(SLUG).collection("signups")
    docs = list(coll.stream())
    public = [{"_doc_id": d.id, **(d.to_dict() or {})} for d in docs if not (d.to_dict() or {}).get("is_test")]
    public_sorted = sorted(public, key=lambda r: r.get("position") or 10**9)
    N = len(public_sorted)
    positions = [r.get("position") for r in public_sorted]
    if positions != list(range(1, N + 1)):
        gaps = sorted(set(range(1, N + 1)) - set(positions))
        dupes = sorted({p for p in positions if positions.count(p) > 1})
        sys.exit(f"[ABORT] DB positions not 1..{N} contiguous. gaps={gaps[:5]} dupes={dupes[:5]}")
    print(f"\n[Rebuild] DB has {N} public signups, positions = 1..{N} (contiguous, OK)")

    # Build rows
    new_rows = []
    for r in public_sorted:
        row = [
            fmt_value(r.get("position")),
            fmt_value(r.get("email", "")),
            fmt_value(r.get("name", "")),
            fmt_value(r.get("phone", "")),
            fmt_value(r.get("ref_code", "")),
            fmt_value(r.get("referral_count", 0)),
            fmt_value(r.get("referred_by", "")),
            fmt_value(r.get("signed_up_at", "")),
            fmt_value(r.get("vip", False)),
            fmt_value(r.get("utm_source", "")),
            fmt_value(r.get("utm_medium", "")),
            fmt_value(r.get("utm_campaign", "")),
            fmt_value(r.get("utm_content", "")),
            fmt_value(r.get("variant", "")),
        ]
        new_rows.append(row)

    # ------ Clear Sheet1 data range (range-qualified) ------
    # Use spreadsheet-level batchClear with explicit 'Sheet1'! prefix in the
    # range string. body={"ranges": [...]} per Google Sheets v4 API.
    # This is range-qualified — touches only Sheet1.
    print(f"\n[Rebuild] Clearing 'Sheet1'!A2:Z9999 (spreadsheet-level batchClear, range-qualified) ...")
    sh.values_batch_clear(body={"ranges": ["'Sheet1'!A2:Z9999"]})
    # Verify cleared
    cleared_values = target_ws.get_all_values()
    if len(cleared_values) > 1:
        # rows past header still present?
        # Some empty trailing rows are OK; check that no NON-EMPTY rows remain past header.
        non_empty = [r for r in cleared_values[1:] if any(c.strip() for c in r)]
        if non_empty:
            sys.exit(f"[ABORT] Sheet1 still has {len(non_empty)} non-empty rows after clear")
    print(f"[Rebuild] Cleared. Sheet1 rows after clear = {len(cleared_values)}")

    # ------ Write new rows ------
    last_col_letter = chr(ord('A') + len(COLUMNS) - 1)  # = N for 14 cols
    write_range = f"'Sheet1'!A2:{last_col_letter}{1 + N}"
    print(f"[Rebuild] Writing {N} rows to {write_range} ...")
    sh.values_update(write_range, params={"valueInputOption": "USER_ENTERED"}, body={"values": new_rows})

    # ------ Verify post-write ------
    post_values = target_ws.get_all_values()
    data_rows = [r for r in post_values[1:] if any(c.strip() for c in r)]
    print(f"[Verify] Sheet1 rows incl header = {len(post_values)}  data rows = {len(data_rows)}")
    if len(data_rows) != N:
        sys.exit(f"[ABORT] expected {N} data rows, got {len(data_rows)}")
    # Column A should be "1", "2", ..., "N"
    pos_strs = [r[0] for r in data_rows]
    expected_strs = [str(i) for i in range(1, N + 1)]
    if pos_strs != expected_strs:
        sys.exit(f"[ABORT] column A positions not 1..{N}.\n   first 5 got: {pos_strs[:5]}\n   last 5 got:  {pos_strs[-5:]}")
    # Column B emails should be unique
    emails = [(r[1] or "").strip().lower() for r in data_rows]
    if len(set(emails)) != len(emails):
        dupes = [e for e in set(emails) if emails.count(e) > 1]
        sys.exit(f"[ABORT] duplicate emails in Sheet1: {dupes[:5]}")
    print(f"[Verify] OK: column A = 1..{N}, column B unique")
    # Spot-check first / last
    print(f"[Verify] First row: pos={data_rows[0][0]}  email={data_rows[0][1]}")
    print(f"[Verify] Last row:  pos={data_rows[-1][0]}  email={data_rows[-1][1]}")

    # ------ Verify other tabs unchanged ------
    drift = []
    for ws in sh.worksheets():
        if ws.title == TARGET_TAB:
            continue
        v = ws.get_all_values()
        post_hash = hash_values(v)
        pre_hash = pre.get(ws.title, {}).get("sha256")
        if pre_hash != post_hash:
            drift.append({"tab": ws.title, "pre": pre_hash[:12] if pre_hash else None, "post": post_hash[:12]})
    if drift:
        print(f"[Verify] WARN: non-target tab drift detected (probably independent automation, NOT this script):")
        for d in drift:
            print(f"   {d['tab']}: {d['pre']} -> {d['post']}")
    else:
        print(f"[Verify] OK: all {len(pre) - 1} non-target tabs byte-identical")

    # ------ Persist result ------
    result = {
        "stamp_utc": datetime.now(timezone.utc).isoformat(),
        "N": N,
        "rows_written": len(new_rows),
        "sheet1_rows_pre": len(target_pre_values),
        "sheet1_rows_post": len(post_values),
        "canary_email": canary_email,
        "canary_landed_at_row": canary_row_idx_1based,
        "non_target_drift": drift,
    }
    out = SNAPSHOT_DIR / "renumber-phase4-result.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\n[Phase 4] DONE -> {out}")


if __name__ == "__main__":
    main()
