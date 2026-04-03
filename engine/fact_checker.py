"""
Fact Checker — Axis 2 of the scoring engine.

Extracts numeric claims and product assertions from ad text,
matches them against a structured facts register.
100% deterministic — no LLM involvement.

Returns: {score, claims_found, verified, unverified, contradicted, details}
"""

import json
import re
from pathlib import Path


def load_facts(client_dir: Path) -> dict:
    """Load the structured facts register for a client."""
    facts_path = client_dir / "facts.json"
    with open(facts_path) as f:
        return json.load(f)


def check_facts(ad: dict, facts_data: dict) -> dict:
    """Check all claims in an ad against the facts register.

    Args:
        ad: Ad in canonical JSON format
        facts_data: Loaded facts.json

    Returns:
        {
            "score": 0.0-1.0,
            "claims_found": int,
            "verified": int,
            "unverified": int,
            "contradicted": int,
            "details": [{"claim": str, "fact_id": str, "status": str, "confidence": str}]
        }
    """
    facts = facts_data.get("facts", [])

    # Extract claims from all text fields
    all_text = _get_all_text(ad)
    claims = _extract_claims(all_text)

    if not claims:
        # No verifiable claims found — that's fine, score 1.0
        return {
            "score": 1.0,
            "claims_found": 0,
            "verified": 0,
            "unverified": 0,
            "contradicted": 0,
            "details": [],
        }

    details = []
    verified_weight = 0.0
    total_weight = 0.0

    for claim in claims:
        match = _match_claim_to_fact(claim, facts)
        total_weight += 1.0

        if match["status"] == "verified":
            conf = match["confidence"]
            weight = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.0}.get(conf, 0.0)
            verified_weight += weight
            details.append({
                "claim": claim["text"],
                "fact_id": match["fact_id"],
                "status": "verified",
                "confidence": conf,
            })
        elif match["status"] == "contradicted":
            details.append({
                "claim": claim["text"],
                "fact_id": match.get("fact_id", ""),
                "status": "contradicted",
                "confidence": "",
                "reason": match.get("reason", "Contradicts verified fact"),
            })
            # Any contradiction = score override to 0.0
            return {
                "score": 0.0,
                "claims_found": len(claims),
                "verified": sum(1 for d in details if d["status"] == "verified"),
                "unverified": 0,
                "contradicted": 1,
                "details": details,
            }
        else:
            details.append({
                "claim": claim["text"],
                "fact_id": "",
                "status": "unverified",
                "confidence": "",
            })

    verified_count = sum(1 for d in details if d["status"] == "verified")
    unverified_count = sum(1 for d in details if d["status"] == "unverified")

    score = verified_weight / total_weight if total_weight > 0 else 1.0

    return {
        "score": round(score, 4),
        "claims_found": len(claims),
        "verified": verified_count,
        "unverified": unverified_count,
        "contradicted": 0,
        "details": details,
    }


def _get_all_text(ad: dict) -> str:
    """Concatenate all text fields from the ad."""
    fields = ["primary_text", "headline", "description"]
    parts = []
    for field in fields:
        text = ad.get(field, "")
        if text:
            # Strip blockquote markers
            text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
            parts.append(text)
    return "\n".join(parts)


