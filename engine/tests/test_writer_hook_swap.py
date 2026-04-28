"""Tests for writer._parse_hook_swap_output.

_parse_hook_swap_output is introduced alongside generate_hook_swap_variant
(feat/hypothesis-hook-swap, not yet merged to main at the time of this audit).
These tests are written now so they run green the moment that PR merges.

All tests use `pytest.importorskip` to gracefully skip if the function is not
yet present in writer.py — they will NOT block CI on the current branch.

Covers the same shape matrix as test_hypothesis_generator.py:
  1. Valid JSON object (happy path)
  2. Fenced markdown code block
  3. JSON object buried in prose (regex-extracted)
  4. Missing required keys → returns None
  5. Malformed / empty input → returns None
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# Gracefully skip if the function hasn't been merged yet.
try:
    from writer import _parse_hook_swap_output  # type: ignore[import]
    _SKIP_REASON = None
except (ImportError, AttributeError):
    _parse_hook_swap_output = None  # type: ignore[assignment]
    _SKIP_REASON = "_parse_hook_swap_output not yet in writer.py (feat/hypothesis-hook-swap not merged)"

pytestmark = pytest.mark.skipif(
    _parse_hook_swap_output is None,
    reason=_SKIP_REASON or "",
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_VALID_PAYLOAD = {
    "new_opening_paragraph": "Last Tuesday Rachel's pasture-raised beef sold out in 40 minutes. That's never happened before.",
    "new_headline": "When it goes, it's gone",
    "hypothesis_id": "H1",
    "change_rationale": "Replaces curiosity-gap opener with a story moment to test which hook type carries the ad.",
}


# ---------------------------------------------------------------------------
# 1. Valid JSON object
# ---------------------------------------------------------------------------

def test_valid_json_object():
    raw = json.dumps(_VALID_PAYLOAD)
    result = _parse_hook_swap_output(raw)
    assert result is not None
    assert result["new_opening_paragraph"] == _VALID_PAYLOAD["new_opening_paragraph"]
    assert result["new_headline"] == _VALID_PAYLOAD["new_headline"]


# ---------------------------------------------------------------------------
# 2. Fenced markdown code block
# ---------------------------------------------------------------------------

def test_fenced_json_block():
    raw = "Here is the variant:\n\n```json\n" + json.dumps(_VALID_PAYLOAD) + "\n```\n\nDone."
    result = _parse_hook_swap_output(raw)
    assert result is not None
    assert result["new_headline"] == _VALID_PAYLOAD["new_headline"]


def test_fenced_plain_block():
    raw = "```\n" + json.dumps(_VALID_PAYLOAD) + "\n```"
    result = _parse_hook_swap_output(raw)
    assert result is not None
    assert "new_opening_paragraph" in result


# ---------------------------------------------------------------------------
# 3. JSON object buried in surrounding prose
# ---------------------------------------------------------------------------

def test_json_in_prose():
    raw = (
        "I've generated the hook-swap variant based on hypothesis H1. "
        + json.dumps(_VALID_PAYLOAD)
        + " The rationale is explained above."
    )
    result = _parse_hook_swap_output(raw)
    assert result is not None
    assert result["hypothesis_id"] == "H1"


# ---------------------------------------------------------------------------
# 4. Missing required keys → None
# ---------------------------------------------------------------------------

def test_missing_new_opening_paragraph():
    bad = {"new_headline": "A headline only — no opening paragraph key"}
    result = _parse_hook_swap_output(json.dumps(bad))
    assert result is None


def test_missing_new_headline():
    bad = {"new_opening_paragraph": "An opening paragraph only — no headline key"}
    result = _parse_hook_swap_output(json.dumps(bad))
    assert result is None


def test_both_keys_required():
    """Verifies that BOTH keys must be present, not just one."""
    both_present = {
        "new_opening_paragraph": "Some opening.",
        "new_headline": "Some headline",
    }
    assert _parse_hook_swap_output(json.dumps(both_present)) is not None


# ---------------------------------------------------------------------------
# 5. Malformed / empty input → None
# ---------------------------------------------------------------------------

def test_empty_string_returns_none():
    result = _parse_hook_swap_output("")
    assert result is None


def test_none_input_returns_none():
    result = _parse_hook_swap_output(None)
    assert result is None


def test_malformed_json_returns_none():
    result = _parse_hook_swap_output("{new_opening_paragraph: missing quotes}")
    assert result is None


def test_plain_prose_returns_none():
    result = _parse_hook_swap_output("This is not JSON at all, just prose.")
    assert result is None


def test_json_list_returns_none():
    """A list is not a valid hook-swap output (must be a dict)."""
    result = _parse_hook_swap_output(json.dumps([_VALID_PAYLOAD]))
    assert result is None
