"""
Scorer — The orchestrator. Combines all 3 axes into a composite score.

v2 ARCHITECTURE:
- Rules and facts are GATES (pass/fail). They don't contribute to the score.
  Break a rule = 0. Contradict a fact = 0. Otherwise, irrelevant.
- The RUBRIC is the entire score (0 to 1.0).
  All discrimination comes from the 10 rubric dimensions.
- 3 rubric dimensions are scored by a SEPARATE LLM API call
  that has zero shared context with the writer agent.

IMMUTABLE — the writer agent cannot modify this file.
"""

import json
from pathlib import Path

from . import rule_checker, fact_checker, rubric_scorer


def load_client(client_dir, shared_dir):
    """Load all client configuration and shared resources."""
    if not isinstance(client_dir, Path):
        client_dir = Path(client_dir)
    if not isinstance(shared_dir, Path):
        shared_dir = Path(shared_dir)

    config_path = client_dir / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    rules = rule_checker.load_rules(shared_dir, client_dir)
    facts = fact_checker.load_facts(client_dir)
    rubric = rubric_scorer.load_rubric(shared_dir)

    return {
        "config": config,
        "rules": rules,
        "facts": facts,
        "rubric": rubric,
        "client_dir": str(client_dir),
        "shared_dir": str(shared_dir),
    }


def score_ad(
    ad,
    client,
    existing_ads=None,
    use_llm=True,
):
    """Score a single ad variant.

    v2 scoring:
    - Rules/facts are gates: any critical failure → composite 0.0
    - Fact accuracy penalises: >30% unverified claims → penalty
    - Composite = rubric_normalized (the rubric IS the score)
    - Verdict thresholds recalibrated for rubric-only scoring
    """
    existing_ads = existing_ads or []
    config = client["config"]

    # Gate 1: Rule compliance
    rules_result = rule_checker.check_rules(
        ad,
        client["rules"],
        critical_rules=config.get("critical_rules", []),
    )

    # Gate 2: Fact accuracy
    facts_result = fact_checker.check_facts(ad, client["facts"])

    # The Score: Rubric (10 dimensions, LLM-scored where needed)
    rubric_result = rubric_scorer.score_rubric(
        ad,
        client["rubric"],
        config,
        existing_ads=existing_ads,
        use_llm=use_llm,
    )

    max_score = config.get("rubric", {}).get("max_score", 66.25)
    rubric_normalized = rubric_result["weighted_total"] / max_score if max_score > 0 else 0

    # Start with rubric as the base score
    composite = rubric_normalized

    # Gate: critical rule failure = 0.0
    if rules_result["critical_failure"]:
        composite = 0.0

    # Gate: contradicted fact = 0.0
    if facts_result["contradicted"] > 0:
        composite = 0.0

    # Penalty: high unverified claim rate drags score down
    # (>30% unverified = 10% penalty per 10% above threshold)
    if facts_result["claims_found"] > 0:
        unverified_rate = facts_result["unverified"] / facts_result["claims_found"]
        if unverified_rate > 0.3:
            penalty = (unverified_rate - 0.3) * 1.0  # 1:1 penalty above 30%
            composite = composite * (1.0 - min(penalty, 0.3))  # cap at 30% reduction

    # Penalty: non-critical rule failures drag score down slightly
    if rules_result["total"] > 0:
        non_critical_failures = sum(
            1 for f in rules_result["failures"] if f["severity"] != "critical"
        )
        if non_critical_failures > 0:
            # 5% penalty per non-critical failure, max 20%
            penalty = min(non_critical_failures * 0.05, 0.20)
            composite = composite * (1.0 - penalty)

    composite = round(max(0.0, composite), 4)

    # Verdict thresholds (recalibrated for rubric-only scoring)
    if rules_result["critical_failure"] or facts_result["contradicted"] > 0:
        verdict = "rewrite"
    elif composite >= 0.85:
        verdict = "production_ready"
    elif composite >= 0.70:
        verdict = "strong_draft"
    elif composite >= 0.55:
        verdict = "needs_work"
    else:
        verdict = "rewrite"

    return {
        "ad_id": ad.get("ad_id", "unknown"),
        "composite": composite,
        "verdict": verdict,
        "rule_compliance": rules_result,
        "fact_accuracy": facts_result,
        "rubric": {
            "weighted_total": rubric_result["weighted_total"],
            "max_possible": rubric_result["max_possible"],
            "raw_scores": rubric_result["raw_scores"],
            "dimension_details": rubric_result["dimension_details"],
        },
        "overrides": {
            "critical_rule_failure": rules_result["critical_failure"],
            "fact_contradiction": facts_result["contradicted"] > 0,
        },
        "penalties": {
            "unverified_claims": facts_result["unverified"],
            "non_critical_rule_failures": sum(
                1 for f in rules_result["failures"] if f["severity"] != "critical"
            ),
        },
        "scoring_method": {
            "deterministic_dimensions": sum(
                1 for d in rubric_result["dimension_details"].values()
                if d["method"] == "deterministic"
            ),
            "llm_judged_dimensions": sum(
                1 for d in rubric_result["dimension_details"].values()
                if d["method"] == "llm"
            ),
            "heuristic_dimensions": sum(
                1 for d in rubric_result["dimension_details"].values()
                if d["method"] == "heuristic"
            ),
        },
    }


