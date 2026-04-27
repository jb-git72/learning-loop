"""
Rubric Scorer — Axis 3 of the scoring engine.

13 dimensions scored 1-5 with weights.
10 deterministic, 3 LLM-judged (via llm_judge.py).

Returns: {weighted_total, max_possible, raw_scores, dimension_details}
"""

import json
import math
import re
from pathlib import Path


def load_rubric(shared_dir: Path, content_type: str = "meta-ad") -> dict:
    """Load the rubric schema for a content type."""
    # Try content-type-specific rubric first
    rubric_path = shared_dir / "rubrics" / f"{content_type}.json"
    if rubric_path.exists():
        with open(rubric_path) as f:
            rubric = json.load(f)
        # Handle inheritance
        if "inherits" in rubric:
            base_path = shared_dir / rubric["inherits"]
            with open(base_path) as f:
                return json.load(f)
        return rubric
    # Fallback to original rubric-schema.json
    rubric_path = shared_dir / "rubric-schema.json"
    with open(rubric_path) as f:
        return json.load(f)


def score_rubric(
    ad: dict,
    rubric: dict,
    client_config: dict,
    existing_ads: list[dict] = None,
    use_llm: bool = True,
    content_type: str = "meta-ad",
) -> dict:
    """Score an ad against all rubric dimensions.

    Args:
        ad: Ad in canonical JSON format
        rubric: Loaded rubric schema for this content type
        client_config: Loaded client config.json
        existing_ads: Other ads in set (for differentiation)
        use_llm: Whether to use LLM for subjective dimensions (False = skip those)
        content_type: Content type being scored (meta-ad, email, landing-page)

    Returns:
        {
            "weighted_total": float,
            "max_possible": float,
            "raw_scores": {"dimension_id": int},
            "dimension_details": {"dimension_id": {"score": int, "method": str, "detail": str}}
        }
    """
    existing_ads = existing_ads or []
    dimensions = rubric.get("dimensions", [])
    rubric_config = client_config.get("rubric", {})
    # Support per-content-type rubric config
    if isinstance(rubric_config, dict) and content_type in rubric_config:
        rubric_config = rubric_config[content_type]
    weights = rubric_config.get("weights", {})
    max_possible = rubric_config.get("max_score", 66.25)

    raw_scores = {}
    dimension_details = {}
    weighted_total = 0.0

    # Track which dims actually contribute so we can compute max_possible from
    # weights that actually applied — instead of trusting a static config value
    # that drifts when dimensions are added/removed or content_type changes.
    applied_weight_sum = 0.0

    for dim in dimensions:
        dim_id = dim["id"]
        weight = weights.get(dim_id, dim.get("default_weight", 1.0))
        method = dim.get("scoring_method", "deterministic")

        if method == "deterministic":
            score, detail = _score_deterministic(dim_id, ad, client_config, existing_ads, content_type=content_type)
        elif method == "llm" and use_llm:
            from . import llm_judge
            score, detail = llm_judge.judge_dimension(dim_id, ad, dim, client_config)
        else:
            # LLM disabled — use heuristic fallback
            score, detail = _score_heuristic_fallback(dim_id, ad)

        # Skip dims that don't apply to this content_type. _score_deterministic
        # signals "no scorer for this content_type" by returning score=None.
        # Previously this returned a dummy 3/5, inflating composite by ~3.0
        # weighted points on every meta-ad (lp_readability) and would now also
        # silently inflate other clients' scores via the new dimensions.
        if score is None:
            continue

        # Skip dims that have zero weight — they're opt-in for this client.
        if weight <= 0:
            continue

        score = max(1, min(5, score))  # Clamp to 1-5
        raw_scores[dim_id] = score
        weighted_total += score * weight
        applied_weight_sum += weight
        dimension_details[dim_id] = {
            "score": score,
            "weight": weight,
            "weighted": round(score * weight, 2),
            "method": method if (method == "deterministic" or use_llm) else "heuristic",
            "detail": detail,
        }

    # Compute max_possible from the weights that actually applied (× 5 max raw).
    # Fall back to the config value only if no dims applied at all (defensive).
    computed_max = applied_weight_sum * 5
    effective_max = computed_max if computed_max > 0 else max_possible

    return {
        "weighted_total": round(weighted_total, 2),
        "max_possible": round(effective_max, 2),
        "raw_scores": raw_scores,
        "dimension_details": dimension_details,
    }


# --- Deterministic scoring functions ---

def _score_deterministic(
    dim_id: str, ad: dict, config: dict, existing_ads: list[dict],
    content_type: str = "meta-ad",
) -> tuple[int, str]:
    """Route to the correct deterministic scorer."""
    # Common scorers (work for all content types)
    common_scorers = {
        "specificity": _score_specificity,
        "differentiation": _score_differentiation,
        "objection_preemption": _score_objection_preemption,
        "opening_diversity": _score_opening_diversity,
        "sentence_variance": _score_sentence_variance,
        "emotional_register": _score_emotional_register,
        # Recalibration-v1 additions (calibrated against the live $2-lead FMTH ad)
        "ownership_framing": _score_ownership_framing,
        "scarcity_register": _score_scarcity_register,
        "founder_voice": _score_founder_voice,
        "csf_placement": _score_csf_placement,
    }

    # Meta-ad specific
    meta_scorers = {
        "receptionist_test": _score_receptionist_test,
        "cta_clarity": _score_cta_clarity,
        "platform_fit": _score_platform_fit,
        "scroll_stop_hook": _score_scroll_stop_hook,
    }

    # Landing page specific
    landing_scorers = {
        "hero_clarity": _score_hero_clarity,
        "proof_density": _score_proof_density,
        "cta_prominence": _score_cta_prominence,
        "scroll_depth_pull": _score_scroll_depth_pull,
        "cta_clarity": _score_cta_clarity,  # reuse
        "scroll_stop_hook": _score_scroll_stop_hook,  # reuse for hook scoring
        "lp_readability": _score_lp_readability,
    }

    # Email specific
    email_scorers = {
        "subject_line_power": _score_subject_line_power,
        "body_flow": _score_body_flow,
        "cta_clarity": _score_cta_clarity,  # reuse
        "personalization": _score_personalization,
        "scroll_stop_hook": _score_scroll_stop_hook,  # reuse for opening hook
    }

    # SMS specific (small set — most email/meta dimensions don't apply at 160 chars)
    sms_scorers = {
        "char_efficiency": _score_sms_char_efficiency,
        "compliance_fit": _score_sms_compliance_fit,
        "cta_clarity": _score_sms_cta_clarity,
    }

    # Select scorer set based on content type
    type_scorers = {
        "meta-ad": meta_scorers,
        "landing-page": landing_scorers,
        "email": email_scorers,
        "sms": sms_scorers,
    }

    scorers = {**common_scorers, **type_scorers.get(content_type, meta_scorers)}

    scorer = scorers.get(dim_id)
    if scorer:
        # Handle different scorer signatures
        if dim_id in ("differentiation", "opening_diversity", "emotional_register"):
            return scorer(ad, existing_ads)
        elif dim_id in ("receptionist_test", "cta_clarity", "platform_fit", "cta_prominence", "objection_preemption", "compliance_fit"):
            return scorer(ad, config)
        elif dim_id in ("hero_clarity",):
            return scorer(ad, config)
        else:
            return scorer(ad)
    # No scorer registered for this dim under this content_type — caller skips
    # the dim instead of crediting it with a dummy 3/5.
    return None, "No scorer available for dimension"


