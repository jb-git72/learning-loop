"""Phase 3 — Wait + observe organic signups (~5 min window).

Records DB state at T0, sleeps 5 min, records state at T1. Lists any new
non-test arrivals during the window and verifies their positions are
sequential starting from (counter_at_T0 + 1).
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")

PROJECT = "launcher-lab-proposals"
SLUG = "fmth-ecb582"
SNAPSHOT_DIR = Path("/Users/jb/Documents/GitHub/learning-loop/clients/farm-thru/data-snapshots")
WAIT_SECONDS = 300  # 5 min


def db_state(db):
    coll = db.collection("campaigns").document(SLUG).collection("signups")
    docs = list(coll.stream())
    parsed = [{"_doc_id": d.id, **(d.to_dict() or {})} for d in docs]
    public = [r for r in parsed if r.get("is_test") is not True]
    counter_ref = (db.collection("campaigns").document(SLUG)
                   .collection("meta").document("counters"))
    counter_val = (counter_ref.get().to_dict() or {}).get("signup_count")
    return parsed, public, counter_val


def main():
    from google.cloud import firestore  # type: ignore

    out = {"started_at": datetime.now(timezone.utc).isoformat(),
           "wait_seconds": WAIT_SECONDS}
    db = firestore.Client(project=PROJECT)

    print(f"\n{'=' * 70}")
    print(f"PHASE 3 — Observation window ({WAIT_SECONDS}s)")
    print(f"{'=' * 70}\n")

    pre_parsed, pre_public, pre_counter = db_state(db)
    pre_emails = {(r.get("email") or "").lower() for r in pre_parsed}
    pre_max_public_pos = max((r.get("position") or 0) for r in pre_public)
    print(f"T0 ({datetime.now(timezone.utc).isoformat()}):")
    print(f"  DB total: {len(pre_parsed)}")
    print(f"  DB public: {len(pre_public)}")
    print(f"  Counter: {pre_counter}")
    print(f"  Max public position: {pre_max_public_pos}")
    out["pre"] = {
        "db_total": len(pre_parsed),
        "db_public": len(pre_public),
        "counter": pre_counter,
        "max_public_position": pre_max_public_pos,
    }

    print(f"\nSleeping {WAIT_SECONDS}s ({WAIT_SECONDS // 60} min)...")
    time.sleep(WAIT_SECONDS)

    post_parsed, post_public, post_counter = db_state(db)
    post_emails = {(r.get("email") or "").lower() for r in post_parsed}
    post_max_public_pos = max((r.get("position") or 0) for r in post_public)
    print(f"\nT1 ({datetime.now(timezone.utc).isoformat()}):")
    print(f"  DB total: {len(post_parsed)} (delta {len(post_parsed) - len(pre_parsed)})")
    print(f"  DB public: {len(post_public)} (delta {len(post_public) - len(pre_public)})")
    print(f"  Counter: {post_counter} (delta {post_counter - pre_counter})")
    print(f"  Max public position: {post_max_public_pos} (delta {post_max_public_pos - pre_max_public_pos})")
    out["post"] = {
        "db_total": len(post_parsed),
        "db_public": len(post_public),
        "counter": post_counter,
        "max_public_position": post_max_public_pos,
    }

    new_emails = post_emails - pre_emails
    new_arrivals = []
    for r in post_parsed:
        e = (r.get("email") or "").lower()
        if e in new_emails:
            new_arrivals.append({
                "email": e,
                "position": r.get("position"),
                "is_test": r.get("is_test"),
                "signed_up_at": r.get("signed_up_at"),
            })
    new_arrivals.sort(key=lambda x: x.get("signed_up_at") or "")

    print(f"\nNEW arrivals during window: {len(new_arrivals)}")
    for r in new_arrivals:
        print(f"  pos={r['position']:>4}  is_test={r['is_test']!s:6s}  {r['email']}  @ {r['signed_up_at'][:25] if r['signed_up_at'] else 'NONE'}")

    public_arrivals = [r for r in new_arrivals if r.get("is_test") is not True]
    test_arrivals = [r for r in new_arrivals if r.get("is_test") is True]

    # Verify: public arrivals' positions are sequential starting from pre_max_public_pos + 1?
    # Note: their positions in the field reflect counter values, NOT necessarily
    # consecutive within the public set — because test signups in between also
    # bump the counter. So check: public arrivals' positions strictly increasing
    # AND public arrivals fill into the new contiguous public range.
    contiguity_ok = True
    contiguity_notes = []
    if public_arrivals:
        sorted_by_time = sorted(public_arrivals, key=lambda x: x.get("signed_up_at") or "")
        prior_max = pre_max_public_pos
        for r in sorted_by_time:
            # The position should be >= prior_max + 1 (could be higher if test signups landed in between)
            if r["position"] is None or r["position"] <= prior_max:
                contiguity_ok = False
                contiguity_notes.append(f"{r['email']} pos={r['position']} <= prior_max {prior_max}")
            prior_max = r["position"]

    # Also check: the new max public position should equal pre_max + len(public_arrivals)
    # IF there were no test signups that also got positions in between
    expected_post_max = pre_max_public_pos + len(public_arrivals) + len(test_arrivals)
    # Actually, post_max_public_pos can be < this if test signups got positions >= public arrivals
    # Just check: post_max >= pre_max + len(public_arrivals)
    expected_min_post_max = pre_max_public_pos + len(public_arrivals)

    print(f"\nVERIFY:")
    print(f"  Public arrivals: {len(public_arrivals)}")
    print(f"  Test arrivals:   {len(test_arrivals)}")
    print(f"  Public positions strictly increasing in time-order: {'PASS' if contiguity_ok else 'FAIL'}")
    if contiguity_notes:
        for n in contiguity_notes:
            print(f"    {n}")

    out["new_arrivals_during_window"] = new_arrivals
    out["public_arrivals"] = public_arrivals
    out["test_arrivals"] = test_arrivals
    out["contiguity_ok"] = contiguity_ok
    out["contiguity_notes"] = contiguity_notes

    # Final position contiguity recheck
    public_positions = sorted(r.get("position") for r in post_public if r.get("position") is not None)
    expected = list(range(1, len(post_public) + 1))
    contiguous_after = (public_positions == expected)
    print(f"\n  Final DB public positions contiguous 1..{len(post_public)}: {'PASS' if contiguous_after else 'FAIL'}")
    if not contiguous_after:
        gaps = sorted(set(expected) - set(public_positions))
        print(f"    GAPS: {gaps[:10]}")
        out["final_pos_gaps"] = gaps
    out["contiguous_after"] = contiguous_after

    all_pass = contiguity_ok and contiguous_after
    out["overall_pass"] = all_pass
    print(f"\n  OVERALL: {'PASS' if all_pass else 'FAIL'}")

    out_path = SNAPSHOT_DIR / "verify-phase3-observation.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n[Phase 3] DONE -> {out_path}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
