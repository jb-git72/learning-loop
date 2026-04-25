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
import sys
from pathlib import Path
from datetime import datetime

_root = Path(__file__).parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from scripts.lint_content import lint as lint_content


# --- Load canonical hook and tactic registries from shared/ ---
def _load_hooks_registry() -> tuple[dict, dict]:
    """Load hooks.json and build HOOK_TEMPLATES + HOOK_METADATA dicts."""
    hooks_path = _root / "shared" / "hooks.json"
    if hooks_path.exists():
        with open(hooks_path) as f:
            data = json.load(f)
        templates = {}
        metadata = {}
        for h in data.get("hooks", []):
            templates[h["id"]] = h["template"]
            metadata[h["id"]] = {
                "benchmark_hit_rate": h.get("benchmark_hit_rate", 0.05),
                "benchmark_spend_use_ratio": h.get("benchmark_spend_use_ratio", 1.0),
                "best_verticals": h.get("best_verticals", ["all"]),
                "best_content_types": h.get("best_content_types", ["meta-ad"]),
                "scorer_compatible_pattern": h.get("scorer_compatible_pattern", ""),
                "content_type_adaptations": h.get("content_type_adaptations", {}),
            }
        return templates, metadata
    # Fallback to hardcoded if hooks.json missing
    return {
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
    }, {}


def _load_tactics_registry() -> dict:
    """Load tactics.json and return a dict keyed by tactic ID."""
    tactics_path = _root / "shared" / "tactics.json"
    if tactics_path.exists():
        with open(tactics_path) as f:
            data = json.load(f)
        return {t["id"]: t for t in data.get("tactics", [])}
    return {}


HOOK_TEMPLATES, HOOK_METADATA = _load_hooks_registry()
TACTICS_REGISTRY = _load_tactics_registry()


