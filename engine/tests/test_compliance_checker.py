"""Tests for engine/compliance_checker.py.

These tests use the real seed rules at
shared/regulatory/csf-australia/compliance_rules.json. No live LLM calls
are made — every test that would touch the LLM passes enable_llm=False
(or covers a non-LLM rule).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Allow `from engine.compliance_checker import ...` when pytest is run
# from inside engine/tests.
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from engine.compliance_checker import (  # noqa: E402
    ComplianceResult,
    Violation,
    _clear_cache,
    check_compliance,
)


@pytest.fixture(autouse=True)
def _clean_cache():
    """Reset module-level cache between tests so per-test rules paths work."""
    _clear_cache()
    yield
    _clear_cache()


# -------------------------------------------------------------------------
# 1. required_phrase passes when present
# -------------------------------------------------------------------------

def test_required_phrase_passes_when_present():
    text = (
        "Back this Aussie regen brand on Birchal during the offer window. "
        "Always consider the general CSF risk warning and offer document before investing."
    )
    result = check_compliance(text, content_type="email", enable_llm=False)

    assert isinstance(result, ComplianceResult)
    adv001_violations = [
        v for v in result.blocking_violations + result.warnings + result.advisory
        if v.rule_id == "ADV-001"
    ]
    assert adv001_violations == []


# -------------------------------------------------------------------------
# 2. required_phrase fails when missing
# -------------------------------------------------------------------------

def test_required_phrase_fails_when_missing():
    text = "Back our regen-ag raise on Birchal — register your interest today."
    result = check_compliance(text, content_type="email", enable_llm=False)

    blocking_ids = [v.rule_id for v in result.blocking_violations]
    assert "ADV-001" in blocking_ids

    adv001 = next(v for v in result.blocking_violations if v.rule_id == "ADV-001")
    assert adv001.severity == "BLOCKING"
    assert adv001.fix_message  # non-empty fix instructions
    assert "RG-261.92" in adv001.source_ref


# -------------------------------------------------------------------------
# 3. regex_forbidden fails when present
# -------------------------------------------------------------------------

def test_regex_forbidden_fails_when_present():
    text = (
        "Lock in your $5 refundable VIP deposit today. "
        "Always consider the general CSF risk warning and offer document before investing."
    )
    result = check_compliance(text, content_type="meta-ad", enable_llm=False)

    blocking_ids = [v.rule_id for v in result.blocking_violations]
    assert "ADV-002" in blocking_ids

    adv002 = next(v for v in result.blocking_violations if v.rule_id == "ADV-002")
    assert "$5" in adv002.matched_text
    assert adv002.line_hint  # context window populated


# -------------------------------------------------------------------------
# 4. regex_forbidden passes when match is inside whitelist context
# -------------------------------------------------------------------------

def test_regex_forbidden_passes_with_whitelist():
    # The "$50" pattern requires the words min/investment/minimum next to it,
    # so we exercise whitelist suppression on a different vector: confirm the
    # farmer-pay / market-size phrasing does not trip ADV-002.
    text = (
        "We pay farmers $3.80/kg at the farmgate, in a $130B grocery market. "
        "Always consider the general CSF risk warning and offer document before investing."
    )
    result = check_compliance(text, content_type="landing-page", enable_llm=False)

    adv002_violations = [v for v in result.blocking_violations if v.rule_id == "ADV-002"]
    assert adv002_violations == []


def test_regex_forbidden_whitelist_suppresses_match(tmp_path):
    """Tighter whitelist test — author a rule whose forbidden pattern would
    fire, and verify the whitelist context suppresses it."""
    rules = {
        "jurisdiction": "AU-CSF",
        "regulations_covered": ["TEST"],
        "rules": [
            {
                "rule_id": "TST-001",
                "category": "test",
                "claim": "Forbidden in copy unless used in farmer-pay context",
                "source_ref": ["TEST"],
                "severity": "BLOCKING",
                "scope": {
                    "content_types": ["email"],
                    "phase": "always",
                    "applies_to": "issuer",
                },
                "check_type": "regex_forbidden",
                "forbidden_patterns": [r"\$3\.80"],
                "whitelist_contexts": ["farmer pay"],
                "violation_message": "test",
            }
        ],
    }
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps(rules))

    suppressed = check_compliance(
        "We pay farmer pay rates of $3.80/kg.",
        content_type="email",
        rules_path=str(rules_path),
        enable_llm=False,
    )
    assert [v.rule_id for v in suppressed.blocking_violations] == []

    _clear_cache()
    triggered = check_compliance(
        "Membership is $3.80 per delivery.",
        content_type="email",
        rules_path=str(rules_path),
        enable_llm=False,
    )
    assert [v.rule_id for v in triggered.blocking_violations] == ["TST-001"]


# -------------------------------------------------------------------------
# 5. content_type scope filtering
# -------------------------------------------------------------------------

def test_content_type_scope_filtering(tmp_path):
    """A rule scoped to landing-page must not fire when content_type=email."""
    rules = {
        "jurisdiction": "AU-CSF",
        "regulations_covered": ["TEST"],
        "rules": [
            {
                "rule_id": "LP-ONLY-001",
                "category": "test",
                "claim": "Landing-page-only rule",
                "source_ref": ["TEST"],
                "severity": "BLOCKING",
                "scope": {
                    "content_types": ["landing-page"],
                    "phase": "always",
                    "applies_to": "issuer",
                },
                "check_type": "regex_forbidden",
                "forbidden_patterns": ["forbidden token"],
                "violation_message": "should not appear in emails",
            }
        ],
    }
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps(rules))

    text = "This email contains the forbidden token clearly."

    email_result = check_compliance(
        text, content_type="email", rules_path=str(rules_path), enable_llm=False
    )
    assert email_result.blocking_violations == []
    assert email_result.rules_evaluated == 0
    assert email_result.rules_skipped_out_of_scope == 1
    assert email_result.passed is True

    _clear_cache()
    lp_result = check_compliance(
        text, content_type="landing-page", rules_path=str(rules_path), enable_llm=False
    )
    assert [v.rule_id for v in lp_result.blocking_violations] == ["LP-ONLY-001"]


# -------------------------------------------------------------------------
# 6. llm_judge skipped silently when disabled
# -------------------------------------------------------------------------

def test_llm_judge_skipped_when_disabled():
    """ADV-004 is the only llm_judge rule in the seed file. With
    enable_llm=False it must not appear in any violation list, regardless
    of what the copy says."""
    text = (
        "Our forecast revenue is $100M next year, no basis given. "
        "Always consider the general CSF risk warning and offer document before investing."
    )
    result = check_compliance(text, content_type="meta-ad", enable_llm=False)

    all_violations = (
        result.blocking_violations + result.warnings + result.advisory
    )
    assert all(v.rule_id != "ADV-004" for v in all_violations)

    # The skipped LLM rule should be counted in rules_skipped_out_of_scope.
    assert result.rules_skipped_out_of_scope >= 1


# -------------------------------------------------------------------------
# 7. Any BLOCKING violation makes passed=False
# -------------------------------------------------------------------------

def test_blocking_violation_sets_passed_false():
    text = "Reply to this email to invest in our raise."
    result = check_compliance(text, content_type="email", enable_llm=False)

    assert result.passed is False
    assert len(result.blocking_violations) > 0
    blocking_ids = [v.rule_id for v in result.blocking_violations]
    assert "ADV-003" in blocking_ids


def test_clean_copy_passes_overall():
    """Sanity check — a copy that meets ADV-001 and avoids the forbidden
    patterns should pass with passed=True (LLM rule disabled)."""
    text = (
        "Back this Aussie regen brand on Birchal during the live offer. "
        "Always consider the general CSF risk warning and offer document before investing."
    )
    result = check_compliance(text, content_type="email", enable_llm=False)
    assert result.passed is True
    assert result.blocking_violations == []


# -------------------------------------------------------------------------
# 8. FMTH-PRIORITY-001 — founder-directive ban on "priority" word family
# -------------------------------------------------------------------------

def test_fmth_priority_blocks_priority_access():
    """FMTH-PRIORITY-001 must fire when 'priority access' appears in copy.

    Per founder directive 2026-04-26 (CSF-VIP-BIRCHAL-SUBMISSION.md §9),
    the word 'priority' is globally banned in FMTH VIP / investment copy.
    """
    text = (
        "Lock in priority access to the FarmThru investment offer when our "
        "Birchal CSF round opens. Place a small refundable deposit to secure VIP. "
        "Always consider the general CSF risk warning and offer document before investing."
    )
    result = check_compliance(text, content_type="landing-page", enable_llm=False)

    blocking_ids = [v.rule_id for v in result.blocking_violations]
    assert "FMTH-PRIORITY-001" in blocking_ids
    assert result.passed is False


def test_fmth_priority_blocks_priority_sms():
    """The compound 'priority SMS' is one of the explicit retired phrasings
    in CSF-VIP-BIRCHAL-SUBMISSION.md §9 — must fire FMTH-PRIORITY-001.
    """
    text = (
        "We'll send you a priority SMS the moment the round opens at Birchal. "
        "Always consider the general CSF risk warning and offer document before investing."
    )
    result = check_compliance(text, content_type="email", enable_llm=False)

    blocking_ids = [v.rule_id for v in result.blocking_violations]
    assert "FMTH-PRIORITY-001" in blocking_ids


def test_fmth_priority_passes_when_replaced_with_early():
    """The founder-approved replacement for 'priority' is 'early'. Copy that
    uses 'early access' instead of 'priority access' must NOT trigger
    FMTH-PRIORITY-001.
    """
    text = (
        "Lock in early access to the FarmThru investment offer when our "
        "Birchal CSF round opens. Place a small refundable deposit to secure VIP. "
        "Always consider the general CSF risk warning and offer document before investing."
    )
    result = check_compliance(text, content_type="landing-page", enable_llm=False)

    blocking_ids = [v.rule_id for v in result.blocking_violations]
    assert "FMTH-PRIORITY-001" not in blocking_ids


def test_fmth_priority_passes_on_birchal_approved_phrasing():
    """Birchal-approved phrasing 'early private access to the investment offer'
    must pass FMTH-PRIORITY-001 (no banned word) and is NOT blocked by any
    'early access' rule (no such rule exists in the shared set — confirmed
    by the existing ADV-004/MISL-004 prompts which explicitly do not flag
    access-timing language as forecasts).
    """
    text = (
        "VIP investors get early private access to the investment offer at Birchal "
        "when our CSF round opens, plus founder updates from Rachel and the team. "
        "Always consider the general CSF risk warning and offer document before investing."
    )
    result = check_compliance(text, content_type="landing-page", enable_llm=False)

    blocking_ids = [v.rule_id for v in result.blocking_violations]
    assert "FMTH-PRIORITY-001" not in blocking_ids


# -------------------------------------------------------------------------
# 9. FMTH-NO-DOLLAR-METAAD — Meta platform-policy ban on explicit $ amounts
# -------------------------------------------------------------------------

def test_fmth_no_dollar_metaad_blocks_explicit_amount():
    """FMTH-NO-DOLLAR-METAAD must fire when a meta-ad contains an explicit
    dollar amount. Meta financial-vertical platform policy frequently
    rejects ads with explicit $ amounts. Writer must paraphrase to
    'a small refundable deposit' or similar prose.
    """
    text = (
        "Be part of FarmThru. Lock in early access to invest from $50 when our "
        "CSF round opens. Reserve your spot with a small refundable deposit. "
        "See the general CSF risk warning + offer document."
    )
    result = check_compliance(text, content_type="meta-ad", enable_llm=False)

    blocking_ids = [v.rule_id for v in result.blocking_violations]
    assert "FMTH-NO-DOLLAR-METAAD" in blocking_ids
    assert result.passed is False


def test_fmth_no_dollar_metaad_passes_when_paraphrased():
    """Meta-ad copy that paraphrases dollar values via prose ('a small
    refundable deposit') must NOT trigger FMTH-NO-DOLLAR-METAAD. Confirms
    the canonical Task 3 rewrite pattern (PR #94) is forward-compatible.
    """
    text = (
        "Be part of FarmThru. Lock in early access to invest when our CSF "
        "round opens. Reserve your spot with a small refundable deposit. "
        "See the general CSF risk warning + offer document."
    )
    result = check_compliance(text, content_type="meta-ad", enable_llm=False)

    blocking_ids = [v.rule_id for v in result.blocking_violations]
    assert "FMTH-NO-DOLLAR-METAAD" not in blocking_ids


def test_fmth_no_dollar_metaad_does_not_fire_on_landing_page():
    """The no-$ rule is scoped to meta-ad ONLY — landing pages and emails
    can (and should) state the exact deposit amount. Guards against
    accidental scope creep that would over-restrict LP/email copy.
    """
    text = (
        "Reserve your VIP spot. Place a $5 refundable deposit to lock in "
        "early access to the investment offer when our Birchal CSF round "
        "opens. Always consider the general CSF risk warning and offer "
        "document before investing."
    )
    result = check_compliance(text, content_type="landing-page", enable_llm=False)

    all_ids = [v.rule_id for v in result.blocking_violations + result.warnings + result.advisory]
    assert "FMTH-NO-DOLLAR-METAAD" not in all_ids
    # Rule must have been excluded by scope (not in evaluated_rule_ids).
    assert "FMTH-NO-DOLLAR-METAAD" not in result.evaluated_rule_ids


def test_fmth_no_dollar_metaad_does_not_fire_on_email():
    """Companion to the LP test — the no-$ rule must also be out-of-scope
    for emails. Emails are a longer-form channel where exact deposit
    amounts are appropriate (and required by FMTH-010 refundable disclaimer).
    """
    text = (
        "Reserve your VIP spot for a $5 refundable deposit. We'll send the "
        "offer link via Birchal when the CSF round opens. Always consider "
        "the general CSF risk warning and offer document before investing."
    )
    result = check_compliance(text, content_type="email", enable_llm=False)

    assert "FMTH-NO-DOLLAR-METAAD" not in result.evaluated_rule_ids
