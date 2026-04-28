"""
Writer — The mutable variant generator (the train.py analog).

This file generates new ad copy variants. The autonomous agent
can modify this file freely to improve generation strategy.

The writer does NOT import from engine/ — it never sees the scorer's
internals, rubric weights, or rule definitions.
"""

import json
import os
import re
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

    # Defensive: ADV-001 (founder-directed universal CSF safe-harbour gate)
    # requires the canonical line on every channel. The prompt instructs the
    # writer to include it but observation shows it sometimes drops the line on
    # improve/mutate runs that focus on hook punch. Auto-append rather than let
    # an otherwise-good variant score 0.0 / rewrite at the compliance gate.
    # Only applies to clients/configs that opt in via approve_csf_autoappend.
    config_for_check = _load_json(client_dir / "config.json")
    if (config_for_check.get("client_id") == "farm-thru"
            and content_type in ("meta-ad", "email", "landing-page")):
        ad = _ensure_csf_safeharbour(ad, content_type)

    return ad


_CSF_CANONICAL = "*Always consider the general CSF risk warning and offer document before investing."
# Require the FULL canonical line — loose paraphrase checks were passing DISC-001-banned
# wording ("See the general CSF risk warning + offer document") because the substring
# "general CSF risk warning" matched. The canonical asterisked line is the ONLY accepted
# form (ADV-001 + DISC-001); anything else fails compliance and should trigger auto-append.
_CSF_SHORT_PARAPHRASE_RE = re.compile(
    r"\*Always\s+consider\s+the\s+general\s+CSF\s+risk\s+warning\s+and\s+offer\s+document\s+before\s+investing",
    re.IGNORECASE,
)


