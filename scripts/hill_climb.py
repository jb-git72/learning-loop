#!/usr/bin/env python3
"""Hill-climb all content to strong_draft+ before human review.

Supports two strategies:
  --strategy greedy        Original 1-candidate-per-iteration (backwards compat)
  --strategy evolutionary  Population-based with mutation, crossover, wildcard,
                           and dimension-targeted improvement (default)

Usage:
  python3 scripts/hill_climb.py farm-thru 3
  python3 scripts/hill_climb.py farm-thru 3 --strategy=evolutionary --population=5
  python3 scripts/hill_climb.py farm-thru 3 --type=meta-ad --target=0.75
"""

import argparse
import json
import os
import random
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
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
from engine.llm_judge import score_pairwise
from scripts.lint_content import lint
from writer import generate_variant, HOOK_TEMPLATES, HOOK_METADATA


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="Hill-climb content to strong_draft+")
    parser.add_argument("client", nargs="?", default="farm-thru", help="Client ID")
    parser.add_argument("iterations", nargs="?", type=int, default=3, help="Max iterations per item")
    parser.add_argument("--type", dest="type_filter", default=None, help="Filter by content_type (e.g. meta-ad)")
    parser.add_argument("--target", type=float, default=0.70, help="Target composite score (default 0.70)")
    parser.add_argument("--strategy", choices=["greedy", "evolutionary"], default="evolutionary",
                        help="Hill-climbing strategy (default: evolutionary)")
    parser.add_argument("--population", type=int, default=3, help="Candidates per iteration in evolutionary mode (default 3)")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM scoring (deterministic only)")
    parser.add_argument("--use-pairwise", action="store_true", help="Enable pairwise comparison gating on accepted candidates")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent ads per iteration in evolutionary mode (default 4)")
    parser.add_argument("--tournament", action="store_true", help="Tournament mode: cull bottom 50%% after each iteration")

    # Support legacy positional-only invocation: hill_climb.py <client> <iters>
    # Also support the old --type=X inline style
    args, unknown = parser.parse_known_args()
    for u in unknown:
        if u.startswith("--type="):
            args.type_filter = u.split("=", 1)[1]
    return args


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_ad_id(ad: dict) -> str:
    return ad.get("ad_id", ad.get("page_id", ad.get("email_id", "?")))


def _get_weak_dimensions(report: dict, threshold: int = 3, max_dims: int = 2) -> list:
    """Find the weakest rubric dimensions from a score report.

    Returns list of (dim_name, score, max_score) tuples for dimensions
    scoring at or below threshold (out of 5), limited to max_dims.
    """
    dim_details = report.get("rubric", {}).get("dimension_details", {})
    weak = []
    for dim_id, detail in dim_details.items():
        score = detail.get("score", 5)
        if score <= threshold:
            weak.append((dim_id, score, 5))
    # Sort by score ascending (weakest first), then cap
    weak.sort(key=lambda x: x[1])
    return weak[:max_dims]


def _load_industry_playbook(client_dir: Path) -> dict:
    """Load the industry playbook for this client (JSON). Falls back to general."""
    config_path = client_dir / "config.json"
    industry = "general"
    if config_path.exists():
        with open(config_path) as f:
            industry = json.load(f).get("industry", "general")
    playbook_path = root / "shared" / "playbooks" / f"{industry}.json"
    if not playbook_path.exists():
        playbook_path = root / "shared" / "playbooks" / "general.json"
    if playbook_path.exists():
        with open(playbook_path) as f:
            return json.load(f)
    return {}


def _pick_mutated_hook(current_hook: str, playbook: dict = None,
                       recent_hooks: list = None) -> str:
    """Pick a hook weighted by benchmark hit rate and industry playbook.

    Uses: benchmark_hit_rate × industry_hook_weight × recency_factor.
    20% of the time picks purely random to preserve exploration.
    """
    available = [h for h in HOOK_TEMPLATES if h != current_hook]
    if not available:
        return current_hook

    # 20% pure random for exploration
    if random.random() < 0.2:
        return random.choice(available)

    # Weighted selection
    hook_weights_from_playbook = playbook.get("hook_weights", {}) if playbook else {}
    recent = set(recent_hooks or [])

    weights = []
    for h in available:
        meta = HOOK_METADATA.get(h, {})
        hit_rate = meta.get("benchmark_hit_rate", 0.05)
        industry_weight = hook_weights_from_playbook.get(h, 1.0)
        recency_factor = 0.5 if h in recent else 1.0
        weights.append(hit_rate * industry_weight * recency_factor)

    return random.choices(available, weights=weights, k=1)[0]


