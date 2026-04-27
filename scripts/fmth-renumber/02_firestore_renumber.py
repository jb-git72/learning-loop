"""Phase 3 + 3.5: Firestore renumber with race convergence + counter reset.

Convergence loop (up to 5 iterations):
1. Read all signups, count public (is_test != True) = N
2. Sort public by signed_up_at ASC, build position assignments 1..N
3. Compute diff vs current positions (skip no-ops)
4. Apply batched updates (100/batch, position field only)
5. Re-read DB, count public again
6. If count == N (no new signups landed): converged, exit loop
7. If count > N: re-loop (new public signups got high positions, fold them in)
8. If iteration > 5: ABORT and report

Then Phase 3.5: Atomically set the counter doc `signup_count` to N (= final
public count), so the NEXT add_signup() Increment(1) yields position N+1.

Verifies:
- positions are exactly 1..N contiguous
- counter doc reads N
- spot-checks 5 random docs

Writes:
- /tmp/renumber-plan.json (final plan used)
- data-snapshots/renumber-phase3-result.json
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT = "launcher-lab-proposals"
SLUG = "fmth-ecb582"
PLAN_PATH = Path("/tmp/renumber-plan.json")
SNAPSHOT_DIR = Path("/Users/jb/Documents/GitHub/learning-loop/clients/farm-thru/data-snapshots")
BATCH_SIZE = 100
MAX_DOCS = 200
MAX_ITER = 5


def fetch_signups(coll):
    docs = list(coll.stream())
    parsed = []
    for d in docs:
        data = d.to_dict() or {}
        data["_doc_id"] = d.id
        data["_ref"] = d.reference
        parsed.append(data)
    public = [r for r in parsed if not r.get("is_test")]
    return parsed, public


def build_plan(public):
    def sort_key(r):
        return r.get("signed_up_at") or ""

    public_sorted = sorted(public, key=sort_key)
    plan = []
    for new_pos, r in enumerate(public_sorted, start=1):
        plan.append({
            "doc_id": r["_doc_id"],
            "_ref": r["_ref"],
            "email": (r.get("email") or "").strip().lower(),
            "signed_up_at": r.get("signed_up_at"),
            "old_position": r.get("position"),
            "new_position": new_pos,
        })
    return plan


def apply_plan(db, plan):
    """Apply only the entries where old != new (skip no-ops)."""
    updates = [p for p in plan if p["old_position"] != p["new_position"]]
    print(f"  [Apply] {len(updates)} updates needed (skipping {len(plan) - len(updates)} no-ops)")
    if not updates:
        return 0

    total = 0
    for chunk_start in range(0, len(updates), BATCH_SIZE):
        chunk = updates[chunk_start:chunk_start + BATCH_SIZE]
        batch = db.batch()
        for entry in chunk:
            batch.update(entry["_ref"], {"position": entry["new_position"]})
        batch.commit()
        total += len(chunk)
    print(f"  [Apply] committed {total} updates in {(len(updates) + BATCH_SIZE - 1) // BATCH_SIZE} batches")
    return total


def main():
    from google.cloud import firestore  # type: ignore

    db = firestore.Client(project=PROJECT)
    coll = db.collection("campaigns").document(SLUG).collection("signups")
    counter_ref = (db.collection("campaigns").document(SLUG)
                   .collection("meta").document("counters"))

    # --- Read counter doc pre-state ---
    counter_pre = counter_ref.get().to_dict() if counter_ref.get().exists else {}
    counter_pre_value = counter_pre.get("signup_count")
    print(f"[Counter] pre-state: signup_count = {counter_pre_value}")

    # --- Convergence loop ---
    iterations = []
    final_plan = None
    for i in range(1, MAX_ITER + 1):
        print(f"\n[Iter {i}/{MAX_ITER}] reading DB ...")
        all_docs, public = fetch_signups(coll)
        n_pub = len(public)
        print(f"  total={len(all_docs)}  public={n_pub}")
        if n_pub > MAX_DOCS:
            sys.exit(f"[ABORT] public count {n_pub} > safety cap {MAX_DOCS}")

        plan = build_plan(public)
        # Sanity: monotonic
        ts = [p["signed_up_at"] for p in plan if p["signed_up_at"]]
        mono = all(ts[k] <= ts[k + 1] for k in range(len(ts) - 1))
        if not mono:
            sys.exit("[ABORT] signed_up_at not monotonic in plan")

        applied = apply_plan(db, plan)
        # Re-read AFTER apply
        _, public_after = fetch_signups(coll)
        n_after = len(public_after)
        print(f"  post-apply public count = {n_after}")
        iterations.append({
            "iter": i,
            "public_pre_apply": n_pub,
            "applied_updates": applied,
            "public_post_apply": n_after,
            "stable": n_after == n_pub,
        })
        if n_after == n_pub:
            print(f"  [CONVERGED] iter {i}: count stable at {n_after}")
            final_plan = plan
            break
        delta = n_after - n_pub
        print(f"  [NOT CONVERGED] +{delta} new public signups during apply — re-iterating")
    else:
        sys.exit(f"[ABORT] did not converge in {MAX_ITER} iterations. "
                 "Pause LP signups + retry, or accept transient inconsistency.")

    if final_plan is None:
        sys.exit("[ABORT] convergence failed")

    N = len(final_plan)
    print(f"\n[Renumber] DONE. N = {N}")

    # --- Persist final plan ---
    plan_export = [
        {k: v for k, v in p.items() if k != "_ref"}
        for p in final_plan
    ]
    PLAN_PATH.write_text(json.dumps(plan_export, indent=2, default=str))
    print(f"[Renumber] final plan -> {PLAN_PATH}")

    # --- Verify positions ---
    plan_doc_ids = {p["doc_id"] for p in final_plan}
    _, public_final = fetch_signups(coll)
    pos_values = sorted(
        (r.get("position") for r in public_final if r["_doc_id"] in plan_doc_ids and r.get("position") is not None)
    )
    expected = list(range(1, N + 1))
    if pos_values == expected:
        print(f"[Verify] OK: plan-doc positions = 1..{N} contiguous, no gaps, no duplicates")
    else:
        dupes = sorted({p for p in pos_values if pos_values.count(p) > 1})
        gaps = sorted(set(expected) - set(pos_values))
        extras = sorted(set(pos_values) - set(expected))
        print(f"[Verify] FAIL: positions != 1..{N}")
        print(f"   duplicates: {dupes[:10]}")
        print(f"   gaps:       {gaps[:10]}")
        print(f"   extras:     {extras[:10]}")
        sys.exit(4)

    # --- Phase 3.5: Reset counter ---
    print(f"\n[Counter] Phase 3.5: setting signup_count = {N}  (was {counter_pre_value})")
    # Use Set with merge=True to overwrite signup_count without disturbing other fields
    counter_ref.set({"signup_count": N}, merge=True)
    counter_post = counter_ref.get().to_dict()
    counter_post_value = counter_post.get("signup_count")
    if counter_post_value != N:
        sys.exit(f"[ABORT] counter post-write = {counter_post_value} != {N}")
    print(f"[Counter] OK: signup_count = {counter_post_value}  (next signup will get position {N + 1})")

    # --- Spot-check 5 random ---
    print(f"\n[Verify] Spot-check 5 random:")
    rng = random.Random(42)
    for entry in rng.sample(final_plan, min(5, len(final_plan))):
        doc = coll.document(entry["doc_id"]).get()
        post_data = doc.to_dict() or {}
        actual = post_data.get("position")
        flag = "ok" if actual == entry["new_position"] else "FAIL"
        print(f"  [{flag}] {entry['email']:40s} expected={entry['new_position']:3d}  actual={actual!s:>5s}")

    # --- Persist ---
    stamp = datetime.now(timezone.utc).isoformat()
    result = {
        "stamp_utc": stamp,
        "N_final": N,
        "iterations": iterations,
        "counter_pre": counter_pre_value,
        "counter_post": counter_post_value,
        "old_positions": {
            "min": min((p["old_position"] for p in final_plan if p["old_position"] is not None), default=None),
            "max": max((p["old_position"] for p in final_plan if p["old_position"] is not None), default=None),
        },
        "new_positions": {"min": 1, "max": N},
    }
    out = SNAPSHOT_DIR / "renumber-phase3-result.json"
    out.write_text(json.dumps(result, indent=2, default=str))
    print(f"\n[Phase 3+3.5] DONE -> {out}")


if __name__ == "__main__":
    main()
