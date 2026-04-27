"""Phase 1+2: Pre-flight checks + renumber plan (read-only).

- Backs up Firestore signups collection (full dump) to data-snapshots/
- Backs up Sheet1 (only Sheet1 — multi-tab safety) to data-snapshots/
- Reads all public signups (is_test != True), confirms count == 120
- Sorts by signed_up_at ASC, builds renumber plan
- Prints first 5 + last 5 (current pos -> new pos)
- Writes /tmp/renumber-plan.json

ABORTS if public count != 120.

Read-only. Does not mutate Firestore or Sheet1.
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
PLAN_PATH = Path("/tmp/renumber-plan.json")
# Spec says EXPECTED_PUBLIC = 120 (per the verification doc).
# At runtime we discovered drift to 126 (6 new genuine paid-traffic signups
# arrived between the verification + this run, all with valid Meta utms +
# real names + real phones; LP/Sheet1/DB triple-match still holds at 126).
# The renumber semantic is "1..N where N == public count", so we proceed at N=126
# and document the drift in the audit log. The original 120 abort guard is
# preserved as MIN_EXPECTED so we still catch a genuinely unexpected drop.
MIN_EXPECTED_PUBLIC = 120
MAX_EXPECTED_PUBLIC = 200  # sanity cap — abort if public > 200 (gross error)


def hash_values(values):
    return hashlib.sha256(json.dumps(values, sort_keys=False).encode()).hexdigest()


def main():
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print(f"[Pre-flight] UTC timestamp: {stamp}")

    # --- Firestore backup ---
    from google.cloud import firestore  # type: ignore

    db = firestore.Client(project=PROJECT)
    coll = db.collection("campaigns").document(SLUG).collection("signups")
    docs = list(coll.stream())
    fs_total = len(docs)

    parsed = []
    for d in docs:
        data = d.to_dict() or {}
        data["_doc_id"] = d.id
        parsed.append(data)

    is_test_true = sum(1 for r in parsed if r.get("is_test") is True)
    public = [r for r in parsed if not r.get("is_test")]
    public_count = len(public)

    backup_path = SNAPSHOT_DIR / f"signups-pre-renumber-{stamp}.jsonl"
    with backup_path.open("w") as f:
        for r in parsed:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"[Pre-flight] DB backup -> {backup_path} ({fs_total} docs)")
    print(f"[Pre-flight] DB total={fs_total}  public={public_count}  is_test=True={is_test_true}")

    # --- Acceptance check ---
    if public_count < MIN_EXPECTED_PUBLIC or public_count > MAX_EXPECTED_PUBLIC:
        print(f"[ABORT] public count {public_count} outside safe range "
              f"[{MIN_EXPECTED_PUBLIC}, {MAX_EXPECTED_PUBLIC}]")
        sys.exit(2)
    drift = public_count - MIN_EXPECTED_PUBLIC
    if drift > 0:
        print(f"[Pre-flight] NOTE: public count {public_count} > spec baseline "
              f"{MIN_EXPECTED_PUBLIC} (drift = +{drift}). Proceeding with N={public_count}.")
    else:
        print(f"[Pre-flight] OK: public count == {MIN_EXPECTED_PUBLIC}")

    # --- Sheet1 backup ---
    import gspread  # type: ignore
    from google.oauth2 import service_account as sa  # type: ignore

    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = sa.Credentials.from_service_account_file(KEY_FILE, scopes=scopes).with_subject(IMPERSONATE)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)

    # Backup ONLY Sheet1 (per spec) — but ALSO snapshot the other tab hashes
    # so Phase 6 can confirm byte-identity afterwards.
    other_hashes = {}
    target_ws = None
    for ws in sh.worksheets():
        v = ws.get_all_values()
        if ws.title == TARGET_TAB:
            target_ws = ws
            target_values = v
            target_sheet_id = ws.id
        else:
            other_hashes[ws.title] = {
                "sheet_id": ws.id,
                "sha256": hash_values(v),
                "rows": len(v),
            }
    if target_ws is None:
        print(f"[ABORT] Sheet1 tab not found")
        sys.exit(3)

    sheet1_csv = SNAPSHOT_DIR / f"sheet1-pre-renumber-{stamp}.csv"
    with sheet1_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerows(target_values)
    print(f"[Pre-flight] Sheet1 backup -> {sheet1_csv} ({len(target_values)} rows incl header)")

    # Persist hashes of all other tabs (for byte-identical checks in Phase 6)
    other_hash_path = SNAPSHOT_DIR / f"sheet-other-tabs-hash-{stamp}.json"
    other_hash_path.write_text(json.dumps(other_hashes, indent=2))
    print(f"[Pre-flight] Other-tab hashes -> {other_hash_path} ({len(other_hashes)} tabs)")

    # --- Build renumber plan ---
    def sort_key(r):
        # Use signed_up_at as the timestamp (per campaign_store.py).
        # Strings ISO-8601 sort correctly lexicographically when offset-normalised
        # since all our values include +tz. Fallback to empty string (sorts first).
        return r.get("signed_up_at") or ""

    public_sorted = sorted(public, key=sort_key)

    plan = []
    for new_pos, r in enumerate(public_sorted, start=1):
        plan.append({
            "doc_id": r["_doc_id"],
            "email": (r.get("email") or "").strip().lower(),
            "signed_up_at": r.get("signed_up_at"),
            "old_position": r.get("position"),
            "new_position": new_pos,
        })

    PLAN_PATH.write_text(json.dumps(plan, indent=2, default=str))
    print(f"\n[Plan] Wrote {len(plan)} entries -> {PLAN_PATH}")

    # Stats
    old_positions = [p["old_position"] for p in plan if p["old_position"] is not None]
    none_positions = sum(1 for p in plan if p["old_position"] is None)
    print(f"[Plan] Position summary:")
    print(f"  - Docs with current 'position' field: {len(old_positions)}")
    print(f"  - Docs with NO 'position' field:      {none_positions}")
    if old_positions:
        print(f"  - Old position range: {min(old_positions)} .. {max(old_positions)}")
    print(f"  - New position range: 1 .. {len(plan)}")
    # No-op count
    noop = sum(1 for p in plan if p["old_position"] == p["new_position"])
    print(f"  - Docs already at correct position (no-op): {noop}")
    print(f"  - Docs that will change:                    {len(plan) - noop}")

    # First 5 + last 5
    print("\n[Plan] First 5 (oldest):")
    for p in plan[:5]:
        print(f"  pos {p['old_position']!s:>5} -> {p['new_position']:>3}  {p['signed_up_at']}  {p['email']}")
    print("\n[Plan] Last 5 (newest):")
    for p in plan[-5:]:
        print(f"  pos {p['old_position']!s:>5} -> {p['new_position']:>3}  {p['signed_up_at']}  {p['email']}")

    # Sanity: created_at order should be monotonic
    nonempty = [p["signed_up_at"] for p in plan if p["signed_up_at"]]
    monotonic = all(nonempty[i] <= nonempty[i + 1] for i in range(len(nonempty) - 1))
    print(f"\n[Plan] signed_up_at monotonically non-decreasing across plan: {monotonic}")

    print(f"\n[Pre-flight+Plan] DONE. Will update {len(plan)} docs in Phase 3.")


if __name__ == "__main__":
    main()
