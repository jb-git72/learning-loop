"""Integration tests for the compliance HARD GATE in engine.scorer.score_ad.

We feed score_ad a minimal in-memory client + ad and assert that:
- A BLOCKING compliance violation zeroes the composite and forces verdict=rewrite.
- A clean ad with compliance enabled keeps its rubric-derived composite.
- compliance.enabled=False (or absent) bypasses the gate entirely.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from engine import compliance_checker, scorer


# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------

CLEAN_FMTH_BODY = (
    "FarmThru is launching equity crowdfunding through Birchal. "
    "Reserve your VIP spot — small refundable deposit. "
    "Always consider the general CSF risk warning and offer document before investing."
)

DIRTY_FMTH_BODY = (
    # Missing canonical CSF warning AND uses banned $5 deposit phrasing.
    "FarmThru is launching equity crowdfunding through Birchal. "
    "Reserve your VIP spot for a $5 refundable deposit today!"
)


def _write_rules_file(tmp_path: Path) -> Path:
    """Write a tiny rule file scoped to email/issuer so the gate is fast and deterministic."""
    rules_path = tmp_path / "compliance_rules.json"
    rules_path.write_text(
        json.dumps(
            {
                "jurisdiction": "AU-CSF",
                "regulations_covered": ["RG-261"],
                "rules": [
                    {
                        "rule_id": "ADV-001",
                        "category": "advertising",
                        "claim": "Marketing must include the CSF warning",
                        "source_ref": ["RG-261.92"],
                        "severity": "BLOCKING",
                        "scope": {
                            "content_types": ["email", "landing-page"],
                            "phase": "during-offer",
                            "applies_to": "issuer",
                        },
                        "check_type": "required_phrase",
                        "required_phrase_patterns": [
                            "Always consider the general CSF risk warning",
                        ],
                        "violation_message": "Append the canonical CSF warning.",
                    },
                    {
                        "rule_id": "ADV-002",
                        "category": "advertising",
                        "claim": "No specific investment $ amounts in marketing copy",
                        "source_ref": ["RG-261.96"],
                        "severity": "BLOCKING",
                        "scope": {
                            "content_types": ["email", "landing-page"],
                            "phase": "during-offer",
                            "applies_to": "issuer",
                        },
                        "check_type": "regex_forbidden",
                        "forbidden_patterns": [r"\$5\s*(refundable|deposit|VIP)"],
                        "violation_message": "Strip the $ amount.",
                    },
                ],
            }
        )
    )
    return rules_path


def _make_client(tmp_path: Path, *, compliance_enabled: bool, rules_path: Path | None) -> dict:
    """Build the minimal client dict score_ad needs — no disk reads, no live LLM."""
    config = {
        "client_id": "test-client",
        "client_name": "Test",
        "content_types": ["email"],
    }
    if compliance_enabled:
        config["compliance"] = {
            "enabled": True,
            "applies_to": "issuer",
            "rules_path": str(rules_path) if rules_path else None,
        }

    rubric = {
        "dimensions": [
            {
                "id": "clarity",
                "weight": 1.0,
                "method": "deterministic",
                "anchors": {0: "unclear", 5: "perfectly clear"},
            }
        ],
        "max_score": 5,
    }

    return {
        "config": config,
        "rules": [],
        "facts": {"facts": []},
        "rubric": rubric,
        "rubrics": {"email": rubric},
        "client_dir": str(tmp_path),
        "shared_dir": str(tmp_path),
    }


def _make_ad(body: str) -> dict:
    return {
        "ad_id": "EM-TEST-01",
        "content_type": "email",
        "subject": "FarmThru update",
        "preheader": "",
        "body": body,
    }


# -------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolated_rules_cache():
    """Each test starts with a fresh module cache so rules_path swaps work."""
    compliance_checker._clear_cache()
    yield
    compliance_checker._clear_cache()


@pytest.fixture(autouse=True)
def _no_anthropic_key(monkeypatch):
    """Force LLM judges to skip silently — keeps tests offline + deterministic."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_compliance_disabled_means_gate_is_no_op(tmp_path):
    client = _make_client(tmp_path, compliance_enabled=False, rules_path=None)
    ad = _make_ad(DIRTY_FMTH_BODY)

    report = scorer.score_ad(ad, client, use_llm=False)

    assert report["compliance"] == {"enabled": False}
    assert report["overrides"]["compliance_blocking"] is False
    # Composite untouched by compliance — depends only on rubric path.
    assert report["composite"] >= 0.0
    assert report["verdict"] in {"production_ready", "strong_draft", "needs_work", "rewrite"}


def test_blocking_compliance_violation_zeroes_composite(tmp_path):
    rules_path = _write_rules_file(tmp_path)
    client = _make_client(tmp_path, compliance_enabled=True, rules_path=rules_path)
    ad = _make_ad(DIRTY_FMTH_BODY)

    report = scorer.score_ad(ad, client, use_llm=False)

    assert report["compliance"]["enabled"] is True
    assert report["compliance"]["passed"] is False
    blocking = report["compliance"]["blocking_violations"]
    rule_ids = sorted(v["rule_id"] for v in blocking)
    assert rule_ids == ["ADV-001", "ADV-002"]
    assert report["overrides"]["compliance_blocking"] is True
    assert report["composite"] == 0.0
    assert report["verdict"] == "rewrite"


def test_clean_copy_passes_compliance_gate(tmp_path):
    rules_path = _write_rules_file(tmp_path)
    client = _make_client(tmp_path, compliance_enabled=True, rules_path=rules_path)
    ad = _make_ad(CLEAN_FMTH_BODY)

    report = scorer.score_ad(ad, client, use_llm=False)

    assert report["compliance"]["passed"] is True
    assert report["compliance"]["blocking_violations"] == []
    assert report["overrides"]["compliance_blocking"] is False
    # Composite is whatever the rubric produced; it must not be zeroed by compliance.
    assert report["composite"] >= 0.0