def _score_specificity(ad: dict) -> tuple[int, str]:
    """Count concrete numbers, dollar amounts, and specific details."""
    text = _get_all_text(ad)

    # Count dollar amounts
    money_count = len(re.findall(r'\$[\d,]+', text))
    # Count other numbers with context
    number_count = len(re.findall(
        r'\b\d+[\+]?\s*(?:clinics|vet clinics|visits?|year|month|%|stars?|reviews?|min'
        r'|farms?|customers?|families|days?|hours?|km|stops?|investors?|spots?)',
        text, re.IGNORECASE
    ))
    # Spelled-out cardinal numbers used as specifics ("Eight NSW farms", "One hub")
    # Recalibration-v1: live ad uses "Eight farms. One hub." which previously scored 0.
    word_number_count = len(re.findall(
        r'\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|'
        r'twenty|thirty|forty|fifty|hundred|thousand)\s+'
        r'(?:nsw|au|sydney|farms?|hubs?|families|customers?|years?|days?|months?|weeks?)',
        text, re.IGNORECASE
    ))
    # Count specific names (pet names, brand names, client-specific names, geographies)
    name_count = len(re.findall(
        r'\b(?:Luna|Max|Bella|Charlie|Milo|Best for Pet|VetChat|My Pawtal'
        r'|FarmThru|Farm Thru|Rachel|Bundarra|Collins|Brookvale|Birchal'
        r'|Paris Creek|Farmer Brown|Little Yarran|Northern Beaches|Kempsey'
        r'|South.?Western NSW|Sydney|Australia)\b',
        text, re.IGNORECASE
    ))

    total = money_count + number_count + word_number_count + name_count
    detail = (f"{money_count} dollar amounts, {number_count} numbers, "
              f"{word_number_count} spelled-out, {name_count} names = {total} specifics")

    if total >= 7:
        return 5, detail
    elif total >= 5:
        return 4, detail
    elif total >= 3:
        return 3, detail
    elif total >= 1:
        return 2, detail
    return 1, detail


def _score_receptionist_test(ad: dict, config: dict) -> tuple[int, str]:
    """Check if ad answers the receptionist test questions.

    Uses question-to-pattern mapping from config, or falls back to
    client-specific defaults based on client_id.
    """
    questions = config.get("receptionist_test_questions", [])
    text = _get_all_text(ad).lower()
    client_id = config.get("client_id", "")
    answered = 0
    details = []

    # Config-driven patterns (preferred), hardcoded fallback for backwards compat
    config_patterns = config.get("receptionist_test_patterns", [])
    if config_patterns:
        checks = [(p[0], p[1]) for p in config_patterns]
    elif client_id == "farm-thru":
        checks = [
            ("what", r'\b(farm.?thru|regenerative|grocery)\b'),
            ("source", r'\b(farm|paddock|pasture|grass.fed|rachel|bundarra)\b'),
            ("different", r'(days?\s+(?:old|not)|not\s+weeks|cold storage|middlem|direct|hub.and.collect)'),
            ("how", r'(waitlist|join|sign up|reserve|nearest hub|brookvale|collect|order)'),
            ("why_now", r'(be part of|own a piece|limited|first access|movement|vote.*wallet)'),
        ]
    else:
        checks = [
            ("what", r'\b(wellness plan|pet plan|membership|plan that|plan for)\b'),
            ("included", r'(consult|vaccination|dental|blood test|urine test|vetchat)'),
            ("cost", r'\$\d'),
            ("savings", r'(save|saving|saved)\s+\$'),
            ("start", r'(find a|check availability|sign up|get started|learn more)'),
        ]

    for label, pattern in checks:
        if re.search(pattern, text, re.IGNORECASE):
            answered += 1
            details.append(f"{label}: yes")
        else:
            details.append(f"{label}: no")

    detail = f"{answered}/{len(checks)} answered: {', '.join(details)}"
    score = max(1, answered)
    return score, detail


def _score_cta_clarity(ad: dict, config: dict) -> tuple[int, str]:
    """Check if CTA is on the approved list and clear.

    Recalibration-v1: funnel-aware approved list (TOF=email/notify, MOF=register,
    BOF=invest) and a +1 bonus when the body links the CTA action to a concrete
    consequence ("leave your email — we'll tell you the moment it goes live").
    """
    cta = ad.get("cta", "").strip()
    funnel = ad.get("funnel", "").upper()
    body = _get_primary_text(ad)
    approved = config.get("approved_ctas", [])

    # Handle multi-content-type format (dict of lists or dict of dict-by-funnel)
    if isinstance(approved, dict):
        content_type = ad.get("content_type", "meta-ad")
        approved = approved.get(content_type, approved.get("meta-ad", []))

    # Some clients (FMTH) use a dict keyed by funnel/campaign bucket
    # (e.g. {"brand": [...], "cfe_waitlist": [...], "cfe_campaign": [...]}).
    if isinstance(approved, dict):
        # Flatten across all buckets — exact matching against any approved CTA wins.
        flattened = []
        for bucket, ctas in approved.items():
            if isinstance(ctas, list):
                flattened.extend(ctas)
        approved = flattened

    if not cta:
        return 1, "No CTA found"

    # Outcome-stated CTA detection: body explains what happens after the action.
    # Patterns the live $2-lead ad uses: "Leave your email — we'll tell you the
    # moment it goes live." Body links action to its consequence.
    outcome_patterns = [
        r"leave\s+your\s+email[^.]*?we'?ll\s+(?:tell|let|notify|email)",
        r"sign\s+up[^.]*?we'?ll\s+(?:tell|let|notify|send)",
        r"register[^.]*?(?:we'?ll|you'?ll)\s+(?:tell|hear|get|receive)",
        r"join[^.]*?(?:we'?ll|you'?ll)\s+(?:tell|let|notify|send|hear)",
        r"(?:we'?ll|you'?ll)\s+(?:tell|let|notify)\s+you\s+(?:the\s+moment|when)",
    ]
    has_outcome = any(re.search(p, body, re.IGNORECASE) for p in outcome_patterns)

    # Exact match (case-sensitive)
    if cta in approved:
        if has_outcome:
            return 5, f"CTA matches approved list AND body states outcome: '{cta}'"
        return 5, f"CTA matches approved list: '{cta}'"

    # Close match (case-insensitive)
    for approved_cta in approved:
        if cta.lower() == approved_cta.lower():
            return 5 if has_outcome else 4, (
                f"CTA close match (case diff)" + (" + outcome stated" if has_outcome else "") + f": '{cta}'"
            )

    # Has a CTA but not on approved list — check if it's a sensible TOF/MOF action verb
    if re.search(r'(find|check|see|get|learn|start|sign|join|try|leave|register|reserve|save|secure)', cta, re.IGNORECASE):
        # Outcome stated lifts a non-approved-list CTA from 3 to 4 — the reader
        # knows what happens next regardless of literal CTA wording.
        return (4, f"CTA off-list but outcome stated in body: '{cta}'") if has_outcome else (
            3, f"CTA present but not on approved list: '{cta}'"
        )

    return 2, f"Weak or unclear CTA: '{cta}'"