def generate_variant(
    angle: str,
    tactic: str,
    hook_type: str,
    funnel: str,
    client_dir: Path,
    current_best: dict = None,
    recent_failures: list = None,
    wildcard: bool = False,
    content_type: str = "meta-ad",
    mode: str = "improve",
    donor_ad: dict = None,
    weak_dimensions: list = None,
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
        content_type: Content type (meta-ad, email, landing-page)
        mode: Generation mode — "improve" (default), "mutate", "wildcard",
              "crossover", or "targeted"
        donor_ad: High-scoring ad to blend with in crossover mode
        weak_dimensions: List of (dim_name, score, max_score) tuples for
                         targeted mode

    Returns:
        Ad in canonical JSON format
    """
    # Backwards compat: if wildcard=True, override mode
    if wildcard:
        mode = "wildcard"

    # Load client context
    config = _load_json(client_dir / "config.json")
    tone = _load_text(client_dir / "tone.md")
    learnings = _load_learnings(client_dir, content_type)
    facts = _load_json(client_dir / "facts.json")

    # Build the generation prompt (split for caching)
    base_context, variant_instruction = _build_prompt(
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
        wildcard=(mode == "wildcard"),
        content_type=content_type,
        mode=mode,
        donor_ad=donor_ad,
        weak_dimensions=weak_dimensions,
    )

    # Temperature varies by mode
    temp_map = {
        "improve": 0.7,
        "mutate": 0.8,
        "wildcard": 0.9,
        "crossover": 0.6,
        "targeted": 0.5,
    }
    temperature = temp_map.get(mode, 0.7)

    # Generate via LLM (base_context cached as system prompt)
    raw_output = _call_llm(variant_instruction, temperature=temperature,
                           system_context=base_context)

    # Parse the output into canonical format
    ad = _parse_output(raw_output, angle, tactic, hook_type, funnel, content_type)

    # Lint gate — retry up to 2 times if violations found
    shared_dir = client_dir.parent.parent / "shared"
    max_lint_retries = 2
    for lint_attempt in range(max_lint_retries):
        lint_result = lint_content(ad, client_dir, shared_dir)
        if lint_result.passed:
            break

        # Build violation context for the retry prompt
        violation_lines = [
            f"- [{v['layer']}] {v['rule_id']} in {v['field']}: {v['detail']}"
            for v in lint_result.violations[:5]
        ]
        violation_text = "\n".join(violation_lines)

        retry_prompt = (
            variant_instruction
            + f"\n\nPREVIOUS ATTEMPT FAILED LINT CHECK (attempt {lint_attempt + 1}):\n"
            + violation_text
            + "\n\nFix ALL of the above violations in your next attempt. "
            + "Do NOT include any of the flagged terms or patterns."
        )
        raw_output = _call_llm(retry_prompt, system_context=base_context)
        ad = _parse_output(raw_output, angle, tactic, hook_type, funnel, content_type)
    else:
        # All retries exhausted — attach lint failures for the caller
        final_lint = lint_content(ad, client_dir, shared_dir)
        if not final_lint.passed:
            ad["_lint_failures"] = [
                {"rule_id": v["rule_id"], "field": v["field"], "detail": v["detail"]}
                for v in final_lint.violations
            ]

    return ad


def _build_scoring_guide(content_type: str, config: dict) -> str:
    """Build a condensed scoring guide so the writer knows what it'll be scored on."""
    client_id = config.get("client_id", "")

    # Objection preemption — config-driven, hardcoded fallback
    objection_signals = config.get("prompt_objection_signals", "")
    if not objection_signals:
        if client_id == "farm-thru":
            objection_signals = 'Include: "no middlemen/wholesalers", mention Sydney/Brookvale area, acknowledge risk for CFE content.'
        else:
            objection_signals = 'Include: "no joining fee", "no waiting period", "cancel anytime", "not insurance".'

    guide = f"""SCORING GUIDE:
STRUCTURE (highest-weighted dimension): Hook → Proof → Bridge → CTA. Each section earns the next. "Velvet slide" — if removing a paragraph doesn't break the flow, cut it. Score 5 = "invisible structure." Score 1 = "list of features."
MOTIVATION: Tap the FELT need, not features. "I didn't know what my kids were eating" not "farm-direct grocery." People buy on emotion, rationalize with logic.
ANGLE: ONE proposition per piece. Every sentence reinforces it. Competing themes = score 2.
HOOK: The first line determines your hook score. Highest-scoring patterns: named person + action verb ("Sarah walked in..."), quoted objection (open with "), story moment (yesterday, last week, walked in). Also strong: questions (?), numbers/dollars ($, digits first), if/then ("If you..."). Generic openers score lowest.
SPECIFICITY: 5-7 concrete signals (dollars, numbers, named farms/people). Vague = score 1.
OBJECTION PREEMPTION: {objection_signals}
HEADLINES: 4 U's — Urgent, Unique, Ultra-specific, Useful. Sentence case only.
SENTENCES: 14-16 words avg. Conversational tone. Contractions OK. Omit needless words."""
    return guide


def _build_rules_summary(config: dict, content_type: str) -> str:
    """Build a condensed rules summary from config. Falls back to hardcoded for backwards compat."""
    # Config-driven rules (preferred)
    prompt_rules = config.get("prompt_rules", {})
    if isinstance(prompt_rules, dict) and content_type in prompt_rules:
        rules = "RULES (violating ANY zeros your score — read carefully):\n" + prompt_rules[content_type]
        return _append_compliance_summary(rules, config, content_type)

    # Hardcoded fallback for clients without prompt_rules in config
    client_id = config.get("client_id", "")
    if client_id == "farm-thru":
        rules = """RULES (violating ANY zeros your score — read carefully):
- NEVER name competitors: Woolworths, Coles, Aldi, Harris Farm. Say "supermarkets" or "the big chains"
- NEVER say "delivered to your door/kitchen/doorstep" — FarmThru is hub-and-collect
- Sentence case headlines only — NEVER Title Case
- No fabricated stats: "50+ farms" and "2,000+ customers" are FALSE"""
        ct_rules = prompt_rules.get(content_type, "")
        if ct_rules:
            rules += "\n" + ct_rules
    else:
        rules = """RULES:
- No em-dashes (use full stops, commas, or colons)
- No commands ("stop", "add it up", "do the maths")
- No condescension ("we'll wait", "simple maths")
- Lead with value/benefit, not price"""

    return _append_compliance_summary(rules, config, content_type)


def _append_compliance_summary(rules_text: str, config: dict, content_type: str) -> str:
    """Append a regulatory-compliance summary when the client opts in.

    Reads the same compliance_rules.json the scorer uses, filters to BLOCKING
    rules in scope for this content_type + applies_to, and inlines the rule
    claims so the writer LLM sees the exact gates that will zero its score.
    Skips silently if compliance is disabled or the rules file is unavailable.
    """
    compliance_cfg = config.get("compliance", {}) or {}
    if not compliance_cfg.get("enabled"):
        return rules_text

    try:
        from engine import compliance_checker
        rules_path = compliance_cfg.get("rules_path")
        data = compliance_checker._load_rules(rules_path)
    except Exception:
        return rules_text

    applies_to = compliance_cfg.get("applies_to", "issuer")
    blocking_claims = []
    for rule in data.get("rules", []):
        if rule.get("severity") != "BLOCKING":
            continue
        if not compliance_checker._rule_in_scope(rule, content_type, applies_to):
            continue
        claim = rule.get("claim", "").strip()
        if claim:
            blocking_claims.append(f"- [{rule.get('rule_id', '?')}] {claim}")

    if not blocking_claims:
        return rules_text

    # Cap to avoid swamping the prompt; the writer doesn't need the full library.
    cap = int(compliance_cfg.get("prompt_rule_cap", 12))
    shown = blocking_claims[:cap]
    overflow = len(blocking_claims) - len(shown)

    header = (
        "\n\nREGULATORY COMPLIANCE (BLOCKING — failing any zeros your score):"
    )
    body = "\n".join(shown)
    footer = (
        f"\n... +{overflow} more BLOCKING rules from the CSF rule library are also enforced."
        if overflow > 0
        else ""
    )
    return rules_text + header + "\n" + body + footer


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
    content_type: str = "meta-ad",
    mode: str = "improve",
    donor_ad: dict = None,
    weak_dimensions: list = None,
) -> str:
    """Build the variant generation prompt."""
    client_name = config.get("client_name", "Unknown")
    product = config.get("product", "Unknown")

    # Get content-type-specific approved CTAs
    approved_ctas = config.get("approved_ctas", [])
    if isinstance(approved_ctas, dict):
        approved_ctas = approved_ctas.get(content_type, approved_ctas.get("meta-ad", []))

    # Get content-type-specific platform constraints
    constraints = config.get("platform_constraints", {})
    if isinstance(constraints, dict) and content_type in constraints:
        constraints = constraints[content_type]

    # Load industry playbook context if available
    industry = config.get("industry", "general")
    playbook_md_path = _root / "shared" / "playbooks" / f"{industry}.md"
    if not playbook_md_path.exists():
        playbook_md_path = _root / "shared" / "playbooks" / "general.md"
    industry_context = ""
    if playbook_md_path.exists():
        industry_context = _load_text(playbook_md_path)[:400]

    # Build facts context — relevant facts for this angle
    facts_text = _select_relevant_facts(facts, angle, content_type)

    # Build scoring guide and rules summary
    scoring_guide = _build_scoring_guide(content_type, config)
    rules_summary = _build_rules_summary(config, content_type)

    # Hook template + content-type adaptation
    hook_template = HOOK_TEMPLATES.get(hook_type, "Write a compelling hook.")
    hook_meta = HOOK_METADATA.get(hook_type, {})
    hook_adaptation = hook_meta.get("content_type_adaptations", {}).get(content_type, "")
    if hook_adaptation:
        hook_template += f" [{content_type} tip: {hook_adaptation}]"

    # Tactic structure guidance
    tactic_info = TACTICS_REGISTRY.get(tactic, {})
    tactic_structure = ""
    if tactic_info:
        tactic_structure = f"\nTACTIC STRUCTURE: {tactic_info.get('structure', '')}"
        tactic_guidance = tactic_info.get("guidance", "")
        if tactic_guidance:
            tactic_structure += f"\nTACTIC GUIDANCE: {tactic_guidance}"

    # Hill-climbing context — show the right fields per content type
    beat_text = ""
    if current_best and not wildcard:
        score_to_beat = current_best.get('score', {}).get('composite', 'unknown')
        if content_type == "landing-page":
            beat_text = f"""
CURRENT BEST FOR THIS SLOT:
Headline: {current_best.get('headline', '')}
Subhead: {current_best.get('subhead', '')}
Hero copy: {current_best.get('hero_copy', '')[:200]}...
Score to beat: {score_to_beat}
"""
        elif content_type == "email":
            beat_text = f"""
CURRENT BEST FOR THIS SLOT:
Subject: {current_best.get('subject', '')}
Preheader: {current_best.get('preheader', '')}
Body opening: {current_best.get('body', '')[:200]}...
Score to beat: {score_to_beat}
"""
        else:  # meta-ad
            beat_text = f"""
CURRENT BEST FOR THIS SLOT:
Headline: {current_best.get('headline', '')}
Primary text: {current_best.get('primary_text', '')[:200]}...
Description: {current_best.get('description', '')}
Score to beat: {score_to_beat}
"""
        beat_text += """
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

    # Crossover instruction
    crossover_text = ""
    if mode == "crossover" and donor_ad:
        donor_headline = donor_ad.get("headline", donor_ad.get("subject", ""))
        donor_opening = ""
        for field in ("primary_text", "body", "hero_copy"):
            text = donor_ad.get(field, "")
            if text:
                donor_opening = text[:200]
                break
        crossover_text = f"""