def generate_hook_swap_variant(
    seed_ad: dict,
    hypothesis: dict,
    client_dir: Path,
    content_type: str = "meta-ad",
) -> dict:
    """Generate a hook-swap variant of a seed ad.

    Holds body (paragraphs 2+), description, CTA, and the asterisked CSF
    footnote VERBATIM from the seed. Generates ONLY:
    - A new opening paragraph (line 1 of primary_text — the hook)
    - A new headline

    Driven by a hypothesis dict (from engine.hypothesis_generator). Each
    variant is a deliberate test of one hypothesis about what makes the seed
    work — variant scores then tell us whether the hypothesised element was
    actually carrying the win.

    Args:
        seed_ad: The high-performing seed ad (canonical JSON format)
        hypothesis: Structured hypothesis dict with keys: id, claim,
            load_bearing_element, alternative_hook_seed,
            alternative_headline_seed, expected_direction
        client_dir: Path to client config directory
        content_type: Content type (currently only meta-ad supported)

    Returns:
        New ad in canonical format. Body / description / CTA / CSF footnote
        identical to seed; only opening paragraph + headline are new. Carries
        _hypothesis_id and _hypothesis_claim metadata fields for traceability.
    """
    if content_type != "meta-ad":
        raise NotImplementedError(
            f"hook_swap is meta-ad-only for now (got {content_type}). "
            "LP/email body locking would need a different segmentation."
        )

    config = _load_json(client_dir / "config.json")
    tone = _load_text(client_dir / "tone.md")
    learnings = _load_learnings(client_dir, content_type)
    constraints = _resolve_platform_constraints(config, content_type)
    approved_ctas = _resolve_approved_ctas(config, content_type, seed_ad)

    seed_body_paragraphs = (seed_ad.get("primary_text") or "").split("\n\n")
    if len(seed_body_paragraphs) < 2:
        # Body is too short to safely lock — fall back to keeping all of it
        # except the first sentence.
        seed_body_locked = ""
    else:
        # Keep paragraphs 2..end. The first paragraph is the hook we're swapping.
        seed_body_locked = "\n\n".join(p for p in seed_body_paragraphs[1:] if p.strip())

    seed_block = (
        f"SEED HEADLINE: {seed_ad.get('headline', '')}\n"
        f"SEED OPENING PARAGRAPH (this is what you are REPLACING):\n"
        f"{seed_body_paragraphs[0] if seed_body_paragraphs else ''}\n\n"
        f"BODY YOU MUST PRESERVE VERBATIM (paragraphs 2 onward, including the "
        f"asterisked CSF footnote):\n---\n{seed_body_locked}\n---\n"
        f"SEED DESCRIPTION (preserve verbatim): {seed_ad.get('description', '')}\n"
        f"SEED CTA (preserve verbatim): {seed_ad.get('cta', '')}"
    )

    hypothesis_block = (
        f"HYPOTHESIS BEING TESTED ({hypothesis.get('id', 'H?')})\n"
        f"Claim: {hypothesis.get('claim', '')}\n"
        f"Load-bearing element of seed: {hypothesis.get('load_bearing_element', '')}\n"
        f"Probe direction for new hook: {hypothesis.get('alternative_hook_seed', '')}\n"
        f"Probe direction for new headline: {hypothesis.get('alternative_headline_seed', '')}\n"
        f"Expected direction (what we predict): {hypothesis.get('expected_direction', 'unknown')}"
    )

    headline_max = constraints.get("headline_max_chars", 40)
    primary_max = constraints.get("primary_text_max_chars", 500)

    instruction = f"""You are doing a HOOK-SWAP probe on a high-performing ad.

Your job is narrow:
1. Write a NEW opening paragraph (1-3 short sentences, ideally one) that replaces the seed's first paragraph and tests the hypothesis below.
2. Write a NEW headline (≤{headline_max} characters, sentence case).
3. Do NOT touch the body, description, CTA, or CSF footnote — those are locked.

The body that follows your hook is FIXED, so your new opening must flow naturally INTO that body. Read the locked body before writing.

{seed_block}

{hypothesis_block}

CONSTRAINTS:
- New opening paragraph: max ~3 sentences, must connect smoothly to the locked body
- New headline: ≤{headline_max} chars, sentence case, no Title Case, no em-dashes
- Total primary_text (your new opening + locked body) must be ≤{primary_max} chars
- CTA must remain "{seed_ad.get('cta', '')}"
- Description must remain "{seed_ad.get('description', '')}"

CLIENT TONE GUARDRAILS:
{tone[:500]}

OUTPUT FORMAT (respond with ONLY this JSON, no other text):
{{
  "new_opening_paragraph": "your replacement for line 1",
  "new_headline": "your replacement headline"
}}"""

    raw = _call_llm(instruction, temperature=0.7)

    parsed = _parse_hook_swap_output(raw)
    if not parsed:
        # Fall back: retry once with a stricter prompt
        retry = instruction + "\n\nIMPORTANT: respond with ONLY a JSON object containing exactly the keys 'new_opening_paragraph' and 'new_headline'. No commentary."
        raw = _call_llm(retry, temperature=0.5)
        parsed = _parse_hook_swap_output(raw)
    if not parsed:
        raise RuntimeError(f"hook_swap: could not parse hypothesis-driven output for {hypothesis.get('id')}")

    new_opening = parsed["new_opening_paragraph"].strip()
    new_headline = parsed["new_headline"].strip()

    # Headline length defense — Sonnet sometimes overshoots the constraint.
    # Single retry with a tighter framing before falling back to a hard truncation
    # at the last word boundary. Keep variant shippable rather than failing.
    if len(new_headline) > headline_max:
        retry_short = (
            f"Your previous headline was {len(new_headline)} chars; the limit is {headline_max}. "
            f"Rewrite the headline ONLY (≤{headline_max} chars). Respond with JSON: "
            f'{{"new_headline": "..."}}'
        )
        retry_raw = _call_llm(retry_short, temperature=0.4)
        try:
            data = json.loads(retry_raw)
            if isinstance(data, dict) and data.get("new_headline"):
                candidate = data["new_headline"].strip()
                if len(candidate) <= headline_max:
                    new_headline = candidate
        except (json.JSONDecodeError, AttributeError):
            pass
        # Hard fallback — truncate at last word boundary if still over
        if len(new_headline) > headline_max:
            truncated = new_headline[:headline_max].rsplit(" ", 1)[0]
            new_headline = truncated.rstrip(",.;:") if truncated else new_headline[:headline_max]

    new_primary = new_opening + ("\n\n" + seed_body_locked if seed_body_locked else "")

    variant = dict(seed_ad)
    variant["primary_text"] = new_primary
    variant["headline"] = new_headline
    variant["description"] = seed_ad.get("description", "")
    variant["cta"] = seed_ad.get("cta", "")
    # Generation metadata — strip any prior _ad_id stamping; caller (hill_climb_from_seed)
    # will assign LIVE-VARIANT-NN identifiers based on rank.
    variant.pop("ad_id", None)
    variant["_hypothesis_id"] = hypothesis.get("id")
    variant["_hypothesis_claim"] = hypothesis.get("claim")
    variant["_hypothesis_element"] = hypothesis.get("load_bearing_element")
    variant["_hypothesis_expected"] = hypothesis.get("expected_direction")
    variant["_mode"] = "hook_swap"
    variant["generated_at"] = datetime.now(tz=None).isoformat()

    # Defensive CSF re-check. The locked body (paragraphs 2+ from the seed)
    # should already include the asterisked CSF footnote, so this is a no-op
    # in normal operation. The call exists as belt-and-suspenders for the
    # single-paragraph-seed edge case (where seed_body_locked is empty and
    # the variant is effectively new copy without a footnote).
    variant = _ensure_csf_safeharbour(variant, content_type)
    return variant