def _score_platform_fit(ad: dict, config: dict) -> tuple[int, str]:
    """Check character limits and conversational tone."""
    content_type = ad.get("content_type", "meta-ad")
    constraints = config.get("platform_constraints", {})
    # Support per-content-type constraints
    if isinstance(constraints, dict) and content_type in constraints:
        constraints = constraints[content_type]
    violations = []

    # Content-type-specific field checks
    field_limits = {
        "meta-ad": [
            ("primary_text", "primary_text_max_chars", 500),
            ("headline", "headline_max_chars", 40),
            ("description", "description_max_chars", 125),
        ],
        "landing-page": [
            ("headline", "headline_max_chars", 80),
            ("subhead", "subhead_max_chars", 200),
            ("hero_copy", "hero_copy_max_chars", 500),
        ],
        "email": [
            ("subject", "subject_max_chars", 60),
            ("preheader", "preheader_max_chars", 100),
            ("body", "body_max_chars", 2000),
        ],
        "sms": [
            ("body", "body_max_chars", 320),
        ],
    }

    for field_name, constraint_key, default_max in field_limits.get(content_type, field_limits["meta-ad"]):
        text = ad.get(field_name, "")
        max_len = constraints.get(constraint_key, default_max)
        if text and len(text) > max_len:
            violations.append(f"{field_name}: {len(text)}/{max_len} chars")

    # Corporate jargon check (applies to all content types)
    all_text = _get_all_text(ad)
    jargon = re.findall(
        r'\b(comprehensive|solution|leverage|synergy|optimize|innovative|cutting-edge|best-in-class|utilize|implement|streamline)\b',
        all_text, re.IGNORECASE
    )
    if jargon:
        violations.append(f"corporate jargon: {', '.join(jargon[:3])}")

    if not violations:
        return 5, "All platform constraints met, conversational tone"
    elif len(violations) == 1:
        return 3, f"1 violation: {violations[0]}"
    else:
        return max(1, 4 - len(violations)), f"{len(violations)} violations: {'; '.join(violations)}"


def _score_objection_preemption(ad: dict, config: dict = None) -> tuple[int, str]:
    """Check for objection pre-emption signals relevant to the content."""
    config = config or {}
    text = _get_all_text(ad).lower()
    signals = 0
    found = []

    # Config-driven patterns (preferred), hardcoded fallback for backwards compat
    config_patterns = config.get("objection_preemption_patterns", [])
    if config_patterns:
        checks = [(p[0], p[1]) for p in config_patterns]
    else:
        client_id = config.get("client_id", "")
        if client_id == "farm-thru":
            checks = [
                ("no commitment", r'no\s+commitment|order when you want|no lock.in'),
                ("hub clarity", r'brookvale|nearest hub|collect from|hub.and.collect|monday.*friday'),
                ("risk acknowledged", r'can\'t\s+promise|no\s+guarantee|honest about'),
                ("no middlemen", r'no\s+(?:warehouse|wholesaler|middlem)|direct|zero middlem'),
                ("provenance", r'named farm|know.*farmer|trace|where.*food.*comes|paddock'),
            ]
        else:
            checks = [
                ("no joining fee", r'no\s+(?:joining|sign[- ]?up)\s+fee'),
                ("no waiting period", r'no\s+wait(?:ing)?\s+period'),
                ("cancel anytime", r'cancel\s+any\s*time'),
                ("not insurance", r'not\s+insurance|isn\'t\s+insurance'),
                ("no claims/excess", r'no\s+(?:claims|excess)'),
            ]

    for label, pattern in checks:
        if re.search(pattern, text):
            signals += 1
            found.append(label)

    detail = f"{signals}/{len(checks)} objection signals: {', '.join(found) if found else 'none'}"
    score = max(1, signals)
    return score, detail


def _score_scroll_stop_hook(ad: dict) -> tuple[int, str]:
    """Classify the first line and score its scroll-stop potential."""
    primary = _get_primary_text(ad).strip()
    # Get first non-empty, non-blockquote line
    first_line = ""
    for line in primary.split("\n"):
        line = line.strip().strip(">").strip()
        if line:
            first_line = line
            break

    if not first_line:
        return 1, "No opening line found"

    # Curiosity-gap / novelty hook: low-cost-to-investigate mystery with a narrow,
    # plausible boundary. Live $2-lead FMTH ad opens this way:
    # "We're about to open something up that's never been done with a grocery store in Australia."
    # Pre-recalibration this was scored as a generic opener (2/5).
    # Curiosity-gap patterns. Tightened so the loose phrase "for the first time"
    # only fires when bound by a category/geography (e.g. "first time in Australia")
    # — otherwise it lifts every generic "for the first time, we're shipping..." ad.
    curiosity_phrases = [
        r"we'?re\s+about\s+to\s+(?:open|launch|unveil|do|share|show|tell)",
        r"(?:something|what)\s+that'?s?\s+never\s+been",
        r"never\s+been\s+done\s+(?:with|by|in|before)",
        r"for\s+the\s+first\s+time\s+(?:ever|in\s+(?:australia|nsw|sydney|grocery|retail))",
        r"(?:something|what|the\s+thing)\s+we'?ve\s+(?:been\s+)?(?:working|building|quietly)",
        r"we'?ve\s+been\s+quietly\s+(?:building|working)",
        r"open\s+something\s+up",
        r"about\s+to\s+do\s+something\s+(?:no|new)",
    ]
    for pat in curiosity_phrases:
        if re.search(pat, first_line, re.IGNORECASE):
            return 5, f"Curiosity-gap hook: '{first_line[:60]}...'"

    # Story hook: specific moment, person, action, or named subject doing something
    if re.search(r'(last\s+\w+day|yesterday|this morning|walked in|picked up|called|booked|was\s+\w+ing|started|lost|changed|grew up|moved|quit|left)', first_line, re.IGNORECASE):
        return 5, f"Story hook with specific moment: '{first_line[:60]}...'"

    # Named person story hook: "[Name] was/did/had..."
    if re.search(r'^[A-Z][a-z]+\s+(?:was|had|did|didn|couldn|started|lost|quit|left|grew)', first_line):
        return 5, f"Named story hook: '{first_line[:60]}...'"

    # Quoted objection: starts with quote marks or "I"
    if re.match(r'^["\u201c]', first_line) or re.match(r'^"', first_line):
        return 5, f"Quoted objection hook: '{first_line[:60]}...'"

    # Question hook
    if first_line.endswith("?"):
        return 4, f"Question hook: '{first_line[:60]}...'"

    # Statistic hook: opens with number
    if re.match(r'^[\$\d]', first_line):
        return 4, f"Statistic/number hook: '{first_line[:60]}...'"

    # Bold claim
    if re.search(r'(that\'s not a typo|you read that right|sounds too good)', first_line, re.IGNORECASE):
        return 4, f"Bold claim hook: '{first_line[:60]}...'"

    # If/then
    if re.match(r'^if\s+', first_line, re.IGNORECASE):
        return 4, f"If/then hook: '{first_line[:60]}...'"

    # Generic statement
    return 2, f"Generic opening: '{first_line[:60]}...'"


