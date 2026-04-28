"""
Hypothesis Generator — PR #125 addition.

Takes a seed ad and its rubric score report and generates testable
hypotheses about which load-bearing elements to swap/improve.

A hypothesis is a claim: "If we change element X in direction D,
the rubric score should change by Z."

Each hypothesis maps to a `generate_variant` mode + targeted weak_dim
so the hill_climb_from_seed script can execute and verify it.
"""

from __future__ import annotations

import random
from typing import Any


# ---------------------------------------------------------------------------
# Dimension metadata — load-bearing element classification
# ---------------------------------------------------------------------------

# Each entry: dim_id -> {load_bearing_element, testable_swap, predicted_direction,
#                        hypothesis_template, mode_hint, confidence_prior}
_DIM_META: dict[str, dict] = {
    "scroll_stop_hook": {
        "load_bearing_element": "hook_type",
        "testable_swap": "hook_swap",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Swapping a score-{score} hook ({current}) to a higher-potential hook "
            "type should raise scroll_stop_hook toward 5/5 and lift composite."
        ),
        "mode_hint": "mutate",
        "confidence_prior": 0.70,
    },
    "specificity": {
        "load_bearing_element": "concrete_details",
        "testable_swap": "add_specifics",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Adding named farms, geographies, or spelled-out cardinals should raise "
            "specificity from {score}/5 toward 4-5 and lift composite."
        ),
        "mode_hint": "targeted",
        "confidence_prior": 0.65,
    },
    "motivation_match": {
        "load_bearing_element": "emotional_resonance",
        "testable_swap": "reframe_felt_need",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Reframing the primary_text to speak to the reader's felt need "
            "(not product features) should raise motivation_match from {score}/5."
        ),
        "mode_hint": "targeted",
        "confidence_prior": 0.60,
    },
    "cta_clarity": {
        "load_bearing_element": "cta_outcome_statement",
        "testable_swap": "add_outcome_cta",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Replacing the cta with an outcome-stated version "
            "should raise cta_clarity from {score}/5."
        ),
        "mode_hint": "targeted",
        "confidence_prior": 0.55,
    },
    "objection_preemption": {
        "load_bearing_element": "objection_signals",
        "testable_swap": "add_objection_signals",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Adding explicit objection signals (hub clarity, no commitment, "
            "no middlemen, provenance) should raise objection_preemption from {score}/5."
        ),
        "mode_hint": "targeted",
        "confidence_prior": 0.60,
    },
    "angle_clarity": {
        "load_bearing_element": "single_proposition",
        "testable_swap": "tighten_angle",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Removing competing themes and focusing every sentence on one "
            "proposition should raise angle_clarity from {score}/5."
        ),
        "mode_hint": "targeted",
        "confidence_prior": 0.55,
    },
    "tactic_execution": {
        "load_bearing_element": "tactic_pattern",
        "testable_swap": "strengthen_tactic",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Strengthening the tactic execution (e.g. more vivid proof, "
            "stronger social proof) should raise tactic_execution from {score}/5."
        ),
        "mode_hint": "improve",
        "confidence_prior": 0.50,
    },
    "platform_fit": {
        "load_bearing_element": "headline_length",
        "testable_swap": "trim_headline",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Trimming the headline to <=40 chars should resolve the platform_fit "
            "penalty (current score: {score}/5)."
        ),
        "mode_hint": "targeted",
        "confidence_prior": 0.75,
    },
    "founder_voice": {
        "load_bearing_element": "first_person_build_language",
        "testable_swap": "add_founder_voice",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Adding 'we've built' or 'we're about to' language should raise "
            "founder_voice from {score}/5."
        ),
        "mode_hint": "targeted",
        "confidence_prior": 0.55,
    },
    "ownership_framing": {
        "load_bearing_element": "ownership_language",
        "testable_swap": "add_ownership_signals",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Adding 'own a piece' or 'you'll be able to own' with an investment "
            "context trigger should raise ownership_framing from {score}/5."
        ),
        "mode_hint": "targeted",
        "confidence_prior": 0.60,
    },
    "scarcity_register": {
        "load_bearing_element": "soft_scarcity_signals",
        "testable_swap": "add_soft_scarcity",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Adding soft-scarcity signals (first access, registration opens soon, "
            "limited spots) should raise scarcity_register from {score}/5."
        ),
        "mode_hint": "targeted",
        "confidence_prior": 0.55,
    },
    "differentiation": {
        "load_bearing_element": "vocabulary_diversity",
        "testable_swap": "diversify_vocabulary",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Rewriting with less overlap against the existing ads (bigram Jaccard) "
            "should raise differentiation from {score}/5."
        ),
        "mode_hint": "mutate",
        "confidence_prior": 0.45,
    },
    "emotional_register": {
        "load_bearing_element": "emotional_vocabulary",
        "testable_swap": "enrich_emotion",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Enriching emotional vocabulary (values-aligned words, feeling nouns) "
            "should raise emotional_register from {score}/5."
        ),
        "mode_hint": "targeted",
        "confidence_prior": 0.50,
    },
    # Dims that are usually locked (score=5) — probe shows no room to improve
    "csf_placement": {
        "load_bearing_element": "asterisked_csf_footnote",
        "testable_swap": "none",
        "predicted_direction": "NEUTRAL",
        "hypothesis_template": (
            "csf_placement is already at {score}/5 — hook_swap variants "
            "should preserve this (body is locked)."
        ),
        "mode_hint": "improve",
        "confidence_prior": 0.90,
    },
    "receptionist_test": {
        "load_bearing_element": "brand_clarity_signals",
        "testable_swap": "none",
        "predicted_direction": "NEUTRAL",
        "hypothesis_template": (
            "receptionist_test at {score}/5 — most variants should preserve this."
        ),
        "mode_hint": "improve",
        "confidence_prior": 0.80,
    },
    "opening_diversity": {
        "load_bearing_element": "opening_uniqueness",
        "testable_swap": "swap_opener",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Changing the opening pattern should raise opening_diversity "
            "from {score}/5 by reducing overlap with cohort openers."
        ),
        "mode_hint": "mutate",
        "confidence_prior": 0.50,
    },
    "sentence_variance": {
        "load_bearing_element": "sentence_length_range",
        "testable_swap": "vary_sentence_length",
        "predicted_direction": "LIFT",
        "hypothesis_template": (
            "Mixing short punchy lines with longer flowing sentences should "
            "raise sentence_variance from {score}/5."
        ),
        "mode_hint": "targeted",
        "confidence_prior": 0.50,
    },
}


