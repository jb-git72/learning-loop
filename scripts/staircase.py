#!/usr/bin/env python3
"""Staircase (successive halving) ad racing simulator.

Replays Meta Ads Manager CSV exports day-by-day to simulate which ads
would survive budget allocation rounds. Compares staircase ROAS vs
actual ROAS and optionally correlates with quality engine scores.

Usage:
    python3 scripts/staircase.py path/to/meta-export.csv
    python3 scripts/staircase.py export.csv --window 5 --min-survivors 5
    python3 scripts/staircase.py export.csv --scored scored.json --metric roas
    python3 scripts/staircase.py export.csv --json
"""

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

root = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Column aliases — Meta exports use inconsistent names across locales/dates
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
    "date": ["Day", "Date", "Reporting starts", "date", "Reporting start"],
}


# ---------------------------------------------------------------------------
# CSV parsing helpers
# ---------------------------------------------------------------------------

def _resolve_columns(header: list) -> dict:
    """Map canonical field names to column indices. First alias match wins."""
    # Normalize header: strip whitespace
    clean = [h.strip() for h in header]
    mapping = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in clean:
                mapping[canonical] = clean.index(alias)
                break
    return mapping


def _parse_number(raw: str) -> float:
    """Strip currency symbols, commas, pct signs. Return 0.0 for blanks."""
    if not raw or not raw.strip():
        return 0.0
    cleaned = raw.strip().replace("$", "").replace(",", "").replace("%", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


_DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%b %d, %Y",
                 "%B %d, %Y", "%d-%m-%Y"]


def _parse_date(raw: str) -> date:
    """Try common date formats. Raises ValueError if none match."""
    s = raw.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {raw!r}")


def parse_meta_csv(csv_path: Path) -> tuple:
    """Parse a Meta Ads Manager CSV export.

    Returns (rows, warnings) where each row is a dict with canonical keys.
    """
    warnings = []
    rows = []

    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        col_map = _resolve_columns(header)

        # Check required columns
        required = {"ad_name", "spend", "date"}
        missing = required - set(col_map.keys())
        if missing:
            print(f"ERROR: Missing required columns: {missing}", file=sys.stderr)
            print(f"Found columns: {header}", file=sys.stderr)
            sys.exit(1)

        for i, raw_row in enumerate(reader, start=2):
            if not raw_row or len(raw_row) < 2:
                continue

            ad_name = raw_row[col_map["ad_name"]].strip() if "ad_name" in col_map else ""
            if not ad_name:
                continue  # skip summary rows

            try:
                row = {
                    "ad_name": ad_name,
                    "impressions": _parse_number(raw_row[col_map["impressions"]]) if "impressions" in col_map else 0,
                    "clicks": _parse_number(raw_row[col_map["clicks"]]) if "clicks" in col_map else 0,
                    "spend": _parse_number(raw_row[col_map["spend"]]),
                    "conversions": _parse_number(raw_row[col_map["conversions"]]) if "conversions" in col_map else 0,
                    "revenue": _parse_number(raw_row[col_map["revenue"]]) if "revenue" in col_map else 0,
                    "date": _parse_date(raw_row[col_map["date"]]),
                }
                rows.append(row)
            except (IndexError, ValueError) as e:
                warnings.append(f"Row {i}: {e}")

    if warnings:
        print(f"Parsed {len(rows)} rows with {len(warnings)} warnings", file=sys.stderr)
        for w in warnings[:5]:
            print(f"  {w}", file=sys.stderr)

    return rows, warnings


# ---------------------------------------------------------------------------
# Data aggregation
# ---------------------------------------------------------------------------

def _build_daily_data(rows: list) -> tuple:
    """Group rows into day_data[ad_name][date] = {metrics}.

    Returns (day_data, sorted_dates, ad_names).
    """
    day_data = defaultdict(dict)
    all_dates = set()
    all_ads = set()

    for row in rows:
        ad = row["ad_name"]
        d = row["date"]
        all_dates.add(d)
        all_ads.add(ad)
        # Accumulate if multiple rows per ad per day (e.g. breakdowns)
        if d in day_data[ad]:
            existing = day_data[ad][d]
            for key in ("impressions", "clicks", "spend", "conversions", "revenue"):
                existing[key] += row[key]
        else:
            day_data[ad][d] = {k: row[k] for k in
                               ("impressions", "clicks", "spend", "conversions", "revenue")}

    return dict(day_data), sorted(all_dates), sorted(all_ads)