def _score_differentiation(ad: dict, existing_ads: list[dict]) -> tuple[int, str]:
    """Measure how different this ad is from existing ads using bigram Jaccard similarity.

    Filters to same content_type before comparing. Uses bigram overlap instead of
    single-word Jaccard to catch phrase-level similarity.
    """
    if not existing_ads:
        return 4, "No existing ads to compare — default to 4"

    ad_text = _get_all_text(ad)
    ad_bigrams = _bigrams(_tokenize_list(ad_text))
    if not ad_bigrams:
        return 1, "Empty ad text"

    # Filter to same content_type (backwards-compatible: if missing, compare all)
    # Exclude the ad itself from comparison (by identity or matching ID)
    ad_id = ad.get("ad_id", ad.get("page_id", ad.get("email_id")))
    content_type = ad.get("content_type")
    if content_type:
        comparable = [
            o for o in existing_ads
            if o.get("content_type") == content_type and o is not ad
            and o.get("ad_id", o.get("page_id", o.get("email_id"))) != ad_id
        ]
    else:
        comparable = [
            o for o in existing_ads if o is not ad
            and o.get("ad_id", o.get("page_id", o.get("email_id"))) != ad_id
        ]

    if not comparable:
        return 4, "No comparable ads of same content_type"

    similarities = []
    for other in comparable:
        other_bigrams = _bigrams(_tokenize_list(_get_all_text(other)))
        if other_bigrams:
            jaccard = len(ad_bigrams & other_bigrams) / len(ad_bigrams | other_bigrams)
            similarities.append(jaccard)

    if not similarities:
        return 4, "No comparable ads with text"

    avg_sim = sum(similarities) / len(similarities)
    max_sim = max(similarities)

    detail = f"Avg bigram sim: {avg_sim:.3f}, max: {max_sim:.3f} (vs {len(comparable)} same-type ads)"

    # Determine score from average similarity (tighter thresholds for bigrams)
    if avg_sim < 0.08:
        score = 5
    elif avg_sim < 0.15:
        score = 4
    elif avg_sim < 0.25:
        score = 3
    elif avg_sim < 0.40:
        score = 2
    else:
        score = 1

    # Max similarity cap: if any single ad is too close, cap at 3
    if max_sim > 0.5 and score > 3:
        uncapped = score
        score = 3
        detail += f" [capped from {uncapped} — max_sim {max_sim:.3f} > 0.5]"

    return score, detail


def _score_hero_clarity(ad: dict, config: dict) -> tuple[int, str]:
    """Score landing page hero clarity — can visitor understand what/who/action in 5 seconds?"""
    headline = ad.get("headline", "")
    subhead = ad.get("subhead", "")
    hero_copy = ad.get("hero_copy", "")
    cta = ad.get("cta", "")

    score = 1
    details = []

    # Headline exists and is concise
    if headline:
        word_count = len(headline.split())
        if word_count <= 12:
            score += 1
            details.append(f"headline: {word_count} words (good)")
        else:
            details.append(f"headline: {word_count} words (too long)")
    else:
        details.append("headline: missing")

    # Subhead adds clarity (and must be concise)
    if subhead:
        sub_len = len(subhead)
        if sub_len <= 120:
            score += 1
            details.append(f"subhead: {sub_len} chars (good)")
        else:
            details.append(f"subhead: {sub_len} chars (too long, max 120)")
    else:
        details.append("subhead: missing")

    # CTA visible in hero
    if cta:
        score += 1
        details.append(f"cta: '{cta}'")
    else:
        details.append("cta: missing from hero")

    # Hero copy provides context
    if hero_copy and len(hero_copy) > 20:
        score += 1
        details.append("hero_copy: present")

    score = min(5, score)
    return score, f"{score}/5 hero elements: {', '.join(details)}"


def _score_proof_density(ad: dict) -> tuple[int, str]:
    """Score landing page proof density — stats, testimonials, named sources."""
    all_text = _get_all_text(ad)
    proof_count = 0
    found = []

    # Statistics (numbers with context)
    stats = re.findall(r'\d+[\+%]?\s*(?:farms?|customers?|families|investors?|years?|days?)', all_text, re.IGNORECASE)
    if stats:
        proof_count += 1
        found.append(f"stats: {len(stats)}")

    # Dollar amounts
    money = re.findall(r'\$[\d,]+', all_text)
    if money:
        proof_count += 1
        found.append(f"money: {len(money)}")

    # Testimonials (quoted text or attribution patterns)
    quotes = re.findall(r'["\u201c].{20,}["\u201d]', all_text)
    if quotes:
        proof_count += 1
        found.append(f"quotes: {len(quotes)}")

    # Named sources (Name, Location or Name from X)
    names = re.findall(r'(?:[A-Z][a-z]+),?\s+(?:[A-Z][a-z]+|NSW|VIC|QLD|SA|WA|TAS|NT|ACT)', all_text)
    if names:
        proof_count += 1
        found.append(f"named: {len(names)}")

    # Third-party citations (Source:, per X, according to)
    citations = re.findall(r'(?:source|per|according to|IBISWorld|Shopify|Birchal)', all_text, re.IGNORECASE)
    if citations:
        proof_count += 1
        found.append(f"citations: {len(citations)}")

    detail = f"{proof_count}/5 proof types: {', '.join(found) if found else 'none'}"
    score = max(1, proof_count)
    return score, detail


def _score_cta_prominence(ad: dict, config: dict) -> tuple[int, str]:
    """Score landing page CTA prominence — visible, repeated, compelling."""
    cta = ad.get("cta", "")
    all_text = _get_all_text(ad)

    if not cta:
        return 1, "No CTA found"

    # Check approved CTAs
    approved = config.get("approved_ctas", {})
    if isinstance(approved, dict):
        # Multi-content-type format
        approved_list = approved.get("landing-page", approved.get("meta-ad", []))
    else:
        approved_list = approved

    score = 2  # Has a CTA = at least 2
    details = []

    # On approved list
    if cta in approved_list or cta.lower() in [a.lower() for a in approved_list]:
        score += 1
        details.append("approved CTA")

    # CTA text appears multiple times (repeated on page)
    cta_mentions = len(re.findall(re.escape(cta), all_text, re.IGNORECASE))
    if cta_mentions >= 2:
        score += 1
        details.append(f"repeated {cta_mentions}x")

    # Action-specific (not generic)
    if re.search(r'(join|save|reserve|secure|get|start)', cta, re.IGNORECASE):
        score += 1
        details.append("action-specific")

    score = min(5, score)
    return score, f"CTA '{cta}': {', '.join(details) if details else 'basic'}"


def _score_scroll_depth_pull(ad: dict) -> tuple[int, str]:
    """Score landing page scroll depth pull — does each section pull to the next?"""
    sections = ad.get("sections", [])
    headline = ad.get("headline", "")
    hero_copy = ad.get("hero_copy", "")

    score = 1
    details = []

    # Has enough sections
    section_count = len(sections)
    if 4 <= section_count <= 8:
        score += 1
        details.append(f"{section_count} sections (optimal)")
    elif section_count > 0:
        details.append(f"{section_count} sections")
    else:
        details.append("no sections")
        return score, f"1/5: {', '.join(details)}"

    # Sections have headings
    headings = [s.get("heading", "") for s in sections if isinstance(s, dict)]
    headed_count = sum(1 for h in headings if h)
    if headed_count == section_count:
        score += 1
        details.append("all sections headed")
    elif headed_count > 0:
        details.append(f"{headed_count}/{section_count} headed")

    # Headings are benefit-oriented (not generic like "About Us")
    benefit_headings = sum(1 for h in headings if h and re.search(
        r'(how|why|what|your|get|join|save|better|fresh|real|future|farm)', h, re.IGNORECASE
    ))
    if benefit_headings >= section_count * 0.5:
        score += 1
        details.append("benefit-oriented headings")

    # Progressive new content (sections aren't repetitive)
    if section_count >= 3:
        score += 1
        details.append("sufficient depth")

    score = min(5, score)
    return score, f"{score}/5 scroll pull: {', '.join(details)}"


