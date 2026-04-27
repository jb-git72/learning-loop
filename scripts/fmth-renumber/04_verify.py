"""Phase 6: End-to-end verification (read-only).

- Spot-check 10 random docs: DB position vs Sheet1 position vs signed_up_at order
- Spot-check 3 reconciliation appends from prior cleanup (now should have early
  positions matching their signed_up_at):
    ant@antheawilliamson.com, tabandu@bigpond.com, test+20260425@example.com
- Hit live LP, confirm signupCount matches DB public count
- Confirm `is_test != True` query count
- Confirm 7 non-target Sheet tabs byte-identical to pre-renumber snapshot
- Confirm counter doc value
- Print any signup whose signed_up_at falls inside the renumber window
  (so audit doc can document race-window observers)
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROJECT = "launcher-lab-proposals"
SLUG = "fmth-ecb582"
SHEET_ID = "1ooyw7zCCP039ml_4cZfPbhrxtFKuQsFa5VSfsyq6NhA"
KEY_FILE = "/Users/jb/Documents/GitHub/sales-skill/.gdocs-sync-key.json"
IMPERSONATE = "jeremy@launcherlab.com.au"
TARGET_TAB = "Sheet1"
LP_URL = "https://join.farmthru.com.au/campaigns/fmth-ecb582/"
SNAPSHOT_DIR = Path("/Users/jb/Documents/GitHub/learning-loop/clients/farm-thru/data-snapshots")


def hash_values(values):
    return hashlib.sha256(json.dumps(values, sort_keys=False).encode()).hexdigest()


def fetch_lp_count():
    req = urllib.request.Request(LP_URL, headers={"User-Agent": "verify/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    matches = re.findall(r"signupCount[\"']?\s*[:=]\s*(\d+)", html)
    return int(matches[0]) if matches else None


def main():
    from google.cloud import firestore  # type: ignore
    import gspread  # type: ignore
    from google.oauth2 import service_account as sa  # type: ignore

    out = {"phases": {}}

    # ------ DB ------
    db = firestore.Client(project=PROJECT)
    coll = db.collection("campaigns").document(SLUG).collection("signups")
    docs = list(coll.stream())
    parsed = [{"_doc_id": d.id, **(d.to_dict() or {})} for d in docs]
    public = [r for r in parsed if not r.get("is_test")]
    is_test_true = sum(1 for r in parsed if r.get("is_test") is True)
    public_count = len(public)
    public_by_pos = sorted(public, key=lambda r: r.get("position") or 10**9)
    pos_values = [r.get("position") for r in public_by_pos]
    expected = list(range(1, public_count + 1))
    pos_ok = pos_values == expected

    counter_ref = (db.collection("campaigns").document(SLUG)
                   .collection("meta").document("counters"))
    counter_val = (counter_ref.get().to_dict() or {}).get("signup_count")

    print(f"[DB] total={len(parsed)}  public={public_count}  is_test=True={is_test_true}")
    print(f"[DB] positions 1..{public_count} contiguous? {pos_ok}")
    print(f"[DB] counter signup_count = {counter_val}  (next signup -> position {counter_val + 1 if counter_val is not None else '?'})")

    # ------ Sheet1 ------
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = sa.Credentials.from_service_account_file(KEY_FILE, scopes=scopes).with_subject(IMPERSONATE)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    target_ws = sh.worksheet(TARGET_TAB)
    sheet_values = target_ws.get_all_values()
    sheet_data = [r for r in sheet_values[1:] if any(c.strip() for c in r)]
    sheet_positions = [r[0] for r in sheet_data]
    sheet_emails = [(r[1] or "").strip().lower() for r in sheet_data]
    sheet_pos_ok = sheet_positions == [str(i) for i in range(1, public_count + 1)]

    print(f"\n[Sheet1] data rows={len(sheet_data)}  positions 1..{public_count} contiguous? {sheet_pos_ok}")

    # ------ LP ------
    lp_count = fetch_lp_count()
    print(f"\n[LP] signupCount = {lp_count}")
    triple_ok = (public_count == len(sheet_data) == lp_count)
    print(f"[Triple-match] DB({public_count}) == Sheet1({len(sheet_data)}) == LP({lp_count}) ? {triple_ok}")

    out["phases"]["counts"] = {
        "db_total": len(parsed),
        "db_public": public_count,
        "db_is_test": is_test_true,
        "sheet1_data_rows": len(sheet_data),
        "lp_signup_count": lp_count,
        "counter_signup_count": counter_val,
        "db_pos_contiguous": pos_ok,
        "sheet_pos_contiguous": sheet_pos_ok,
        "triple_match": triple_ok,
    }

    # ------ Spot-check 10 random ------
    print(f"\n[Spot-check] 10 random docs:")
    rng = random.Random(7)
    sample = rng.sample(public_by_pos, min(10, len(public_by_pos)))
    sheet_email_to_pos = {e: int(p) for p, e in zip(sheet_positions, sheet_emails) if p.isdigit()}
    spot = []
    for r in sample:
        e = (r.get("email") or "").strip().lower()
        db_pos = r.get("position")
        sheet_pos = sheet_email_to_pos.get(e)
        ok = (db_pos == sheet_pos)
        flag = "ok" if ok else "FAIL"
        print(f"  [{flag}] {e:40s}  db_pos={db_pos!s:>5s}  sheet_pos={sheet_pos!s:>5s}  signed_up_at={r.get('signed_up_at','')[:25]}")
        spot.append({"email": e, "db_pos": db_pos, "sheet_pos": sheet_pos, "ok": ok})
    out["phases"]["spot_check_10"] = spot

    # ------ Reconciliation appends ------
    print(f"\n[Spot-check] 3 reconciliation appends from prior cleanup:")
    recon_emails = ["ant@antheawilliamson.com", "tabandu@bigpond.com", "test+20260425@example.com"]
    db_by_email = {(r.get("email") or "").strip().lower(): r for r in parsed}
    recon_status = []
    for e in recon_emails:
        rec = db_by_email.get(e)
        if not rec:
            print(f"  [MISS] {e:40s} not in DB")
            recon_status.append({"email": e, "in_db": False})
            continue
        db_pos = rec.get("position")
        is_test = rec.get("is_test")
        sheet_pos = sheet_email_to_pos.get(e)
        signed = rec.get("signed_up_at", "")
        # Public reconciliation appends should now have positions matching signed_up_at order
        # (i.e., their NEW position should be in early-middle of the 1..N range,
        # not stuck at the bottom). The is_test=True one (test+20260425@example.com) is NOT in Sheet1.
        if is_test is True:
            note = "is_test=True (excluded from Sheet1)"
        elif sheet_pos == db_pos:
            note = "OK (DB == Sheet1)"
        else:
            note = f"MISMATCH (DB={db_pos} Sheet1={sheet_pos})"
        print(f"  {e:40s}  db_pos={db_pos!s:>5s}  sheet_pos={sheet_pos!s:>5s}  is_test={is_test!s:6s}  signed_up_at={signed[:25]}  {note}")
        recon_status.append({
            "email": e, "in_db": True, "db_pos": db_pos, "sheet_pos": sheet_pos,
            "is_test": is_test, "signed_up_at": signed, "note": note,
        })
    out["phases"]["reconciliation_appends"] = recon_status

    # ------ Non-target tab byte-identity ------
    print(f"\n[Multi-tab safety] checking other tabs byte-identical to pre-renumber snapshot:")
    # Find the latest pre-renumber other-tabs hash file
    candidates = sorted(SNAPSHOT_DIR.glob("sheet-other-tabs-hash-*.json"))
    if not candidates:
        print(f"  [WARN] no pre-renumber other-tab hash file found — skipping byte-identity check")
        out["phases"]["multi_tab_safety"] = {"status": "no_baseline"}
    else:
        baseline = json.loads(candidates[-1].read_text())
        print(f"  baseline file: {candidates[-1].name}  ({len(baseline)} tabs)")
        tab_results = []
        for ws in sh.worksheets():
            if ws.title == TARGET_TAB:
                continue
            v = ws.get_all_values()
            post_hash = hash_values(v)
            pre = baseline.get(ws.title, {})
            pre_hash = pre.get("sha256")
            if pre_hash is None:
                status = "NO_BASELINE"
            elif pre_hash == post_hash:
                status = "BYTE-IDENTICAL"
            else:
                status = "DRIFT"
            print(f"  [{status:14s}] {ws.title:25s} pre={pre_hash[:12] if pre_hash else 'n/a':12s}  post={post_hash[:12]}")
            tab_results.append({
                "tab": ws.title, "status": status,
                "pre_sha": pre_hash, "post_sha": post_hash,
                "pre_rows": pre.get("rows"), "post_rows": len(v),
            })
        out["phases"]["multi_tab_safety"] = tab_results

    # ------ Race window: docs with signed_up_at after pre-renumber snapshot ------
    # Find latest signups-pre-renumber snapshot
    snap_candidates = sorted(SNAPSHOT_DIR.glob("signups-pre-renumber-*.jsonl"))
    if snap_candidates:
        # Get the EARLIEST snapshot (start of run); not the latest
        earliest = snap_candidates[0]
        print(f"\n[Race window] earliest pre-renumber snapshot: {earliest.name}")
        with earliest.open() as f:
            snap = [json.loads(line) for line in f]
        snap_emails = {(r.get("email") or "").strip().lower() for r in snap if r.get("email")}
        new_arrivals = [r for r in public if (r.get("email") or "").strip().lower() not in snap_emails]
        if new_arrivals:
            print(f"  {len(new_arrivals)} new public signups arrived during the renumber:")
            for r in sorted(new_arrivals, key=lambda x: x.get("signed_up_at", "")):
                print(f"    {r.get('signed_up_at','')[:25]:25s}  pos={r.get('position'):>3}  {r.get('email')}")
        else:
            print(f"  No new public signups arrived during the renumber window")
        out["phases"]["race_window"] = {
            "snapshot_file": earliest.name,
            "new_arrivals_count": len(new_arrivals),
            "new_arrivals": [{"email": (r.get("email") or "").strip().lower(),
                              "signed_up_at": r.get("signed_up_at"),
                              "position": r.get("position")} for r in new_arrivals],
        }

    # ------ Summary ------
    print(f"\n{'=' * 70}\nFINAL VERIFICATION SUMMARY\n{'=' * 70}")
    all_ok = (pos_ok and sheet_pos_ok and triple_ok
              and counter_val == public_count
              and all(s["ok"] for s in spot))
    print(f"  Triple match (DB == Sheet1 == LP): {triple_ok}")
    print(f"  DB positions 1..N contiguous:      {pos_ok}")
    print(f"  Sheet1 positions 1..N contiguous:  {sheet_pos_ok}")
    print(f"  Counter == public count:           {counter_val == public_count}  ({counter_val} vs {public_count})")
    print(f"  All 10 spot-checks pass:           {all(s['ok'] for s in spot)}")
    print(f"\n  OVERALL: {'PASS' if all_ok else 'FAIL'}")
    out["overall_pass"] = all_ok

    out_path = SNAPSHOT_DIR / "renumber-verify-result.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n[Verify] DONE -> {out_path}")


if __name__ == "__main__":
    main()