CROSSOVER MODE: Blend the current ad's angle with the style of a high-scoring donor.
DONOR AD (use as style inspiration, not content to copy):
  Headline: {donor_headline}
  Opening: {donor_opening}...
Take the donor's rhythm, structure, and emotional register.
Apply them to YOUR angle ({angle}) and YOUR facts. Do not copy the donor's claims.
"""

    # Targeted improvement instruction
    targeted_text = ""
    if mode == "targeted" and weak_dimensions:
        dim_lines = []
        for dim_name, dim_score, dim_max in weak_dimensions:
            guidance = _dimension_improvement_guidance(dim_name)
            dim_lines.append(f"- {dim_name}: {dim_score}/{dim_max}. {guidance}")
        targeted_text = """
TARGETED IMPROVEMENT: Your weakest scoring dimensions are listed below.
Focus specifically on improving these while maintaining everything else:
""" + "\n".join(dim_lines) + "\n"

    # Content-type-specific constraints and output format
    if content_type == "landing-page":
        constraints_text = f"""- Headline: max {constraints.get('headline_max_chars', 80)} characters
- Subhead: max {constraints.get('subhead_max_chars', 200)} characters
- Hero copy: max {constraints.get('hero_copy_max_chars', 500)} characters
- Section body: max {constraints.get('section_body_max_chars', 1000)} characters per section
- Platform: web (landing page)
- CTA must be one of: {', '.join(approved_ctas)}"""
        output_format = """{
  "headline": "H1 hero headline",
  "subhead": "supporting text below headline",
  "hero_copy": "above-the-fold body copy",
  "sections": [
    {"heading": "section heading", "body": "section body copy"},
    {"heading": "section heading", "body": "section body copy"},
    {{"heading": "Compliance", "body": "{config.get('landing_page_compliance', 'Include relevant compliance disclaimer here.')}"}}

  ],
  "cta": "one of the approved CTAs",
  "creative_brief": "brief visual direction (1-2 sentences)"
}"""
        content_label = "landing page variant"
        config_extra = config.get("prompt_extra_rules", {}).get("landing-page", "")
        if config_extra:
            extra_rules = config_extra
        else:
            extra_rules = """- Include financial disclaimer if discussing investment