def _score_lp_readability(ad: dict) -> tuple[int, str]:
    """Score landing page readability — scannability, paragraph density, formatting."""
    hero_copy = ad.get("hero_copy", "")
    subhead = ad.get("subhead", "")
    sections = ad.get("sections", [])

    score = 1
    details = []

    # Collect all body text
    all_text = hero_copy
    for s in sections:
        if isinstance(s, dict):
            all_text += " " + s.get("body", "")

    if not all_text.strip():
        return 1, "1/5: no body text"

    # 1. Paragraph density — more line breaks = more scannable
    paragraphs = [p.strip() for p in all_text.split("\n\n") if p.strip()]
    if len(paragraphs) >= 6:
        score += 1
        details.append(f"{len(paragraphs)} paragraphs (good density)")
    elif len(paragraphs) >= 3:
        details.append(f"{len(paragraphs)} paragraphs (ok)")
    else:
        details.append(f"{len(paragraphs)} paragraphs (too dense)")

    # 2. Average sentence length — 13-18 words is ideal
    sentences = re.split(r'[.!?]+', all_text)
    sentences = [s.strip() for s in sentences if len(s.strip().split()) >= 3]
    if sentences:
        avg_words = sum(len(s.split()) for s in sentences) / len(sentences)
        if 10 <= avg_words <= 20:
            score += 1
            details.append(f"avg {avg_words:.0f} words/sentence (good)")
        elif avg_words > 25:
            details.append(f"avg {avg_words:.0f} words/sentence (too long)")
        else:
            details.append(f"avg {avg_words:.0f} words/sentence")

    # 3. No em dashes — they read cold/editorial
    em_dash_count = len(re.findall(r'[\u2014\u2013]', all_text))
    if em_dash_count == 0:
        score += 1
        details.append("no em dashes")
    else:
        details.append(f"{em_dash_count} em dashes (remove)")

    # 4. Subhead is concise
    if subhead and len(subhead) <= 120:
        score += 1
        details.append(f"subhead: {len(subhead)} chars")
    elif subhead:
        details.append(f"subhead: {len(subhead)} chars (over 120)")

    score = min(5, max(1, score))
    return score, f"{score}/5 readability: {', '.join(details)}"


def _score_subject_line_power(ad: dict) -> tuple[int, str]:
    """Score email subject line — curiosity, specificity, length."""
    subject = ad.get("subject", "")
    if not subject:
        return 1, "No subject line"

    score = 2  # Has a subject = at least 2
    details = []

    # Word count sweet spot (6-10)
    word_count = len(subject.split())
    if 6 <= word_count <= 10:
        score += 1
        details.append(f"{word_count} words (sweet spot)")
    else:
        details.append(f"{word_count} words")

    # Contains specificity (number, name, concrete detail)
    if re.search(r'(\d+|\$|%|[A-Z][a-z]+\'s)', subject):
        score += 1
        details.append("specific")

    # No spam triggers
    spam = re.search(r'(free|act now|limited|!!!|ALL CAPS|\U0001f525|\U0001f4b0)', subject, re.IGNORECASE)
    if not spam:
        score += 1
        details.append("no spam triggers")
    else:
        details.append(f"spam trigger: {spam.group()}")

    score = min(5, score)
    return score, f"Subject '{subject[:40]}': {', '.join(details)}"


def _score_body_flow(ad: dict) -> tuple[int, str]:
    """Score email body flow and readability."""
    body = ad.get("body", ad.get("primary_text", ""))
    if not body:
        return 1, "No body content"

    score = 2  # Has body = at least 2
    details = []

    # Length check
    if len(body) <= 2000:
        score += 1
        details.append(f"{len(body)} chars (within limit)")
    else:
        details.append(f"{len(body)} chars (over 2000)")

    # Paragraph structure (line breaks)
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    if len(paragraphs) >= 3:
        score += 1
        details.append(f"{len(paragraphs)} paragraphs")
    else:
        details.append(f"only {len(paragraphs)} paragraphs")

    # No paragraph too long (max 3 sentences)
    long_paras = sum(1 for p in paragraphs if p.count(". ") > 3)
    if long_paras == 0:
        score += 1
        details.append("good paragraph length")
    else:
        details.append(f"{long_paras} long paragraphs")

    score = min(5, score)
    return score, f"{score}/5 flow: {', '.join(details)}"


def _score_personalization(ad: dict) -> tuple[int, str]:
    """Score email personalization and relevance."""
    body = ad.get("body", ad.get("primary_text", ""))
    subject = ad.get("subject", "")
    all_text = subject + " " + body

    if not all_text.strip():
        return 1, "No content to evaluate"

    score = 1
    details = []

    # Personalization tokens
    if re.search(r'\{(?:first_name|name|city)\}|\[Name\]', all_text):
        score += 1
        details.append("has merge tags")

    # References reader's context (waitlist, prior action, interest)
    if re.search(r'(you (?:joined|signed up|registered|expressed)|your (?:spot|place|deposit)|waitlist)', all_text, re.IGNORECASE):
        score += 1
        details.append("references reader context")

    # Conversational/personal tone (I/we/you ratio)
    you_count = len(re.findall(r'\byou(?:r|\'re|\'ll)?\b', all_text, re.IGNORECASE))
    we_count = len(re.findall(r'\b(?:I|we|our)\b', all_text, re.IGNORECASE))
    if you_count >= 3:
        score += 1
        details.append(f"reader-focused ({you_count} 'you' refs)")

    # Specific timing or action reference
    if re.search(r'(this week|today|tomorrow|on \w+day|hours?|minutes?)', all_text, re.IGNORECASE):
        score += 1
        details.append("time-specific")

    score = min(5, score)
    return score, f"{score}/5 personalization: {', '.join(details) if details else 'generic'}"


# --- SMS-specific deterministic scorers ---

# Average expanded URL length used to estimate SMS segment fit when merge tags
# are still in {{birchal_url}} form. Birchal short URLs and most produced shortlinks
# land in the 25-32 char range; 30 is conservative.
_SMS_URL_PLACEHOLDER_EXPANDED = 30


def _expanded_sms_length(body: str) -> int:
    """Estimate the real on-the-wire SMS length, expanding {{...}} merge tags
    to a realistic URL length. Plain text is counted verbatim."""
    if not body:
        return 0
    # Replace any {{...}} merge tag with an estimated expanded length placeholder
    expanded = re.sub(r"\{\{[^{}]+\}\}", "X" * _SMS_URL_PLACEHOLDER_EXPANDED, body)
    return len(expanded)