def _pick_wildcard_hook(playbook: dict = None, tested_hooks: set = None) -> str:
    """Pick a hook for wildcard mode — prefer untested high-potential hooks."""
    all_hooks = list(HOOK_TEMPLATES.keys())
    tested = tested_hooks or set()
    untested = [h for h in all_hooks if h not in tested]

    if untested and playbook:
        # Weight untested hooks by industry playbook weights
        hook_weights = playbook.get("hook_weights", {})
        weights = [hook_weights.get(h, 1.0) for h in untested]
        return random.choices(untested, weights=weights, k=1)[0]
    elif untested:
        return random.choice(untested)
    else:
        return random.choice(all_hooks)


def _pick_donor_ad(all_items: list, current_ad: dict, content_type: str):
    """Pick a high-scoring donor ad of the same content type for crossover.

    Returns the ad dict of the best-scoring ad that isn't the current one,
    or None if no suitable donor exists.
    """
    candidates = [
        item for item in all_items
        if item["ad"].get("content_type") == content_type
        and _get_ad_id(item["ad"]) != _get_ad_id(current_ad)
        and item.get("score", 0) > 0
    ]
    if not candidates:
        return None
    # Sort by score descending, pick from top 3
    candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
    top = candidates[:3]
    return random.choice(top)["ad"]


def _generate_and_lint(ad, item, client_dir, shared_dir, client, all_ads, recent_failures,
                       mode, hook_type, donor_ad, weak_dimensions, use_llm):
    """Generate one candidate, lint it, score it if lint passes.

    Returns (new_ad, new_score, new_report, status_msg) or None on failure.
    """
    content_type = ad.get("content_type", "meta-ad")
    try:
        new_ad = generate_variant(
            angle=ad.get("angle", "quality-craft"),
            tactic=ad.get("tactic", "general"),
            hook_type=hook_type,
            funnel=ad.get("funnel", "TOF"),
            client_dir=client_dir,
            current_best=ad,
            recent_failures=recent_failures[-5:],
            content_type=content_type,
            mode=mode,
            donor_ad=donor_ad,
            weak_dimensions=weak_dimensions,
        )

        # Preserve metadata from original
        for key in ["ad_id", "page_id", "email_id", "email_type"]:
            if key in ad:
                new_ad[key] = ad[key]

        # Lint gate
        lint_result = lint(new_ad, client_dir, shared_dir)
        if not lint_result.passed:
            details = "; ".join(v["detail"][:60] for v in lint_result.violations[:3])
            return None, 0, None, f"LINT FAIL ({mode}): {details}"

        # Deterministic pre-screen: skip LLM judge for obvious losers
        if use_llm:
            old_score = item.get("score", 0)
            pre_report = score_ad(new_ad, client, existing_ads=all_ads, use_llm=False)
            if pre_report["composite"] < old_score - 0.15:
                return new_ad, pre_report["composite"], pre_report, None

        # Full score (with LLM judge if enabled)
        new_report = score_ad(new_ad, client, existing_ads=all_ads, use_llm=use_llm)
        new_score = new_report["composite"]
        return new_ad, new_score, new_report, None

    except Exception as e:
        return None, 0, None, f"ERROR ({mode}): {e}"


# ---------------------------------------------------------------------------
# Greedy strategy (original behavior)
# ---------------------------------------------------------------------------

