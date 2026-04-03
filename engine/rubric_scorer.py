"""
Rubric Scorer — Axis 3 of the scoring engine.

10 dimensions scored 1-5 with weights.
7 deterministic, 3 LLM-judged (via llm_judge.py).

Returns: {weighted_total, max_possible, raw_scores, dimension_details}
"""

import json
import re
from pathlib import Path


def load_rubric(shared_dir: Path) -> dict:
    """Load the rubric schema."""
    rubric_path = shared_dir / "rubric-schema.json"
    with open(rubric_path) as f:
        return json.load(f)


def score_rubric(
    ad: dict,
    rubric: dict,
    client_config: dict,
    existing_ads: list[dict] = None,
    use_llm: bool = True,
) -> dict:
    """Score an ad against all 10 rubric dimensions.

    Args:
        ad: Ad in canonical JSON format
        rubric: Loaded rubric-schema.json
        client_config: Loaded client config.json
        existing_ads: Other ads in set (for differentiation)
        use_llm: Whether to use LLM for subjective dimensions (False = skip those)

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
    weights = client_config.get("rubric", {}).get("weights", {})
    max_possible = client_config.get("rubric", {}).get("max_score", 66.25)

    raw_scores = {}
    dimension_details = {}
    weighted_total = 0.0

    for dim in dimensions:
        dim_id = dim["id"]
        weight = weights.get(dim_id, dim.get("default_weight", 1.0))
        method = dim.get("scoring_method", "deterministic")

        if method == "deterministic":
            score, detail = _score_deterministic(dim_id, ad, client_config, existing_ads)
        elif method == "llm" and use_llm:
            from . import llm_judge
            score, detail = llm_judge.judge_dimension(dim_id, ad, dim, client_config)
        else:
            # LLM disabled — use heuristic fallback
            score, detail = _score_heuristic_fallback(dim_id, ad)

        score = max(1, min(5, score))  # Clamp to 1-5
        raw_scores[dim_id] = score
        weighted_total += score * weight
        dimension_details[dim_id] = {
            "score": score,
            "weight": weight,
            "weighted": round(score * weight, 2),
            "method": method if (method == "deterministic" or use_llm) else "heuristic",
            "detail": detail,
        }

    return {
        "weighted_total": round(weighted_total, 2),
        "max_possible": max_possible,
        "raw_scores": raw_scores,
        "dimension_details": dimension_details,
    }


# --- Deterministic scoring functions ---

def _score_deterministic(
    dim_id: str, ad: dict, config: dict, existing_ads: list[dict]
) -> tuple[int, str]:
    """Route to the correct deterministic scorer."""
    scorers = {
        "specificity": _score_specificity,
        "receptionist_test": _score_receptionist_test,
        "cta_clarity": _score_cta_clarity,
        "platform_fit": _score_platform_fit,
        "objection_preemption": _score_objection_preemption,
        "scroll_stop_hook": _score_scroll_stop_hook,
        "differentiation": _score_differentiation,
    }
    scorer = scorers.get(dim_id)
    if scorer:
        if dim_id == "differentiation":
            return scorer(ad, existing_ads)
        elif dim_id == "receptionist_test":
            return scorer(ad, config)
        elif dim_id in ("cta_clarity", "platform_fit"):
            return scorer(ad, config)
        else:
            return scorer(ad)
    return 3, "No scorer available"


def _score_specificity(ad: dict) -> tuple[int, str]:
    """Count concrete numbers, dollar amounts, and specific details."""
    text = _get_all_text(ad)

    # Count dollar amounts
    money_count = len(re.findall(r'\$[\d,]+', text))
    # Count other numbers with context
    number_count = len(re.findall(r'\b\d+[\+]?\s*(?:clinics|visits?|year|month|%|stars?|reviews?|min)', text, re.IGNORECASE))
    # Count specific names (pet names, brand names)
    name_count = len(re.findall(r'\b(?:Luna|Max|Bella|Charlie|Milo|Best for Pet|VetChat|My Pawtal)\b', text, re.IGNORECASE))

    total = money_count + number_count + name_count
    detail = f"{money_count} dollar amounts, {number_count} numbers, {name_count} names = {total} specifics"

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
    """Check if ad answers the receptionist test questions."""
    questions = config.get("receptionist_test_questions", [
        "What is it?", "What's included?", "How much does it cost?",
        "How much will I save?", "How do I start?"
    ])
    text = _get_all_text(ad).lower()
    answered = 0
    details = []

    # What is it? — mentions "plan", "membership", "wellness"
    if re.search(r'\b(wellness plan|pet plan|membership|plan that|plan for)\b', text):
        answered += 1
        details.append("what: yes")
    else:
        details.append("what: no")

    # What's included? — mentions at least 2 inclusions
    inclusions = re.findall(r'(consult|vaccination|dental|blood test|urine test|vetchat|nail trim|boarding|parasite|desexing|microchip)', text)
    if len(set(inclusions)) >= 2:
        answered += 1
        details.append(f"included: yes ({len(set(inclusions))} items)")
    else:
        details.append("included: no")

    # How much? — mentions a dollar amount
    if re.search(r'\$\d', text):
        answered += 1
        details.append("cost: yes")
    else:
        details.append("cost: no")

    # How much will I save? — mentions savings or cost comparison
    if re.search(r'(save|saving|saved)\s+\$|(\$\d+.*vs|\d+.*less|pay.*instead)', text):
        answered += 1
        details.append("savings: yes")
    else:
        details.append("savings: no")

    # How do I start? — mentions CTA or sign up method
    if re.search(r'(find a|check availability|sign up|get started|learn more|see (the|what)|bestforpet)', text):
        answered += 1
        details.append("start: yes")
    else:
        details.append("start: no")

    detail = f"{answered}/{len(questions)} answered: {', '.join(details)}"
    score = max(1, answered)  # 0 answered = 1, 5 answered = 5
    return score, detail


def _score_cta_clarity(ad: dict, config: dict) -> tuple[int, str]:
    """Check if CTA is on the approved list and clear."""
    cta = ad.get("cta", "").strip()
    approved = config.get("approved_ctas", [])

    if not cta:
        return 1, "No CTA found"

    # Exact match
    if cta in approved:
        return 5, f"CTA matches approved list: '{cta}'"

    # Close match (case-insensitive)
    for approved_cta in approved:
        if cta.lower() == approved_cta.lower():
            return 4, f"CTA close match (case diff): '{cta}'"

    # Has a CTA but not on approved list
    if re.search(r'(find|check|see|get|learn|start|sign|join|try)', cta, re.IGNORECASE):
        return 3, f"CTA present but not on approved list: '{cta}'"

    return 2, f"Weak or unclear CTA: '{cta}'"


def _score_platform_fit(ad: dict, config: dict) -> tuple[int, str]:
    """Check character limits and conversational tone."""
    constraints = config.get("platform_constraints", {})
    violations = []

    primary_text = ad.get("primary_text", "")
    headline = ad.get("headline", "")
    description = ad.get("description", "")

    # Character limit checks
    pt_max = constraints.get("primary_text_max_chars", 500)
    hl_max = constraints.get("headline_max_chars", 40)
    desc_max = constraints.get("description_max_chars", 125)

    if len(primary_text) > pt_max:
        violations.append(f"primary_text: {len(primary_text)}/{pt_max} chars")
    if headline and len(headline) > hl_max:
        violations.append(f"headline: {len(headline)}/{hl_max} chars")
    if description and len(description) > desc_max:
        violations.append(f"description: {len(description)}/{desc_max} chars")

    # Corporate jargon check
    jargon = re.findall(
        r'\b(comprehensive|solution|leverage|synergy|optimize|innovative|cutting-edge|best-in-class|utilize|implement|streamline)\b',
        primary_text, re.IGNORECASE
    )
    if jargon:
        violations.append(f"corporate jargon: {', '.join(jargon[:3])}")

    if not violations:
        return 5, "All platform constraints met, conversational tone"
    elif len(violations) == 1:
        return 3, f"1 violation: {violations[0]}"
    else:
        return max(1, 4 - len(violations)), f"{len(violations)} violations: {'; '.join(violations)}"


def _score_objection_preemption(ad: dict) -> tuple[int, str]:
    """Check for low-risk trio and key disclaimers."""
    text = _get_all_text(ad).lower()
    signals = 0
    found = []

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

    detail = f"{signals}/5 objection signals: {', '.join(found) if found else 'none'}"
    score = max(1, signals)
    return score, detail


def _score_scroll_stop_hook(ad: dict) -> tuple[int, str]:
    """Classify the first line and score its scroll-stop potential."""
    primary = ad.get("primary_text", "").strip()
    # Get first non-empty, non-blockquote line
    first_line = ""
    for line in primary.split("\n"):
        line = line.strip().strip(">").strip()
        if line:
            first_line = line
            break

    if not first_line:
        return 1, "No opening line found"

    # Story hook: specific day/time/action
    if re.search(r'(last\s+\w+day|yesterday|this morning|walked in|picked up|called|booked)', first_line, re.IGNORECASE):
        return 5, f"Story hook with specific moment: '{first_line[:60]}...'"

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
    """Measure how different this ad is from existing ads using Jaccard similarity."""
    if not existing_ads:
        return 4, "No existing ads to compare — default to 4"

    ad_words = _tokenize(_get_all_text(ad))
    if not ad_words:
        return 1, "Empty ad text"

    similarities = []
    for other in existing_ads:
        other_words = _tokenize(_get_all_text(other))
        if other_words:
            jaccard = len(ad_words & other_words) / len(ad_words | other_words)
            similarities.append(jaccard)

    if not similarities:
        return 4, "No comparable ads"

    avg_sim = sum(similarities) / len(similarities)
    max_sim = max(similarities)

    detail = f"Avg similarity: {avg_sim:.2f}, max: {max_sim:.2f} (vs {len(existing_ads)} ads)"

    if avg_sim < 0.2:
        return 5, detail
    elif avg_sim < 0.3:
        return 4, detail
    elif avg_sim < 0.4:
        return 3, detail
    elif avg_sim < 0.6:
        return 2, detail
    return 1, detail


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
        has_hook = bool(ad.get("headline"))
        has_body = len(ad.get("primary_text", "")) > 50
        has_cta = bool(ad.get("cta"))
        score = 1 + has_hook + has_body + has_cta
        return min(score, 4), f"Heuristic: hook={has_hook}, body={has_body}, cta={has_cta}"

    return 3, "Heuristic: default middle score"


# --- Utilities ---

def _get_all_text(ad: dict) -> str:
    """Concatenate all text fields."""
    fields = ["primary_text", "headline", "description"]
    parts = []
    for field in fields:
        text = ad.get(field, "")
        if text:
            text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
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
