#!/usr/bin/env python3
"""Verify anti-convergence scoring changes.

Scores all items for a client with --no-llm, prints dimension variance,
checks spread and diversity, and optionally runs pairwise comparisons.

Usage: python3 scripts/verify_scoring.py farm-thru
"""

import json
import os
import statistics
import sys
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
from engine.llm_judge import score_pairwise


def _get_ad_id(ad: dict) -> str:
    return ad.get("ad_id", ad.get("page_id", ad.get("email_id", "?")))


def main():
    client_slug = sys.argv[1] if len(sys.argv) > 1 else "farm-thru"

    client_dir = root / "clients" / client_slug
    shared_dir = root / "shared"
    client = load_client(client_dir, shared_dir)

    # Collect all content
    loop_dir = client_dir / "loop"
    all_items = []
    for subdir in ["meta-ads", "landing-pages", "emails"]:
        content_dir = loop_dir / subdir
        if not content_dir.exists():
            continue
        for f in sorted(content_dir.iterdir()):
            if f.suffix == ".json" and f.name not in ("test-ad.json", "review-batch.json"):
                with open(f) as fh:
                    ad = json.load(fh)
                all_items.append({"path": f, "ad": ad, "subdir": subdir})

    all_ads = [item["ad"] for item in all_items]

    print(f"Loaded {len(all_items)} items for {client_slug}")
    print()

    # Score all items (no LLM — deterministic only)
    print("Scoring all items (deterministic, no LLM)...")
    reports = []
    critical_failures = 0
    for item in all_items:
        report = score_ad(item["ad"], client, existing_ads=all_ads, use_llm=False)
        item["report"] = report
        item["score"] = report["composite"]
        reports.append(report)
        if report["overrides"]["critical_rule_failure"]:
            critical_failures += 1
    print(f"  Scored {len(reports)} items, {critical_failures} critical failures")
    print()

    # Build dimension variance table
    dim_scores = {}  # dim_id -> list of scores
    for report in reports:
        for dim_id, detail in report["rubric"]["dimension_details"].items():
            dim_scores.setdefault(dim_id, []).append(detail["score"])

    print("=== DIMENSION VARIANCE TABLE ===")
    print(f"{'Dimension':<25} {'Avg':>5} {'StdDev':>7} {'Min':>4} {'Max':>4} {'N':>3}")
    print("-" * 55)
    checks_passed = 0
    checks_failed = 0
    differentiation_spread_ok = True
    diversity_dims_present = []
    diversity_dims_expected = ["opening_diversity", "sentence_variance", "emotional_register"]

    for dim_id in sorted(dim_scores.keys()):
        scores = dim_scores[dim_id]
        avg = statistics.mean(scores)
        std = statistics.stdev(scores) if len(scores) > 1 else 0.0
        mn = min(scores)
        mx = max(scores)
        print(f"  {dim_id:<23} {avg:5.2f} {std:7.3f} {mn:4d} {mx:4d} {len(scores):3d}")

        # Track diversity dimensions
        if dim_id in diversity_dims_expected:
            diversity_dims_present.append(dim_id)

    print()

    # Check 1: No critical failures
    print("=== CHECKS ===")
    if critical_failures == 0:
        print("  [PASS] No critical rule failures")
        checks_passed += 1
    else:
        print(f"  [FAIL] {critical_failures} critical rule failure(s)")
        checks_failed += 1

    # Check 2: Differentiation spread
    if "differentiation" in dim_scores:
        diff_std = statistics.stdev(dim_scores["differentiation"]) if len(dim_scores["differentiation"]) > 1 else 0.0
        if diff_std > 0.5:
            print(f"  [PASS] Differentiation spread: std_dev={diff_std:.3f} (>0.5)")
            checks_passed += 1
        else:
            print(f"  [FAIL] Differentiation spread: std_dev={diff_std:.3f} (<=0.5, need >0.5)")
            checks_failed += 1
            differentiation_spread_ok = False
    else:
        print("  [SKIP] No differentiation dimension found")

    # Check 3: Diversity dimensions present and varied
    found_diversity = [d for d in diversity_dims_expected if d in dim_scores]
    if found_diversity:
        print(f"  [PASS] Diversity dimensions present: {', '.join(found_diversity)}")
        checks_passed += 1
        for d in found_diversity:
            std = statistics.stdev(dim_scores[d]) if len(dim_scores[d]) > 1 else 0.0
            status = "PASS" if std > 0.3 else "WARN"
            print(f"    [{status}] {d} variance: std_dev={std:.3f}")
    else:
        print(f"  [INFO] No diversity dimensions ({', '.join(diversity_dims_expected)}) found in rubric — skipping")

    print()

    # Pairwise comparison tests
    print("=== PAIRWISE COMPARISON ===")

    # Sort by composite score
    scored_items = sorted(all_items, key=lambda x: x["score"], reverse=True)

    if len(scored_items) < 2:
        print("  [SKIP] Need at least 2 items for pairwise comparison")
    else:
        # Test 1: Compare top vs bottom (should score 1-2, meaning bottom is worse)
        top_ad = scored_items[0]["ad"]
        bottom_ad = scored_items[-1]["ad"]
        top_id = _get_ad_id(top_ad)
        bottom_id = _get_ad_id(bottom_ad)
        top_score = scored_items[0]["score"]
        bottom_score = scored_items[-1]["score"]

        print(f"  Test 1: top ({top_id}, {top_score:.3f}) vs bottom ({bottom_id}, {bottom_score:.3f})")
        print(f"    Calling score_pairwise(bottom_as_new, top_as_current)...")

        pw_score, pw_reason = score_pairwise(bottom_ad, top_ad, client["config"])
        if pw_score <= 2:
            print(f"    [PASS] Pairwise={pw_score}/5 — bottom correctly rated worse: {pw_reason}")
            checks_passed += 1
        elif pw_score == 3:
            print(f"    [WARN] Pairwise={pw_score}/5 — rated equal despite score gap: {pw_reason}")
        else:
            print(f"    [FAIL] Pairwise={pw_score}/5 — bottom rated better than top: {pw_reason}")
            checks_failed += 1

        # Test 2: Compare two similar-scoring ads (should score ~3)
        mid = len(scored_items) // 2
        if mid > 0 and mid < len(scored_items) - 1:
            ad_a = scored_items[mid]["ad"]
            ad_b = scored_items[mid + 1]["ad"]
            a_id = _get_ad_id(ad_a)
            b_id = _get_ad_id(ad_b)
            a_score = scored_items[mid]["score"]
            b_score = scored_items[mid + 1]["score"]

            print(f"  Test 2: mid ({a_id}, {a_score:.3f}) vs adjacent ({b_id}, {b_score:.3f})")
            print(f"    Calling score_pairwise(adjacent_as_new, mid_as_current)...")

            pw_score2, pw_reason2 = score_pairwise(ad_b, ad_a, client["config"])
            if 2 <= pw_score2 <= 4:
                print(f"    [PASS] Pairwise={pw_score2}/5 — similar ads rated close: {pw_reason2}")
                checks_passed += 1
            else:
                print(f"    [WARN] Pairwise={pw_score2}/5 — unexpected for similar ads: {pw_reason2}")

    print()

    # Summary
    total = checks_passed + checks_failed
    status = "PASS" if checks_failed == 0 else "FAIL"
    print(f"=== SUMMARY: {status} ({checks_passed}/{total} checks passed) ===")
    return 0 if checks_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