def run_greedy(all_items, all_ads, client, client_dir, shared_dir, max_iterations, target, use_llm,
               use_pairwise=False):
    """Original 1-candidate-per-iteration greedy hill-climb."""
    recent_failures = []
    improved = 0

    for iteration in range(max_iterations):
        below = [i for i in all_items if i["score"] < target]
        if not below:
            print(f"All items at target after iteration {iteration}!")
            break

        print(f"--- Iteration {iteration + 1}: {len(below)} items below target ---")

        for item in below:
            ad = item["ad"]
            ad_id = _get_ad_id(ad)
            content_type = ad.get("content_type", "meta-ad")
            old_score = item["score"]

            print(f"  {ad_id} ({content_type}): {old_score:.3f} [{item['verdict']}] -> generating...", end=" ", flush=True)

            new_ad, new_score, new_report, err = _generate_and_lint(
                ad, item, client_dir, shared_dir, client, all_ads, recent_failures,
                mode="improve", hook_type=ad.get("hook_type", "story"),
                donor_ad=None, weak_dimensions=None, use_llm=use_llm,
            )

            if err:
                recent_failures.append(f"{ad_id}: {err}")
                print(err)
                continue

            if new_score > old_score:
                if use_pairwise:
                    pw_score, pw_reason = score_pairwise(
                        new_ad, ad, client["config"],
                    )
                    if pw_score <= 2:
                        delta = new_score - old_score
                        recent_failures.append(f"{ad_id}: pairwise rejected ({pw_score}/5)")
                        print(f"PAIRWISE REJECT: rubric +{delta:.3f} but pairwise {pw_score}/5 — {pw_reason}")
                    else:
                        _accept_candidate(item, new_ad, new_score, new_report, all_ads, ad)
                        improved += 1
                        print(f"{new_score:.3f} [{new_report['verdict']}] IMPROVED (+{new_score - old_score:.3f}) pairwise {pw_score}/5")
                else:
                    _accept_candidate(item, new_ad, new_score, new_report, all_ads, ad)
                    improved += 1
                    print(f"{new_score:.3f} [{new_report['verdict']}] IMPROVED (+{new_score - old_score:.3f})")
            else:
                recent_failures.append(f"{ad_id}: tried {new_ad.get('hook_type', '?')} hook, scored {new_score:.3f}")
                print(f"{new_score:.3f} no improvement, kept original")

        print()

    return improved


# ---------------------------------------------------------------------------
# Evolutionary strategy
# ---------------------------------------------------------------------------

def _build_candidate_configs(ad, all_items, iteration, population_size,
                             playbook, recent_hooks, tested_hooks):
    """Pre-build all candidate config dicts for a single ad (Tier 3).

    Pure function — no API calls, no I/O. Just strategy selection.
    Returns list of candidate config dicts.
    """
    content_type = ad.get("content_type", "meta-ad")
    current_hook = ad.get("hook_type", "story")
    weak_dims = None  # caller passes report separately

    candidates = []

    # Slot 1: exploitation — improve with current hook
    candidates.append({
        "mode": "improve",
        "hook_type": current_hook,
        "donor_ad": None,
        "weak_dimensions": None,
        "label": "improve",
    })

    # Slot 2: exploration via benchmark-informed mutation
    mutated_hook = _pick_mutated_hook(current_hook, playbook, recent_hooks)
    candidates.append({
        "mode": "mutate",
        "hook_type": mutated_hook,
        "donor_ad": None,
        "weak_dimensions": None,
        "label": f"mutate({mutated_hook})",
    })

    return candidates, mutated_hook


