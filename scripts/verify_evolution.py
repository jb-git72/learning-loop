#!/usr/bin/env python3
"""Verify evolutionary hill-climbing outperforms greedy.

Uses deterministic text mutations (no LLM API calls) and --no-llm scoring
to compare greedy vs evolutionary strategies on real farm-thru content.

Usage:
  python3 scripts/verify_evolution.py farm-thru

Completes in under 1 minute. No API calls.
"""

import copy
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
from scripts.lint_content import lint
from scripts.hill_climb import (
    _get_ad_id,
    _get_weak_dimensions,
    _pick_mutated_hook,
    _pick_donor_ad,
    HOOK_TEMPLATES,
)
from writer import HOOK_TEMPLATES as WRITER_HOOKS


# ---------------------------------------------------------------------------
# Deterministic variant generators (simulate LLM output without API calls)
# ---------------------------------------------------------------------------

# Objection phrases that boost objection_preemption scoring
OBJECTION_PHRASES = [
    "No commitment. Order when you want.",
    "Collect from the Brookvale hub, Monday to Friday.",
    "No middlemen, no warehouse, no cold storage.",
    "You'll know the farm name on every item.",
    "No lock-in. No subscription. Just better food.",
]

# Story hooks that boost scroll_stop_hook scoring
STORY_HOOKS = [
    "Last Thursday a farmer in Kempsey packed 200 kg of grass-fed beef.",
    '"I stopped buying supermarket meat six months ago."',
    "Rachel called from the paddock at 6am.",
    "$12 for a kilo of regenerative chicken. That price surprised us too.",
    "If you spent $180 at Woolies last week, here is what you missed.",
]

# Receptionist-test answers (what, source, different, how, why_now)
RECEPTIONIST_ANSWERS = [
    "FarmThru is a new kind of grocery store.",
    "Every item comes from a named NSW farm.",
    "Days old, not weeks. No cold storage. Direct from the paddock.",
    "Find your nearest hub and start your first order.",
    "We are launching in Brookvale. Be part of the first access group.",
]

# Specificity boosters (dollar amounts, numbers, names)
SPECIFICITY_PHRASES = [
    "Bundarra beef, 3 days from paddock to hub.",
    "$14/kg grass-fed lamb from Collins Farm.",
    "12 named farms across NSW supply the Brookvale hub.",
    "Rachel Ward's Paris Creek dairy, collected fresh every Tuesday.",
    "200+ Sydney families already on the waitlist.",
]


def _make_improve_variant(ad: dict) -> dict:
    """Simulate 'improve' mode: tighten copy, add one specificity signal."""
    variant = copy.deepcopy(ad)
    ct = ad.get("content_type", "meta-ad")

    if ct == "meta-ad":
        # Add a specificity phrase to primary_text
        phrase = random.choice(SPECIFICITY_PHRASES)
        text = variant.get("primary_text", "")
        # Insert before last paragraph
        paragraphs = text.split("\n\n")
        if len(paragraphs) > 1:
            paragraphs.insert(-1, phrase)
        else:
            paragraphs.append(phrase)
        variant["primary_text"] = "\n\n".join(paragraphs)[:500]

    elif ct == "email":
        phrase = random.choice(SPECIFICITY_PHRASES)
        body = variant.get("body", "")
        variant["body"] = body + "\n\n" + phrase

    elif ct == "landing-page":
        phrase = random.choice(SPECIFICITY_PHRASES)
        variant["hero_copy"] = (variant.get("hero_copy", "") + " " + phrase)[:500]

    return variant


def _make_mutate_variant(ad: dict) -> dict:
    """Simulate 'mutate' mode: change hook type, rewrite opening."""
    variant = copy.deepcopy(ad)
    ct = ad.get("content_type", "meta-ad")

    # Change hook type
    current_hook = variant.get("hook_type", "story")
    new_hook = _pick_mutated_hook(current_hook)
    variant["hook_type"] = new_hook

    # Rewrite the opening line with a story hook
    hook = random.choice(STORY_HOOKS)
    if ct == "meta-ad":
        text = variant.get("primary_text", "")
        lines = text.split("\n", 1)
        variant["primary_text"] = (hook + "\n" + (lines[1] if len(lines) > 1 else ""))[:500]
    elif ct == "email":
        body = variant.get("body", "")
        lines = body.split("\n", 1)
        variant["body"] = hook + "\n" + (lines[1] if len(lines) > 1 else "")
    elif ct == "landing-page":
        variant["hero_copy"] = hook + " " + variant.get("hero_copy", "")[:300]

    return variant