- Risks and benefits must have equal prominence
- No return projections or guarantees
- Every number must trace to a verified fact above"""

    elif content_type == "email":
        constraints_text = f"""- Subject: max {constraints.get('subject_max_chars', 60)} characters (6-10 words ideal)
- Preheader: max {constraints.get('preheader_max_chars', 100)} characters
- Body: max {constraints.get('body_max_chars', 2000)} characters
- Platform: email
- CTA must be one of: {', '.join(approved_ctas)}"""
        output_format = """{
  "subject": "email subject line",
  "preheader": "preview text shown after subject in inbox",
  "body": "email body copy (use \\n\\n for paragraph breaks)",
  "cta": "one of the approved CTAs",
  "sender_name": "sender display name",
  "creative_brief": "brief email design direction (1-2 sentences)"
}"""
        content_label = "email variant"
        # Config-driven extra rules, fallback to generic
        email_sender = config.get("email_sender", config.get("scoring_context", {}).get("sender", "the team"))
        config_extra = config.get("prompt_extra_rules", {}).get("email", "")
        if config_extra:
            extra_rules = config_extra + f"\n- The sender must be '{email_sender}'"
        else:
            extra_rules = f"""- Single CTA per email
- Short paragraphs (max 3 sentences each)
- Founder voice when appropriate
- Every number must trace to a verified fact above
- The sender must be '{email_sender}'"""

    else:  # meta-ad (default)
        constraints_text = f"""- Primary text: max {constraints.get('primary_text_max_chars', 500)} characters