def _aggregate_window(ad_daily: dict, window_dates: list) -> dict:
    """Sum metrics for one ad across the given dates."""
    totals = {"impressions": 0, "clicks": 0, "spend": 0.0,
              "conversions": 0, "revenue": 0.0}
    for d in window_dates:
        if d in ad_daily:
            for k in totals:
                totals[k] += ad_daily[d][k]
    return totals


# ---------------------------------------------------------------------------
# Metric calculation
# ---------------------------------------------------------------------------

HIGHER_IS_BETTER = {"roas": True, "ctr": True, "cpa": False}


def _calculate_metric(metrics: dict, metric_name: str) -> float:
    """Calculate the chosen metric from aggregated metrics.

    Returns None if the metric is undefined (e.g. CPA with 0 conversions).
    """
    if metric_name == "roas":
        if metrics["spend"] <= 0:
            return None
        return metrics["revenue"] / metrics["spend"]
    elif metric_name == "cpa":
        if metrics["conversions"] <= 0:
            return None  # can't compute CPA with 0 conversions
        return metrics["spend"] / metrics["conversions"]
    elif metric_name == "ctr":
        if metrics["impressions"] <= 0:
            return None
        return metrics["clicks"] / metrics["impressions"]
    return None


# ---------------------------------------------------------------------------
# Staircase algorithm
# ---------------------------------------------------------------------------

def run_staircase(day_data, all_dates, all_ad_names, config):
    """Run successive halving on historical data.

    Returns (rounds, final_winners).
    Each round is a dict with rankings, survivors, eliminated, metrics.
    """
    active_ads = set(all_ad_names)
    rounds = []
    date_cursor = 0
    grace_counter = defaultdict(int)  # ad -> consecutive unevaluatable rounds
    metric = config["metric"]
    higher_better = HIGHER_IS_BETTER[metric]

    while len(active_ads) > config["min_survivors"] and date_cursor < len(all_dates):
        # Determine window
        window_end = min(date_cursor + config["window_days"], len(all_dates))
        window_dates = all_dates[date_cursor:window_end]
        if not window_dates:
            break

        # Aggregate metrics for active ads
        ad_metrics = {}
        for ad in active_ads:
            ad_metrics[ad] = _aggregate_window(day_data.get(ad, {}), window_dates)

        # Calculate metric per ad
        ad_scores = {}
        unevaluatable = []
        for ad in active_ads:
            m = ad_metrics[ad]
            if m["spend"] < config["min_spend"] or m["impressions"] < config["min_impressions"]:
                unevaluatable.append(ad)
                grace_counter[ad] += 1
            else:
                score = _calculate_metric(m, metric)
                if score is None:
                    unevaluatable.append(ad)
                    grace_counter[ad] += 1
                else:
                    ad_scores[ad] = score
                    grace_counter[ad] = 0  # reset grace

        evaluatable = list(ad_scores.items())
        if len(evaluatable) < 2:
            # Not enough data — advance window without eliminating
            date_cursor = window_end
            rounds.append({
                "round": len(rounds),
                "window_start": window_dates[0].isoformat(),
                "window_end": window_dates[-1].isoformat(),
                "active_count": len(active_ads),
                "evaluatable_count": len(evaluatable),
                "skipped": True,
                "reason": "insufficient evaluatable ads",
            })
            continue

        # Rank: sort by metric (descending if higher=better, ascending if lower=better)
        # Tiebreak: lower spend (efficiency), then alphabetical
        evaluatable.sort(key=lambda x: (
            -x[1] if higher_better else x[1],
            ad_metrics[x[0]]["spend"],
            x[0],
        ))

        # Determine cut line
        n_eval = len(evaluatable)
        n_keep = max(
            config["min_survivors"],
            math.ceil(n_eval * (1 - config["elimination_pct"] / 100)),
        )
        n_keep = min(n_keep, n_eval)

        survivors = set(ad for ad, _ in evaluatable[:n_keep])
        eliminated = set(ad for ad, _ in evaluatable[n_keep:])

        # Grace period: unevaluatable ads survive once, eliminated on second round
        for ad in unevaluatable:
            if grace_counter[ad] >= 2:
                eliminated.add(ad)
            else:
                survivors.add(ad)

        round_data = {
            "round": len(rounds),
            "window_start": window_dates[0].isoformat(),
            "window_end": window_dates[-1].isoformat(),
            "active_count": len(active_ads),
            "evaluatable_count": n_eval,
            "rankings": [(ad, score, ad_metrics[ad]) for ad, score in evaluatable],
            "survivors": sorted(survivors),
            "eliminated": sorted(eliminated),
            "unevaluatable": sorted(unevaluatable),
            "skipped": False,
        }
        rounds.append(round_data)

        active_ads = survivors
        date_cursor = window_end

    return rounds, sorted(active_ads)