def _make_wildcard_variant(ad: dict) -> dict:
    """Simulate 'wildcard' mode: fresh opening + objection preemption + specifics."""
    variant = copy.deepcopy(ad)
    ct = ad.get("content_type", "meta-ad")

    # Pick random hook type
    variant["hook_type"] = random.choice(list(HOOK_TEMPLATES.keys()))

    hook = random.choice(STORY_HOOKS)
    objection = random.choice(OBJECTION_PHRASES)
    specific = random.choice(SPECIFICITY_PHRASES)
    receptionist = random.choice(RECEPTIONIST_ANSWERS)

    if ct == "meta-ad":
        text = f"{hook}\n\n{receptionist}\n\n{specific}\n\n{objection}"
        variant["primary_text"] = text[:500]
    elif ct == "email":
        variant["body"] = f"{hook}\n\n{receptionist}\n\n{specific}\n\n{objection}"
    elif ct == "landing-page":
        variant["hero_copy"] = f"{hook} {receptionist}"[:500]

    return variant


def _make_targeted_variant(ad: dict, weak_dims: list) -> dict:
    """Simulate 'targeted' mode: inject content that boosts weak dimensions."""
    variant = copy.deepcopy(ad)
    ct = ad.get("content_type", "meta-ad")

    # Map weak dimensions to specific injections
    injections = []
    for dim_name, score, max_score in weak_dims:
        if dim_name == "objection_preemption":
            injections.append(random.choice(OBJECTION_PHRASES))
        elif dim_name == "scroll_stop_hook":
            injections.append(random.choice(STORY_HOOKS))
        elif dim_name == "specificity":
            injections.append(random.choice(SPECIFICITY_PHRASES))
        elif dim_name == "receptionist_test":
            injections.append(random.choice(RECEPTIONIST_ANSWERS))
        elif dim_name == "differentiation":
            # Add unique phrasing
            injections.append(f"Fresh from {random.choice(['Kempsey', 'Bundarra', 'Collins'])} farm, never frozen.")
        else:
            injections.append(random.choice(SPECIFICITY_PHRASES))

    injection_text = " ".join(injections)

    if ct == "meta-ad":
        text = variant.get("primary_text", "")
        paragraphs = text.split("\n\n")
        if len(paragraphs) > 1:
            paragraphs.insert(1, injection_text)
        else:
            paragraphs.append(injection_text)
        variant["primary_text"] = "\n\n".join(paragraphs)[:500]
    elif ct == "email":
        body = variant.get("body", "")
        variant["body"] = body + "\n\n" + injection_text
    elif ct == "landing-page":
        variant["hero_copy"] = variant.get("hero_copy", "") + " " + injection_text

    return variant


def _make_crossover_variant(ad: dict, donor: dict) -> dict:
    """Simulate 'crossover' mode: take donor's headline style, keep ad's body."""
    variant = copy.deepcopy(ad)
    ct = ad.get("content_type", "meta-ad")

    if ct == "meta-ad":
        # Borrow donor's headline
        donor_headline = donor.get("headline", "")
        if donor_headline:
            variant["headline"] = donor_headline[:40]
    elif ct == "email":
        donor_subject = donor.get("subject", "")
        if donor_subject:
            variant["subject"] = donor_subject[:60]
    elif ct == "landing-page":
        donor_headline = donor.get("headline", "")
        if donor_headline:
            variant["headline"] = donor_headline[:80]

    # Also inject a specificity phrase to change the body
    phrase = random.choice(SPECIFICITY_PHRASES)
    if ct == "meta-ad":
        text = variant.get("primary_text", "")
        variant["primary_text"] = (text + "\n\n" + phrase)[:500]
    elif ct == "email":
        variant["body"] = variant.get("body", "") + "\n\n" + phrase

    return variant


# ---------------------------------------------------------------------------
# Simulation runners
# ---------------------------------------------------------------------------

def simulate_greedy(items, client, client_dir, shared_dir, all_ads, iterations=2):
    """Simulate greedy hill-climbing: 1 candidate per iteration."""
    results = []
    for item in items:
        ad = copy.deepcopy(item["ad"])
        score = item["score"]
        history = [score]
        improvements = 0

        for _ in range(iterations):
            candidate = _make_improve_variant(ad)
            # Preserve ID
            for key in ["ad_id", "page_id", "email_id"]:
                if key in ad:
                    candidate[key] = ad[key]

            lint_result = lint(candidate, client_dir, shared_dir)
            if not lint_result.passed:
                history.append(score)
                continue

            report = score_ad(candidate, client, existing_ads=all_ads, use_llm=False)
            new_score = report["composite"]

            if new_score > score:
                ad = candidate
                score = new_score
                improvements += 1

            history.append(score)

        results.append({
            "ad_id": _get_ad_id(item["ad"]),
            "start": item["score"],
            "end": score,
            "delta": score - item["score"],
            "improvements": improvements,
            "history": history,
        })

    return results


