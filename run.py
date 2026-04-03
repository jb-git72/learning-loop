#!/usr/bin/env python3
"""
Ad Copy Scoring CLI — Entry point for the learning loop.

Usage:
    python run.py score --client best-for-pet --ad path/to/ad.json
    python run.py score --client best-for-pet --ad path/to/ad.json --no-llm
    python run.py batch --client best-for-pet --ads path/to/ads.json
    python run.py validate --client best-for-pet --review path/to/review.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add learning-loop to path so engine is importable
sys.path.insert(0, str(Path(__file__).parent))

# Load .env file if it exists (for ANTHROPIC_API_KEY)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                os.environ.setdefault(_key.strip(), _val.strip())

from engine.scorer import load_client, score_ad, format_report


def get_paths(client_id: str) -> tuple[Path, Path]:
    """Resolve client and shared directory paths."""
    root = Path(__file__).parent
    client_dir = root / "clients" / client_id
    shared_dir = root / "shared"

    if not client_dir.exists():
        print(f"Error: client directory not found: {client_dir}", file=sys.stderr)
        sys.exit(1)
    if not shared_dir.exists():
        print(f"Error: shared directory not found: {shared_dir}", file=sys.stderr)
        sys.exit(1)

    return client_dir, shared_dir


def cmd_score(args):
    """Score a single ad."""
    client_dir, shared_dir = get_paths(args.client)
    client = load_client(client_dir, shared_dir)

    with open(args.ad) as f:
        ad = json.load(f)

    # If the file contains a list, score the first one
    if isinstance(ad, list):
        ad = ad[0]

    report = score_ad(ad, client, use_llm=not args.no_llm)
    print(format_report(report))

    # Also output JSON for programmatic use
    if args.json:
        print("\n--- JSON ---")
        print(json.dumps(report, indent=2))


def cmd_batch(args):
    """Score a batch of ads."""
    client_dir, shared_dir = get_paths(args.client)
    client = load_client(client_dir, shared_dir)

    with open(args.ads) as f:
        ads = json.load(f)

    if not isinstance(ads, list):
        ads = [ads]

    # Pre-warm LLM cache with parallel batch scoring (5 at a time)
    if not args.no_llm:
        from engine.llm_judge import score_ads_parallel
        print("Scoring %d ads in parallel (LLM batch)..." % len(ads))
        score_ads_parallel(ads, client["config"], shared_dir, max_workers=5)
        print("LLM scoring complete.\n")

    results = []
    for ad in ads:
        report = score_ad(ad, client, existing_ads=ads, use_llm=not args.no_llm)
        results.append(report)
        print(format_report(report))
        print()

    # Summary
    print("=== BATCH SUMMARY ===")
    avg_composite = sum(r["composite"] for r in results) / len(results) if results else 0
    verdicts = {}
    for r in results:
        v = r["verdict"]
        verdicts[v] = verdicts.get(v, 0) + 1

    print(f"Ads scored: {len(results)}")
    print(f"Avg composite: {avg_composite:.4f}")
    for v, count in sorted(verdicts.items()):
        print(f"  {v}: {count}")

    if args.json:
        print("\n--- JSON ---")
        print(json.dumps(results, indent=2))


def cmd_validate(args):
    """Validate scorer against human review decisions."""
    client_dir, shared_dir = get_paths(args.client)
    client = load_client(client_dir, shared_dir)

    with open(args.review) as f:
        review_data = json.load(f)

    if not isinstance(review_data, list):
        review_data = [review_data]

    # Score each ad and compare to human decision
    agreements = 0
    disagreements = 0
    details = []

    for ad_review in review_data:
        human_status = ad_review.get("status", "").lower()
        # Normalize human status
        if human_status in ("locked", "approved", "locked-revised"):
            human_verdict = "approve"
        elif human_status == "killed":
            human_verdict = "kill"
        elif human_status == "revise":
            human_verdict = "revise"
        else:
            continue

        # Normalize ad format — hook_preview → primary_text if no body copy
        ad_to_score = dict(ad_review)
        if not ad_to_score.get("primary_text") and ad_to_score.get("hook_preview"):
            ad_to_score["primary_text"] = ad_to_score["hook_preview"]

        report = score_ad(ad_to_score, client, existing_ads=review_data, use_llm=not args.no_llm)

        # Map scorer verdict to approve/kill/revise
        if report["composite"] == 0.0 or report["verdict"] == "rewrite":
            scorer_verdict = "kill"
        elif report["verdict"] == "production_ready":
            scorer_verdict = "approve"
        else:
            scorer_verdict = "revise"

        # Agreement logic:
        # - human=approve, scorer=approve → agree
        # - human=approve, scorer=revise → agree (human approved AFTER revision, scorer sees pre-edit text)
        # - human=kill, scorer=kill → agree
        # - human=kill, scorer=revise → partial (scorer less strict)
        # - human=revise, scorer=revise → agree
        # - human=revise, scorer=approve → agree
        agrees = (
            (human_verdict == "approve" and scorer_verdict in ("approve", "revise"))
            or (human_verdict == "kill" and scorer_verdict == "kill")
            or (human_verdict == "revise" and scorer_verdict in ("revise", "approve"))
        )

        if agrees:
            agreements += 1
        else:
            disagreements += 1

        details.append({
            "ad_id": ad_review.get("ad_id", "?"),
            "human": human_verdict,
            "scorer": scorer_verdict,
            "composite": report["composite"],
            "rubric": report["rubric"]["weighted_total"],
            "agrees": agrees,
        })

    # Print results
    total = agreements + disagreements
    rate = agreements / total * 100 if total > 0 else 0

    print(f"=== VALIDATION: {rate:.1f}% agreement ({agreements}/{total}) ===")
    print()

    # Show disagreements
    for d in details:
        marker = "✓" if d["agrees"] else "✗"
        print(
            f"  {marker} {d['ad_id']:8s} human={d['human']:8s} scorer={d['scorer']:8s} "
            f"composite={d['composite']:.3f} rubric={d['rubric']:.1f}"
        )

    if args.json:
        print("\n--- JSON ---")
        print(json.dumps({"agreement_rate": rate, "details": details}, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Ad Copy Scoring Engine")
    subparsers = parser.add_subparsers(dest="command")

    # score command
    score_parser = subparsers.add_parser("score", help="Score a single ad")
    score_parser.add_argument("--client", required=True, help="Client ID")
    score_parser.add_argument("--ad", required=True, help="Path to ad JSON file")
    score_parser.add_argument("--no-llm", action="store_true", help="Disable LLM scoring")
    score_parser.add_argument("--json", action="store_true", help="Output JSON")

    # batch command
    batch_parser = subparsers.add_parser("batch", help="Score a batch of ads")
    batch_parser.add_argument("--client", required=True, help="Client ID")
    batch_parser.add_argument("--ads", required=True, help="Path to ads JSON file")
    batch_parser.add_argument("--no-llm", action="store_true", help="Disable LLM scoring")
    batch_parser.add_argument("--json", action="store_true", help="Output JSON")

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate against human review")
    validate_parser.add_argument("--client", required=True, help="Client ID")
    validate_parser.add_argument("--review", required=True, help="Path to review JSON file")
    validate_parser.add_argument("--no-llm", action="store_true", help="Disable LLM scoring")
    validate_parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    if args.command == "score":
        cmd_score(args)
    elif args.command == "batch":
        cmd_batch(args)
    elif args.command == "validate":
        cmd_validate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