def _score_sms_char_efficiency(ad: dict) -> tuple[int, str]:
    """Score SMS for single-segment fit. <=140 = 5; 141-160 single-seg = 4;
    161-320 with justification = 3; 161-320 without justification = 2; >320 = 1."""
    body = ad.get("body", "")
    if not body:
        return 1, "No body content"
    expanded_len = _expanded_sms_length(body)
    raw_len = len(body)
    purpose = ad.get("purpose", "")
    # Confirmations and compliance-required content can justify two segments
    two_seg_justified = purpose in ("purchase-confirmation", "founder-update")

    if expanded_len > 320:
        return 1, f"{expanded_len} chars expanded ({raw_len} raw) — over 320 (3+ segments)"
    if expanded_len > 160:
        if two_seg_justified:
            return 3, f"{expanded_len} chars expanded ({raw_len} raw) — 2 segments, justified by purpose={purpose}"
        return 2, f"{expanded_len} chars expanded ({raw_len} raw) — 2 segments, single segment was achievable"
    if expanded_len > 140:
        return 4, f"{expanded_len} chars expanded ({raw_len} raw) — single segment, could be tighter"
    return 5, f"{expanded_len} chars expanded ({raw_len} raw) — tight single segment"


def _score_sms_cta_clarity(ad: dict, config: dict) -> tuple[int, str]:
    """SMS CTA clarity: link present (the URL IS the CTA) or transactional
    confirmation explicitly says no action needed."""
    body = ad.get("body", "")
    purpose = ad.get("purpose", "")
    cta = ad.get("cta", "").strip()

    # Detect link or merge tag pointing to a URL
    has_link = bool(
        re.search(r"https?://|\{\{[^{}]*url[^{}]*\}\}", body, re.IGNORECASE)
    )
    # Confirmations don't need a link — they need a clear "you're in" signal
    is_confirmation = purpose in ("purchase-confirmation", "transactional")

    if is_confirmation:
        if re.search(r"\b(you'?re in|secured|confirmed|locked in|received)\b", body, re.IGNORECASE):
            return 5, f"Confirmation with clear status signal — no link needed"
        if cta:
            return 4, f"Confirmation with explicit cta={cta!r}"
        return 3, "Confirmation present but no clear status word — recipient may be unsure"

    # Marketing / round-opens etc.: link is the CTA
    if has_link:
        # Bonus if the link sits naturally in the message (not at very end after opt-out)
        return 5, "Link present — natural single tap target"
    if cta:
        return 3, f"No link but explicit cta={cta!r}"
    return 1, "No link and no explicit CTA — recipient unsure what to do"


def _score_sms_compliance_fit(ad: dict, config: dict) -> tuple[int, str]:
    """SMS compliance signals:
    - Marketing sends (audience != transactional/customers replying to action) need 'Reply STOP'
    - Investment-context SMS need either a URL (→ risk warning page) OR the short paraphrase
    - Transactional confirmations need neither
    """
    body = ad.get("body", "")
    purpose = ad.get("purpose", "")
    audience = ad.get("audience", "")

    is_transactional = purpose in ("purchase-confirmation", "transactional")
    is_marketing_send = audience in ("vip-investors", "waitlist", "all-subscribers") and not is_transactional

    has_opt_out = bool(re.search(r"\b(reply\s+stop|stop\s+to\s+opt\s*out)\b", body, re.IGNORECASE))
    has_url = bool(re.search(r"https?://|\{\{[^{}]*url[^{}]*\}\}", body, re.IGNORECASE))
    has_short_paraphrase = bool(re.search(r"general\s+CSF\s+risk\s+warning", body, re.IGNORECASE))

    # Investment context: anything that mentions the offer, Birchal, or VIP early access
    investment_context = bool(
        re.search(r"\b(birchal|csf|invest|offer|early access|vip)\b", body, re.IGNORECASE)
    )

    notes = []

    # Marketing send opt-out check
    if is_marketing_send:
        if has_opt_out:
            notes.append("opt-out present")
            opt_out_score = 2
        else:
            notes.append("MARKETING SEND missing 'Reply STOP'")
            opt_out_score = 0
    else:
        notes.append("transactional — no opt-out required")
        opt_out_score = 2

    # Investment context safe-harbour route
    if investment_context:
        if has_url or has_short_paraphrase:
            if has_url:
                notes.append("URL routes to risk-warning page (safe-harbour OK)")
            if has_short_paraphrase:
                notes.append("short paraphrase 'general CSF risk warning' present")
            inv_score = 3
        else:
            notes.append("INVESTMENT CONTEXT but no URL and no risk-warning paraphrase")
            inv_score = 0
    else:
        notes.append("non-investment SMS")
        inv_score = 3

    total = opt_out_score + inv_score  # 0..5
    return max(1, total), f"{total}/5 compliance: {'; '.join(notes)}"


def _score_opening_diversity(ad: dict, existing_ads: list[dict]) -> tuple[int, str]:
    """Score how unique this ad's opening is relative to other same-type ads."""
    content_type = ad.get("content_type", "meta-ad")
    primary = _get_primary_text(ad).strip()

    if not primary:
        return 3, "No primary text to evaluate"

    # Get first line (or first sentence)
    first_line = ""
    for line in primary.split("\n"):
        line = line.strip().strip(">").strip()
        if line:
            first_line = line
            break
    if not first_line:
        return 3, "No opening line found"

    # Extract words from opening
    words = re.findall(r'\b[a-zA-Z]+\b', first_line.lower())
    if not words:
        return 3, "No words in opening line"

    first_word = words[0]
    first_three = " ".join(words[:3]) if len(words) >= 3 else " ".join(words)

    # Filter existing_ads to same content type
    same_type = [a for a in existing_ads if a.get("content_type", "meta-ad") == content_type]
    if not same_type:
        return 5, f"No same-type ads to compare — opening: '{first_three}'"

    # Get openings of same-type ads (skip self)
    ad_id = ad.get("ad_id", ad.get("page_id", ad.get("email_id", "")))
    first_word_matches = 0
    three_word_matches = 0
    for other in same_type:
        other_id = other.get("ad_id", other.get("page_id", other.get("email_id", "")))
        if ad_id and other_id and ad_id == other_id:
            continue
        other_primary = _get_primary_text(other).strip()
        if not other_primary:
            continue
        if other_primary == primary:
            continue
        other_first_line = ""
        for line in other_primary.split("\n"):
            line = line.strip().strip(">").strip()
            if line:
                other_first_line = line
                break
        if not other_first_line:
            continue
        other_words = re.findall(r'\b[a-zA-Z]+\b', other_first_line.lower())
        if not other_words:
            continue
        other_first = other_words[0]
        other_three = " ".join(other_words[:3]) if len(other_words) >= 3 else " ".join(other_words)
        if other_first == first_word:
            first_word_matches += 1
        if other_three == first_three:
            three_word_matches += 1

    detail = f"Opening '{first_three}': first word shared with {first_word_matches}, first 3 words shared with {three_word_matches} of {len(same_type)} same-type ads"

    if three_word_matches > 0:
        return 1, detail
    if first_word_matches >= 3:
        return 2, detail
    if first_word_matches == 2:
        return 3, detail
    if first_word_matches == 1:
        return 4, detail
    return 5, detail


def _score_sentence_variance(ad: dict) -> tuple[int, str]:
    """Score sentence-length variety (rhythm) in ad copy."""
    primary = _get_primary_text(ad).strip()
    if not primary:
        return 3, "No primary text to evaluate"

    # Split into sentences on `. ` or `.\n` or `?\n` or `!` or `? ` or `!\n`
    sentences = re.split(r'(?<=[.!?])[\s\n]+', primary)
    # Filter out empty and very short fragments
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip().split()) >= 2]

    if len(sentences) <= 1:
        return 2, f"{len(sentences)} sentence(s) — not enough to measure variance"

    word_counts = [len(s.split()) for s in sentences]
    avg = sum(word_counts) / len(word_counts)
    variance = sum((c - avg) ** 2 for c in word_counts) / len(word_counts)
    std_dev = math.sqrt(variance)

    detail = f"{len(sentences)} sentences, avg {avg:.1f} words, std dev {std_dev:.1f}"

    if std_dev > 8:
        return 5, detail
    elif std_dev > 5:
        return 4, detail
    elif std_dev > 3:
        return 3, detail
    elif std_dev > 1:
        return 2, detail
    return 1, detail