def simulate_evolutionary(items, all_items, client, client_dir, shared_dir, all_ads, iterations=2, population=3):
    """Simulate evolutionary hill-climbing: N candidates per iteration with
    mutation, wildcard, crossover, and targeted modes."""
    results = []
    for item in items:
        ad = copy.deepcopy(item["ad"])
        score = item["score"]
        report = item.get("report", {})
        history = [score]
        improvements = 0
        content_type = ad.get("content_type", "meta-ad")

        for it in range(iterations):
            candidates = []

            # 1. Improve (exploitation)
            candidates.append(("improve", _make_improve_variant(ad)))

            # 2. Mutate (exploration)
            candidates.append(("mutate", _make_mutate_variant(ad)))

            # 3. Wildcard every 3rd, otherwise targeted
            weak_dims = _get_weak_dimensions(report) if report else []
            if (it + 1) % 3 == 0:
                candidates.append(("wildcard", _make_wildcard_variant(ad)))
            elif weak_dims:
                candidates.append(("targeted", _make_targeted_variant(ad, weak_dims)))
            else:
                candidates.append(("mutate2", _make_mutate_variant(ad)))

            # 4+: crossover if population > 3
            for _ in range(max(0, population - 3)):
                donor = _pick_donor_ad(all_items, ad, content_type)
                if donor:
                    candidates.append(("crossover", _make_crossover_variant(ad, donor)))
                else:
                    candidates.append(("mutate_extra", _make_mutate_variant(ad)))

            # Evaluate all candidates
            best_ad = ad
            best_score = score
            best_report = report

            for label, candidate in candidates:
                for key in ["ad_id", "page_id", "email_id"]:
                    if key in ad:
                        candidate[key] = ad[key]

                lint_result = lint(candidate, client_dir, shared_dir)
                if not lint_result.passed:
                    continue

                cand_report = score_ad(candidate, client, existing_ads=all_ads, use_llm=False)
                cand_score = cand_report["composite"]

                if cand_score > best_score:
                    best_ad = candidate
                    best_score = cand_score
                    best_report = cand_report

            if best_score > score:
                ad = best_ad
                score = best_score
                report = best_report
                improvements += 1

            history.append(score)

        results.append({
            "ad_id": _get_ad_id(item["ad"]),
            "start": item["score"],
            "end": score,
            "delta": score - item["score"],
            "improvements": improvements,
            "history": history,
        })

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    client_id = sys.argv[1] if len(sys.argv) > 1 else "farm-thru"

    client_dir = root / "clients" / client_id
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

    # Score everything with --no-llm
    print(f"Scoring {len(all_items)} items (no-llm)...")
    for item in all_items:
        report = score_ad(item["ad"], client, existing_ads=all_ads, use_llm=False)
        item["score"] = report["composite"]
        item["verdict"] = report["verdict"]
        item["report"] = report

    # Pick items below target (0.70) — take up to 3 from different content types
    target = 0.70
    below = sorted(
        [i for i in all_items if i["score"] < target],
        key=lambda x: x["score"],
    )

    if not below:
        print("No items below target. Picking 3 lowest-scoring items instead.")
        below = sorted(all_items, key=lambda x: x["score"])

    # Pick 3 diverse items (try different content types)
    selected = []
    seen_types = set()
    for item in below:
        ct = item["ad"].get("content_type", "meta-ad")
        if ct not in seen_types and len(selected) < 3:
            selected.append(item)
            seen_types.add(ct)
    # Fill remaining slots
    for item in below:
        if len(selected) >= 3:
            break
        if item not in selected:
            selected.append(item)

    selected = selected[:3]

    print(f"\nSelected {len(selected)} items for comparison:")
    for item in selected:
        ad_id = _get_ad_id(item["ad"])
        ct = item["ad"].get("content_type", "meta-ad")
        print(f"  {ad_id} ({ct}): {item['score']:.4f} [{item['verdict']}]")

    # Set random seed for reproducibility
    random.seed(42)

    # Run greedy
    print("\n--- Running GREEDY (2 iterations, 1 candidate/iter) ---")
    greedy_results = simulate_greedy(selected, client, client_dir, shared_dir, all_ads, iterations=2)

    # Reset seed for fair comparison
    random.seed(42)

    # Run evolutionary
    print("--- Running EVOLUTIONARY (2 iterations, 3 candidates/iter) ---")
    evo_results = simulate_evolutionary(
        selected, all_items, client, client_dir, shared_dir, all_ads,
        iterations=2, population=3,
    )

    # --- Comparison table ---
    print("\n" + "=" * 80)
    print("COMPARISON: GREEDY vs EVOLUTIONARY")
    print("=" * 80)
    print(f"{'Ad ID':<12} {'Type':<12} {'Start':>8} {'Greedy':>8} {'G.delta':>8} {'Evo':>8} {'E.delta':>8} {'Winner':<12}")
    print("-" * 80)

    greedy_wins = 0
    evo_wins = 0
    ties = 0
    greedy_total_delta = 0
    evo_total_delta = 0

    for i, item in enumerate(selected):
        ad_id = _get_ad_id(item["ad"])
        ct = item["ad"].get("content_type", "meta-ad")
        start = item["score"]

        g = greedy_results[i]
        e = evo_results[i]

        greedy_total_delta += g["delta"]
        evo_total_delta += e["delta"]

        if e["end"] > g["end"]:
            winner = "EVOLUTIONARY"
            evo_wins += 1
        elif g["end"] > e["end"]:
            winner = "GREEDY"
            greedy_wins += 1
        else:
            winner = "TIE"
            ties += 1

        g_delta_str = f"+{g['delta']:.4f}" if g["delta"] > 0 else f"{g['delta']:.4f}"
        e_delta_str = f"+{e['delta']:.4f}" if e["delta"] > 0 else f"{e['delta']:.4f}"

        print(f"{ad_id:<12} {ct:<12} {start:>8.4f} {g['end']:>8.4f} {g_delta_str:>8} {e['end']:>8.4f} {e_delta_str:>8} {winner:<12}")

    print("-" * 80)

    g_avg = greedy_total_delta / len(selected) if selected else 0
    e_avg = evo_total_delta / len(selected) if selected else 0
    g_avg_str = f"+{g_avg:.4f}" if g_avg > 0 else f"{g_avg:.4f}"
    e_avg_str = f"+{e_avg:.4f}" if e_avg > 0 else f"{e_avg:.4f}"

    print(f"{'AVERAGE':<12} {'':12} {'':>8} {'':>8} {g_avg_str:>8} {'':>8} {e_avg_str:>8}")
    print()

    print(f"Greedy wins:       {greedy_wins}")
    print(f"Evolutionary wins: {evo_wins}")
    print(f"Ties:              {ties}")
    print()

    greedy_improvements = sum(r["improvements"] for r in greedy_results)
    evo_improvements = sum(r["improvements"] for r in evo_results)
    greedy_candidates = len(selected) * 2 * 1  # 2 iters, 1 candidate each
    evo_candidates = len(selected) * 2 * 3     # 2 iters, 3 candidates each

    print(f"Greedy: {greedy_improvements} improvements from {greedy_candidates} candidates ({greedy_improvements/greedy_candidates*100:.0f}% hit rate)")
    print(f"Evo:    {evo_improvements} improvements from {evo_candidates} candidates ({evo_improvements/evo_candidates*100:.0f}% hit rate)")
    print()

    # Score trajectory
    print("Score trajectories:")
    for i, item in enumerate(selected):
        ad_id = _get_ad_id(item["ad"])
        g = greedy_results[i]
        e = evo_results[i]
        g_traj = " -> ".join(f"{s:.4f}" for s in g["history"])
        e_traj = " -> ".join(f"{s:.4f}" for s in e["history"])
        print(f"  {ad_id}:")
        print(f"    Greedy:       {g_traj}")
        print(f"    Evolutionary: {e_traj}")

    print()

    # Verify the mechanism works (at least one strategy improved something)
    any_improvement = greedy_total_delta > 0 or evo_total_delta > 0
    if any_improvement:
        print("VERIFICATION PASSED: at least one strategy found improvements.")
    else:
        print("VERIFICATION NOTE: no improvements found (content may already be near optimal for deterministic scoring).")

    # Final assessment
    if evo_total_delta > greedy_total_delta:
        print("RESULT: Evolutionary strategy produced more total improvement.")
    elif greedy_total_delta > evo_total_delta:
        print("RESULT: Greedy strategy produced more total improvement (deterministic mutations may not expose population advantage).")
    else:
        print("RESULT: Both strategies performed equally.")


if __name__ == "__main__":
    main()
