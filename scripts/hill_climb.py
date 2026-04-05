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

        # Score
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

def run_evolutionary(all_items, all_ads, client, client_dir, shared_dir,
                     max_iterations, target, population_size, use_llm,
                     use_pairwise=False):
    """Population-based evolutionary hill-climb with mutation, crossover,
    wildcard, and dimension-targeted improvement.

    Uses benchmark hit rates and industry playbooks to weight hook mutation.
    """
    recent_failures = []
    improved = 0
    recent_hooks_per_item = {}  # track recent hooks tried per ad_id
    tested_hooks_per_item = {}  # track all hooks ever tried per ad_id

    # Load config and industry playbook
    config_path = client_dir / "config.json"
    with open(config_path) as f:
        config = json.load(f)
    angles = config.get("angles_in_use", [])
    playbook = _load_industry_playbook(client_dir)

    for iteration in range(max_iterations):
        below = [i for i in all_items if i["score"] < target]
        if not below:
            print(f"All items at target after iteration {iteration}!")
            break

        print(f"--- Iteration {iteration + 1}: {len(below)} items below target (pop={population_size}) ---")

        for item in below:
            ad = item["ad"]
            ad_id = _get_ad_id(ad)
            content_type = ad.get("content_type", "meta-ad")
            old_score = item["score"]
            current_hook = ad.get("hook_type", "story")

            # Get weak dimensions for targeted mode
            weak_dims = _get_weak_dimensions(item.get("report", {}))

            # Track hooks for this item
            recent_hooks = recent_hooks_per_item.get(ad_id, [])
            tested_hooks = tested_hooks_per_item.setdefault(ad_id, {current_hook})

            print(f"  {ad_id} ({content_type}): {old_score:.3f} [{item['verdict']}]", flush=True)

            # Build candidate strategies for this iteration
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

            # Generate and score all candidates
            best_candidate = None
            best_score = old_score
            best_report = None
            best_label = None

            for cand in candidates:
                new_ad, new_score, new_report, err = _generate_and_lint(
                    ad, item, client_dir, shared_dir, client, all_ads, recent_failures,
                    mode=cand["mode"], hook_type=cand["hook_type"],
                    donor_ad=cand["donor_ad"], weak_dimensions=cand["weak_dimensions"],
                    use_llm=use_llm,
                )

                if err:
                    recent_failures.append(f"{ad_id}: {err}")
                    print(f"    [{cand['label']}] {err}")
                    continue

                status = "+" if new_score > old_score else "="
                print(f"    [{cand['label']}] {new_score:.3f} {status}")

                if new_score > best_score:
                    best_candidate = new_ad
                    best_score = new_score
                    best_report = new_report
                    best_label = cand["label"]

            # Track all hooks tried this iteration for recency weighting
            tried_this_round = [c["hook_type"] for c in candidates]
            recent_hooks_per_item[ad_id] = (recent_hooks + tried_this_round)[-6:]
            tested_hooks.update(tried_this_round)

            # Accept the best if it improved (with optional pairwise gate)
            if best_candidate and best_score > old_score:
                if use_pairwise:
                    pw_score, pw_reason = score_pairwise(
                        best_candidate, ad, client["config"], weak_dims,
                    )
                    if pw_score <= 2:
                        delta = best_score - old_score
                        print(f"    => PAIRWISE REJECT: rubric +{delta:.3f} but pairwise {pw_score}/5 — {pw_reason}")
                    else:
                        _accept_candidate(item, best_candidate, best_score, best_report, all_ads, ad)
                        improved += 1
                        print(f"    => ACCEPTED [{best_label}] {best_score:.3f} (+{best_score - old_score:.3f}) pairwise {pw_score}/5")
                else:
                    _accept_candidate(item, best_candidate, best_score, best_report, all_ads, ad)
                    improved += 1
                    print(f"    => ACCEPTED [{best_label}] {best_score:.3f} (+{best_score - old_score:.3f})")
            else:
                print(f"    => no improvement, kept original")

        print()

    return improved


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
    if args.strategy == "greedy":
        improved = run_greedy(
            all_items, all_ads, client, client_dir, shared_dir,
            args.iterations, args.target, use_llm,
            use_pairwise=args.use_pairwise,
        )
    else:
        improved = run_evolutionary(
            all_items, all_ads, client, client_dir, shared_dir,
            args.iterations, args.target, args.population, use_llm,
            use_pairwise=args.use_pairwise,
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


if __name__ == "__main__":
    main()