def _build_remaining_candidates(candidates, mutated_hook, ad, all_items, iteration,
                                population_size, playbook, recent_hooks, tested_hooks,
                                weak_dims):
    """Build slots 3+ after weak_dims are known."""
    content_type = ad.get("content_type", "meta-ad")
    current_hook = ad.get("hook_type", "story")

    # Slot 3: wildcard every 3rd iteration, otherwise targeted
    if (iteration + 1) % 3 == 0:
        wc_hook = _pick_wildcard_hook(playbook, tested_hooks)
        candidates.append({
            "mode": "wildcard",
            "hook_type": wc_hook,
            "donor_ad": None,
            "weak_dimensions": None,
            "label": f"wildcard({wc_hook})",
        })
    elif weak_dims:
        candidates.append({
            "mode": "targeted",
            "hook_type": current_hook,
            "donor_ad": None,
            "weak_dimensions": weak_dims,
            "label": f"targeted({weak_dims[0][0]})",
        })
    else:
        # Fallback: another mutation with a different hook
        alt_hook = _pick_mutated_hook(mutated_hook, playbook, recent_hooks)
        candidates.append({
            "mode": "mutate",
            "hook_type": alt_hook,
            "donor_ad": None,
            "weak_dimensions": None,
            "label": f"mutate({alt_hook})",
        })

    # Slots 4+: crossover candidates if population > 3
    for _ in range(max(0, population_size - 3)):
        donor = _pick_donor_ad(all_items, ad, content_type)
        if donor:
            candidates.append({
                "mode": "crossover",
                "hook_type": current_hook,
                "donor_ad": donor,
                "weak_dimensions": None,
                "label": f"crossover({_get_ad_id(donor)})",
            })
        else:
            # No donor available — fall back to targeted or mutate
            if weak_dims:
                candidates.append({
                    "mode": "targeted",
                    "hook_type": current_hook,
                    "donor_ad": None,
                    "weak_dimensions": weak_dims,
                    "label": f"targeted({weak_dims[0][0]})",
                })
            else:
                candidates.append({
                    "mode": "mutate",
                    "hook_type": _pick_mutated_hook(current_hook, playbook, recent_hooks),
                    "donor_ad": None,
                    "weak_dimensions": None,
                    "label": "mutate(fallback)",
                })

    return candidates


def _process_single_candidate(cand, ad, item, client_dir, shared_dir, client,
                              all_ads, use_llm):
    """Process one candidate: generate, lint, score. Thread-safe.

    Returns (cand_label, new_ad, new_score, new_report, err).
    """
    new_ad, new_score, new_report, err = _generate_and_lint(
        ad, item, client_dir, shared_dir, client, all_ads, [],
        mode=cand["mode"], hook_type=cand["hook_type"],
        donor_ad=cand["donor_ad"], weak_dimensions=cand["weak_dimensions"],
        use_llm=use_llm,
    )
    return cand["label"], new_ad, new_score, new_report, err


