#!/usr/bin/env python3
"""Extract learnings from scored content batches.

Analyses scored content to surface which hook × tactic × angle
combinations score highest and lowest for a client. Output is a
report for human review — findings can be promoted into learnings.md.

Usage:
    python3 scripts/extract_learnings.py farm-thru
    python3 scripts/extract_learnings.py farm-thru --min-count 3
    python3 scripts/extract_learnings.py farm-thru --append
"""

import argparse
import json
import os
import sys
from collections import defaultdict
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


def parse_args():
    parser = argparse.ArgumentParser(description="Extract learnings from scored batches")
    parser.add_argument("client", help="Client ID")
    parser.add_argument("--min-count", type=int, default=2,
                        help="Min items per group to report (default 2)")
    parser.add_argument("--append", action="store_true",
                        help="Append findings to learnings.md (after manual section)")
    parser.add_argument("--no-llm", action="store_true",
                        help="Disable LLM scoring (deterministic only)")
    return parser.parse_args()


def collect_and_score(client_dir, shared_dir, client, use_llm):
    """Collect all content and score it. Returns list of scored items."""
    loop_dir = client_dir / "loop"
    items = []
    all_ads = []

    # Collect all ads first
    for subdir in ["meta-ads", "landing-pages", "emails"]:
        content_dir = loop_dir / subdir
        if not content_dir.exists():
            continue
        for f in sorted(content_dir.iterdir()):
            if f.suffix == ".json" and f.name not in ("test-ad.json", "review-batch.json"):
                with open(f) as fh:
                    ad = json.load(fh)
                all_ads.append(ad)
                items.append({"path": f, "ad": ad})

    # Score each
    scored = []
    for item in items:
        report = score_ad(item["ad"], client, existing_ads=all_ads, use_llm=use_llm)
        scored.append({
            "ad": item["ad"],
            "path": str(item["path"]),
            "composite": report["composite"],
            "verdict": report["verdict"],
            "dimensions": report.get("rubric", {}).get("dimension_details", {}),
        })

    return scored


def analyse_combinations(scored, min_count):
    """Group by hook_type, tactic, angle and compute stats."""
    groups = {
        "hook_type": defaultdict(list),
        "tactic": defaultdict(list),
        "angle": defaultdict(list),
        "hook_x_tactic": defaultdict(list),
        "hook_x_angle": defaultdict(list),
    }

    for item in scored:
        ad = item["ad"]
        score = item["composite"]
        hook = ad.get("hook_type", "unknown")
        tactic = ad.get("tactic", "unknown")
        angle = ad.get("angle", "unknown")

        groups["hook_type"][hook].append(score)
        groups["tactic"][tactic].append(score)
        groups["angle"][angle].append(score)
        groups["hook_x_tactic"][f"{hook} + {tactic}"].append(score)
        groups["hook_x_angle"][f"{hook} + {angle}"].append(score)

    # Compute stats per group
    results = {}
    for group_name, group_data in groups.items():
        stats = []
        for key, scores in group_data.items():
            if len(scores) >= min_count:
                avg = sum(scores) / len(scores)
                stats.append({
                    "key": key,
                    "count": len(scores),
                    "avg_composite": round(avg, 4),
                    "min": round(min(scores), 4),
                    "max": round(max(scores), 4),
                })
        stats.sort(key=lambda x: x["avg_composite"], reverse=True)
        results[group_name] = stats

    return results


def print_report(results, scored):
    """Print a human-readable report."""
    total = len(scored)
    avg_all = sum(s["composite"] for s in scored) / total if total else 0
    verdicts = defaultdict(int)
    for s in scored:
        verdicts[s["verdict"]] += 1

    print(f"\n{'='*60}")
    print(f"LEARNING EXTRACTION REPORT")
    print(f"{'='*60}")
    print(f"Total items scored: {total}")
    print(f"Average composite: {avg_all:.4f}")
    for v in ["production_ready", "strong_draft", "needs_work", "rewrite"]:
        print(f"  {v}: {verdicts.get(v, 0)}")
    print()

    for group_name, stats in results.items():
        if not stats:
            continue
        print(f"\n--- {group_name.upper().replace('_', ' ')} ---")
        print(f"{'Key':<35} {'Count':>5} {'Avg':>8} {'Min':>8} {'Max':>8}")
        print("-" * 68)
        for s in stats:
            marker = ""
            if s["avg_composite"] >= 0.70:
                marker = " [strong]"
            elif s["avg_composite"] < 0.55:
                marker = " [weak]"
            print(f"{s['key']:<35} {s['count']:>5} {s['avg_composite']:>8.4f} {s['min']:>8.4f} {s['max']:>8.4f}{marker}")

    # Top 3 and bottom 3 overall combinations
    all_combos = []
    for group_name in ["hook_x_tactic", "hook_x_angle"]:
        all_combos.extend(results.get(group_name, []))
    all_combos.sort(key=lambda x: x["avg_composite"], reverse=True)

    if all_combos:
        print(f"\n--- TOP COMBINATIONS ---")
        for s in all_combos[:5]:
            print(f"  {s['key']}: {s['avg_composite']:.4f} (n={s['count']})")

        print(f"\n--- WEAKEST COMBINATIONS ---")
        for s in all_combos[-3:]:
            print(f"  {s['key']}: {s['avg_composite']:.4f} (n={s['count']})")


def generate_learnings_section(results):
    """Generate a markdown section for appending to learnings.md."""
    lines = [
        "",
        "## Auto-Extracted Patterns (from scored batches)",
        "",
    ]

    # Top hooks
    hook_stats = results.get("hook_type", [])
    if hook_stats:
        top_hooks = [s for s in hook_stats if s["avg_composite"] >= 0.65][:5]
        if top_hooks:
            lines.append("### Best-performing hook types")
            for s in top_hooks:
                lines.append(f"- **{s['key']}**: avg {s['avg_composite']:.3f} (n={s['count']})")
            lines.append("")

    # Top combinations
    combo_stats = results.get("hook_x_angle", [])
    if combo_stats:
        top_combos = [s for s in combo_stats if s["avg_composite"] >= 0.65][:5]
        if top_combos:
            lines.append("### Best hook × angle combinations")
            for s in top_combos:
                lines.append(f"- **{s['key']}**: avg {s['avg_composite']:.3f} (n={s['count']})")
            lines.append("")

    # Weak patterns to avoid
    weak_hooks = [s for s in hook_stats if s["avg_composite"] < 0.55]
    if weak_hooks:
        lines.append("### Underperforming patterns")
        for s in weak_hooks[-3:]:
            lines.append(f"- **{s['key']}**: avg {s['avg_composite']:.3f} (n={s['count']})")
        lines.append("")

    return "\n".join(lines)


def main():
    args = parse_args()

    client_dir = root / "clients" / args.client
    shared_dir = root / "shared"
    client = load_client(client_dir, shared_dir)
    use_llm = not args.no_llm

    print(f"Scoring all content for {args.client}...")
    scored = collect_and_score(client_dir, shared_dir, client, use_llm)

    if not scored:
        print("No content found to analyse.")
        return

    results = analyse_combinations(scored, args.min_count)
    print_report(results, scored)

    if args.append:
        section = generate_learnings_section(results)
        if section.strip():
            learnings_path = client_dir / "learnings.md"
            with open(learnings_path, "a") as f:
                f.write(section)
            print(f"\nAppended auto-extracted patterns to {learnings_path}")
        else:
            print("\nNo patterns met the threshold for appending.")


if __name__ == "__main__":
    main()
