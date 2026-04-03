"""
Writer — The mutable variant generator (the train.py analog).

This file generates new ad copy variants. The autonomous agent
can modify this file freely to improve generation strategy.

The writer does NOT import from engine/ — it never sees the scorer's
internals, rubric weights, or rule definitions.
"""

import json
import os
import subprocess
import random
from pathlib import Path
from datetime import datetime


# --- Hook type templates ---
HOOK_TEMPLATES = {
    "question": "Open with a genuine question the audience has asked themselves. Not rhetorical — real.",
    "statistic": "Open with a specific, surprising number that creates an anchor.",
    "bold_claim": "Open with a value proposition so strong it triggers disbelief.",
    "confession": "Open with an honest admission that earns trust through vulnerability.",
    "contrarian": "Open by challenging a common assumption the audience holds.",
    "if_then": "Open with an if/then structure that lets the maths sell.",
    "quoted_objection": "Open with a real objection in quotes, then address it.",
    "story": "Open with a specific moment — a day, an action, a cost. Make it real.",
    "direct_address": "Open by speaking directly to the reader's situation.",
    "pattern_interrupt": "Open with something unexpected that doesn't look like an ad.",
}


def generate_variant(
    angle: str,
    tactic: str,
    hook_type: str,
    funnel: str,
    client_dir: Path,
    current_best: dict = None,
    recent_failures: list = None,
    wildcard: bool = False,
) -> dict:
    """Generate a new ad copy variant.

    Args:
        angle: Target angle ID (e.g., "price-value")
        tactic: Target tactic (e.g., "cost-of-inaction")
        hook_type: Target hook type (e.g., "story", "question")
        funnel: Funnel stage ("TOF", "MOF", "BOF")
        client_dir: Path to client config directory
        current_best: Current best ad for this slot (to beat)
        recent_failures: Last few discards for this slot
        wildcard: If True, try something novel instead of hill-climbing

    Returns:
        Ad in canonical JSON format
    """
    # Load client context
    config = _load_json(client_dir / "config.json")
    tone = _load_text(client_dir / "tone.md")
    learnings = _load_text(client_dir / "learnings.md")
    facts = _load_json(client_dir / "facts.json")

    # Build the generation prompt
    prompt = _build_prompt(
        angle=angle,
        tactic=tactic,
        hook_type=hook_type,
        funnel=funnel,
        config=config,
        tone=tone,
        learnings=learnings,
        facts=facts,
        current_best=current_best,
        recent_failures=recent_failures or [],
        wildcard=wildcard,
    )

    # Generate via LLM
    raw_output = _call_llm(prompt)

    # Parse the output into canonical ad format
    ad = _parse_output(raw_output, angle, tactic, hook_type, funnel)

    return ad


def _build_prompt(
    angle: str,
    tactic: str,
    hook_type: str,
    funnel: str,
    config: dict,
    tone: str,
    learnings: str,
    facts: dict,
    current_best: dict,
    recent_failures: list,
    wildcard: bool,
) -> str:
    """Build the variant generation prompt."""
    client_name = config.get("client_name", "Unknown")
    product = config.get("product", "Unknown")
    approved_ctas = config.get("approved_ctas", [])
    constraints = config.get("platform_constraints", {})

    # Build facts context — relevant facts for this angle
    facts_text = _select_relevant_facts(facts, angle)

    # Hook template
    hook_template = HOOK_TEMPLATES.get(hook_type, "Write a compelling hook.")

    # Hill-climbing context
    beat_text = ""
    if current_best and not wildcard:
        beat_text = f"""
CURRENT BEST FOR THIS SLOT:
Headline: {current_best.get('headline', '')}
Primary text: {current_best.get('primary_text', '')[:200]}...
Score to beat: {current_best.get('score', {}).get('composite', 'unknown')}

Your goal: write something BETTER than the above. Change the angle of attack,
tighten the opening, find a more specific proof point, or try a different
emotional register. Don't repeat what's already working — improve on it.
"""

    # Failure context
    failure_text = ""
    if recent_failures:
        failure_text = "\nRECENT FAILURES (don't repeat these approaches):\n"
        for f in recent_failures[-5:]:
            failure_text += f"- {f}\n"

    # Wildcard instruction
    wildcard_text = ""
    if wildcard:
        wildcard_text = """
WILDCARD MODE: Ignore the current best. Try something completely different.
A new hook type, a different emotional register, a surprising opening.
The goal is exploration, not optimisation.
"""

    return f"""Write ONE ad variant for {client_name} — {product}.

ANGLE: {angle}
TACTIC: {tactic}
HOOK TYPE: {hook_type} — {hook_template}
FUNNEL: {funnel}

CONSTRAINTS:
- Primary text: max {constraints.get('primary_text_max_chars', 500)} characters
- Headline: max {constraints.get('headline_max_chars', 40)} characters
- Description: max {constraints.get('description_max_chars', 125)} characters
- Platform: {constraints.get('platform', 'meta')}
- CTA must be one of: {', '.join(approved_ctas)}

TONE GUIDELINES:
{tone[:500]}

CREATIVE LEARNINGS (what works and what fails):
{learnings[:500]}

VERIFIED FACTS (use only these — every number must trace back):
{facts_text}
{beat_text}{failure_text}{wildcard_text}
IMPORTANT RULES:
- No em-dashes (use full stops, commas, or colons)
- No commands ("stop", "add it up", "do the maths")
- No condescension ("we'll wait", "simple maths")
- Lead with value/benefit, not price
- Include "not insurance" or equivalent disclaimer
- Close with the low-risk trio: "No joining fee. No waiting period. Cancel anytime."
- Every number must trace to a verified fact above

OUTPUT FORMAT (respond with ONLY this JSON, no other text):
{{
  "primary_text": "your ad body copy here",
  "headline": "your headline here",
  "description": "your description here",
  "cta": "one of the approved CTAs",
  "creative_brief": "brief visual direction (1-2 sentences)"
}}"""