def _score_emotional_register(ad: dict, existing_ads: list[dict]) -> tuple[int, str]:
    """Score the uniqueness of this ad's emotional register (opening style)."""
    content_type = ad.get("content_type", "meta-ad")
    register = _classify_register(ad)

    # Filter existing_ads to same content type
    same_type = [a for a in existing_ads if a.get("content_type", "meta-ad") == content_type]
    if not same_type:
        return 5, f"Register: {register} — no same-type ads to compare"

    # Count how many same-type ads share this register (skip self)
    ad_id = ad.get("ad_id", ad.get("page_id", ad.get("email_id", "")))
    ad_primary = _get_primary_text(ad).strip()
    same_register = 0
    total = 0
    for a in same_type:
        other_id = a.get("ad_id", a.get("page_id", a.get("email_id", "")))
        if ad_id and other_id and ad_id == other_id:
            continue
        if _get_primary_text(a).strip() == ad_primary:
            continue
        total += 1
        if _classify_register(a) == register:
            same_register += 1
    pct = (same_register / total) * 100 if total else 0

    detail = f"Register: {register} — {same_register}/{total} same-type ads share it ({pct:.0f}%)"

    if same_register == 0:
        return 5, detail
    elif pct < 15:
        return 4, detail
    elif pct <= 30:
        return 3, detail
    elif pct <= 50:
        return 2, detail
    return 1, detail


# --- Recalibration-v1 dimensions ---
#
# These were added after the live $2-lead Farm Thru ad ("never been done with a
# grocery store in Australia…") scored 0.71 / strong_draft on the prior rubric
# despite being a top performer in market. Each dimension encodes a lever that
# the prior rubric missed or actively penalised. See validation/scorer-recalibration-v1.json
# for the canonical positive example and target deltas.

def _score_ownership_framing(ad: dict) -> tuple[int, str]:
    """Reward ownership / belonging language over transactional 'invest in' language.

    'Own a piece of', 'be part of', 'you'll be able to own', 'your share' all
    convert investment from a transaction into an identity. Confirmed in the live
    ad and in two of the loop's prior 'production_ready' CFE outputs.
    """
    text = _get_all_text(ad).lower()
    # Investment context required for ownership framing to be credited — without
    # it, "your share" or "joining the family" mean grocery-share or community,
    # not ownership. This avoids spurious 4/5 on pure brand/grocery ads.
    investment_context = bool(
        re.search(r"\b(invest|investment|raise|raising|csf|crowdfund|own\s+a\s+piece|equity)\b", text)
    )
    patterns = [
        (r"\bown\s+a\s+piece\s+of\b", "own a piece"),
        (r"\bown\s+the\s+(?:future|outcome|story)\b", "own the future"),
        (r"\byou'?ll\s+be\s+able\s+to\s+own\b", "you'll be able to own"),
        (r"\bbe\s+part\s+of\s+(?:it|what|building|something)\b", "be part of it"),
    ]
    # These patterns can fire on non-investment copy, so only count them when
    # an investment context is present elsewhere in the ad.
    investment_only_patterns = [
        (r"\byour\s+(?:share|stake|piece)\b", "your share/stake"),
        (r"\bjoin(?:ing)?\s+(?:us|the\s+(?:movement|family|community))\b", "join us / the movement"),
    ]
    found = [label for pat, label in patterns if re.search(pat, text)]
    if investment_context:
        found.extend(label for pat, label in investment_only_patterns if re.search(pat, text))
    if len(found) >= 2:
        return 5, f"Ownership framing: {', '.join(found)}"
    if len(found) == 1:
        return 4, f"Ownership framing: {found[0]}"
    # Penalise transactional-only investment language with no ownership frame
    if re.search(r"\binvest\s+(?:in|now|from\s+\$)", text) and not found:
        return 2, "Transactional 'invest' language only — no ownership frame"
    return 3, "No ownership framing detected (neutral)"


def _score_scarcity_register(ad: dict) -> tuple[int, str]:
    """Reward soft / future-tense scarcity. Penalise hard-pressure scarcity.

    Soft: 'opens soon', 'first in gets first access', 'we'll tell you the moment',
    'registration opens'. Reads as a queue forming, not a panic.

    Hard: 'ends today', 'last chance', 'act now', 'limited time only'. Triggers
    suspicion on considered / regulated purchases (CFE, large basket grocery).
    """
    text = _get_all_text(ad).lower()
    soft = [
        r"opens?\s+soon",
        r"first\s+in\s+gets?\s+first\s+access",
        r"we'?ll\s+tell\s+you\s+(?:the\s+moment|when)",
        r"registration\s+opens?",
        r"be\s+ready\s+when",
        r"early\s+access",
        r"join\s+the\s+(?:waitlist|notify\s+list)",
        r"get\s+(?:in|on)\s+(?:early|the\s+list)",
    ]
    hard = [
        r"ends?\s+today",
        r"last\s+chance",
        r"limited\s+time\s+only",
        r"act\s+now",
        r"hurry",
        r"don'?t\s+miss\s+out",
        r"while\s+supplies\s+last",
        r"only\s+\d+\s+(?:hours?|minutes?|spots?\s+left)",
    ]
    soft_hits = [p for p in soft if re.search(p, text)]
    hard_hits = [p for p in hard if re.search(p, text)]

    if soft_hits and not hard_hits:
        if len(soft_hits) >= 2:
            return 5, f"{len(soft_hits)} soft scarcity signals (queue, not panic)"
        return 4, "Soft scarcity present, no hard pressure"
    if not soft_hits and not hard_hits:
        return 3, "No scarcity signals"
    if soft_hits and hard_hits:
        return 2, f"Mixed: {len(soft_hits)} soft + {len(hard_hits)} hard (hard pressure undermines)"
    return 1, f"{len(hard_hits)} hard-pressure signals (suspicion-triggering for CFE/considered)"


def _score_founder_voice(ad: dict) -> tuple[int, str]:
    """Reward first-person plural with build-language: 'we've built',
    'we're opening', 'we made'. This signals founder credibility and earned
    authority rather than corporate distance.
    """
    text = _get_all_text(ad).lower()
    patterns = [
        r"we'?ve\s+(?:built|made|created|been\s+(?:building|working))",
        r"we'?re\s+(?:about\s+to|opening|launching|building)",
        r"we\s+built\b",
        r"we\s+(?:partnered|connect|started|made)\b",
        r"i'?ve\s+been\s+(?:farming|working|building)",
    ]
    hits = [p for p in patterns if re.search(p, text)]
    # Pronoun balance: first-person plural should appear naturally
    we_count = len(re.findall(r"\bwe(?:'(?:re|ve|ll))?\b", text))
    if len(hits) >= 2:
        return 5, f"Founder voice: {len(hits)} build-language hits, {we_count} 'we' refs"
    if len(hits) == 1:
        return 4, f"Founder voice: 1 build-language hit, {we_count} 'we' refs"
    if we_count >= 3:
        return 3, f"First-person plural present but no build language ({we_count} 'we')"
    return 2, "Corporate / third-person voice"