def _process_single_ad(item, all_items, all_ads, client, client_dir, shared_dir,
                        iteration, population_size, playbook,
                        recent_hooks_per_item, tested_hooks_per_item,
                        use_llm, use_pairwise, all_items_lock):
    """Process all candidates for a single ad in parallel (Tier 1).

    Returns (ad_id, improved_flag, output_lines, hook_updates).
    hook_updates is (ad_id, tried_hooks) for the caller to apply.
    """
    ad = item["ad"]
    ad_id = _get_ad_id(ad)
    content_type = ad.get("content_type", "meta-ad")
    old_score = item["score"]
    current_hook = ad.get("hook_type", "story")
    output_lines = []

    # Get weak dimensions for targeted mode
    weak_dims = _get_weak_dimensions(item.get("report", {}))

    # Track hooks for this item (read snapshot — safe since each ad has its own keys)
    recent_hooks = recent_hooks_per_item.get(ad_id, [])
    tested_hooks = tested_hooks_per_item.setdefault(ad_id, {current_hook})

    output_lines.append(f"  {ad_id} ({content_type}): {old_score:.3f} [{item['verdict']}]")

    # Tier 3: Pre-build all candidate configs before any API calls
    candidates, mutated_hook = _build_candidate_configs(
        ad, all_items, iteration, population_size, playbook, recent_hooks, tested_hooks
    )
    candidates = _build_remaining_candidates(
        candidates, mutated_hook, ad, all_items, iteration, population_size,
        playbook, recent_hooks, tested_hooks, weak_dims
    )

    # Tier 1: Run all candidates in parallel
    best_candidate = None
    best_score = old_score
    best_report = None
    best_label = None
    failures = []

    with ThreadPoolExecutor(max_workers=population_size) as executor:
        futures = {
            executor.submit(
                _process_single_candidate, cand, ad, item, client_dir, shared_dir,
                client, all_ads, use_llm
            ): cand
            for cand in candidates
        }

        tracker_entries = []
        for future in as_completed(futures):
            label, new_ad, new_score, new_report, err = future.result()
            cand = futures[future]

            if err:
                failures.append(f"{ad_id}: {err}")
                output_lines.append(f"    [{label}] {err}")
                tracker_entries.append({
                    "ad_id": ad_id, "iteration": iteration + 1,
                    "mode": cand["mode"], "hook_type": cand["hook_type"],
                    "label": label, "old_score": round(old_score, 4),
                    "new_score": None, "delta": None, "won": False, "error": err,
                })
                continue

            delta = round(new_score - old_score, 4)
            status = "+" if new_score > old_score else "="
            output_lines.append(f"    [{label}] {new_score:.3f} {status}")
            tracker_entries.append({
                "ad_id": ad_id, "iteration": iteration + 1,
                "mode": cand["mode"], "hook_type": cand["hook_type"],
                "label": label, "old_score": round(old_score, 4),
                "new_score": round(new_score, 4), "delta": delta,
                "won": False, "error": None,
            })

            if new_score > best_score:
                best_candidate = new_ad
                best_score = new_score
                best_report = new_report
                best_label = label

    # Mark winner in tracker
    if best_label:
        for entry in tracker_entries:
            if entry["label"] == best_label and entry["won"] is False and entry.get("new_score") is not None:
                entry["won"] = True
                break

    # Track all hooks tried this iteration for recency weighting
    tried_this_round = [c["hook_type"] for c in candidates]
    hook_updates = (ad_id, recent_hooks, tried_this_round)

    # Accept the best if it improved (with optional pairwise gate)
    improved_flag = 0
    if best_candidate and best_score > old_score:
        if use_pairwise:
            pw_score, pw_reason = score_pairwise(
                best_candidate, ad, client["config"], weak_dims,
            )
            if pw_score <= 2:
                delta = best_score - old_score
                output_lines.append(f"    => PAIRWISE REJECT: rubric +{delta:.3f} but pairwise {pw_score}/5 -- {pw_reason}")
            else:
                with all_items_lock:
                    _accept_candidate(item, best_candidate, best_score, best_report, all_ads, ad)
                improved_flag = 1
                output_lines.append(f"    => ACCEPTED [{best_label}] {best_score:.3f} (+{best_score - old_score:.3f}) pairwise {pw_score}/5")
        else:
            with all_items_lock:
                _accept_candidate(item, best_candidate, best_score, best_report, all_ads, ad)
            improved_flag = 1
            output_lines.append(f"    => ACCEPTED [{best_label}] {best_score:.3f} (+{best_score - old_score:.3f})")
    else:
        output_lines.append(f"    => no improvement, kept original")

    return ad_id, improved_flag, output_lines, hook_updates, failures, tracker_entries