def format_report(report):
    """Format a score report as human-readable text."""
    lines = []
    lines.append("=== Score Report: %s ===" % report["ad_id"])
    lines.append("Composite: %.4f" % report["composite"])
    lines.append("Verdict: %s" % report["verdict"].upper())
    lines.append("")

    if report["overrides"]["critical_rule_failure"]:
        lines.append("!! CRITICAL RULE FAILURE — score overridden to 0.0")
    if report["overrides"]["fact_contradiction"]:
        lines.append("!! FACT CONTRADICTION — score overridden to 0.0")

    pen = report.get("penalties", {})
    if pen.get("non_critical_rule_failures", 0) > 0:
        lines.append("!! %d non-critical rule failure(s) — score penalised" % pen["non_critical_rule_failures"])
    if pen.get("unverified_claims", 0) > 0:
        lines.append("!! %d unverified claim(s) — score may be penalised" % pen["unverified_claims"])
    lines.append("")

    # Rule compliance
    rc = report["rule_compliance"]
    gate = "PASS" if not report["overrides"]["critical_rule_failure"] else "FAIL"
    lines.append("--- Rules [%s]: %d/%d passed ---" % (gate, rc["passed"], rc["total"]))
    if rc["failures"]:
        for f in rc["failures"]:
            sev = "CRITICAL" if f["severity"] == "critical" else "FAIL"
            lines.append("  [%s] %s: %s" % (sev, f["rule_id"], f["detail"]))
    lines.append("")

    # Fact accuracy
    fa = report["fact_accuracy"]
    gate = "PASS" if report["overrides"]["fact_contradiction"] is False else "FAIL"
    lines.append("--- Facts [%s]: %d/%d verified ---" % (gate, fa["verified"], fa["claims_found"]))
    if fa["details"]:
        for d in fa["details"]:
            status = d["status"].upper()
            conf = " (%s)" % d["confidence"] if d.get("confidence") else ""
            fact = " -> %s" % d["fact_id"] if d.get("fact_id") else ""
            lines.append("  [%s%s] %s%s" % (status, conf, d["claim"], fact))
    lines.append("")

    # Rubric — THE SCORE
    rb = report["rubric"]
    lines.append("--- Rubric: %.1f/%.1f (%.1f%%) ---" % (
        rb["weighted_total"], rb["max_possible"],
        rb["weighted_total"] / rb["max_possible"] * 100 if rb["max_possible"] > 0 else 0
    ))
    for dim_id, detail in rb["dimension_details"].items():
        method_tag = "[%s]" % detail["method"][:3].upper()
        lines.append(
            "  %s %s: %d/5 (w=%.2fx -> %.1f) — %s" % (
                method_tag, dim_id, detail["score"],
                detail["weight"], detail["weighted"],
                detail["detail"][:80],
            )
        )
    lines.append("")

    sm = report["scoring_method"]
    lines.append(
        "Scoring: %d deterministic, %d LLM, %d heuristic" % (
            sm["deterministic_dimensions"],
            sm["llm_judged_dimensions"],
            sm["heuristic_dimensions"],
        )
    )

    return "\n".join(lines)