def _resolve_platform_constraints(config: dict, content_type: str) -> dict:
    pc = config.get("platform_constraints", {})
    if isinstance(pc, dict) and content_type in pc:
        return pc[content_type]
    return pc if isinstance(pc, dict) else {}


def _resolve_approved_ctas(config: dict, content_type: str, seed_ad: dict) -> list:
    approved = config.get("approved_ctas", [])
    if isinstance(approved, dict):
        approved = approved.get(content_type, approved.get("meta-ad", []))
    if isinstance(approved, dict):
        # Flatten phase buckets
        flattened = []
        for v in approved.values():
            if isinstance(v, list):
                flattened.extend(v)
        approved = flattened
    return approved


_HOOK_SWAP_JSON_RE = re.compile(r"\{[\s\S]*?\"new_opening_paragraph\"[\s\S]*?\}")


def _parse_hook_swap_output(raw):
    if not raw:
        return None
    # Reject top-level JSON arrays — valid output is always a dict.
    raw_stripped = raw.strip()
    if raw_stripped.startswith("["):
        return None
    # Strip markdown fences if present
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
    candidates = [raw]
    if fence_match:
        candidates.insert(0, fence_match.group(1))
    obj_match = _HOOK_SWAP_JSON_RE.search(raw)
    if obj_match:
        candidates.insert(0, obj_match.group(0))
    for c in candidates:
        try:
            data = json.loads(c)
            if isinstance(data, dict) and "new_opening_paragraph" in data and "new_headline" in data:
                return data
        except json.JSONDecodeError:
            continue
    return None


def _ensure_csf_safeharbour(ad: dict, content_type: str) -> dict:
    """Append the canonical CSF safe-harbour footnote if missing.

    ADV-001 (founder-directed 2026-04-27) requires this on every channel. If
    the writer drops it, append rather than fail the variant — the asterisked
    final-paragraph placement is what csf_placement rewards.
    """
    body_field = "primary_text" if content_type == "meta-ad" else (
        "body" if content_type == "email" else "hero_copy"
    )
    body = ad.get(body_field, "")
    if not body:
        return ad
    if _CSF_SHORT_PARAPHRASE_RE.search(body):
        return ad
    # Append on a new paragraph; preserve trailing whitespace handling.
    ad[body_field] = body.rstrip() + "\n\n" + _CSF_CANONICAL
    ad.setdefault("_auto_appends", []).append("csf_safeharbour")
    return ad


def build_synthetic_hypothesis_from_dim(dim_name: str, seed_ad: dict) -> dict:
    """Build a minimal hypothesis dict from a single weak rubric dimension.

    Used when routing random-mode targeted hill-climbing to hook_swap: instead of
    rewriting the entire primary_text (which loses locked high-scoring dims), we
    produce a hook_swap variant whose instruction is derived from the known dimension
    improvement guidance. This preserves the body, description, CTA, and CSF footnote
    from the seed while generating a new opening + headline targeting the weak dim.

    The returned dict is compatible with generate_hook_swap_variant's hypothesis arg.
    """
    guidance = _dimension_improvement_guidance(dim_name)
    # Map dimension names to hook directions that commonly target them
    _dim_to_hook_direction = {
        "scroll_stop_hook": "curiosity-gap or story-moment opener that avoids generic framing",
        "motivation_match": "emotionally resonant opener that names the felt need, not the product",
        "angle_clarity": "opener that states ONE clear proposition and removes all competing themes",
        "specificity": "opener that leads with a concrete detail (number, name, location, or action)",
        "objection_preemption": "opener that directly addresses the reader's most likely hesitation",
        "cta_clarity": "opener that makes the next action and its consequence vivid",
        "ownership_framing": "opener that frames the opportunity as identity/belonging, not transaction",
        "scarcity_register": "opener that implies future scarcity without using hard-sell urgency language",
        "founder_voice": "opener with a specific founder-voice moment ('We've built', 'We're about to')",
        "differentiation": "opener that uses entirely different language from the existing body",
        "tactic_execution": "opener that clearly establishes the Hook → Proof → Bridge → CTA structure",
    }
    hook_direction = _dim_to_hook_direction.get(
        dim_name,
        f"opener specifically engineered to lift the '{dim_name}' rubric dimension",
    )
    seed_id = seed_ad.get("ad_id", "seed")
    return {
        "id": f"SYN-{dim_name[:12].upper()}",
        "claim": (
            f"The '{dim_name}' dimension is underperforming in {seed_id}. "
            f"A new opening that targets this dimension should lift the composite "
            f"without degrading the locked body elements."
        ),
        "load_bearing_element": dim_name,
        "test": f"Replace the opening paragraph with one that maximises '{dim_name}'. Keep all other content identical.",
        "alternative_hook_seed": hook_direction,
        "alternative_headline_seed": f"New headline that reinforces the '{dim_name}' improvement",
        "expected_direction": "performance_lifts",
        "confidence_prior": 0.55,
        "knowledge_used": [f"dimension/{dim_name}", "targeted_improvement_guidance"],
        "_synthetic": True,
    }


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
        rules = _append_content_type_rules(rules, config, content_type)
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

    rules = _append_content_type_rules(rules, config, content_type)
    return _append_compliance_summary(rules, config, content_type)


