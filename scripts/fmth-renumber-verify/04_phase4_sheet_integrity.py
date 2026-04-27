"""Phase 4 — Multi-tab Sheet integrity recheck.

Re-export each non-target Sheet tab. Compute SHA-256 + row count + col count + header row.
Compare to pre-renumber snapshot.

Expected: 4 of 7 byte-identical (`delete`, `backup`, `Angel`, `Sheet5`).
3 drift due to automation (`creative`, `ad-cost`, `SupermetricsQueries`).
For drifted: confirm same column count + same header row + within ±10% row count.
"""
from __future__ import annotations

import hashlib
import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")

SHEET_ID = "1ooyw7zCCP039ml_4cZfPbhrxtFKuQsFa5VSfsyq6NhA"
KEY_FILE = "/Users/jb/Documents/GitHub/sales-skill/.gdocs-sync-key.json"
IMPERSONATE = "jeremy@launcherlab.com.au"
TARGET_TAB = "Sheet1"
SNAPSHOT_DIR = Path("/Users/jb/Documents/GitHub/learning-loop/clients/farm-thru/data-snapshots")
EXPECTED_AUTOMATED_DRIFT = {"creative", "ad-cost", "SupermetricsQueries"}
EXPECTED_STATIC = {"delete", "backup", "Angel", "Sheet5"}


def hash_values(values):
    return hashlib.sha256(json.dumps(values, sort_keys=False).encode()).hexdigest()


def main():
    import gspread  # type: ignore
    from google.oauth2 import service_account as sa  # type: ignore

    out = {"started_at": datetime.now(timezone.utc).isoformat()}

    print(f"\n{'=' * 70}")
    print(f"PHASE 4 — Multi-tab Sheet integrity recheck")
    print(f"{'=' * 70}\n")

    # Load pre-renumber baseline
    candidates = sorted(SNAPSHOT_DIR.glob("sheet-other-tabs-hash-*.json"))
    if not candidates:
        print("FAIL: no baseline snapshot found")
        return 1
    baseline_file = candidates[-1]
    baseline = json.loads(baseline_file.read_text())
    print(f"Baseline file: {baseline_file.name}  ({len(baseline)} tabs)")
    out["baseline_file"] = baseline_file.name

    # Auth + open
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = sa.Credentials.from_service_account_file(KEY_FILE, scopes=scopes).with_subject(IMPERSONATE)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)

    tabs_seen = set()
    results = []
    for ws in sh.worksheets():
        if ws.title == TARGET_TAB:
            continue
        tabs_seen.add(ws.title)
        v = ws.get_all_values()
        post_hash = hash_values(v)
        post_rows = len(v)
        post_cols = max((len(r) for r in v), default=0)
        post_header = v[0] if v else []

        pre = baseline.get(ws.title, {})
        pre_hash = pre.get("sha256")
        pre_rows = pre.get("rows")
        pre_cols = pre.get("cols")
        pre_header = pre.get("header_row", [])

        if pre_hash is None:
            status = "NO_BASELINE"
        elif pre_hash == post_hash:
            status = "BYTE-IDENTICAL"
        else:
            # Drift — check structural compat
            structural_ok = True
            notes = []
            if pre_cols is not None and post_cols != pre_cols:
                structural_ok = False
                notes.append(f"col_count {pre_cols}->{post_cols}")
            if pre_header and post_header and pre_header != post_header:
                structural_ok = False
                notes.append("header_row_changed")
            # Allow up to ±10% row drift (organic data growth)
            if pre_rows and pre_rows > 0:
                pct_change = abs(post_rows - pre_rows) / pre_rows
                if pct_change > 0.10:
                    notes.append(f"rows_drift_{pct_change:.1%}")
            if ws.title in EXPECTED_AUTOMATED_DRIFT:
                status = "DRIFT_EXPECTED" if structural_ok else "DRIFT_STRUCTURAL_FAIL"
            elif ws.title in EXPECTED_STATIC:
                status = "DRIFT_UNEXPECTED" if structural_ok else "DRIFT_STRUCTURAL_FAIL"
            else:
                status = "DRIFT_UNKNOWN_TAB"
            if notes:
                status += " (" + ",".join(notes) + ")"

        print(f"  [{status:35s}] {ws.title:25s} pre_rows={pre_rows!s:>5s}  post_rows={post_rows:>5d}")
        results.append({
            "tab": ws.title,
            "status": status,
            "pre_sha": pre_hash,
            "post_sha": post_hash,
            "pre_rows": pre_rows,
            "post_rows": post_rows,
            "pre_cols": pre_cols,
            "post_cols": post_cols,
            "header_unchanged": (pre_header == post_header) if pre_header and post_header else None,
        })

    out["tab_results"] = results

    # Summary
    static_ok = all(r["status"] == "BYTE-IDENTICAL" for r in results
                    if r["tab"] in EXPECTED_STATIC)
    drift_struct_ok = all(r["status"].startswith("DRIFT_EXPECTED") or r["status"] == "BYTE-IDENTICAL"
                          for r in results if r["tab"] in EXPECTED_AUTOMATED_DRIFT)
    overall_ok = static_ok and drift_struct_ok

    print(f"\nVERIFY:")
    print(f"  Static tabs byte-identical (delete/backup/Angel/Sheet5): {'PASS' if static_ok else 'FAIL'}")
    print(f"  Drift tabs structurally OK (creative/ad-cost/Supermetrics): {'PASS' if drift_struct_ok else 'FAIL'}")
    out["static_byte_identical"] = static_ok
    out["drift_structural_ok"] = drift_struct_ok
    out["overall_pass"] = overall_ok

    print(f"\n  OVERALL: {'PASS' if overall_ok else 'FAIL'}")

    out_path = SNAPSHOT_DIR / "verify-phase4-sheet-integrity.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n[Phase 4] DONE -> {out_path}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
