#!/usr/bin/env python3
"""A/B test: three chained evolution approaches for landing pages.

Tests whether chaining crossover + mutation in the same generation
produces better landing pages than plain crossover alone.

Approach A (baseline):  Plain crossover — 1 API call
Approach B (combo):     Crossover with mutated hook in same prompt — 1 API call
Approach C (chain):     Crossover first, then mutate result — 2 API calls

Usage:
  python3 scripts/test_chained_evolution.py
"""

import json
import os
import random
import sys
import time
from pathlib import Path

root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

# Load .env
env_path = root / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

from engine.scorer import load_client, score_ad
from writer import generate_variant, HOOK_TEMPLATES, HOOK_METADATA
from scripts.hill_climb import _pick_mutated_hook, _load_industry_playbook

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

TARGET_LPS = ["LP-A", "LP-F", "LP-D", "LP-P"]
CANDIDATES_PER_APPROACH = 2
CLIENT_SLUG = "farm-thru"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_all_ads(client_dir: Path) -> list:
    """Load all content files for the existing_ads parameter."""
    all_ads = []
    for subdir in ["meta-ads", "landing-pages", "emails"]:
        content_dir = client_dir / "loop" / subdir
        if content_dir.exists():
            for f in sorted(content_dir.iterdir()):
                if f.suffix == ".json" and f.name not in ("test-ad.json", "review-batch.json"):
                    with open(f) as fh:
                        all_ads.append(json.load(fh))
    return all_ads