- Headline: max {constraints.get('headline_max_chars', 40)} characters
- Description: max {constraints.get('description_max_chars', 125)} characters
- Platform: {constraints.get('platform', 'meta')}
- CTA must be one of: {', '.join(approved_ctas)}"""
        output_format = """{
  "primary_text": "your ad body copy here",
  "headline": "your headline here",
  "description": "your description here",
  "cta": "one of the approved CTAs",
  "creative_brief": "brief visual direction (1-2 sentences)"
}"""
        content_label = "ad variant"
        # Config-driven extra rules, fallback to generic
        config_extra = config.get("prompt_extra_rules", {}).get("meta-ad", "")
        if config_extra:
            extra_rules = config_extra
        else:
            extra_rules = """- No em-dashes (use full stops, commas, or colons)
- No commands ("stop", "add it up", "do the maths")
- No condescension ("we'll wait", "simple maths")
- Lead with value/benefit, not price
- Every number must trace to a verified fact above
- Description field should complement the headline, not repeat it"""

    # Build industry context section
    industry_section = ""
    if industry_context:
        industry_section = f"\nINDUSTRY CONTEXT ({industry}):\n{industry_context}\n"

    # Split into base context (cacheable) and variant instruction (unique)
    base_context = f"""You are a direct-response copywriter for {client_name} — {product}.

{scoring_guide}

{rules_summary}

CONSTRAINTS:
{constraints_text}

TONE GUIDELINES:
{tone[:600]}
{industry_section}
CREATIVE LEARNINGS:
{learnings}

VERIFIED FACTS (use only these — every number must trace back):
{facts_text}

IMPORTANT RULES:
{extra_rules}

OUTPUT FORMAT (respond with ONLY this JSON, no other text):
{output_format}"""

    variant_instruction = f"""Write ONE {content_label}.