# ---------------------------------------------------------------------------
# Budget simulation
# ---------------------------------------------------------------------------

def simulate_budget(rounds, day_data, all_dates, all_ad_names, config):
    """Compare actual ROAS vs staircase-simulated ROAS.

    Assumption: ad ROAS is intrinsic (scales linearly with budget).
    This is a simplification documented as a caveat.
    """
    # Actual totals across entire date range
    actual_spend = 0.0
    actual_revenue = 0.0
    ad_totals = {}
    for ad in all_ad_names:
        totals = _aggregate_window(day_data.get(ad, {}), all_dates)
        ad_totals[ad] = totals
        actual_spend += totals["spend"]
        actual_revenue += totals["revenue"]

    actual_roas = actual_revenue / actual_spend if actual_spend > 0 else 0

    # Track which ads were alive in each window under staircase
    eliminated_at = {}  # ad -> round number eliminated
    for r in rounds:
        if r.get("skipped"):
            continue
        for ad in r.get("eliminated", []):
            if ad not in eliminated_at:
                eliminated_at[ad] = r["round"]

    # Budget waste: spend on ads the staircase would have eliminated
    waste = 0.0
    for ad, elim_round in eliminated_at.items():
        # Sum spend AFTER the elimination round
        if elim_round < len(rounds):
            elim_date_idx = 0
            for i, r in enumerate(rounds):
                if i == elim_round and not r.get("skipped"):
                    # This ad was killed at end of this round's window
                    break
                if not r.get("skipped"):
                    elim_date_idx += config["window_days"]

            # Sum spend from post-elimination dates
            post_dates = all_dates[elim_date_idx:]
            post_metrics = _aggregate_window(day_data.get(ad, {}), post_dates)
            waste += post_metrics["spend"]

    # Simulated staircase ROAS: survivors' ROAS applied to full budget
    # (budget redistributed, not saved)
    survivor_ads = set(all_ad_names) - set(eliminated_at.keys())
    survivor_spend = sum(ad_totals[ad]["spend"] for ad in survivor_ads)
    survivor_revenue = sum(ad_totals[ad]["revenue"] for ad in survivor_ads)
    survivor_roas = survivor_revenue / survivor_spend if survivor_spend > 0 else 0

    # Projected: if eliminated budget went to survivors proportionally
    projected_revenue = 0.0
    if survivor_spend > 0:
        for ad in survivor_ads:
            ad_roas = ad_totals[ad]["revenue"] / ad_totals[ad]["spend"] if ad_totals[ad]["spend"] > 0 else 0
            share = ad_totals[ad]["spend"] / survivor_spend
            projected_revenue += ad_roas * (share * actual_spend)

    projected_roas = projected_revenue / actual_spend if actual_spend > 0 else 0

    return {
        "actual_spend": actual_spend,
        "actual_revenue": actual_revenue,
        "actual_roas": actual_roas,
        "survivor_roas": survivor_roas,
        "projected_roas": projected_roas,
        "budget_waste": waste,
        "waste_pct": (waste / actual_spend * 100) if actual_spend > 0 else 0,
        "improvement_pct": ((projected_roas - actual_roas) / actual_roas * 100) if actual_roas > 0 else 0,
        "n_survivors": len(survivor_ads),
        "n_eliminated": len(eliminated_at),
    }


# ---------------------------------------------------------------------------
# Quality score correlation (optional)
# ---------------------------------------------------------------------------

def load_quality_scores(scored_path: Path) -> dict:
    """Load scored JSON → {ad_id: composite_score}."""
    with open(scored_path) as f:
        data = json.load(f)

    scores = {}
    results = data if isinstance(data, list) else data.get("results", data.get("items", []))
    for item in results:
        ad_id = item.get("ad_id", item.get("id", ""))
        composite = item.get("composite", item.get("score", 0))
        if ad_id:
            scores[ad_id] = composite
    return scores


def match_quality_scores(ad_names: list, quality_map: dict) -> dict:
    """Match Meta ad_names to quality scores via 3-tier matching."""
    matched = {}
    for ad_name in ad_names:
        # Exact match
        if ad_name in quality_map:
            matched[ad_name] = quality_map[ad_name]
            continue
        # Prefix match
        for qid, score in quality_map.items():
            if ad_name.startswith(qid):
                matched[ad_name] = score
                break
        else:
            # Substring match
            for qid, score in quality_map.items():
                if qid in ad_name:
                    matched[ad_name] = score
                    break
    return matched


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


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _fmt_metric(value, metric_name: str) -> str:
    if value is None:
        return "N/A"
    if metric_name == "roas":
        return f"{value:.2f}x"
    elif metric_name == "cpa":
        return f"${value:.2f}"
    elif metric_name == "ctr":
        return f"{value:.2%}"
    return f"{value:.3f}"


