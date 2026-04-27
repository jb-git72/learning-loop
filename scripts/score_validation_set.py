#!/usr/bin/env python3
"""Score validation/scorer-recalibration-v1.json with the new rubric.

Compares every ad's new composite against its prior score (live ad: 0.7133;
comparison cohort: pulled from clients/farm-thru/loop/scored_r3_pass8.json).
Emits a CSV report and a one-line PASS/FAIL line on the live ad's target (>=0.85).
"""
import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Load .env so the LLM judge has its API key
env_path = ROOT.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from engine.scorer import load_client, score_ad

VALIDATION_PATH = ROOT / "validation" / "scorer-recalibration-v1.json"
PRIOR_SCORES_PATH = ROOT / "clients" / "farm-thru" / "loop" / "scored_r3_pass8.json"
LIVE_PRIOR_COMPOSITE = 0.7133  # from earlier session run

PRIOR_BY_ID = {}
if PRIOR_SCORES_PATH.exists():
    prior_data = json.loads(PRIOR_SCORES_PATH.read_text())
    for r in prior_data.get("results", []):
        PRIOR_BY_ID[r["ad_id"]] = r.get("composite", 0.0)
PRIOR_BY_ID["LIVE-FMTH-NEVER-DONE"] = LIVE_PRIOR_COMPOSITE


def main() -> int:
    validation = json.loads(VALIDATION_PATH.read_text())
    client_dir = ROOT / "clients" / "farm-thru"
    shared_dir = ROOT / "shared"
    client = load_client(client_dir, shared_dir)

    rows = []
    ads = [validation["positive"]] + validation["comparison_cohort"]

    use_llm = os.environ.get("ANTHROPIC_API_KEY") is not None

    for ad in ads:
        report = score_ad(ad, client, existing_ads=ads, use_llm=use_llm)
        ad_id = ad["ad_id"]
        new_composite = report["composite"]
        prior = PRIOR_BY_ID.get(ad_id, 0.0)
        delta = round(new_composite - prior, 4)
        verdict = report["verdict"]

        # Pull the new dimension scores (recalibration-v1)
        dim_details = report.get("rubric", {}).get("dimension_details", {})
        new_dims = {
            d: dim_details.get(d, {}).get("score", "-")
            for d in (
                "ownership_framing",
                "scarcity_register",
                "founder_voice",
                "csf_placement",
                "scroll_stop_hook",
                "specificity",
                "cta_clarity",
            )
        }

        rows.append({
            "ad_id": ad_id,
            "label": ad.get("label", ""),
            "old_composite": round(prior, 4),
            "new_composite": new_composite,
            "delta": delta,
            "verdict": verdict,
            **{f"d_{k}": v for k, v in new_dims.items()},
        })

    # Write CSV
    out_path = ROOT / "validation" / "calibration-report.csv"
    if rows:
        with out_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    # Print summary
    print()
    print("=" * 78)
    print("Calibration report — recalibration-v1")
    print("=" * 78)
    for r in rows:
        delta_str = f"{r['delta']:+.4f}"
        print(f"{r['ad_id']:30s} {r['old_composite']:.4f} -> {r['new_composite']:.4f} ({delta_str})  {r['verdict']}")
    print()

    live = next(r for r in rows if r["ad_id"] == "LIVE-FMTH-NEVER-DONE")
    target = validation["target"]["positive_min_composite"]
    print(f"Live $2-lead ad target: >= {target}")
    print(f"Live $2-lead ad result: {live['new_composite']:.4f}")
    if live["new_composite"] >= target:
        print(f"PASS (live ad cleared {target} target by +{live['new_composite']-target:.4f})")
        return 0
    else:
        print(f"FAIL (live ad below target by {target-live['new_composite']:.4f}) — iterate weights")
        return 1


if __name__ == "__main__":
    sys.exit(main())