ANGLE: {angle}
TACTIC: {tactic}{tactic_structure}
HOOK TYPE: {hook_type} — {hook_template}
FUNNEL: {funnel}
{beat_text}{failure_text}{wildcard_text}{crossover_text}{targeted_text}
Respond with ONLY the JSON output."""

    return base_context, variant_instruction


def _dimension_improvement_guidance(dim_name: str) -> str:
    """Return specific improvement guidance for a weak rubric dimension."""
    guidance = {
        "angle_clarity": "Sharpen to ONE proposition. Every sentence must reinforce it. Remove competing themes.",
        "motivation_match": "Tap the FELT need. 'I didn't know what my kids were eating' not 'farm-direct grocery.' Emotion first, logic second.",
        "tactic_execution": "Hook -> Proof -> Bridge -> CTA. Each section earns the next. If removing a paragraph doesn't break the flow, cut it.",
        "specificity": "Add 5-7 concrete signals: dollar amounts, numbers, named farms/people. Replace vague claims with proof.",
        "objection_preemption": "Include: 'no commitment', 'order when you want', mention the hub, acknowledge risk, reference provenance.",
        "receptionist_test": "Answer: What is it? Where does food come from? How is it different? How do I start? Why now?",
        "scroll_stop_hook": "Best: named person + action ('Sarah walked in last Tuesday'), story moment ('Yesterday I opened...'), quoted objection (start with \"). Strong: question (end with ?), number/dollar first ('$50 covers...', '14 farms...'), if/then ('If you...'). NEVER generic statements.",
        "cta_clarity": "Use an approved CTA exactly as listed. Make it specific and action-oriented.",
        "platform_fit": "Stay within character limits. Use conversational tone. No corporate jargon.",
        "differentiation": "Use unique language. Avoid phrases from other ads in the set. Find a fresh angle of attack.",
        "hero_clarity": "Headline + subhead + CTA must answer 'what/who/action' in 5 seconds.",
        "proof_density": "Add stats, dollar amounts, testimonial quotes, named sources, third-party citations.",
        "cta_prominence": "Repeat the CTA, use action-specific language, ensure it's on the approved list.",
        "scroll_depth_pull": "4-8 sections with benefit-oriented headings. Each section pulls to the next.",
        "lp_readability": "ZERO em dashes. Subhead under 120 chars. Short paragraphs (max 3 sentences). Sentences 13-18 words. Lots of line breaks for scannability.",
        "subject_line_power": "6-10 words, include a specific detail (number/name), avoid spam triggers.",
        "body_flow": "Short paragraphs (max 3 sentences). Clear paragraph breaks. Under 2000 chars.",
        "personalization": "Reference the reader's context (waitlist, prior action). Use 'you' frequently. Add time-specific details.",
    }
    return guidance.get(dim_name, "Improve this dimension specifically.")


def _select_relevant_facts(facts_data: dict, angle: str, content_type: str = "meta-ad") -> str:
    """Select facts most relevant to the given angle."""
    facts = facts_data.get("facts", [])
    lines = []

    # Always include pricing and core inclusions
    priority_categories = ["pricing", "inclusions", "savings", "exclusions"]

    # Angle-specific priorities
    angle_categories = {
        # Best for Pet angles
        "price-value": ["pricing", "savings"],
        "simplicity-clarity": ["inclusions", "how_it_works"],
        "safety-risk": ["inclusions", "exclusions"],
        "empathy-understanding": ["savings", "social_proof"],
        "outcome-results": ["savings", "social_proof"],
        "anti-insurance": ["exclusions", "social_proof"],
        # FarmThru angles
        "cause-purpose": ["positioning", "business_model", "farm_partners"],
        "transformation-storytelling": ["farm_partners", "product_quality", "social_proof"],
        "social-belonging": ["business_model", "social_proof", "farm_partners"],
        "quality-craft": ["product_quality", "farm_partners"],
        "transparency-safety": ["investment", "market", "business_model"],
        "empathy-founder": ["positioning", "farm_partners", "social_proof"],
        "urgency-scarcity": ["investment", "business_model"],
        "investment-thesis": ["investment", "market", "business_model"],
        "comparison-switching": ["product_quality", "business_model", "positioning"],
    }
    extra = angle_categories.get(angle, [])

    # Meta-ads must never include investment facts — they leak $50, Birchal, etc. into copy
    if content_type == "meta-ad":
        extra = [c for c in extra if c != "investment"]
        priority_categories = [c for c in priority_categories if c != "investment"]

    shown = set()
    for fact in facts:
        cat = fact.get("category", "")
        if cat in priority_categories or cat in extra:
            if fact["fact_id"] not in shown:
                conf = fact.get("confidence", "MEDIUM")
                lines.append(f"[{fact['fact_id']}] ({conf}) {fact['claim']}")
                shown.add(fact["fact_id"])

    return "\n".join(lines[:25])  # Cap at 25 facts to fit in context


def _call_llm(prompt: str, temperature: float = 0.7,
              system_context: str = None) -> str:
    """Call LLM to generate ad copy. Sonnet 4.6 via API with prompt caching.

    If system_context is provided, it's sent as a cached system prompt
    (identical for all candidates of the same ad). The prompt becomes
    just the variant-specific instruction.
    """
    # API (fast, reliable)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            kwargs = {
                "model": "claude-sonnet-4-6",
                "max_tokens": 2000,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_context:
                kwargs["system"] = [{
                    "type": "text",
                    "text": system_context,
                    "cache_control": {"type": "ephemeral"},
                }]
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            import sys
            print(f"API failed: {e}", file=sys.stderr)

    # CLI fallback
    import tempfile
    claude_path = os.path.expanduser("~/.local/bin/claude")
    tf_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tf:
            tf.write(prompt)
            tf_path = tf.name
        with open(tf_path) as pf:
            prompt_text = pf.read()
        result = subprocess.run(
            [claude_path, "--model", "opus", "--print", "-p", "-"],
            input=prompt_text,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        import sys
        print(f"CLI failed: {e}", file=sys.stderr)
    finally:
        if tf_path:
            try:
                os.unlink(tf_path)
            except OSError:
                pass

    return '{"error": "No LLM available"}'


def _parse_output(
    raw: str, angle: str, tactic: str, hook_type: str, funnel: str,
    content_type: str = "meta-ad",
) -> dict:
    """Parse LLM output into canonical format for any content type."""
    import re

    # Try to extract JSON from the response (handle nested objects for landing pages)
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            id_prefix = angle[:2].upper()
            seq = random.randint(100, 999)

            base = {
                "angle": angle,
                "tactic": tactic,
                "hook_type": hook_type,
                "funnel": funnel,
                "content_type": content_type,
                "creative_brief": data.get("creative_brief", ""),
                "generated_at": datetime.now().isoformat(),
            }

            if content_type == "landing-page":
                base["page_id"] = f"{id_prefix}-LP-{seq}"
                base["headline"] = data.get("headline", "")
                base["subhead"] = data.get("subhead", "")
                base["hero_copy"] = data.get("hero_copy", "")
                base["sections"] = data.get("sections", [])
                base["cta"] = data.get("cta", "Join the Waitlist")
            elif content_type == "email":
                base["email_id"] = f"{id_prefix}-EM-{seq}"
                base["subject"] = data.get("subject", "")
                base["preheader"] = data.get("preheader", "")
                base["body"] = data.get("body", "")
                base["cta"] = data.get("cta", "Join the Waitlist")
                base["sender_name"] = data.get("sender_name", "")
            else:  # meta-ad
                base["ad_id"] = f"{id_prefix}-{seq}"
                base["primary_text"] = data.get("primary_text", "")
                base["headline"] = data.get("headline", "")
                base["description"] = data.get("description", "")
                base["cta"] = data.get("cta", "Learn More")

            return base
        except json.JSONDecodeError:
            pass

    # Fallback: return error
    return {
        "ad_id": "ERROR",
        "angle": angle,
        "tactic": tactic,
        "hook_type": hook_type,
        "funnel": funnel,
        "content_type": content_type,
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


def _load_learnings(client_dir: Path, content_type: str) -> str:
    """Load learnings: common rules + content-type-specific patterns.

    Reads learnings.md (index/common rules) and learnings-{content_type}.md
    if it exists. This replaces the old 1600-char truncation approach — each
    file is compact and focused, so no truncation needed.
    """
    common_path = client_dir / "learnings.md"
    type_path = client_dir / f"learnings-{content_type}.md"

    parts = []
    if common_path.exists():
        parts.append(_load_text(common_path))
    if type_path.exists():
        parts.append(_load_text(type_path))

    combined = "\n\n".join(parts)
    # Safety cap at 4000 chars to avoid blowing up the prompt
    return combined[:4000]


def _load_text(path: Path) -> str:
    with open(path) as f:
        return f.read()