def generate_hypotheses(
    ad: dict,
    score_report: dict,
    n: int = 4,
    exclude_neutral: bool = True,
    min_score_gap: int = 1,
    random_seed: int | None = None,
) -> list[dict]:
    """Generate n testable hypotheses ranked by expected improvement.

    Each hypothesis is:
    {
        "dim_id": str,
        "load_bearing_element": str,
        "current_score": int,
        "max_score": 5,
        "score_gap": int,
        "predicted_direction": "LIFT" | "NEUTRAL" | "DROP",
        "claim": str,
        "mode_hint": str,       # maps to generate_variant mode
        "confidence_prior": float,
        "expected_gain": float, # confidence_prior * score_gap * weight
        "testable_swap": str,
    }
    """
    if random_seed is not None:
        random.seed(random_seed)

    dim_details = score_report.get("rubric", {}).get("dimension_details", {})
    content_type = ad.get("content_type", "meta-ad")

    # Build candidate hypotheses from dims with room to improve
    candidates = []
    for dim_id, meta in _DIM_META.items():
        if dim_id not in dim_details:
            continue
        current_score = dim_details[dim_id].get("score", 5)
        weight = dim_details[dim_id].get("weight", 1.0)
        score_gap = 5 - current_score

        if score_gap < min_score_gap:
            continue
        if exclude_neutral and meta["predicted_direction"] == "NEUTRAL":
            continue

        claim = meta["hypothesis_template"].format(
            score=current_score,
            current=ad.get("hook_type", "?"),
        )

        expected_gain = meta["confidence_prior"] * score_gap * weight

        candidates.append({
            "dim_id": dim_id,
            "load_bearing_element": meta["load_bearing_element"],
            "current_score": current_score,
            "max_score": 5,
            "score_gap": score_gap,
            "predicted_direction": meta["predicted_direction"],
            "claim": claim,
            "mode_hint": meta["mode_hint"],
            "confidence_prior": meta["confidence_prior"],
            "expected_gain": round(expected_gain, 4),
            "testable_swap": meta["testable_swap"],
        })

    # Sort by expected_gain descending (best hypothesis first)
    candidates.sort(key=lambda x: x["expected_gain"], reverse=True)

    # Always include the highest-expected-gain dims; add a random low-priority
    # one for diversity of probe.
    if len(candidates) > n:
        top = candidates[: n - 1]
        rest = candidates[n - 1:]
        wildcard = random.choice(rest) if rest else None
        selected = top + ([wildcard] if wildcard else [])
        selected = selected[:n]
    else:
        selected = candidates[:n]

    return selected


def hypothesis_summary(hypotheses: list[dict]) -> str:
    """Return a compact table for logging."""
    lines = [
        f"{'Dim':>26} {'Gap':>4} {'LBE':>28} {'Prior':>6} {'ExpGain':>8} {'Mode':>10}"
    ]
    lines.append("-" * 90)
    for h in hypotheses:
        lines.append(
            f"{h['dim_id']:>26} {h['score_gap']:>4} {h['load_bearing_element']:>28} "
            f"{h['confidence_prior']:>6.2f} {h['expected_gain']:>8.4f} {h['mode_hint']:>10}"
        )
    return "\n".join(lines)