def run_evolutionary(all_items, all_ads, client, client_dir, shared_dir,
                     max_iterations, target, population_size, use_llm,
                     use_pairwise=False, max_workers=4, tournament=False):
    """Population-based evolutionary hill-climb with mutation, crossover,
    wildcard, and dimension-targeted improvement.

    Uses benchmark hit rates and industry playbooks to weight hook mutation.

    Tier 1: Candidates within an ad run in parallel (ThreadPoolExecutor).
    Tier 2: Ads within an iteration run in parallel (up to max_workers).
    Tier 3: Candidate configs are pre-built before any API calls.
    """
    recent_failures = []
    improved = 0
    recent_hooks_per_item = {}  # track recent hooks tried per ad_id
    tested_hooks_per_item = {}  # track all hooks ever tried per ad_id
    strategy_tracker = []  # every candidate attempt for post-run analysis

    # Tier 3: Pre-warm — load config and playbook once
    config_path = client_dir / "config.json"
    with open(config_path) as f:
        config = json.load(f)
    angles = config.get("angles_in_use", [])
    playbook = _load_industry_playbook(client_dir)

    # Lock for thread-safe updates to all_items/all_ads
    all_items_lock = threading.Lock()

    for iteration in range(max_iterations):
        below = [i for i in all_items if i["score"] < target]
        if not below:
            print(f"All items at target after iteration {iteration}!")
            break

        print(f"--- Iteration {iteration + 1}: {len(below)} items below target (pop={population_size}, workers={max_workers}) ---")

        # Tier 2: Process multiple ads concurrently within each iteration
        with ThreadPoolExecutor(max_workers=max_workers) as ad_executor:
            ad_futures = {
                ad_executor.submit(
                    _process_single_ad, item, all_items, all_ads, client,
                    client_dir, shared_dir, iteration, population_size, playbook,
                    recent_hooks_per_item, tested_hooks_per_item,
                    use_llm, use_pairwise, all_items_lock
                ): item
                for item in below
            }

            for future in as_completed(ad_futures):
                ad_id, improved_flag, output_lines, hook_updates, failures, tracker_entries = future.result()

                # Print buffered output for this ad (no interleaving)
                for line in output_lines:
                    print(line, flush=True)

                # Apply hook tracking updates
                hk_ad_id, hk_recent, hk_tried = hook_updates
                recent_hooks_per_item[hk_ad_id] = (hk_recent + hk_tried)[-6:]
                tested_hooks_per_item.setdefault(hk_ad_id, set()).update(hk_tried)

                # Collect failures and tracker
                recent_failures.extend(failures)
                strategy_tracker.extend(tracker_entries)

                improved += improved_flag

        # Tournament mode: cull bottom 50% after each iteration
        if tournament and iteration < max_iterations - 1:
            all_items.sort(key=lambda x: x["score"], reverse=True)
            keep = max(3, len(all_items) // 2)  # floor of 3 to avoid degenerate runs
            culled = len(all_items) - keep
            all_items[:] = all_items[:keep]
            print(f"  TOURNAMENT: kept top {keep}, culled {culled} (lowest was {all_items[-1]['score']:.3f})")

        print()

    return improved, strategy_tracker


# ---------------------------------------------------------------------------
# Strategy analysis
# ---------------------------------------------------------------------------

def _write_strategy_analysis(tracker, loop_dir, args):
    """Write strategy tracker to JSON and print summary stats."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    tracker_path = loop_dir / f"strategy-tracker-{ts}.json"

    by_mode = {}
    for entry in tracker:
        mode = entry["mode"]
        if mode not in by_mode:
            by_mode[mode] = {"attempts": 0, "wins": 0, "errors": 0,
                             "deltas": [], "positive_deltas": []}
        by_mode[mode]["attempts"] += 1
        if entry["error"]:
            by_mode[mode]["errors"] += 1
        elif entry["delta"] is not None:
            by_mode[mode]["deltas"].append(entry["delta"])
            if entry["delta"] > 0:
                by_mode[mode]["positive_deltas"].append(entry["delta"])
        if entry["won"]:
            by_mode[mode]["wins"] += 1

    summary = {}
    for mode, stats in sorted(by_mode.items()):
        n = stats["attempts"]
        wins = stats["wins"]
        deltas = stats["deltas"]
        pos = stats["positive_deltas"]
        summary[mode] = {
            "attempts": n, "wins": wins,
            "win_rate": round(wins / n, 3) if n > 0 else 0,
            "errors": stats["errors"],
            "improvements": len(pos),
            "improvement_rate": round(len(pos) / len(deltas), 3) if deltas else 0,
            "avg_delta": round(sum(deltas) / len(deltas), 4) if deltas else 0,
            "avg_positive_delta": round(sum(pos) / len(pos), 4) if pos else 0,
            "max_delta": round(max(deltas), 4) if deltas else 0,
        }

    output = {
        "run_ts": ts, "client": args.client,
        "strategy": args.strategy, "population": args.population,
        "iterations": args.iterations, "target": args.target,
        "workers": args.workers,
        "total_candidates": len(tracker),
        "summary_by_mode": summary, "raw": tracker,
    }

    with open(tracker_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n=== STRATEGY ANALYSIS (saved to {tracker_path.name}) ===")
    print(f"{'Mode':<12} {'Attempts':>8} {'Wins':>5} {'Win%':>6} {'Improv':>7} {'Avg Δ':>8} {'Avg Win Δ':>10} {'Max Δ':>8}")
    print("-" * 75)
    for mode in ["improve", "mutate", "targeted", "crossover", "wildcard"]:
        if mode in summary:
            s = summary[mode]
            print(f"{mode:<12} {s['attempts']:>8} {s['wins']:>5} {s['win_rate']:>5.1%} "
                  f"{s['improvements']:>7} {s['avg_delta']:>+8.4f} {s['avg_positive_delta']:>+10.4f} {s['max_delta']:>+8.4f}")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _accept_candidate(item, new_ad, new_score, new_report, all_ads, old_ad):
    """Accept a better candidate: update item, all_ads list, and write to disk."""
    item["ad"] = new_ad
    item["score"] = new_score
    item["verdict"] = new_report["verdict"]
    item["report"] = new_report
    # Update in all_ads list
    try:
        idx = all_ads.index(old_ad)
        all_ads[idx] = new_ad
    except ValueError:
        all_ads.append(new_ad)
    # Write to disk
    with open(item["path"], "w") as f:
        json.dump(new_ad, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    client_dir = root / "clients" / args.client
    shared_dir = root / "shared"
    client = load_client(client_dir, shared_dir)
    use_llm = not args.no_llm

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

    # Build full ads list for differentiation scoring BEFORE filtering
    all_ads = [item["ad"] for item in all_items]

    if args.type_filter:
        all_items = [i for i in all_items if i["ad"].get("content_type") == args.type_filter]
        print(f"Filtered to {len(all_items)} {args.type_filter} items")

    print(f"Loaded {len(all_items)} items. Target: {args.target:.2f} (strong_draft)")
    print(f"Max iterations per item: {args.iterations}")
    print(f"Strategy: {args.strategy} (population={args.population})")
    print(f"LLM scoring: {'enabled' if use_llm else 'disabled (deterministic only)'}")
    print(f"Pairwise gating: {'enabled' if args.use_pairwise else 'disabled'}")
    print(f"Workers: {args.workers} (concurrent ads per iteration)")
    print()

    # Initial scoring
    for item in all_items:
        report = score_ad(item["ad"], client, existing_ads=all_ads, use_llm=use_llm)
        item["score"] = report["composite"]
        item["verdict"] = report["verdict"]
        item["report"] = report

    below = [i for i in all_items if i["score"] < args.target]
    above = [i for i in all_items if i["score"] >= args.target]
    print(f"Initial: {len(above)} at target, {len(below)} below target")
    print()

    # Run the selected strategy
    strategy_tracker = []
    if args.strategy == "greedy":
        improved = run_greedy(
            all_items, all_ads, client, client_dir, shared_dir,
            args.iterations, args.target, use_llm,
            use_pairwise=args.use_pairwise,
        )
    else:
        improved, strategy_tracker = run_evolutionary(
            all_items, all_ads, client, client_dir, shared_dir,
            args.iterations, args.target, args.population, use_llm,
            use_pairwise=args.use_pairwise,
            max_workers=args.workers,
            tournament=args.tournament,
        )

    # Final summary
    verdicts = {}
    for item in all_items:
        v = item["verdict"]
        verdicts[v] = verdicts.get(v, 0) + 1

    avg = sum(i["score"] for i in all_items) / len(all_items) if all_items else 0
    still_below = sum(1 for i in all_items if i["score"] < args.target)

    print(f"=== HILL-CLIMB COMPLETE ===")
    print(f"Strategy: {args.strategy}")
    print(f"Improvements made: {improved}")
    print(f"Avg composite: {avg:.4f}")
    print(f"Still below target: {still_below}")
    for v in ["production_ready", "strong_draft", "needs_work", "rewrite"]:
        print(f"  {v}: {verdicts.get(v, 0)}")

    if strategy_tracker:
        _write_strategy_analysis(strategy_tracker, loop_dir, args)


if __name__ == "__main__":
    main()
