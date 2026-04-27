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
from dataclasses import asdict
from pathlib import Path

from . import compliance_checker, fact_checker, rubric_scorer, rule_checker


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

    # Load rubrics for all supported content types
    rubrics = {}
    content_types = config.get("content_types", ["meta-ad"])
    for ct in content_types:
        rubrics[ct] = rubric_scorer.load_rubric(shared_dir, content_type=ct)
    # Backwards compat: also keep default rubric
    if "meta-ad" not in rubrics:
        rubrics["meta-ad"] = rubric_scorer.load_rubric(shared_dir)

    return {
        "config": config,
        "rules": rules,
        "facts": facts,
        "rubric": rubrics.get("meta-ad", {}),  # backwards compat
        "rubrics": rubrics,
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

    # Determine content type from ad or default to meta-ad
    content_type = ad.get("content_type", "meta-ad")
    rubric = client.get("rubrics", {}).get(content_type, client.get("rubric", {}))

    # Gate 0: Regulatory compliance (HARD GATE — runs before client rules)
    # BLOCKING violations zero the composite, same as critical_rule_failure.
    # Off by default for clients that don't opt in via config.compliance.enabled.
    compliance_cfg = config.get("compliance", {}) or {}
    compliance_enabled = bool(compliance_cfg.get("enabled", False))
    if compliance_enabled:
        compliance_text = fact_checker._get_all_text(ad)
        compliance_result = compliance_checker.check_compliance(
            text=compliance_text,
            content_type=content_type,
            applies_to=compliance_cfg.get("applies_to", "issuer"),
            rules_path=compliance_cfg.get("rules_path"),
            enable_llm=use_llm and compliance_cfg.get("enable_llm", True),
            model=compliance_cfg.get("model"),
        )
    else:
        compliance_result = compliance_checker.ComplianceResult()

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
        rubric,
        config,
        existing_ads=existing_ads,
        use_llm=use_llm,
        content_type=content_type,
    )

    rubric_config = config.get("rubric", {})
    # Support per-content-type rubric config
    if isinstance(rubric_config, dict) and content_type in rubric_config:
        rubric_config = rubric_config[content_type]
    # Prefer the dynamic max_possible computed by the rubric scorer (sum of
    # weights that actually applied × 5). Falls back to config max_score only
    # if the dynamic value is zero (defensive — should never happen in practice).
    # Recalibration-v1 fix: previously we trusted the static config max_score,
    # which silently understated the divisor when dimensions without a scorer
    # for the content_type still credited a dummy 3/5 to the numerator.
    dynamic_max = rubric_result.get("max_possible", 0)
    config_max = rubric_config.get("max_score", 66.25)
    max_score = dynamic_max if dynamic_max > 0 else config_max
    rubric_normalized = rubric_result["weighted_total"] / max_score if max_score > 0 else 0

    # Start with rubric as the base score
    composite = rubric_normalized

    # Gate: regulatory BLOCKING violation = 0.0 (runs first — pulled copy)
    if compliance_enabled and not compliance_result.passed:
        composite = 0.0

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

    # Penalty: compliance WARNINGs (non-blocking) — 3% each, capped at 15%.
    # Smaller hit than client-rule failures because these come from a much
    # larger and noisier rule library.
    compliance_warning_count = len(compliance_result.warnings)
    if compliance_enabled and compliance_warning_count > 0:
        penalty = min(compliance_warning_count * 0.03, 0.15)
        composite = composite * (1.0 - penalty)

    composite = round(max(0.0, composite), 4)

    # Verdict thresholds (recalibrated for rubric-only scoring)
    if (
        (compliance_enabled and not compliance_result.passed)
        or rules_result["critical_failure"]
        or facts_result["contradicted"] > 0
    ):
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
        "compliance": _serialize_compliance(compliance_result, compliance_enabled),
        "rule_compliance": rules_result,
        "fact_accuracy": facts_result,
        "rubric": {
            "weighted_total": rubric_result["weighted_total"],
            "max_possible": rubric_result["max_possible"],
            "raw_scores": rubric_result["raw_scores"],
            "dimension_details": rubric_result["dimension_details"],
        },
        "overrides": {
            "compliance_blocking": compliance_enabled and not compliance_result.passed,
            "critical_rule_failure": rules_result["critical_failure"],
            "fact_contradiction": facts_result["contradicted"] > 0,
        },
        "penalties": {
            "unverified_claims": facts_result["unverified"],
            "non_critical_rule_failures": sum(
                1 for f in rules_result["failures"] if f["severity"] != "critical"
            ),
            "compliance_warnings": compliance_warning_count,
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


def _serialize_compliance(result, enabled):
    """Convert ComplianceResult dataclass into a JSON-friendly dict."""
    if not enabled:
        return {"enabled": False}
    return {
        "enabled": True,
        "passed": result.passed,
        "rules_evaluated": result.rules_evaluated,
        "rules_skipped_out_of_scope": result.rules_skipped_out_of_scope,
        "blocking_violations": [asdict(v) for v in result.blocking_violations],
        "warnings": [asdict(v) for v in result.warnings],
        "advisory": [asdict(v) for v in result.advisory],
    }


def format_report(report):
    """Format a score report as human-readable text."""
    lines = []
    lines.append("=== Score Report: %s ===" % report["ad_id"])
    lines.append("Composite: %.4f" % report["composite"])
    lines.append("Verdict: %s" % report["verdict"].upper())
    lines.append("")

    if report["overrides"].get("compliance_blocking"):
        lines.append("!! REGULATORY COMPLIANCE FAILURE — score overridden to 0.0")
    if report["overrides"]["critical_rule_failure"]:
        lines.append("!! CRITICAL RULE FAILURE — score overridden to 0.0")
    if report["overrides"]["fact_contradiction"]:
        lines.append("!! FACT CONTRADICTION — score overridden to 0.0")

    pen = report.get("penalties", {})
    if pen.get("compliance_warnings", 0) > 0:
        lines.append("!! %d compliance warning(s) — score penalised" % pen["compliance_warnings"])
    if pen.get("non_critical_rule_failures", 0) > 0:
        lines.append("!! %d non-critical rule failure(s) — score penalised" % pen["non_critical_rule_failures"])
    if pen.get("unverified_claims", 0) > 0:
        lines.append("!! %d unverified claim(s) — score may be penalised" % pen["unverified_claims"])
    lines.append("")

    # Regulatory compliance (only render when enabled)
    cc = report.get("compliance", {})
    if cc.get("enabled"):
        gate = "PASS" if cc.get("passed") else "FAIL"
        lines.append(
            "--- Compliance [%s]: %d rules evaluated, %d out-of-scope ---"
            % (gate, cc.get("rules_evaluated", 0), cc.get("rules_skipped_out_of_scope", 0))
        )
        for v in cc.get("blocking_violations", []):
            lines.append(
                "  [BLOCKING] %s (%s): %s — %s"
                % (v["rule_id"], "/".join(v["source_ref"]), v["line_hint"], v["fix_message"])
            )
        for v in cc.get("warnings", []):
            lines.append(
                "  [WARNING]  %s (%s): %s"
                % (v["rule_id"], "/".join(v["source_ref"]), v["line_hint"])
            )
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
