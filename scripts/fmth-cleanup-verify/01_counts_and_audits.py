"""Independent verification — Phase 2 (counts) + Phase 3 (sample audits) + Phase 4 (sheet integrity).

Re-derives every count from scratch. Spot-checks 10 deleted emails (should be GONE)
+ 10 legit emails (should be PRESENT). Hashes every non-target Sheet tab pre/post
the prior agent's run via the snapshot CSVs, and verifies the live Sheet1 state.

Read-only. Does not mutate Firestore or any Sheet tab.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import re
import sys
import urllib.request
from pathlib import Path

# --- constants ---
PROJECT = "launcher-lab-proposals"
SLUG = "fmth-ecb582"
SHEET_ID = "1ooyw7zCCP039ml_4cZfPbhrxtFKuQsFa5VSfsyq6NhA"
KEY_FILE = "/Users/jb/Documents/GitHub/sales-skill/.gdocs-sync-key.json"
IMPERSONATE = "jeremy@launcherlab.com.au"
SNAPSHOT_DIR = Path("/Users/jb/Documents/GitHub/learning-loop/clients/farm-thru/data-snapshots")
CSV_PATH = "/Users/jb/Downloads/CFE Signups - FarmThru - delete.csv"
LP_URL = "https://join.farmthru.com.au/campaigns/fmth-ecb582/"
SCRIPT_DIR_NAME = "_TEST_EMAIL_PATTERNS"

# Mirror of campaign_store._TEST_EMAIL_PATTERNS so this script is self-contained.
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


def load_csv_emails() -> set[str]:
    out: set[str] = set()
    with open(CSV_PATH, newline="") as f:
        for row in csv.reader(f):
            if len(row) < 2:
                continue
            e = row[1].strip().lower()
            if "@" in e:
                out.add(e)
    return out


def fetch_lp_count() -> tuple[int | None, str]:
    req = urllib.request.Request(LP_URL, headers={"User-Agent": "verify/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return None, f"fetch error: {exc}"
    # The LP renders signupCount into JS CONFIG; also rendered into text.
    matches = re.findall(r"signupCount[\"']?\s*[:=]\s*(\d+)", html)
    if not matches:
        # Fallback: any "X people" pattern near top
        m2 = re.findall(r"(\d{2,4})\s+(?:Australians|people|members|on the waitlist)", html)
        if m2:
            return int(m2[0]), "matched 'X Australians/people/members/on the waitlist'"
        return None, "no signupCount found"
    return int(matches[0]), f"matched signupCount={matches[0]}"


def main():
    out: dict = {"phases": {}}
    print("=" * 70)
    print("PHASE 2 — Independent count check")
    print("=" * 70)

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

    is_test_field_true = sum(1 for r in parsed if r.get("is_test") is True)
    public_count = sum(1 for r in parsed if not r.get("is_test"))

    counter_doc = (
        db.collection("campaigns").document(SLUG)
        .collection("meta").document("counters").get()
    )
    counter_val = (counter_doc.to_dict() or {}).get("signup_count") if counter_doc.exists else None

    # Sheet1
    import gspread  # type: ignore
    from google.oauth2 import service_account as sa  # type: ignore

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = sa.Credentials.from_service_account_file(KEY_FILE, scopes=scopes).with_subject(IMPERSONATE)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    ws_sheet1 = sh.worksheet("Sheet1")
    sheet1_rows = ws_sheet1.get_all_values()
    sheet1_data_count = len(sheet1_rows) - 1  # exclude header

    lp_count, lp_note = fetch_lp_count()

    counts = {
        "DB total signups (Firestore)": fs_total,
        "DB public (is_test != True)": public_count,
        "DB is_test=True": is_test_field_true,
        "Sheet1 data rows (excl header)": sheet1_data_count,
        f"Live LP signupCount ({LP_URL})": lp_count,
        "meta/counters.signup_count": counter_val,
    }
    print()
    for k, v in counts.items():
        print(f"  {k:50s} = {v}")
    print()
    print(f"  LP fetch note: {lp_note}")

    # Acceptance checks
    sumcheck = (public_count + is_test_field_true) == fs_total
    triple_match = (public_count == sheet1_data_count == lp_count)
    counter_match = (counter_val == fs_total)

    print(f"\n  ACCEPTANCE: DB total == public + is_test → {sumcheck}")
    print(f"  ACCEPTANCE: public == Sheet1 == LP        → {triple_match} ({public_count} / {sheet1_data_count} / {lp_count})")
    print(f"  ACCEPTANCE: counter_doc == DB total       → {counter_match} ({counter_val} / {fs_total})")

    out["phases"]["2_counts"] = {
        "counts": counts,
        "lp_note": lp_note,
        "sumcheck_db_total_eq_public_plus_test": sumcheck,
        "triple_match_public_sheet_lp": triple_match,
        "counter_eq_db_total": counter_match,
    }

    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("PHASE 3a — Random 10 from CSV-delete-set should be GONE from DB")
    print("=" * 70)
    csv_emails = load_csv_emails()
    delete_result = json.loads((SNAPSHOT_DIR / "db-delete-result-20260427T094109Z.json").read_text())
    db_deleted_set = set(delete_result["deleted_emails"])
    print(f"  CSV unique emails: {len(csv_emails)}")
    print(f"  Prior-agent reported 32 deletes from DB; sampling 10 of those.")

    rng = random.Random(42)  # deterministic
    db_emails_now = {(r.get("email", "") or "").strip().lower() for r in parsed}
    sample_deleted = rng.sample(sorted(db_deleted_set), min(10, len(db_deleted_set)))
    deleted_check = []
    for e in sample_deleted:
        present = e in db_emails_now
        deleted_check.append({"email": e, "present_in_db_now": present, "expected": False})
        flag = "FAIL" if present else "ok"
        print(f"  [{flag}] {e:55s} present={present}")
    out["phases"]["3a_deleted_sample"] = deleted_check

    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("PHASE 3b — Random 10 legit emails should be PRESENT + INTACT")
    print("=" * 70)
    legit_records = [
        r for r in parsed
        if r.get("email") and not is_test_email(r.get("email", ""))
    ]
    print(f"  Total non-test-pattern emails in DB: {len(legit_records)}")
    sample_legit = rng.sample(legit_records, min(10, len(legit_records)))
    sheet1_emails_now = {(r[1] or "").strip().lower() for r in sheet1_rows[1:] if len(r) >= 2}
    legit_check = []
    for r in sample_legit:
        e = r["email"].strip().lower()
        in_sheet = e in sheet1_emails_now
        is_test_field = r.get("is_test")
        ok = (is_test_field in (False, None)) and in_sheet
        legit_check.append({
            "email": e,
            "is_test_field": is_test_field,
            "in_sheet1": in_sheet,
            "ok": ok,
        })
        flag = "ok" if ok else "FAIL"
        print(f"  [{flag}] {e:55s} is_test={is_test_field!s:6s} in_sheet={in_sheet}")
    out["phases"]["3b_legit_sample"] = legit_check

    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("PHASE 3c — Historical missing-is_test stragglers")
    print("=" * 70)
    stragglers = [
        "jeremy+viptest1@launcherlab.com.au",
        "jeremy+test1@launcherlab.com.au",
        "test+20260425@example.com",
        "jeremy+fmth-test@launcherlab.com.au",
    ]
    straggler_status = []
    db_by_email = {(r.get("email", "") or "").strip().lower(): r for r in parsed}
    for e in stragglers:
        rec = db_by_email.get(e.lower())
        exists = rec is not None
        is_test_field = rec.get("is_test") if rec else None
        regex_says_test = is_test_email(e)
        straggler_status.append({
            "email": e,
            "exists_in_db": exists,
            "is_test_field": is_test_field,
            "is_test_email_regex": regex_says_test,
            "_doc_id": rec.get("_doc_id") if rec else None,
        })
        print(f"  {e:50s} exists={exists}  is_test_field={is_test_field!s:6s}  regex_says_test={regex_says_test}")
    out["phases"]["3c_stragglers"] = straggler_status

    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("PHASE 4 — Sheet integrity (multi-tab safety)")
    print("=" * 70)

    # Load every snapshot CSV, hash, fetch live, hash, compare
    tab_files = {
        "Angel": "sheet-pre-cleanup-20260427T094106Z-tab-Angel.csv",
        "backup": "sheet-pre-cleanup-20260427T094106Z-tab-backup.csv",
        "creative": "sheet-pre-cleanup-20260427T094106Z-tab-creative.csv",
        "delete": "sheet-pre-cleanup-20260427T094106Z-tab-delete.csv",
        "Sheet5": "sheet-pre-cleanup-20260427T094106Z-tab-Sheet5.csv",
        "SupermetricsQueries": "sheet-pre-cleanup-20260427T094106Z-tab-SupermetricsQueries.csv",
        # Note: ad-cost backup file uses underscored name (per dir listing)
        "ad-cost": "sheet-pre-cleanup-20260427T094106Z-tab-ad_cost.csv",
    }

    def hash_values(values):
        return hashlib.sha256(json.dumps(values, sort_keys=False).encode()).hexdigest()

    def hash_csv(path: Path) -> tuple[str, list[list[str]]]:
        with open(path, newline="") as f:
            reader = csv.reader(f)
            rows = [r for r in reader]
        return hash_values(rows), rows

    tab_results = []
    for tab_name, fname in tab_files.items():
        snap_path = SNAPSHOT_DIR / fname
        if not snap_path.is_file():
            print(f"  [MISS] snapshot for {tab_name}: {fname} not found")
            tab_results.append({"tab": tab_name, "status": "MISSING_SNAPSHOT"})
            continue
        snap_hash, snap_rows = hash_csv(snap_path)
        try:
            ws = sh.worksheet(tab_name)
        except gspread.WorksheetNotFound:  # type: ignore
            print(f"  [MISS] tab {tab_name} not found in live sheet")
            tab_results.append({"tab": tab_name, "status": "TAB_MISSING_LIVE"})
            continue
        live_values = ws.get_all_values()
        live_hash = hash_values(live_values)
        match = (snap_hash == live_hash)
        flag = "BYTE-IDENTICAL" if match else "DRIFT"
        print(f"  [{flag}] {tab_name:25s} snap_rows={len(snap_rows):4d} live_rows={len(live_values):4d}  "
              f"snap_sha={snap_hash[:12]} live_sha={live_hash[:12]}")
        tab_results.append({
            "tab": tab_name,
            "status": flag,
            "snap_rows": len(snap_rows),
            "live_rows": len(live_values),
            "snap_sha": snap_hash,
            "live_sha": live_hash,
        })
    out["phases"]["4_sheet_integrity"] = tab_results

    # Sheet1 reconciliation appends
    print("\n  --- Sheet1 reconciliation appends ---")
    recon_emails = ["ant@antheawilliamson.com", "tabandu@bigpond.com", "test+20260425@example.com"]
    recon_check = []
    for e in recon_emails:
        present = e in sheet1_emails_now
        flag = "ok" if present else "FAIL"
        print(f"  [{flag}] {e:50s} present in Sheet1 = {present}")
        recon_check.append({"email": e, "in_sheet1": present})
    out["phases"]["4b_recon_appends"] = recon_check

    # No deleted emails in Sheet1
    leaked = sheet1_emails_now & db_deleted_set
    print(f"\n  Sheet1 vs deleted-set overlap: {len(leaked)} (expected 0)")
    if leaked:
        for e in sorted(leaked):
            print(f"    LEAK: {e}")
    out["phases"]["4c_sheet1_leak"] = {"count": len(leaked), "emails": sorted(leaked)}

    # ------------------------------------------------------------------
    # Persist
    result_path = SNAPSHOT_DIR / "verify-phase2to4-result.json"
    result_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n[Done] result -> {result_path}")


if __name__ == "__main__":
    main()
