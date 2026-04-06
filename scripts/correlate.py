#!/usr/bin/env python3
"""Correlate quality engine scores with real ad performance (ROAS/CPA/CTR).

Joins scored JSON from score_batch.py with Meta Ads Manager CSV metrics.
Computes overall correlation + breakdown by angle, hook, and rubric dimension.

Usage:
    python3 scripts/correlate.py --scored scored.json --csv meta-export.csv
    python3 scripts/correlate.py --scored scored.json --csv export.csv --metric roas
    python3 scripts/correlate.py --scored scored.json --csv export.csv --json
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

root = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# CSV column aliases (same as staircase.py / classify_ads.py)
# ---------------------------------------------------------------------------

COLUMN_ALIASES = {
    "ad_name": ["Ad name", "Ad Name", "ad_name", "Ad"],
    "impressions": ["Impressions", "impressions", "Impr."],
    "clicks": ["Link clicks", "Clicks (all)", "clicks", "Clicks",
               "Outbound clicks", "Link Clicks"],
    "spend": ["Amount spent (AUD)", "Amount spent (USD)", "Amount spent",
              "Spend", "spend", "Cost"],
    "conversions": ["Purchases", "Results", "Conversions", "conversions",
                    "Website purchases", "Offsite conversions"],
    "revenue": ["Purchase ROAS (denominator)", "Conversion value",
                "conversion_value", "revenue", "Revenue",
                "Website purchase conversion value",
                "Website purchases conversion value",
                "Purchases conversion value"],
    "roas": ["Website purchase ROAS (return on advertising spend)",
             "Purchase ROAS", "ROAS", "roas"],
}


def _resolve_columns(header: list) -> dict:
    clean = [h.strip() for h in header]
    mapping = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in clean:
                mapping[canonical] = clean.index(alias)
                break
    return mapping


def _parse_number(raw: str) -> float:
    if not raw or not raw.strip():
        return 0.0
    cleaned = raw.strip().replace("$", "").replace(",", "").replace("%", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_csv_metrics(csv_path: Path) -> dict:
    """Load per-ad metrics from Meta CSV. Returns {ad_name: {metrics}}."""
    ads = {}
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        col_map = _resolve_columns(header)

        if "ad_name" not in col_map:
            print(f"ERROR: No 'Ad name' column. Found: {header}", file=sys.stderr)
            sys.exit(1)

        for row in reader:
            if not row or len(row) < 2:
                continue
            name = row[col_map["ad_name"]].strip()
            if not name:
                continue

            # Aggregate if ad appears multiple times
            if name not in ads:
                ads[name] = {"spend": 0, "revenue": 0, "conversions": 0,
                             "impressions": 0, "clicks": 0, "roas": None}

            m = ads[name]
            m["spend"] += _parse_number(row[col_map["spend"]]) if "spend" in col_map else 0
            m["revenue"] += _parse_number(row[col_map["revenue"]]) if "revenue" in col_map else 0
            m["conversions"] += _parse_number(row[col_map["conversions"]]) if "conversions" in col_map else 0
            m["impressions"] += _parse_number(row[col_map["impressions"]]) if "impressions" in col_map else 0
            m["clicks"] += _parse_number(row[col_map["clicks"]]) if "clicks" in col_map else 0

            # Direct ROAS column (use last value if multiple rows)
            if "roas" in col_map:
                roas_val = _parse_number(row[col_map["roas"]])
                if roas_val > 0:
                    m["roas"] = roas_val

    # Compute ROAS from spend/revenue if not directly available
    for name, m in ads.items():
        if m["roas"] is None and m["spend"] > 0:
            m["roas"] = m["revenue"] / m["spend"]
        elif m["roas"] is None:
            m["roas"] = 0.0

    return ads


def load_scored_json(scored_path: Path) -> list:
    """Load scored results. Returns list of scored ad dicts."""
    with open(scored_path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("results", data.get("items", []))


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def match_ads(scored_ads: list, csv_metrics: dict) -> list:
    """Match scored ads to CSV metrics via original_ad_name or ad_id.

    Returns list of {ad_id, ad_name, composite, roas, angle, hook_type, ...}
    """
    matched = []
    csv_names = set(csv_metrics.keys())

    for ad in scored_ads:
        ad_id = ad.get("ad_id", "")
        original_name = ad.get("original_ad_name", "")
        composite = ad.get("composite", 0)

        # Try matching: original_ad_name (exact) > ad_id in csv > substring
        match_name = None
        if original_name in csv_names:
            match_name = original_name
        elif ad_id in csv_names:
            match_name = ad_id
        else:
            # Substring: check if any CSV name contains ad_id
            for cn in csv_names:
                if ad_id and ad_id in cn:
                    match_name = cn
                    break

        if match_name is None:
            continue

        m = csv_metrics[match_name]
        matched.append({
            "ad_id": ad_id,
            "ad_name": match_name,
            "composite": composite,
            "roas": m["roas"],
            "spend": m["spend"],
            "revenue": m["revenue"],
            "conversions": m["conversions"],
            "angle": ad.get("angle", "?"),
            "hook_type": ad.get("hook_type", "?"),
            "verdict": ad.get("verdict", "?"),
            "dimension_details": ad.get("rubric", {}).get("dimension_details", {}),
        })

    return matched


# ---------------------------------------------------------------------------
# Correlation
# ---------------------------------------------------------------------------

def pearson_r(xs: list, ys: list) -> float:
    """Pearson correlation coefficient. Returns None if n < 3."""
    n = len(xs)
    if n < 3:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    denom = (var_x * var_y) ** 0.5
    return cov / denom if denom > 0 else 0.0


def spearman_r(xs: list, ys: list) -> float:
    """Spearman rank correlation. Returns None if n < 3."""
    n = len(xs)
    if n < 3:
        return None

    def _rank(vals):
        indexed = sorted(range(n), key=lambda i: vals[i])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j < n - 1 and vals[indexed[j]] == vals[indexed[j + 1]]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                ranks[indexed[k]] = avg_rank
            i = j + 1
        return ranks

    return pearson_r(_rank(xs), _rank(ys))


def compute_metric(matched: list, metric: str) -> list:
    """Extract (composite, metric_value) pairs. Filters out invalid entries."""
    pairs = []
    for m in matched:
        if metric == "roas":
            val = m["roas"]
            if val is not None and m["spend"] > 0:
                pairs.append((m["composite"], val))
        elif metric == "cpa":
            if m["conversions"] > 0 and m["spend"] > 0:
                pairs.append((m["composite"], m["spend"] / m["conversions"]))
        elif metric == "ctr":
            imp = m.get("impressions", 0)
            clicks = m.get("clicks", 0)
            if imp > 0:
                pairs.append((m["composite"], clicks / imp))
        elif metric == "purchases":
            if m["conversions"] > 0:
                pairs.append((m["composite"], m["conversions"]))
    return pairs


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_results(matched: list, metric: str, min_spend: float):
    """Print human-readable correlation analysis."""
    # Filter by min spend
    filtered = [m for m in matched if m["spend"] >= min_spend]

    if not filtered:
        print("No ads matched with sufficient spend.")
        return

    print(f"=== QUALITY vs PERFORMANCE CORRELATION ===")
    print(f"Matched ads: {len(filtered)} (min spend: ${min_spend:.0f})")
    print(f"Metric: {metric.upper()}")
    print()

    # Overall correlation
    pairs = compute_metric(filtered, metric)
    if len(pairs) >= 3:
        composites = [p[0] for p in pairs]
        metrics = [p[1] for p in pairs]
        r = pearson_r(composites, metrics)
        rho = spearman_r(composites, metrics)
        print(f"Overall Pearson  r (quality vs {metric}): {r:.3f} (n={len(pairs)})")
        print(f"Overall Spearman ρ (quality vs {metric}): {rho:.3f} (n={len(pairs)})")
        print()

        best_r = max(abs(r), abs(rho))
        if best_r >= 0.6:
            print("  Strong correlation — scoring engine predicts performance well")
        elif best_r >= 0.3:
            print("  Moderate correlation — some signal, check dimension breakdown")
        else:
            print("  Weak correlation — scorer needs recalibration")
        print()
    else:
        print(f"Not enough data for overall correlation (n={len(pairs)})")
        print()

    # Top and bottom ads
    if metric == "cpa":
        filtered.sort(key=lambda m: m["spend"] / m["conversions"] if m["conversions"] > 0 else float("inf"))
    else:
        filtered.sort(key=lambda m: m.get("roas", 0), reverse=True)

    print(f"--- TOP 10 BY {metric.upper()} ---")
    for i, m in enumerate(filtered[:10], 1):
        roas_str = f"{m['roas']:.1f}x" if m["roas"] else "N/A"
        print(f"  #{i:<3} {m['ad_name'][:45]:<45} "
              f"ROAS={roas_str:>7}  quality={m['composite']:.3f}  "
              f"[{m['angle']}/{m['hook_type']}]")
    print()

    print(f"--- BOTTOM 10 BY {metric.upper()} ---")
    for i, m in enumerate(filtered[-10:], len(filtered) - 9):
        roas_str = f"{m['roas']:.1f}x" if m["roas"] else "N/A"
        print(f"  #{i:<3} {m['ad_name'][:45]:<45} "
              f"ROAS={roas_str:>7}  quality={m['composite']:.3f}  "
              f"[{m['angle']}/{m['hook_type']}]")
    print()

    # Breakdown by angle
    print(f"--- BY ANGLE ---")
    angle_groups = defaultdict(list)
    for m in filtered:
        angle_groups[m["angle"]].append(m)

    angle_stats = []
    for angle, ads in angle_groups.items():
        avg_roas = sum(a["roas"] for a in ads if a["roas"]) / len(ads) if ads else 0
        avg_quality = sum(a["composite"] for a in ads) / len(ads) if ads else 0
        avg_spend = sum(a["spend"] for a in ads) / len(ads) if ads else 0
        angle_stats.append((angle, len(ads), avg_roas, avg_quality, avg_spend))

    angle_stats.sort(key=lambda x: x[2], reverse=True)
    print(f"  {'Angle':<30} {'n':>4} {'Avg ROAS':>10} {'Avg Quality':>12} {'Avg Spend':>10}")
    print(f"  {'-'*30} {'-'*4} {'-'*10} {'-'*12} {'-'*10}")
    for angle, n, avg_r, avg_q, avg_s in angle_stats:
        print(f"  {angle:<30} {n:>4} {avg_r:>9.1f}x {avg_q:>11.3f} ${avg_s:>9.0f}")
    print()

    # Breakdown by hook
    print(f"--- BY HOOK ---")
    hook_groups = defaultdict(list)
    for m in filtered:
        hook_groups[m["hook_type"]].append(m)

    hook_stats = []
    for hook, ads in hook_groups.items():
        avg_roas = sum(a["roas"] for a in ads if a["roas"]) / len(ads) if ads else 0
        avg_quality = sum(a["composite"] for a in ads) / len(ads) if ads else 0
        hook_stats.append((hook, len(ads), avg_roas, avg_quality))

    hook_stats.sort(key=lambda x: x[2], reverse=True)
    print(f"  {'Hook':<25} {'n':>4} {'Avg ROAS':>10} {'Avg Quality':>12}")
    print(f"  {'-'*25} {'-'*4} {'-'*10} {'-'*12}")
    for hook, n, avg_r, avg_q in hook_stats:
        print(f"  {hook:<25} {n:>4} {avg_r:>9.1f}x {avg_q:>11.3f}")
    print()

    # Dimension-level correlation (which rubric dimensions predict ROAS?)
    dim_names = set()
    for m in filtered:
        dim_names.update(m.get("dimension_details", {}).keys())

    if dim_names:
        print(f"--- DIMENSION CORRELATION WITH {metric.upper()} ---")
        dim_corrs = []
        for dim in sorted(dim_names):
            dim_pairs = []
            for m in filtered:
                dd = m.get("dimension_details", {})
                if dim in dd:
                    dim_score = dd[dim].get("score", 0)
                    if metric == "roas" and m["roas"] and m["spend"] > 0:
                        dim_pairs.append((dim_score, m["roas"]))
            if len(dim_pairs) >= 3:
                ds = [p[0] for p in dim_pairs]
                ms = [p[1] for p in dim_pairs]
                r = pearson_r(ds, ms)
                rho = spearman_r(ds, ms)
                dim_corrs.append((dim, r, rho, len(dim_pairs)))

        dim_corrs.sort(key=lambda x: abs(x[2]), reverse=True)  # sort by Spearman
        print(f"  {'Dimension':<30} {'Pearson':>8} {'Spearman':>9} {'n':>5}  Signal")
        print(f"  {'-'*30} {'-'*8} {'-'*9} {'-'*5}  {'-'*20}")
        for dim, r, rho, n in dim_corrs:
            strength = "STRONG" if abs(rho) >= 0.4 else "moderate" if abs(rho) >= 0.2 else "weak"
            direction = "+" if rho >= 0 else "-"
            print(f"  {dim:<30} {r:>7.3f} {rho:>8.3f} {n:>5}  {direction} {strength}")
        print()


def print_json_output(matched: list, metric: str, min_spend: float):
    """Print machine-readable JSON."""
    filtered = [m for m in matched if m["spend"] >= min_spend]
    pairs = compute_metric(filtered, metric)

    overall_r = None
    if len(pairs) >= 3:
        overall_r = pearson_r([p[0] for p in pairs], [p[1] for p in pairs])

    # Angle breakdown
    angle_groups = defaultdict(list)
    for m in filtered:
        angle_groups[m["angle"]].append(m)
    angle_summary = {
        a: {"n": len(ads),
            "avg_roas": sum(x["roas"] for x in ads) / len(ads),
            "avg_quality": sum(x["composite"] for x in ads) / len(ads)}
        for a, ads in angle_groups.items()
    }

    output = {
        "n_matched": len(filtered),
        "metric": metric,
        "min_spend": min_spend,
        "overall_pearson_r": overall_r,
        "angle_summary": angle_summary,
        "ads": [{k: v for k, v in m.items() if k != "dimension_details"}
                for m in filtered],
    }
    print(json.dumps(output, indent=2, default=str))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Correlate quality scores with real ad performance")
    parser.add_argument("--scored", required=True,
                        help="Path to scored JSON (from score_batch.py)")
    parser.add_argument("--csv", required=True,
                        help="Path to Meta Ads Manager CSV with performance data")
    parser.add_argument("--metric", choices=["roas", "cpa", "ctr", "purchases"],
                        default="roas", help="Performance metric (default: roas)")
    parser.add_argument("--min-spend", type=float, default=100.0,
                        help="Min spend to include ad in analysis (default: $100)")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output as JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    scored_path = Path(args.scored)
    csv_path = Path(args.csv)

    if not scored_path.exists():
        print(f"ERROR: Scored file not found: {scored_path}", file=sys.stderr)
        sys.exit(1)
    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    # Load data
    scored_ads = load_scored_json(scored_path)
    csv_metrics = load_csv_metrics(csv_path)
    print(f"Loaded {len(scored_ads)} scored ads, {len(csv_metrics)} CSV ads",
          file=sys.stderr)

    # Match
    matched = match_ads(scored_ads, csv_metrics)
    print(f"Matched {len(matched)}/{len(scored_ads)} ads to CSV metrics",
          file=sys.stderr)

    if not matched:
        print("ERROR: No ads matched between scored JSON and CSV.",
              file=sys.stderr)
        print("Check that ad_id or original_ad_name in scored JSON matches "
              "Ad name in CSV.", file=sys.stderr)
        sys.exit(1)

    # Output
    if args.json_output:
        print_json_output(matched, args.metric, args.min_spend)
    else:
        print_results(matched, args.metric, args.min_spend)


if __name__ == "__main__":
    main()
