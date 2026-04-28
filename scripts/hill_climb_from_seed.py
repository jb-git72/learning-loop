#!/usr/bin/env python3
"""Generate variants from a single seed ad, with a wall-clock budget.

Usage:
  python3 scripts/hill_climb_from_seed.py <seed.json> [--max-variants 4] [--max-minutes 10] [--client farm-thru]

Generates variants via improve/mutate/targeted/crossover modes anchored on the
seed, scores each, and writes the top-N by composite to a sibling directory
plus an HTML review.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from engine.scorer import load_client, score_ad
from writer import generate_variant, generate_hook_swap_variant
from engine.hypothesis_generator import generate_hypotheses


MODES = [
    ("improve", None),
    ("mutate", None),
    ("targeted", "scroll_stop_hook"),
    ("targeted", "ownership_framing"),
    ("mutate", None),
    ("improve", None),
    ("targeted", "specificity"),
    ("mutate", None),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("seed", help="Path to seed ad JSON")
    parser.add_argument("--max-variants", type=int, default=4, help="Max variants to keep (default 4)")
    parser.add_argument("--max-minutes", type=float, default=10, help="Wall-clock cap (default 10 min)")
    parser.add_argument("--client", default="farm-thru", help="Client ID (default farm-thru)")
    parser.add_argument(
        "--hypothesis-driven",
        action="store_true",
        help="Use hypothesis-driven hook-swap mode. Generates a structured "
        "hypothesis list from the seed (engine.hypothesis_generator), then "
        "produces ONE hook_swap variant per hypothesis with body / CTA / CSF "
        "locked. Each variant tests a specific theory about why the seed works.",
    )
    parser.add_argument(
        "--hypotheses",
        type=int,
        default=4,
        help="Number of hypotheses to generate when --hypothesis-driven (default 4).",
    )
    args = parser.parse_args()

    seed_path = Path(args.seed)
    seed_ad = json.loads(seed_path.read_text())
    print(f"Seed: {seed_path.name} (ad_id={seed_ad.get('ad_id')}, angle={seed_ad.get('angle')})")
    print(f"Budget: {args.max_minutes:.1f} min wall-clock, keep top {args.max_variants}")

    client_dir = ROOT / "clients" / args.client
    shared_dir = ROOT / "shared"
    client = load_client(client_dir, shared_dir)

    # Score the seed first
    seed_report = score_ad(seed_ad, client, existing_ads=[], use_llm=True)
    print(f"\nSeed composite: {seed_report['composite']:.4f} ({seed_report['verdict']})\n")

    deadline = time.time() + args.max_minutes * 60
    candidates = []  # list of (composite, ad, mode, weak_dim, generated_at)
    attempts = 0

    # Hypothesis-driven path: generate structured hypotheses then produce one
    # hook-swap variant per hypothesis. Body / CTA / CSF are locked from seed.
    if args.hypothesis_driven:
        print(f"Hypothesis-driven mode: generating {args.hypotheses} hypotheses about the seed...")
        hypotheses = generate_hypotheses(
            seed_ad=seed_ad,
            client_config=client["config"],
            client_dir=client_dir,
            shared_dir=shared_dir,
            n=args.hypotheses,
            use_llm=True,
        )
        print(f"Got {len(hypotheses)} hypotheses:")
        for h in hypotheses:
            print(f"  [{h.get('id'):3s}] {h.get('load_bearing_element','?'):28s} confidence={h.get('confidence_prior', 0):.2f} expected={h.get('expected_direction','?')}")
            print(f"        claim: {h.get('claim','')[:120]}")
        print()

        for h in hypotheses:
            if time.time() >= deadline:
                print(f"\n[time cap] {attempts} attempts before deadline")
                break
            attempts += 1
            elapsed = time.time() - (deadline - args.max_minutes * 60)
            remaining = deadline - time.time()
            print(f"[{elapsed:5.1f}s, {remaining:.0f}s left] hypothesis {h.get('id')} — {h.get('load_bearing_element', '?')}")

            try:
                variant = generate_hook_swap_variant(
                    seed_ad=seed_ad,
                    hypothesis=h,
                    client_dir=client_dir,
                    content_type="meta-ad",
                )
            except Exception as e:
                print(f"  FAIL gen: {type(e).__name__}: {e}")
                continue

            variant.setdefault("campaign_phase", seed_ad.get("campaign_phase", "pre-campaign"))

            try:
                report = score_ad(variant, client, existing_ads=[seed_ad], use_llm=True)
            except Exception as e:
                print(f"  FAIL score: {type(e).__name__}: {e}")
                continue

            composite = report["composite"]
            verdict = report["verdict"]
            delta = composite - seed_report["composite"]
            print(f"  -> composite {composite:.4f} ({verdict}) delta={delta:+.4f}")
            print(f"     headline: {variant.get('headline','')[:70]}")
            print(f"     opening:  {variant.get('primary_text','').splitlines()[0][:90] if variant.get('primary_text') else ''}")

            if composite <= 0.01:
                rc = report.get("rule_compliance", {})
                for f in rc.get("failures", [])[:5]:
                    if f.get("severity") == "critical":
                        print(f"     CRITICAL [{f.get('rule_id')}] {f.get('detail','')[:140]}")
                comp = report.get("compliance", {})
                for v in comp.get("blocking_violations", [])[:3]:
                    print(f"     COMPLIANCE-BLOCK [{v.get('rule_id')}] {v.get('fix_message','')[:140]}")
                print("     skipped")
                continue

            candidates.append({
                "composite": composite,
                "verdict": verdict,
                "ad": variant,
                "mode": "hook_swap",
                "weak_dim": None,
                "hypothesis": h,
                "report": report,
            })

    # Random-mode path (default): cycle through MODES and call generate_variant.
    # Skipped when --hypothesis-driven was used (variants already accumulated).
    if not args.hypothesis_driven:
        for mode, weak_dim in MODES:
            if time.time() >= deadline:
                print(f"\n[time cap] {attempts} attempts before deadline")
                break
            attempts += 1
            elapsed = time.time() - (deadline - args.max_minutes * 60)
            remaining = deadline - time.time()
            print(f"[{elapsed:5.1f}s, {remaining:.0f}s left] attempt {attempts}/{len(MODES)} — mode={mode}"
                  + (f", targeting={weak_dim}" if weak_dim else ""))

            try:
                kwargs = {
                    "angle": seed_ad.get("angle", "urgency-scarcity"),
                    "tactic": seed_ad.get("tactic", "novelty-insider-access"),
                    "hook_type": seed_ad.get("hook_type", "curiosity"),
                    "funnel": seed_ad.get("funnel", "TOF"),
                    "client_dir": client_dir,
                    "current_best": seed_ad,
                    "content_type": "meta-ad",
                    "mode": mode,
                }
                if mode == "targeted" and weak_dim:
                    # Pass weak_dimensions as a list of (name, score, max) tuples
                    kwargs["weak_dimensions"] = [(weak_dim, 2, 5)]
                variant = generate_variant(**kwargs)
            except Exception as e:
                print(f"  FAIL gen: {type(e).__name__}: {e}")
                continue

            # Make sure variant has campaign_phase set (defensive — schema default
            # fires for new generations but we are explicit about pre-campaign).
            variant.setdefault("campaign_phase", seed_ad.get("campaign_phase", "pre-campaign"))

            try:
                report = score_ad(variant, client, existing_ads=[seed_ad], use_llm=True)
            except Exception as e:
                print(f"  FAIL score: {type(e).__name__}: {e}")
                continue

            composite = report["composite"]
            verdict = report["verdict"]
            delta = composite - seed_report["composite"]
            print(f"  -> composite {composite:.4f} ({verdict}) delta={delta:+.4f}")
            print(f"     headline: {variant.get('headline','')[:70]}")

            # Skip critical failures (composite 0) — but log why so we can
            # diagnose systemic gen issues fast.
            if composite <= 0.01:
                rc = report.get("rule_compliance", {})
                for f in rc.get("failures", [])[:5]:
                    if f.get("severity") == "critical":
                        print(f"     CRITICAL [{f.get('rule_id')}] {f.get('detail','')[:140]}")
                comp = report.get("compliance", {})
                for v in comp.get("blocking_violations", [])[:3]:
                    print(f"     COMPLIANCE-BLOCK [{v.get('rule_id')}] {v.get('fix_message','')[:140]}")
                print("     skipped")
                continue

            candidates.append({
                "composite": composite,
                "verdict": verdict,
                "ad": variant,
                "mode": mode,
                "weak_dim": weak_dim,
                "report": report,
            })

    print(f"\n=== Generated {len(candidates)} viable variants in {(time.time() - (deadline - args.max_minutes*60)):.1f}s ===")

    # Sort by composite, take top N
    candidates.sort(key=lambda c: -c["composite"])
    top = candidates[: args.max_variants]

    # Write outputs
    out_dir = ROOT / "clients" / args.client / "loop" / "live-ad-variants"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Wipe previous run so old variants don't pollute the directory.
    for old in out_dir.glob("*.json"):
        old.unlink()

    summary = {
        "seed_ad_id": seed_ad.get("ad_id"),
        "seed_composite": seed_report["composite"],
        "seed_verdict": seed_report["verdict"],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "max_minutes": args.max_minutes,
        "attempts": attempts,
        "viable": len(candidates),
        "kept": len(top),
        "results": [],
    }

    print(f"\n=== Top {len(top)} variants ===")
    for i, c in enumerate(top, start=1):
        ad = c["ad"]
        ad_id = ad.get("ad_id") or f"VARIANT-{i}"
        ad_id = f"LIVE-VARIANT-{i:02d}"
        ad["ad_id"] = ad_id
        path = out_dir / f"{ad_id}.json"
        # Persist composite + verdict alongside the ad for the review HTML.
        ad["_composite"] = round(c["composite"], 4)
        ad["_verdict"] = c["verdict"]
        ad["_mode"] = c["mode"]
        ad["_weak_dim"] = c["weak_dim"]
        path.write_text(json.dumps(ad, indent=2) + "\n")
        target_suffix = f", target={c['weak_dim']}" if c['weak_dim'] else ""
        print(f"  #{i} {ad_id} composite={c['composite']:.4f} ({c['verdict']}) mode={c['mode']}{target_suffix}")
        print(f"     headline: {ad.get('headline','')}")
        summary["results"].append({
            "rank": i,
            "ad_id": ad_id,
            "composite": round(c["composite"], 4),
            "verdict": c["verdict"],
            "mode": c["mode"],
            "weak_dim": c["weak_dim"],
            "headline": ad.get("headline", ""),
            "primary_text": ad.get("primary_text", ""),
            "description": ad.get("description", ""),
            "cta": ad.get("cta", ""),
        })

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\nWrote {len(top)} variants + summary.json to {out_dir}")
    print(f"Total wall-clock: {(time.time() - (deadline - args.max_minutes*60)):.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