def print_results(rounds, winners, budget_sim, quality_matches, config,
                  all_ad_names, day_data, all_dates):
    """Print human-readable staircase results."""
    metric = config["metric"]

    print(f"=== STAIRCASE SIMULATION ===")
    print(f"Ads: {len(all_ad_names)} | "
          f"Dates: {all_dates[0]} to {all_dates[-1]} | "
          f"Rounds: {len([r for r in rounds if not r.get('skipped')])} | "
          f"Metric: {metric.upper()}")
    print(f"Window: {config['window_days']}d | "
          f"Elimination: {config['elimination_pct']}% | "
          f"Min survivors: {config['min_survivors']}")
    print()

    for r in rounds:
        if r.get("skipped"):
            print(f"--- Round {r['round']} ({r['window_start']} - {r['window_end']}): "
                  f"SKIPPED ({r.get('reason', '')}) ---")
            print()
            continue

        n_surv = len(r["survivors"])
        n_elim = len(r["eliminated"])
        print(f"--- Round {r['round']} ({r['window_start']} - {r['window_end']}): "
              f"{r['active_count']} ads -> {n_surv} survivors ---")

        for rank, (ad, score, metrics) in enumerate(r["rankings"][:10], 1):
            status = "SURVIVED" if ad in r["survivors"] else "ELIMINATED"
            marker = " " if ad in r["survivors"] else "x"
            print(f"  {marker} #{rank:<3} {ad:<30} "
                  f"{metric.upper()} {_fmt_metric(score, metric):>8}  "
                  f"${metrics['spend']:>8.2f} spend  "
                  f"${metrics['revenue']:>8.2f} rev")

        if len(r["rankings"]) > 10:
            print(f"  ... and {len(r['rankings']) - 10} more")

        if r["unevaluatable"]:
            print(f"  Grace period: {', '.join(r['unevaluatable'][:5])}"
                  f"{' ...' if len(r['unevaluatable']) > 5 else ''}")

        if r["eliminated"]:
            elim_names = ", ".join(r["eliminated"][:8])
            suffix = " ..." if n_elim > 8 else ""
            print(f"  Eliminated ({n_elim}): {elim_names}{suffix}")
        print()

    # Final winners
    print(f"=== FINAL WINNERS ({len(winners)}) ===")
    for i, ad in enumerate(winners, 1):
        totals = _aggregate_window(day_data.get(ad, {}), all_dates)
        total_metric = _calculate_metric(totals, metric)
        quality = quality_matches.get(ad)
        q_str = f"  (quality: {quality:.3f})" if quality is not None else ""
        print(f"  #{i}  {ad:<30} {metric.upper()} {_fmt_metric(total_metric, metric):>8}"
              f"  ${totals['spend']:.2f} spend{q_str}")
    print()

    # Performance comparison
    print(f"=== PERFORMANCE COMPARISON ===")
    print(f"  Actual {metric.upper()}:      {_fmt_metric(budget_sim['actual_roas'], metric)}"
          f"  (${budget_sim['actual_spend']:,.2f} spend -> "
          f"${budget_sim['actual_revenue']:,.2f} revenue)")
    print(f"  Projected {metric.upper()}:   {_fmt_metric(budget_sim['projected_roas'], metric)}"
          f"  ({budget_sim['improvement_pct']:+.1f}% improvement)")
    print(f"  Budget on eliminated: ${budget_sim['budget_waste']:,.2f}"
          f"  ({budget_sim['waste_pct']:.1f}% of total spend)")
    print(f"  Survivors: {budget_sim['n_survivors']} | "
          f"Eliminated: {budget_sim['n_eliminated']}")
    print()

    # Quality correlation
    if quality_matches:
        # Correlate quality score vs actual ROAS
        paired = []
        for ad in all_ad_names:
            if ad in quality_matches:
                totals = _aggregate_window(day_data.get(ad, {}), all_dates)
                m = _calculate_metric(totals, metric)
                if m is not None:
                    paired.append((quality_matches[ad], m))

        if len(paired) >= 3:
            qs = [p[0] for p in paired]
            ms = [p[1] for p in paired]
            r = pearson_r(qs, ms)
            print(f"=== QUALITY CORRELATION ===")
            print(f"  Pearson r (quality vs {metric}): "
                  f"{r:.3f} (n={len(paired)})")

            # Correlation with survival
            rounds_survived = {}
            for ad in all_ad_names:
                survived = sum(1 for rd in rounds
                               if not rd.get("skipped") and ad in rd.get("survivors", []))
                rounds_survived[ad] = survived

            surv_paired = [(quality_matches[ad], rounds_survived.get(ad, 0))
                           for ad in all_ad_names if ad in quality_matches]
            if len(surv_paired) >= 3:
                qs2 = [p[0] for p in surv_paired]
                ss = [p[1] for p in surv_paired]
                r2 = pearson_r(qs2, ss)
                print(f"  Pearson r (quality vs rounds survived): "
                      f"{r2:.3f} (n={len(surv_paired)})")
            print()