def _select_relevant_facts(facts_data: dict, angle: str) -> str:
    """Select facts most relevant to the given angle."""
    facts = facts_data.get("facts", [])
    lines = []

    # Always include pricing and core inclusions
    priority_categories = ["pricing", "inclusions", "savings", "exclusions"]

    # Angle-specific priorities
    angle_categories = {
        "price-value": ["pricing", "savings"],
        "simplicity-clarity": ["inclusions", "how_it_works"],
        "safety-risk": ["inclusions", "exclusions"],
        "empathy-understanding": ["savings", "social_proof"],
        "outcome-results": ["savings", "social_proof"],
        "anti-insurance": ["exclusions", "social_proof"],
    }
    extra = angle_categories.get(angle, [])

    shown = set()
    for fact in facts:
        cat = fact.get("category", "")
        if cat in priority_categories or cat in extra:
            if fact["fact_id"] not in shown:
                conf = fact.get("confidence", "MEDIUM")
                lines.append(f"[{fact['fact_id']}] ({conf}) {fact['claim']}")
                shown.add(fact["fact_id"])

    return "\n".join(lines[:25])  # Cap at 25 facts to fit in context


def _call_llm(prompt: str) -> str:
    """Call LLM to generate ad copy."""
    # Try Anthropic API first
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception:
            pass

    # Fallback: claude CLI
    try:
        result = subprocess.run(
            ["claude", "--print", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        pass

    return '{"error": "No LLM available"}'


def _parse_output(raw: str, angle: str, tactic: str, hook_type: str, funnel: str) -> dict:
    """Parse LLM output into canonical ad format."""
    import re

    # Try to extract JSON from the response
    json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            ad_id = f"{angle[:2].upper()}-{random.randint(100, 999)}"
            return {
                "ad_id": ad_id,
                "angle": angle,
                "tactic": tactic,
                "hook_type": hook_type,
                "funnel": funnel,
                "primary_text": data.get("primary_text", ""),
                "headline": data.get("headline", ""),
                "description": data.get("description", ""),
                "cta": data.get("cta", "Learn More"),
                "creative_brief": data.get("creative_brief", ""),
                "generated_at": datetime.now().isoformat(),
            }
        except json.JSONDecodeError:
            pass

    # Fallback: return error ad
    return {
        "ad_id": "ERROR",
        "angle": angle,
        "tactic": tactic,
        "hook_type": hook_type,
        "funnel": funnel,
        "primary_text": raw[:500],
        "headline": "PARSE ERROR",
        "description": "",
        "cta": "",
        "creative_brief": "",
        "generated_at": datetime.now().isoformat(),
        "error": "Could not parse LLM output",
    }


def _load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _load_text(path: Path) -> str:
    with open(path) as f:
        return f.read()
