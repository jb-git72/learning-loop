"""Tests for engine/hypothesis_generator._parse_hypothesis_json.

Covers the five JSON shapes the LLM can return:
  1. Valid JSON list of dicts
  2. Single dict (coerced to list)
  3. Markdown fenced code block (```json ... ```)
  4. Bare JSON array buried in prose (regex-extracted)
  5. Malformed / unparseable input (returns empty list)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from engine.hypothesis_generator import _parse_hypothesis_json  # noqa: E402


# ---------------------------------------------------------------------------
# 1. Valid JSON list
# ---------------------------------------------------------------------------

def test_valid_json_list():
    raw = json.dumps([
        {
            "id": "H1",
            "claim": "The curiosity-gap hook is load-bearing.",
            "load_bearing_element": "scroll_stop_hook",
            "test": "Replace with a direct declarative statement.",
            "alternative_hook_seed": "Open with a flat statement of the offer.",
            "alternative_headline_seed": "Direct headline.",
            "expected_direction": "performance_drops",
            "confidence_prior": 0.7,
            "knowledge_used": ["hooks/curiosity_gap"],
        },
        {
            "id": "H2",
            "claim": "Soft scarcity builds urgency without panic.",
            "load_bearing_element": "scarcity_register",
            "test": "Remove all scarcity language.",
            "alternative_hook_seed": "Lead with proof only, no urgency.",
            "alternative_headline_seed": "No-scarcity headline.",
            "expected_direction": "performance_drops",
            "confidence_prior": 0.6,
            "knowledge_used": ["scarcity_register_rubric"],
        },
    ])
    result = _parse_hypothesis_json(raw)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["id"] == "H1"
    assert result[1]["id"] == "H2"


# ---------------------------------------------------------------------------
# 2. Single dict coerced to list
# ---------------------------------------------------------------------------

def test_single_dict_coerced():
    raw = json.dumps({
        "id": "H1",
        "claim": "Ownership framing converts better than transactional framing.",
        "load_bearing_element": "ownership_framing",
        "test": "Replace 'own a piece' with 'invest in'.",
        "alternative_hook_seed": "Use ROI language instead of identity language.",
        "alternative_headline_seed": "Returns-led headline.",
        "expected_direction": "performance_drops",
        "confidence_prior": 0.65,
        "knowledge_used": ["ownership_framing_rubric"],
    })
    result = _parse_hypothesis_json(raw)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["id"] == "H1"
    assert result[0]["load_bearing_element"] == "ownership_framing"


# ---------------------------------------------------------------------------
# 3. Fenced markdown code block (```json ... ```)
# ---------------------------------------------------------------------------

def test_fenced_markdown_block():
    payload = [
        {
            "id": "H1",
            "claim": "Named-person hook earns attention.",
            "load_bearing_element": "scroll_stop_hook",
            "test": "Replace named person with a question hook.",
            "alternative_hook_seed": "Open with a direct question.",
            "alternative_headline_seed": "Question headline.",
            "expected_direction": "performance_drops",
            "confidence_prior": 0.7,
            "knowledge_used": ["hooks/story"],
        }
    ]
    raw = "Here are the hypotheses:\n\n```json\n" + json.dumps(payload) + "\n```\n\nEnd."
    result = _parse_hypothesis_json(raw)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["id"] == "H1"


def test_fenced_plain_block():
    """Handles ``` without the 'json' language tag."""
    payload = [{"id": "H1", "claim": "Test claim."}]
    raw = "```\n" + json.dumps(payload) + "\n```"
    result = _parse_hypothesis_json(raw)
    assert isinstance(result, list)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# 4. Regex-extracted array buried in prose
# ---------------------------------------------------------------------------

def test_regex_extract_array_in_prose():
    payload = [
        {"id": "H1", "claim": "Statistic hook lifts performance."},
        {"id": "H2", "claim": "Soft scarcity is essential."},
    ]
    prose = (
        "After analysing the ad, here are my hypotheses. "
        + json.dumps(payload)
        + " That concludes the analysis."
    )
    result = _parse_hypothesis_json(prose)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["id"] == "H1"
    assert result[1]["id"] == "H2"


# ---------------------------------------------------------------------------
# 5. Malformed / completely unparseable input
# ---------------------------------------------------------------------------

def test_malformed_returns_empty():
    result = _parse_hypothesis_json("This is not JSON at all.")
    assert result == []


def test_empty_string_returns_empty():
    result = _parse_hypothesis_json("")
    assert result == []


def test_none_returns_empty():
    # _parse_hypothesis_json checks `if not raw`
    result = _parse_hypothesis_json(None)
    assert result == []


def test_malformed_json_returns_empty():
    result = _parse_hypothesis_json("[{id: missing_quotes, claim: broken}")
    assert result == []


def test_truncated_array_returns_empty():
    """Partial JSON that starts as an array but is cut off mid-object."""
    result = _parse_hypothesis_json('[{"id": "H1", "claim":')
    assert result == []


# ---------------------------------------------------------------------------
# 6. Edge cases: non-list, non-dict top-level value
# ---------------------------------------------------------------------------

def test_json_number_returns_empty():
    result = _parse_hypothesis_json("42")
    assert result == []


def test_json_string_returns_empty():
    result = _parse_hypothesis_json('"just a string"')
    assert result == []


def test_json_null_returns_empty():
    result = _parse_hypothesis_json("null")
    assert result == []


# ---------------------------------------------------------------------------
# 7. IDs are stamped by generate_hypotheses caller — _parse returns as-is
# ---------------------------------------------------------------------------

def test_ids_preserved():
    payload = [
        {"id": "H3", "claim": "Preserved ID."},
        {"claim": "No ID — caller will stamp it."},
    ]
    result = _parse_hypothesis_json(json.dumps(payload))
    assert result[0]["id"] == "H3"
    assert "id" not in result[1]  # parser doesn't stamp, caller does