def _extract_claims(text: str) -> list[dict]:
    """Extract verifiable claims from ad text.

    Returns a list of claim dicts with 'text' and 'type' fields.
    """
    claims = []
    seen = set()

    # 1. Money amounts: $50/month, $250, $800-$1,300, etc.
    money_pattern = r'\$[\d,]+(?:\.\d{1,2})?(?:\s*[-–—to]+\s*\$?[\d,]+(?:\.\d{1,2})?)?(?:\s*/\s*\w+)?(?:\s*\+)?'
    for match in re.finditer(money_pattern, text):
        claim_text = match.group().strip()
        if claim_text not in seen:
            seen.add(claim_text)
            claims.append({"text": claim_text, "type": "money"})

    # 2. Numbers with context: 270+ clinics, 4.1/5 stars, etc.
    number_context_pattern = r'(\d+[\+]?\s*(?:clinics|vet clinics|locations|practices|reviews?|stars?|visits?|services?|nights?|trims?|%|consult))'
    for match in re.finditer(number_context_pattern, text, re.IGNORECASE):
        claim_text = match.group().strip()
        if claim_text not in seen:
            seen.add(claim_text)
            claims.append({"text": claim_text, "type": "number"})

    # 3. Product feature assertions — check for key phrases
    feature_patterns = [
        (r'unlimited\s+(?:vet\s+)?(?:consult|visit|check)', "unlimited consultations"),
        (r'cancel\s+any\s*time', "cancel anytime"),
        (r'no\s+(?:joining|sign[- ]?up)\s+fee', "no joining fee"),
        (r'no\s+wait(?:ing)?\s+period', "no waiting period"),
        (r'no\s+lock[- ]?in', "no lock-in"),
        (r'not\s+insurance|isn\'t\s+insurance|is\s+not\s+insurance', "not insurance"),
        (r'24/7\s+(?:vet\s*chat|virtual|online)', "24/7 VetChat"),
        (r'all\s+(?:routine\s+)?vaccination', "all vaccinations included"),
        (r'\$250\s+off\s+dental', "$250 off dental"),
        (r'annual\s+blood\s+(?:and\s+urine\s+)?test', "annual blood test"),
        (r'microchip', "microchip included"),
        (r'(?:4|four)\s+nail\s+trims?', "4 nail trims"),
        (r'(?:2|two)\s+nights?\s+(?:cat\s+)?boarding', "2 nights boarding"),
        (r'20%\s+off\s+desexing', "20% off desexing"),
        (r'10%\s+off\s+(?:parasite|heartworm|food|accessories)', "10% off parasite/food"),
    ]
    for pattern, label in feature_patterns:
        if re.search(pattern, text, re.IGNORECASE) and label not in seen:
            seen.add(label)
            claims.append({"text": label, "type": "feature"})

    return claims


def _match_claim_to_fact(claim: dict, facts: list[dict]) -> dict:
    """Try to match a claim to a fact in the register."""
    claim_text = claim["text"].lower()

    # First pass: check for contradictions
    for fact in facts:
        contradicts_if = fact.get("contradicts_if", "")
        if contradicts_if:
            try:
                if re.search(contradicts_if, claim_text, re.IGNORECASE):
                    return {
                        "status": "contradicted",
                        "fact_id": fact["fact_id"],
                        "reason": f"Contradicts {fact['fact_id']}: {fact['claim']}",
                    }
            except re.error:
                pass

    # Second pass: try to match to a fact via claim_patterns
    for fact in facts:
        patterns = fact.get("claim_patterns", [])
        for pattern in patterns:
            if pattern.lower() in claim_text or claim_text in pattern.lower():
                return {
                    "status": "verified",
                    "fact_id": fact["fact_id"],
                    "confidence": fact.get("confidence", "MEDIUM"),
                }

    # Third pass: check money amounts against value_range fields
    if claim["type"] == "money":
        amount = _extract_amount(claim_text)
        if amount is not None:
            for fact in facts:
                vr = fact.get("value_range")
                if vr and vr.get("min") and vr.get("max"):
                    if vr["min"] <= amount <= vr["max"]:
                        return {
                            "status": "verified",
                            "fact_id": fact["fact_id"],
                            "confidence": fact.get("confidence", "MEDIUM"),
                        }

                # Check individual claim_patterns for exact money matches
                for pattern in fact.get("claim_patterns", []):
                    pat_amount = _extract_amount(pattern)
                    if pat_amount is not None and abs(pat_amount - amount) < 0.01:
                        return {
                            "status": "verified",
                            "fact_id": fact["fact_id"],
                            "confidence": fact.get("confidence", "MEDIUM"),
                        }

    return {"status": "unverified"}


def _extract_amount(text: str):
    """Extract a dollar amount from text. Returns None if no amount found."""
    match = re.search(r'\$?([\d,]+(?:\.\d{1,2})?)', text)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            return None
    return None