def print_json_results(rounds, winners, budget_sim, quality_matches,
                       all_ad_names, day_data, all_dates, config):
    """Print machine-readable JSON output."""
    metric = config["metric"]

    # Build elimination summary
    elimination_map = {}
    for r in rounds:
        if r.get("skipped"):
            continue
        for ad in r.get("eliminated", []):
            if ad not in elimination_map:
                totals = _aggregate_window(day_data.get(ad, {}), all_dates)
                elimination_map[ad] = {
                    "ad_name": ad,
                    "eliminated_round": r["round"],
                    f"actual_{metric}": _calculate_metric(totals, metric),
                    "total_spend": totals["spend"],
                    "total_revenue": totals["revenue"],
                    "quality_score": quality_matches.get(ad),
                }

    output = {
        "config": config,
        "summary": budget_sim,
        "rounds": [{k: v for k, v in r.items()
                     if k not in ("rankings",)}  # rankings have non-serializable data
                    for r in rounds],
        "winners": winners,
        "eliminated": list(elimination_map.values()),
    }
    print(json.dumps(output, indent=2, default=str))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Staircase (successive halving) ad racing simulator. "
                    "Replays Meta Ads Manager CSV exports to find winners.")
    parser.add_argument("csv", help="Path to Meta Ads Manager CSV export")
    parser.add_argument("--scored", default=None,
                        help="Path to scored JSON for quality correlation")
    parser.add_argument("--window", type=int, default=3,
                        help="Measurement window in days (default: 3)")
    parser.add_argument("--elimination", type=int, default=50,
                        help="Percent to eliminate each round (default: 50)")
    parser.add_argument("--min-survivors", type=int, default=3,
                        help="Stop when this many ads remain (default: 3)")
    parser.add_argument("--min-impressions", type=int, default=100,
                        help="Minimum impressions to evaluate (default: 100)")
    parser.add_argument("--min-spend", type=float, default=1.0,
                        help="Minimum spend to evaluate (default: 1.0)")
    parser.add_argument("--metric", choices=["roas", "cpa", "ctr"],
                        default="roas",
                        help="Primary ranking metric (default: roas)")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output results as JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    csv_path = Path(args.csv)

    if not csv_path.exists():
        print(f"ERROR: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    # Parse CSV
    rows, warnings = parse_meta_csv(csv_path)
    if not rows:
        print("ERROR: No data rows found in CSV", file=sys.stderr)
        sys.exit(1)

    # Aggregate
    day_data, all_dates, all_ad_names = _build_daily_data(rows)
    print(f"Loaded {len(rows)} rows: {len(all_ad_names)} ads, "
          f"{len(all_dates)} days ({all_dates[0]} to {all_dates[-1]})",
          file=sys.stderr)

    config = {
        "window_days": args.window,
        "elimination_pct": args.elimination,
        "min_survivors": args.min_survivors,
        "min_impressions": args.min_impressions,
        "min_spend": args.min_spend,
        "metric": args.metric,
    }

    # Run staircase
    rounds, winners = run_staircase(day_data, all_dates, all_ad_names, config)

    # Budget simulation
    budget_sim = simulate_budget(rounds, day_data, all_dates, all_ad_names, config)

    # Quality correlation (optional)
    quality_matches = {}
    if args.scored:
        scored_path = Path(args.scored)
        if scored_path.exists():
            quality_map = load_quality_scores(scored_path)
            quality_matches = match_quality_scores(all_ad_names, quality_map)
            print(f"Matched {len(quality_matches)}/{len(all_ad_names)} ads "
                  f"to quality scores", file=sys.stderr)
        else:
            print(f"WARNING: Scored file not found: {scored_path}", file=sys.stderr)

    # Output
    if args.json_output:
        print_json_results(rounds, winners, budget_sim, quality_matches,
                           all_ad_names, day_data, all_dates, config)
    else:
        print_results(rounds, winners, budget_sim, quality_matches, config,
                      all_ad_names, day_data, all_dates)


if __name__ == "__main__":
    main()