def pick_donor(scored_lps: list, current_page_id: str) -> dict:
    """Pick the highest-scoring LP that isn't the current one."""
    candidates = [
        item for item in scored_lps
        if item["ad"]["page_id"] != current_page_id
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[0]["ad"]


def generate_and_score(ad, client, client_dir, shared_dir, all_ads,
                       mode, hook_type, donor_ad, label):
    """Generate one candidate and score it. Returns (score, report, new_ad, label) or None."""
    try:
        new_ad = generate_variant(
            angle=ad.get("angle", "quality-craft"),
            tactic=ad.get("tactic", "general"),
            hook_type=hook_type,
            funnel=ad.get("funnel", "TOF"),
            client_dir=client_dir,
            current_best=ad,
            recent_failures=None,
            content_type="landing-page",
            mode=mode,
            donor_ad=donor_ad,
            weak_dimensions=None,
        )
        # Preserve page_id
        new_ad["page_id"] = ad["page_id"]

        report = score_ad(new_ad, client, existing_ads=all_ads, use_llm=True)
        return {
            "score": report["composite"],
            "verdict": report["verdict"],
            "ad": new_ad,
            "label": label,
        }
    except Exception as e:
        print(f"      ERROR ({label}): {e}")
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    client_dir = root / "clients" / CLIENT_SLUG
    shared_dir = root / "shared"
    client = load_client(client_dir, shared_dir)
    playbook = _load_industry_playbook(client_dir)

    all_ads = load_all_ads(client_dir)

    # Load and score all LPs to find donors + baselines
    lp_dir = client_dir / "loop" / "landing-pages"
    all_lp_items = []
    for f in sorted(lp_dir.iterdir()):
        if f.suffix == ".json" and f.name not in ("test-ad.json", "review-batch.json"):
            with open(f) as fh:
                ad = json.load(fh)
            report = score_ad(ad, client, existing_ads=all_ads, use_llm=True)
            all_lp_items.append({
                "ad": ad,
                "score": report["composite"],
                "verdict": report["verdict"],
                "path": f,
            })
            print(f"  Baseline: {ad['page_id']} = {report['composite']:.3f} [{report['verdict']}]")

    # Filter to target LPs
    target_items = [item for item in all_lp_items if item["ad"]["page_id"] in TARGET_LPS]
    target_items.sort(key=lambda x: TARGET_LPS.index(x["ad"]["page_id"]))

    print(f"\n{'=' * 60}")
    print("=== CHAINED EVOLUTION A/B TEST ===")
    print(f"{'=' * 60}\n")

    # Results storage
    results = {"A": [], "B": [], "C": []}
    per_lp_results = {}

    for item in target_items:
        ad = item["ad"]
        page_id = ad["page_id"]
        current_score = item["score"]
        current_hook = ad.get("hook_type", "story")

        donor = pick_donor(all_lp_items, page_id)
        donor_id = donor.get("page_id", "?") if donor else "none"

        # Pick a mutated hook (different from current)
        mutated_hook = _pick_mutated_hook(current_hook, playbook)

        print(f"{page_id} (current: {current_score:.3f}, hook: {current_hook}, donor: {donor_id}, mutated_hook: {mutated_hook})")

        lp_results = {"A": [], "B": [], "C": []}

        for i in range(CANDIDATES_PER_APPROACH):
            # --- Approach A: Plain crossover ---
            print(f"    A-{i+1}: crossover (plain)...", end=" ", flush=True)
            result_a = generate_and_score(
                ad, client, client_dir, shared_dir, all_ads,
                mode="crossover", hook_type=current_hook,
                donor_ad=donor, label=f"A-{i+1}",
            )
            if result_a:
                lp_results["A"].append(result_a["score"])
                results["A"].append(result_a["score"])
                print(f"{result_a['score']:.3f}")
            else:
                print("FAILED")

            # --- Approach B: Single-call combo (crossover + mutated hook) ---
            print(f"    B-{i+1}: crossover + mutated hook ({mutated_hook})...", end=" ", flush=True)
            result_b = generate_and_score(
                ad, client, client_dir, shared_dir, all_ads,
                mode="crossover", hook_type=mutated_hook,
                donor_ad=donor, label=f"B-{i+1}",
            )
            if result_b:
                lp_results["B"].append(result_b["score"])
                results["B"].append(result_b["score"])
                print(f"{result_b['score']:.3f}")
            else:
                print("FAILED")

            # --- Approach C: Two-call chain ---
            print(f"    C-{i+1}: chain step 1 (crossover)...", end=" ", flush=True)
            step1 = generate_and_score(
                ad, client, client_dir, shared_dir, all_ads,
                mode="crossover", hook_type=current_hook,
                donor_ad=donor, label=f"C-{i+1}-step1",
            )
            if step1:
                print(f"{step1['score']:.3f}", end=" ", flush=True)
                print(f"-> step 2 (mutate to {mutated_hook})...", end=" ", flush=True)
                result_c = generate_and_score(
                    step1["ad"], client, client_dir, shared_dir, all_ads,
                    mode="mutate", hook_type=mutated_hook,
                    donor_ad=None, label=f"C-{i+1}",
                )
                if result_c:
                    lp_results["C"].append(result_c["score"])
                    results["C"].append(result_c["score"])
                    print(f"{result_c['score']:.3f}")
                else:
                    print("FAILED (step 2)")
            else:
                print("FAILED (step 1)")

        per_lp_results[page_id] = {
            "current_score": current_score,
            "current_hook": current_hook,
            "mutated_hook": mutated_hook,
            "donor_id": donor_id,
            "A": lp_results["A"],
            "B": lp_results["B"],
            "C": lp_results["C"],
        }
        print()

    # ---------------------------------------------------------------------------
    # Print results table
    # ---------------------------------------------------------------------------

    print(f"\n{'=' * 60}")
    print("=== RESULTS ===")
    print(f"{'=' * 60}\n")

    for page_id in TARGET_LPS:
        if page_id not in per_lp_results:
            continue
        r = per_lp_results[page_id]
        print(f"{page_id} (current: {r['current_score']:.3f}, hook: {r['current_hook']}, "
              f"mutated: {r['mutated_hook']}, donor: {r['donor_id']})")

        for approach, label in [("A", "plain crossover"), ("B", "single-call combo"), ("C", "two-call chain")]:
            scores = r[approach]
            if scores:
                scores_str = ", ".join(f"{s:.3f}" for s in scores)
                avg = sum(scores) / len(scores)
                print(f"  Approach {approach} ({label:20s}): {scores_str}  avg={avg:.3f}")
            else:
                print(f"  Approach {approach} ({label:20s}): NO DATA")
        print()

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------

    print(f"{'=' * 60}")
    print("=== SUMMARY ===")
    print(f"{'=' * 60}\n")

    header = f"{'':20s} {'Avg Score':>10s}  {'Best Score':>10s}  {'Win Rate':>10s}  {'N':>4s}"
    print(header)
    print("-" * len(header))

    approach_stats = {}
    for approach, label in [("A", "Plain crossover"), ("B", "Single-call combo"), ("C", "Two-call chain")]:
        scores = results[approach]
        if scores:
            avg = sum(scores) / len(scores)
            best = max(scores)
            approach_stats[approach] = {"avg": avg, "best": best, "scores": scores}
            # Win rate: how often this approach produced the best score per LP
        else:
            approach_stats[approach] = {"avg": 0, "best": 0, "scores": []}

    # Calculate win rate per LP
    wins = {"A": 0, "B": 0, "C": 0}
    lp_count = 0
    for page_id in TARGET_LPS:
        if page_id not in per_lp_results:
            continue
        r = per_lp_results[page_id]
        best_per_approach = {}
        for approach in ["A", "B", "C"]:
            if r[approach]:
                best_per_approach[approach] = max(r[approach])

        if best_per_approach:
            lp_count += 1
            winner = max(best_per_approach, key=best_per_approach.get)
            wins[winner] += 1

    for approach, label in [("A", "Plain crossover"), ("B", "Single-call combo"), ("C", "Two-call chain")]:
        stats = approach_stats[approach]
        n = len(stats["scores"])
        win_pct = (wins[approach] / lp_count * 100) if lp_count > 0 else 0
        if n > 0:
            print(f"Approach {approach} ({label:17s}): {stats['avg']:>8.3f}    {stats['best']:>8.3f}    {win_pct:>7.0f}%  {n:>4d}")
        else:
            print(f"Approach {approach} ({label:17s}):      N/A         N/A        N/A     0")

    print()

    # Recommendation
    best_approach = max(approach_stats, key=lambda k: approach_stats[k]["avg"] if approach_stats[k]["scores"] else 0)
    best_label = {"A": "Plain crossover", "B": "Single-call combo", "C": "Two-call chain"}[best_approach]

    if approach_stats[best_approach]["scores"]:
        # Calculate lift vs baseline (A)
        baseline_avg = approach_stats["A"]["avg"] if approach_stats["A"]["scores"] else 0
        best_avg = approach_stats[best_approach]["avg"]
        if baseline_avg > 0 and best_approach != "A":
            lift = (best_avg - baseline_avg) / baseline_avg * 100
            print(f"Recommendation: Approach {best_approach} ({best_label}) produces {lift:+.1f}% higher scores on average vs baseline.")
        elif best_approach == "A":
            print(f"Recommendation: Approach A (Plain crossover) is the baseline winner — chaining does not help.")
        else:
            print(f"Recommendation: Approach {best_approach} ({best_label}) had the highest average score.")

    # Also show vs current scores
    print()
    current_avg = sum(per_lp_results[p]["current_score"] for p in TARGET_LPS if p in per_lp_results) / max(len(per_lp_results), 1)
    print(f"Current LP average: {current_avg:.3f}")
    for approach, label in [("A", "Plain crossover"), ("B", "Single-call combo"), ("C", "Two-call chain")]:
        stats = approach_stats[approach]
        if stats["scores"]:
            delta = stats["avg"] - current_avg
            print(f"  Approach {approach} avg vs current: {delta:+.3f}")


if __name__ == "__main__":
    t0 = time.time()
    main()
    elapsed = time.time() - t0
    print(f"\nTotal runtime: {elapsed:.0f}s ({elapsed/60:.1f}m)")
