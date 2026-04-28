#!/usr/bin/env python3
"""Hypothesis-driven hill-climb from a single seed ad.

Generates testable hypotheses about which load-bearing elements to improve,
runs variants, and records whether each hypothesis was confirmed.

Usage:
  python3 scripts/hill_climb_from_seed.py seed.json [options]

Flags:
  --hypothesis-driven      Enable hypothesis-driven mode (default True)
  --hypotheses N           Number of hypotheses to generate (default 4)
  --max-variants N         Max variants to evaluate (default 4)
  --max-minutes N          Wall-clock cap in minutes (default 6)
  --client CLIENT          Client ID (default: farm-thru)
  --no-llm                 Disable LLM scoring (deterministic only)
  --output-dir DIR         Where to write results (default: validation/empiricist-results-2026-04-28)

Output (in output-dir):
  {seed_id}-results.json   Full results including hypotheses, variant scores, deltas
  {seed_id}-summary.txt    Human-readable summary
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
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
from engine.hypothesis_generator import generate_hypotheses, hypothesis_summary
from scripts.lint_content import lint
from writer import generate_variant


def parse_args():
    parser = argparse.ArgumentParser(description="Hypothesis-driven hill-climb from a seed ad")
    parser.add_argument("seed", help="Path to seed ad JSON file")
    parser.add_argument("--hypothesis-driven", action="store_true", default=True,
                        help="Enable hypothesis-driven mode (default True)")
    parser.add_argument("--hypotheses", type=int, default=4,
                        help="Number of hypotheses to generate (default 4)")
    parser.add_argument("--max-variants", type=int, default=4,
                        help="Max variants to evaluate (default 4)")
    parser.add_argument("--max-minutes", type=float, default=6,
                        help="Wall-clock cap in minutes (default 6)")
    parser.add_argument("--client", default="farm-thru",
                        help="Client ID (default: farm-thru)")
    parser.add_argument("--no-llm", action="store_true",
                        help="Disable LLM scoring (deterministic only)")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory for results")
    return parser.parse_args()


def _get_ad_id(ad: dict) -> str:
    return ad.get("ad_id", ad.get("page_id", ad.get("email_id", "?")))


def _determine_actual_direction(seed_score: float, variant_score: float,
                                delta_threshold: float = 0.01) -> str:
    """Classify actual direction: LIFT, DROP, or NEUTRAL."""
    delta = variant_score - seed_score
    if delta >= delta_threshold:
        return "LIFT"
    elif delta <= -delta_threshold:
        return "DROP"
    return "NEUTRAL"


def _run_variant_for_hypothesis(
    hypothesis: dict,
    seed_ad: dict,
    client: dict,
    client_dir: Path,
    shared_dir: Path,
    all_ads: list,
    use_llm: bool,
    start_time: float,
    max_seconds: float,
) -> dict:
    """Generate and score one variant for a hypothesis.

    Returns a result dict with: hypothesis, variant, scores, delta, confirmed.
    """
    result = {
        "hypothesis": hypothesis,
        "variant": None,
        "seed_score": None,
        "variant_score": None,
        "delta": None,
        "actual_direction": None,
        "confirmed": None,
        "error": None,
        "lint_passed": None,
        "elapsed_secs": None,
    }

    t0 = time.time()

    # Check time budget
    elapsed = time.time() - start_time
    if elapsed >= max_seconds:
        result["error"] = "TIME_BUDGET_EXCEEDED"
        return result

    try:
        # Get weak dimensions from hypothesis
        dim_id = hypothesis["dim_id"]
        weak_dimensions = [(dim_id, hypothesis["current_score"], 5)]

        # Mode from hypothesis hint
        mode = hypothesis["mode_hint"]
        hook_type = seed_ad.get("hook_type", "question")

        # For hook_swap hypotheses, use a different hook
        if hypothesis["testable_swap"] == "hook_swap":
            from writer import HOOK_TEMPLATES, HOOK_METADATA
            available = [h for h in HOOK_TEMPLATES if h != hook_type]
            # Pick the hook with highest benchmark_hit_rate among available
            best_hook = max(available, key=lambda h: HOOK_METADATA.get(h, {}).get("benchmark_hit_rate", 0.05))
            hook_type = best_hook
            mode = "mutate"

        # Generate variant
        variant_ad = generate_variant(
            angle=seed_ad.get("angle", "cause-purpose"),
            tactic=seed_ad.get("tactic", "general"),
            hook_type=hook_type,
            funnel=seed_ad.get("funnel", "TOF"),
            client_dir=client_dir,
            current_best=seed_ad,
            recent_failures=[],
            content_type=seed_ad.get("content_type", "meta-ad"),
            mode=mode,
            weak_dimensions=weak_dimensions if mode == "targeted" else None,
        )

        # Preserve key fields from seed
        for key in ["ad_id", "content_type", "campaign_phase"]:
            if key in seed_ad:
                variant_ad[key] = seed_ad[key]

        # Lint check
        lint_result = lint(variant_ad, client_dir, shared_dir)
        result["lint_passed"] = lint_result.passed
        if not lint_result.passed:
            violations = [v["rule_id"] for v in lint_result.violations[:3]]
            result["error"] = f"LINT_FAIL: {', '.join(violations)}"
            result["variant"] = variant_ad
            result["elapsed_secs"] = round(time.time() - t0, 1)
            return result

        # Score variant
        variant_report = score_ad(variant_ad, client, existing_ads=all_ads, use_llm=use_llm)
        result["variant"] = variant_ad
        result["variant_score"] = round(variant_report["composite"], 4)
        result["variant_report"] = variant_report
        result["delta"] = round(variant_report["composite"] - (result.get("seed_score") or 0), 4)

    except Exception as e:
        result["error"] = f"ERROR: {e}"

    result["elapsed_secs"] = round(time.time() - t0, 1)
    return result


def main():
    args = parse_args()
    start_time = time.time()
    max_seconds = args.max_minutes * 60

    # Resolve paths
    seed_path = Path(args.seed)
    if not seed_path.is_absolute():
        seed_path = Path.cwd() / seed_path
    if not seed_path.exists():
        print(f"ERROR: seed file not found: {seed_path}", file=sys.stderr)
        sys.exit(1)

    with open(seed_path) as f:
        seed_ad = json.load(f)

    seed_id = _get_ad_id(seed_ad)
    content_type = seed_ad.get("content_type", "meta-ad")
    print(f"=== HYPOTHESIS-DRIVEN HILL-CLIMB FROM SEED: {seed_id} ===")
    print(f"Content type: {content_type}")
    print(f"Angle: {seed_ad.get('angle', '?')} | Hook: {seed_ad.get('hook_type', '?')}")
    print(f"Max hypotheses: {args.hypotheses} | Max variants: {args.max_variants}")
    print(f"Wall-clock cap: {args.max_minutes} min")
    print()

    # Load client
    client_dir = root / "clients" / args.client
    shared_dir = root / "shared"
    client = load_client(client_dir, shared_dir)
    use_llm = not args.no_llm

    # Load all existing ads of same content_type for differentiation scoring
    loop_dir = client_dir / "loop"
    all_ads = []
    for subdir in ["meta-ads", "landing-pages", "emails", "sms"]:
        content_dir = loop_dir / subdir
        if not content_dir.exists():
            continue
        for f in sorted(content_dir.iterdir()):
            if f.suffix == ".json" and f.name not in ("test-ad.json", "review-batch.json"):
                try:
                    with open(f) as fh:
                        all_ads.append(json.load(fh))
                except Exception:
                    pass

    # Score the seed
    print("Scoring seed ad...")
    seed_report = score_ad(seed_ad, client, existing_ads=all_ads, use_llm=use_llm)
    seed_score = seed_report["composite"]
    seed_verdict = seed_report["verdict"]

    print(f"Seed score: {seed_score:.4f} [{seed_verdict}]")
    print()

    # Rubric dim details for display
    dim_details = seed_report.get("rubric", {}).get("dimension_details", {})
    print("Seed rubric dims:")
    for dim_id, info in sorted(dim_details.items(), key=lambda x: x[1].get("score", 5)):
        score = info.get("score", "?")
        weight = info.get("weight", "?")
        detail = info.get("detail", "")[:60]
        print(f"  {dim_id:>26}: {score}/5 (w={weight}) — {detail}")
    print()

    # Generate hypotheses
    print(f"Generating {args.hypotheses} hypotheses...")
    hypotheses = generate_hypotheses(
        ad=seed_ad,
        score_report=seed_report,
        n=args.hypotheses,
        exclude_neutral=True,
        min_score_gap=1,
    )

    if not hypotheses:
        print("No testable hypotheses found (seed may already be at max on all dims).")
        sys.exit(0)

    print(f"\nHypotheses ({len(hypotheses)} generated):")
    print(hypothesis_summary(hypotheses))
    print()

    # Run variants (one per hypothesis, up to max_variants)
    n_to_run = min(len(hypotheses), args.max_variants)
    print(f"Running {n_to_run} variants...")
    print()

    results = []
    for i, hyp in enumerate(hypotheses[:n_to_run]):
        elapsed = time.time() - start_time
        remaining = max_seconds - elapsed
        if remaining <= 0:
            print(f"  Time budget exceeded at hypothesis {i+1}/{n_to_run}")
            break

        dim_id = hyp["dim_id"]
        print(f"  [{i+1}/{n_to_run}] Testing: {dim_id} "
              f"(gap={hyp['score_gap']}, expected_gain={hyp['expected_gain']:.4f}, "
              f"mode={hyp['mode_hint']})")

        result = _run_variant_for_hypothesis(
            hypothesis=hyp,
            seed_ad=seed_ad,
            client=client,
            client_dir=client_dir,
            shared_dir=shared_dir,
            all_ads=all_ads,
            use_llm=use_llm,
            start_time=start_time,
            max_seconds=max_seconds,
        )
        result["seed_score"] = seed_score

        if result.get("error"):
            print(f"    ERROR: {result['error']}")
            result["confirmed"] = "INVALID_PROBE"
            result["actual_direction"] = "INVALID"
        elif result.get("variant_score") is not None:
            variant_score = result["variant_score"]
            delta = variant_score - seed_score
            result["delta"] = round(delta, 4)
            actual_dir = _determine_actual_direction(seed_score, variant_score)
            result["actual_direction"] = actual_dir
            predicted = hyp["predicted_direction"]
            confirmed = (actual_dir == predicted)
            result["confirmed"] = "yes" if confirmed else ("no" if actual_dir != "NEUTRAL" else "no_lift")

            print(f"    Variant score: {variant_score:.4f} (delta={delta:+.4f})")
            print(f"    Predicted: {predicted} | Actual: {actual_dir} | Confirmed: {result['confirmed']}")

        results.append(result)
        print()

    total_elapsed = time.time() - start_time
    print(f"Total elapsed: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print()

    # Summary
    print("=== RESULTS SUMMARY ===")
    confirmed_count = sum(1 for r in results if r.get("confirmed") == "yes")
    denied_count = sum(1 for r in results if r.get("confirmed") == "no")
    invalid_count = sum(1 for r in results if r.get("confirmed") in ("INVALID_PROBE", None))
    nolift_count = sum(1 for r in results if r.get("confirmed") == "no_lift")

    valid_deltas = [r["delta"] for r in results if r.get("delta") is not None]
    best_delta = max(valid_deltas) if valid_deltas else 0
    best_variant_score = seed_score + best_delta

    print(f"Confirmed: {confirmed_count} | Denied: {denied_count} | "
          f"No-lift: {nolift_count} | Invalid: {invalid_count}")
    print(f"Best variant: {best_variant_score:.4f} (delta={best_delta:+.4f} vs seed {seed_score:.4f})")
    print()

    # Write output
    output_dir = Path(args.output_dir) if args.output_dir else (
        root / "validation" / "empiricist-results-2026-04-28"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    # Full JSON results (strip variant_report from output to keep it readable)
    output_results = []
    for r in results:
        out = {k: v for k, v in r.items() if k != "variant_report"}
        output_results.append(out)

    output_data = {
        "run_ts": datetime.now(timezone.utc).isoformat(),
        "seed_id": seed_id,
        "seed_path": str(seed_path),
        "seed_score": seed_score,
        "seed_verdict": seed_verdict,
        "seed_dims": {k: v.get("score") for k, v in dim_details.items()},
        "n_hypotheses": len(hypotheses),
        "n_variants_run": len(results),
        "confirmed_count": confirmed_count,
        "denied_count": denied_count,
        "nolift_count": nolift_count,
        "invalid_count": invalid_count,
        "best_delta": round(best_delta, 4),
        "best_variant_score": round(best_variant_score, 4),
        "total_elapsed_secs": round(total_elapsed, 1),
        "hypotheses": hypotheses,
        "results": output_results,
    }

    results_path = output_dir / f"{seed_id}-results.json"
    with open(results_path, "w") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Results written to: {results_path}")

    # Human-readable summary
    summary_lines = [
        f"=== HYPOTHESIS-DRIVEN HILL-CLIMB SUMMARY ===",
        f"Seed: {seed_id} | Score: {seed_score:.4f} [{seed_verdict}]",
        f"Run at: {datetime.now(timezone.utc).isoformat()}",
        f"Elapsed: {total_elapsed:.1f}s",
        f"",
        f"HYPOTHESES TESTED:",
    ]
    for r in results:
        hyp = r["hypothesis"]
        status = r.get("confirmed", "?")
        delta_str = f"{r['delta']:+.4f}" if r.get("delta") is not None else "N/A"
        summary_lines.append(
            f"  [{status:>14}] {hyp['dim_id']:>26} | gap={hyp['score_gap']} | "
            f"LBE={hyp['load_bearing_element']} | delta={delta_str}"
        )

    summary_lines += [
        f"",
        f"VERDICT: {confirmed_count}/{len(results)} confirmed | "
        f"best delta={best_delta:+.4f} | best score={best_variant_score:.4f}",
    ]

    summary_path = output_dir / f"{seed_id}-summary.txt"
    with open(summary_path, "w") as f:
        f.write("\n".join(summary_lines) + "\n")
    print(f"Summary written to: {summary_path}")

    return output_data


if __name__ == "__main__":
    main()