def _append_content_type_rules(rules_text: str, config: dict, content_type: str) -> str:
    """Append client rules that are scoped to a single content_type via the
    `content_types` field in clients/<slug>/rules.json. Keeps meta-ad-only
    rules out of LP / email prompts and vice versa. Currently surfaces just
    the FMTH-NO-DOLLAR-METAAD rule because it materially changes generation
    strategy (writer must paraphrase $ amounts) and is otherwise easy to
    miss.
    """
    client_id = config.get("client_id", "")
    if client_id != "farm-thru" or content_type != "meta-ad":
        return rules_text

    return rules_text + (
        "\n- NEVER include explicit dollar amounts ($5, $50, $10K, $130B etc.) "
        "in primary_text, headline, or description. Reference dollar values "
        "via prose like 'a small refundable deposit' or 'tens of thousands' "
        "instead. [FMTH-NO-DOLLAR-METAAD — Meta financial-vertical platform "
        "policy frequently rejects ads with explicit $ amounts; hard-block.]"
    )


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

    elif content_type == "sms":
        single_seg = constraints.get("body_single_segment_max", 160)
        body_max = constraints.get("body_max_chars", 320)
        constraints_text = f"""- Body: target single segment ({single_seg} chars expanded), hard max {body_max}
- Count the EXPANDED merge tag, not the literal {{{{birchal_url}}}}
- Platform: sms
- One job only — no compound messages"""
        output_format = """{
  "body": "the SMS message text (single segment ideal)",
  "purpose": "round-opens-vip | purchase-confirmation | reminder",
  "audience": "vip-investors | waitlist | customers | all-subscribers",
  "creative_brief": "1 sentence on send context (manual via SMS provider, etc.)"
}"""
        content_label = "SMS variant"
        config_extra = config.get("prompt_extra_rules", {}).get("sms", "")
        if config_extra:
            extra_rules = config_extra
        else:
            extra_rules = """- Single segment (≤160 chars expanded) when possible
- Marketing sends: end with 'Reply STOP to opt out.'
- Investment-context SMS: include URL OR short paraphrase 'general CSF risk warning'
- No em-dashes, no 'priority', no explicit dollar amounts
- One job per SMS — never combine confirmation + drive-to-link"""

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
        "scroll_stop_hook": "CFE pre-campaign gold standard (LIVE-FMTH-NEVER-DONE, $2 CPL): curiosity-gap narrow-bound with category + geo = 'We're about to open something up that's never been done with a grocery store in Australia.' PR #125 H1 CONFIRMED: removing the bound cost -0.19 composite. For non-CFE: named person + action ('Sarah walked in last Tuesday'), story moment ('Yesterday I opened...'), quoted objection (start with \"). Strong: question (end with ?), number first ('14 farms...'). NEVER generic statements.",
        "cta_clarity": "State the action AND its consequence: 'Leave your email -- we'll tell you the moment it goes live.' The consequence removes uncertainty and lifts opt-in rate. CTA button alone scores 2; action + outcome body sentence scores 4-5. Pattern from LIVE-FMTH-NEVER-DONE ($2 CPL).",
        "ownership_framing": "Reframe investment as identity, not transaction. 'Own a piece of', 'be part of what we've built' -- never 'invest from $X' as the lead. PR #125 H2 CONFIRMED: removing ownership framing cost -0.19 composite. Two ownership phrases per ad beats one.",
        "scarcity_register": "Soft / future scarcity only: 'opens soon', 'first in gets first access', 'we'll tell you the moment'. NEVER 'act now', 'last chance', 'limited time only' -- hard scarcity before a CFE offer document exists risks ACL misleading conduct (s18) and signals desperation to trained investors.",
        "founder_voice": "Use 'we've built', 'we're about to', 'we made' in BODY paragraph 2, not opening line. PR #125 H3 DISCONFIRMED founder voice as opener (-0.18 composite vs curiosity gap). Past-tense build language earns authority as a support layer; it cannot carry the hook alone.",
        "csf_placement": "Asterisked footnote in FINAL paragraph only. Never mid-body or in the CTA sentence. Pattern: body ends with outcome CTA, then newline, then '* Always consider the general CSF risk warning and offer document before investing.' LIVE-FMTH-NEVER-DONE uses this pattern and scores 5/5 on csf_placement.",
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
