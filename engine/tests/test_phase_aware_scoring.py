"""Tests for phase-aware scoring introduced in PR #123.

Covers the four scenarios the PR description validated, plus edge cases:

  1. Pre-campaign hard scarcity (act now / ends today) → scarcity_register = 1/5
     with MISL-001 flag in detail string.
  2. Out-of-phase CTA ("Invest Now" on a pre-campaign ad) → cta_clarity = 1/5
     with OUT-OF-PHASE flag in detail string.
  3. Soft scarcity (opens soon / early access) → scarcity_register = 5/5 (or 4/5
     for a single signal) regardless of phase.
  4. Ad without campaign_phase field falls back to config default
     ("pre-campaign") so hard scarcity is still blocked.
  5. During-offer phase: "Invest Now" CTA is in-phase → 5/5.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from engine.rubric_scorer import _score_cta_clarity, _score_scarcity_register  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FMTH_CONFIG_PATH = ROOT / "clients" / "farm-thru" / "config.json"


@pytest.fixture()
def fmth_config():
    with open(FMTH_CONFIG_PATH) as f:
        return json.load(f)


def _meta_ad(**kwargs) -> dict:
    """Build a minimal meta-ad with sensible defaults."""
    base = {
        "content_type": "meta-ad",
        "campaign_phase": "pre-campaign",
        "primary_text": "Hello world.",
        "headline": "Test headline",
        "description": "Test description",
        "cta": "",
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# 1. Pre-campaign hard scarcity → 1/5
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("hard_phrase", [
    "Act now — spots are filling fast.",
    "Last chance to get on the list.",
    "Ends today at midnight.",
    "Hurry — only 50 spots left.",
    "Don't miss out on early access.",
    "Limited time only.",
])
def test_precampaign_hard_scarcity_scores_1(hard_phrase, fmth_config):
    ad = _meta_ad(
        primary_text=f"We're building a grocery store you can own. {hard_phrase} *CSF risk warning.",
        campaign_phase="pre-campaign",
    )
    score, detail = _score_scarcity_register(ad, fmth_config)
    assert score == 1, f"Expected 1/5 for hard scarcity '{hard_phrase}', got {score}: {detail}"
    assert "PRE-CAMPAIGN" in detail or "MISL-001" in detail, (
        f"Expected MISL-001/PRE-CAMPAIGN flag in detail: {detail}"
    )


# ---------------------------------------------------------------------------
# 2. Out-of-phase CTA → 1/5
# ---------------------------------------------------------------------------

def test_invest_now_cta_out_of_phase_precampaign(fmth_config):
    """'Invest Now' is a during-offer CTA. On a pre-campaign ad it must score 1/5."""
    ad = _meta_ad(cta="Invest Now", campaign_phase="pre-campaign")
    score, detail = _score_cta_clarity(ad, fmth_config)
    assert score == 1, f"Expected 1/5 for out-of-phase CTA, got {score}: {detail}"
    assert "OUT-OF-PHASE" in detail, f"Expected OUT-OF-PHASE flag in detail: {detail}"


def test_see_the_opportunity_out_of_phase(fmth_config):
    """'See the Opportunity' is also a cfe_campaign CTA — out-of-phase pre-campaign."""
    ad = _meta_ad(cta="See the Opportunity", campaign_phase="pre-campaign")
    score, detail = _score_cta_clarity(ad, fmth_config)
    assert score == 1, f"Expected 1/5 for out-of-phase CTA, got {score}: {detail}"
    assert "OUT-OF-PHASE" in detail


# ---------------------------------------------------------------------------
# 3. Soft scarcity → 4/5 (single signal) or 5/5 (two+ signals)
# ---------------------------------------------------------------------------

def test_soft_scarcity_single_signal(fmth_config):
    ad = _meta_ad(
        primary_text="Registration opens soon. Leave your email and we'll let you know.",
        campaign_phase="pre-campaign",
    )
    score, detail = _score_scarcity_register(ad, fmth_config)
    assert score >= 4, f"Expected 4-5/5 for soft scarcity, got {score}: {detail}"


def test_soft_scarcity_two_signals_scores_5(fmth_config):
    ad = _meta_ad(
        primary_text=(
            "Registration opens soon. First in gets first access. "
            "Leave your email and we'll tell you the moment it goes live."
        ),
        campaign_phase="pre-campaign",
    )
    score, detail = _score_scarcity_register(ad, fmth_config)
    assert score == 5, f"Expected 5/5 for two soft scarcity signals, got {score}: {detail}"


def test_early_access_is_soft_scarcity(fmth_config):
    """'early access' is explicitly whitelisted by Birchal (FMTH-EARLY-ACCESS-001)."""
    ad = _meta_ad(
        primary_text="Get in early — early access members get priority when the round opens.",
        campaign_phase="pre-campaign",
    )
    score, detail = _score_scarcity_register(ad, fmth_config)
    assert score >= 4, f"Expected 4-5/5 for 'early access', got {score}: {detail}"


# ---------------------------------------------------------------------------
# 4. Missing campaign_phase falls back to config default (pre-campaign)
# ---------------------------------------------------------------------------

def test_missing_phase_falls_back_to_config_default(fmth_config):
    """An ad without campaign_phase should use the config default (pre-campaign)
    and therefore flag hard scarcity as a MISL-001 risk."""
    ad = _meta_ad(
        primary_text="Act now — last chance to join the waitlist.",
    )
    # Remove the phase key entirely
    del ad["campaign_phase"]
    score, detail = _score_scarcity_register(ad, fmth_config)
    assert score == 1, f"Expected 1/5 when phase missing (falls back to pre-campaign), got {score}"
    assert "PRE-CAMPAIGN" in detail or "MISL-001" in detail


def test_missing_phase_cta_falls_back_to_precampaign(fmth_config):
    """Out-of-phase CTA check also uses config default when phase absent."""
    ad = _meta_ad(cta="Invest Now")
    del ad["campaign_phase"]
    score, detail = _score_cta_clarity(ad, fmth_config)
    assert score == 1, f"Expected 1/5 for out-of-phase CTA with missing phase, got {score}"
    assert "OUT-OF-PHASE" in detail


# ---------------------------------------------------------------------------
# 5. During-offer phase: "Invest Now" is in-phase
# ---------------------------------------------------------------------------

def test_invest_now_during_offer_is_in_phase(fmth_config):
    ad = _meta_ad(cta="Invest Now", campaign_phase="during-offer")
    score, detail = _score_cta_clarity(ad, fmth_config)
    # "Invest Now" is on the cfe_campaign list which is allowed during-offer
    assert score >= 4, f"Expected 4-5/5 for in-phase CTA during-offer, got {score}: {detail}"
    assert "OUT-OF-PHASE" not in detail, f"Should not flag OUT-OF-PHASE: {detail}"


def test_join_waitlist_during_offer_is_in_phase(fmth_config):
    """Pre-campaign CTAs (cfe_waitlist) remain valid during-offer."""
    ad = _meta_ad(
        cta="Join the Waitlist",
        campaign_phase="during-offer",
        primary_text="Leave your email — we'll tell you the moment it goes live.",
    )
    score, detail = _score_cta_clarity(ad, fmth_config)
    assert score == 5, f"Expected 5/5 for waitlist CTA with outcome in body, got {score}: {detail}"


# ---------------------------------------------------------------------------
# 6. Post-offer phase: only brand CTAs allowed
# ---------------------------------------------------------------------------

def test_invest_now_post_offer_is_out_of_phase(fmth_config):
    """After the offer closes, 'Invest Now' should be out-of-phase."""
    ad = _meta_ad(cta="Invest Now", campaign_phase="post-offer")
    score, detail = _score_cta_clarity(ad, fmth_config)
    assert score == 1, f"Expected 1/5 for out-of-phase CTA post-offer, got {score}: {detail}"
    assert "OUT-OF-PHASE" in detail


# ---------------------------------------------------------------------------
# 7. Hard scarcity during-offer is not a MISL-001 flag (different treatment)
# ---------------------------------------------------------------------------

def test_hard_scarcity_during_offer_not_misl001(fmth_config):
    """During-offer, hard scarcity is distasteful but not a MISL-001 risk
    because a real deadline exists. Should score 2/5 (mixed) or 1/5 (pure hard),
    but NOT be flagged as PRE-CAMPAIGN MISL-001."""
    ad = _meta_ad(
        primary_text="The round closes in 48 hours. Act now before it's gone.",
        campaign_phase="during-offer",
    )
    score, detail = _score_scarcity_register(ad, fmth_config)
    # Hard scarcity during-offer scores 2/5 (pure hard) — no MISL-001 label
    assert score <= 2, f"Hard scarcity should score low, got {score}: {detail}"
    assert "PRE-CAMPAIGN" not in detail, (
        f"Should not flag PRE-CAMPAIGN for during-offer hard scarcity: {detail}"
    )
    assert "MISL-001" not in detail


# ---------------------------------------------------------------------------
# 8. No scarcity → 3/5 (neutral)
# ---------------------------------------------------------------------------

def test_no_scarcity_scores_3(fmth_config):
    ad = _meta_ad(
        primary_text="We grow food the way it should be grown. Regenerative. Direct.",
        campaign_phase="pre-campaign",
    )
    score, detail = _score_scarcity_register(ad, fmth_config)
    assert score == 3, f"Expected 3/5 for no scarcity signals, got {score}: {detail}"