def _score_csf_placement(ad: dict) -> tuple[int, str]:
    """Reward CSF disclaimer placed as an asterisked / footnoted final line.

    The live $2-lead ad puts the CSF warning behind '*' as the final paragraph.
    The loop has historically blended compliance language into the body, which
    dampens momentum. This dimension separates *presence* (which the rule_checker
    already enforces as a hard gate) from *placement quality*.
    """
    text = _get_primary_text(ad)
    if not text:
        return 1, "No body text"

    # Detect CSF / disclaimer language
    csf_re = re.compile(
        r"(?:general\s+CSF\s+risk\s+warning|consider\s+the\s+general\s+csf|"
        r"offer\s+document\s+before\s+investing|disclosure\s+document\s+on\s+birchal|"
        r"not\s+financial\s+advice)",
        re.IGNORECASE,
    )
    if not csf_re.search(text):
        return 3, "No CSF/disclaimer language present (placement N/A)"

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return 3, "Could not split into paragraphs"

    last_para = paragraphs[-1]
    # Best: final paragraph, asterisked, contains CSF language, nothing else
    if last_para.lstrip().startswith("*") and csf_re.search(last_para):
        # And the asterisked paragraph is short — it's a footnote, not a sermon
        if len(last_para.split()) <= 30:
            return 5, "CSF as asterisked final-paragraph footnote"
        return 4, "CSF asterisked final paragraph but long-winded"
    if csf_re.search(last_para):
        return 4, "CSF in final paragraph but not asterisked"
    # CSF appears mid-body — dampens momentum
    return 2, "CSF blended into body (dampens momentum)"


def _classify_register(ad: dict) -> str:
    """Classify ad opening into an emotional register category."""
    primary = _get_primary_text(ad).strip()
    if not primary:
        return "other"

    # Get first two sentences
    sentences = re.split(r'(?<=[.!?])[\s\n]+', primary)
    sentences = [s.strip() for s in sentences if s.strip()]
    first_sent = sentences[0] if sentences else ""
    first_two = " ".join(sentences[:2]) if sentences else ""

    # Question — first sentence ends with ?
    if first_sent.rstrip().endswith("?"):
        return "question"

    # Direct — starts with "you" or "your"
    if re.match(r'^(?:you|your)\b', first_sent, re.IGNORECASE):
        return "direct"

    # Confession — starts with "I " or "We "
    if re.match(r'^(?:I |We )', first_sent):
        return "confession"

    # Statistic — contains $ or a number in first sentence
    if re.search(r'(?:\$|\b\d+\b)', first_sent):
        return "statistic"

    # Story — named person, day, or specific action in first 2 sentences
    if re.search(
        r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday'
        r'|yesterday|last\s+\w+day|this\s+morning|walked|picked\s+up|called|booked'
        r'|Rachel|Bundarra|Luna|Max|Bella|Charlie|Milo)\b',
        first_two, re.IGNORECASE
    ):
        return "story"
    # Also catch "[Name] was/did..." pattern
    if re.search(r'^[A-Z][a-z]+\s+(?:was|had|did|didn|couldn|started|lost|quit|left|grew)', first_sent):
        return "story"

    # Contrast — contains "vs", "not", "but", "instead" in first 2 sentences
    if re.search(r'\b(?:vs\.?|not|but|instead)\b', first_two, re.IGNORECASE):
        return "contrast"

    return "other"


def _get_primary_text(ad: dict) -> str:
    """Get the primary text field based on content type."""
    content_type = ad.get("content_type", "meta-ad")
    if content_type in ("email", "sms"):
        return ad.get("body", ad.get("primary_text", ""))
    elif content_type == "landing-page":
        return ad.get("hero_copy", ad.get("primary_text", ""))
    return ad.get("primary_text", "")


def _score_heuristic_fallback(dim_id: str, ad: dict) -> tuple[int, str]:
    """Heuristic fallback for LLM-judged dimensions when LLM is disabled."""
    # Simple word-count-based heuristic — not reliable, just a fallback
    text = _get_all_text(ad)
    word_count = len(text.split())

    if dim_id == "angle_clarity":
        # More focused copy (fewer words) tends to have clearer angles
        if 50 <= word_count <= 120:
            return 3, "Heuristic: reasonable length for angle clarity"
        return 2, "Heuristic: length suggests muddled angle"

    if dim_id == "motivation_match":
        # Check for emotional language
        emotional = len(re.findall(
            r'\b(love|worry|guilt|relief|peace|fear|anxiety|stress|joy|happy|confident)\b',
            text, re.IGNORECASE
        ))
        if emotional >= 2:
            return 3, f"Heuristic: {emotional} emotional words found"
        return 2, "Heuristic: low emotional resonance"

    if dim_id == "tactic_execution":
        # Check for basic structure: hook + body + CTA
        has_hook = bool(ad.get("headline") or ad.get("subject"))
        has_body = len(_get_primary_text(ad)) > 50
        has_cta = bool(ad.get("cta"))
        score = 1 + has_hook + has_body + has_cta
        return min(score, 4), f"Heuristic: hook={has_hook}, body={has_body}, cta={has_cta}"

    return 3, "Heuristic: default middle score"


# --- Utilities ---

def _get_all_text(ad: dict) -> str:
    """Concatenate all text fields from any content type."""
    # Check all known text fields across content types
    fields = [
        "primary_text", "headline", "description",  # meta-ad
        "subject", "preheader", "body",  # email
        "hero_copy", "subhead",  # landing page
    ]
    parts = []
    for field in fields:
        text = ad.get(field, "")
        if text:
            text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
            parts.append(text)
    # Handle sections array (landing pages)
    sections = ad.get("sections", [])
    for section in sections:
        if isinstance(section, dict):
            for key in ("heading", "body"):
                text = section.get(key, "")
                if text:
                    parts.append(text)
    return "\n".join(parts)


def _tokenize(text: str) -> set[str]:
    """Simple word tokenization for Jaccard similarity."""
    words = re.findall(r'\b[a-z]+\b', text.lower())
    # Remove stop words
    stops = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "it", "this", "that", "are", "was",
        "be", "has", "had", "have", "do", "does", "did", "will", "would",
        "can", "could", "should", "may", "might", "your", "you", "we", "our",
        "not", "no", "if", "all", "each", "every", "any", "than", "then",
    }
    return {w for w in words if w not in stops and len(w) > 2}


def _tokenize_list(text: str) -> list[str]:
    """Word tokenization returning a list (preserves order for bigram generation)."""
    words = re.findall(r'\b[a-z]+\b', text.lower())
    stops = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "it", "this", "that", "are", "was",
        "be", "has", "had", "have", "do", "does", "did", "will", "would",
        "can", "could", "should", "may", "might", "your", "you", "we", "our",
        "not", "no", "if", "all", "each", "every", "any", "than", "then",
    }
    return [w for w in words if w not in stops and len(w) > 2]


def _bigrams(word_list: list[str]) -> set[tuple[str, str]]:
    """Generate bigrams (consecutive word pairs) from a token list."""
    if len(word_list) < 2:
        return set()
    return {(word_list[i], word_list[i + 1]) for i in range(len(word_list) - 1)}
