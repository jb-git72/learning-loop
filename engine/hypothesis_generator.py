"""Hypothesis Generator — turns a seed ad into structured falsifiable hypotheses
about why it works, plus a probe (hook-swap test) for each.

Used by hill_climb_from_seed.py in `--hypothesis-driven` mode. Each hypothesis
gets one hook_swap variant; the resulting variant scores tell us whether the
hypothesised load-bearing element actually carries the seed.

Output format (strict JSON list):
    [
      {
        "id": "H1",
        "claim": "<plain-English thesis about what makes the seed work>",
        "load_bearing_element": "<which element the hypothesis attributes the win to>",
        "test": "<concrete instruction for the hook-swap probe>",
        "alternative_hook_seed": "<one-sentence direction for the new line 1>",
        "alternative_headline_seed": "<one-line direction for the new headline>",
        "expected_direction": "performance_drops" | "performance_holds" | "performance_lifts",
        "confidence_prior": 0.0-1.0,
        "knowledge_used": ["hooks/<id>", "tactics/<id>", "learnings", "benchmarks", ...]
      },
      ...
    ]
"""
from __future__ import annotations

import json
import re
from pathlib import Path


def generate_hypotheses(
    seed_ad: dict,
    client_config: dict,
    client_dir: Path,
    shared_dir: Path,
    n: int = 4,
    use_llm: bool = True,
) -> list[dict]:
    """Generate N structured hypotheses about why the seed works + a probe per
    hypothesis. Falls back to a deterministic template list when use_llm=False
    so the loop still runs in --no-llm mode."""
    if not use_llm:
        return _fallback_hypotheses(seed_ad, n)

    hooks = _load_hooks(shared_dir)
    tactics = _load_tactics(shared_dir)
    playbook = _load_playbook(shared_dir, client_config)
    learnings = _load_learnings(client_dir, content_type=seed_ad.get("content_type", "meta-ad"))

    prompt = _build_prompt(
        seed_ad=seed_ad,
        client_config=client_config,
        hooks=hooks,
        tactics=tactics,
        playbook=playbook,
        learnings=learnings,
        n=n,
    )

    raw = _call_llm_for_hypotheses(prompt)
    parsed = _parse_hypothesis_json(raw)
    if not parsed:
        return _fallback_hypotheses(seed_ad, n)
    # Cap at n and stamp IDs
    out = []
    for i, h in enumerate(parsed[:n], start=1):
        h["id"] = h.get("id") or f"H{i}"
        out.append(h)
    return out


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_prompt(seed_ad, client_config, hooks, tactics, playbook, learnings, n) -> str:
    seed_block = _format_seed(seed_ad)
    hooks_block = _format_hooks(hooks)
    tactics_block = _format_tactics(tactics)
    playbook_block = _format_playbook(playbook)
    client_block = _format_client_context(client_config)

    return f"""You are a senior performance-marketing strategist analysing a high-performing ad.
The ad is shipping low-cost leads in market. Your job is to identify the LOAD-BEARING ELEMENTS that make it work and propose falsifiable probes that would test each one.

You will return EXACTLY {n} structured hypotheses as a strict JSON array. Each hypothesis names ONE specific element of the seed (a hook pattern, a frame, a structural choice, a piece of language) and proposes a hook-swap probe — a new opening paragraph + headline that holds everything else constant but breaks/replaces that element.

PRINCIPLE: Most ad-variant work fails because it changes too many things at once. A good probe holds the body, description, CTA, and CSF footnote IDENTICAL to the seed and varies ONLY the opening hook + headline. The variant's score then tells us whether the hypothesised element was actually carrying the win.

=== SEED AD ===
{seed_block}

=== CLIENT CONTEXT ===
{client_block}

=== HOOK ARCHETYPES (with benchmark hit rates) ===
{hooks_block}

=== TACTICS ===
{tactics_block}

=== INDUSTRY PLAYBOOK ===
{playbook_block}

=== CLIENT LEARNINGS ===
{learnings}

=== OUTPUT FORMAT ===
Return ONLY a JSON array of {n} hypotheses. Each hypothesis MUST include:

- "id": "H1" through "H{n}"
- "claim": one-sentence thesis about what specific element of the seed is doing the work
- "load_bearing_element": what part of the ad the hypothesis attributes the win to (e.g. "narrow-novelty bound", "ownership framing", "cadence-of-three proof", "founder voice", "soft scarcity", "outcome-stated CTA", "asterisked CSF placement")
- "test": concrete instruction for the probe — "swap line 1 to X to break Y"
- "alternative_hook_seed": one-sentence DIRECTION for the new opening line (NOT the actual line — the writer will write it)
- "alternative_headline_seed": one-line direction for the new headline
- "expected_direction": "performance_drops" if breaking the element should hurt | "performance_holds" if the element doesn't matter | "performance_lifts" if the proposed alt is genuinely stronger
- "confidence_prior": 0.0-1.0 — your confidence in expected_direction before seeing data
- "knowledge_used": list of references that informed this hypothesis (e.g. ["hooks/curiosity_gap", "tactics/pas", "learnings", "benchmarks"])

Diversity rules:
- Hypotheses must cover DIFFERENT elements — not 4 variations on the same idea
- At least ONE hypothesis must propose breaking a hypothesised load-bearing element (expected_direction: performance_drops)
- At least ONE hypothesis must propose an alternative that the priors suggest could LIFT performance (expected_direction: performance_lifts)
- Avoid pure cosmetic swaps. Each test must change the ad's *strategic* hook frame, not just the wording.

Return ONLY the JSON array — no preamble, no commentary, no code fences."""


def _format_seed(ad: dict) -> str:
    fields = []
    for k in ("primary_text", "headline", "description", "cta", "angle", "campaign_phase"):
        v = ad.get(k, "")
        if v:
            fields.append(f"{k}: {v}")
    return "\n".join(fields)


def _format_client_context(config: dict) -> str:
    sc = config.get("scoring_context", {})
    parts = []
    if sc.get("product"):
        parts.append(f"Product: {sc['product'][:300]}")
    if sc.get("audience"):
        parts.append(f"Audience: {sc['audience'][:400]}")
    if sc.get("brand_values"):
        parts.append(f"Brand values: {sc['brand_values'][:200]}")
    return "\n".join(parts)


def _format_hooks(hooks: list) -> str:
    """One-line summary per hook — id, hit-rate, what it does."""
    lines = []
    for h in hooks:
        hr = h.get("benchmark_hit_rate", 0)
        line = f"- {h.get('id')}: hit-rate {hr:.0%}. {h.get('template', '')[:120]}"
        lines.append(line)
    return "\n".join(lines)


def _format_tactics(tactics: list) -> str:
    lines = []
    for t in tactics:
        lines.append(f"- {t.get('id')}: {t.get('structure', '')[:120]}")
    return "\n".join(lines)


def _format_playbook(playbook) -> str:
    if not playbook:
        return "(no industry playbook for this client)"
    parts = []
    for k in ("hook_priors", "best_angles", "audience_motivations", "scarcity_norms"):
        v = playbook.get(k)
        if v:
            parts.append(f"{k}: {json.dumps(v)[:300]}")
    return "\n".join(parts) or "(playbook present but empty for relevant fields)"


def _load_hooks(shared_dir: Path) -> list:
    p = shared_dir / "hooks.json"
    if not p.is_file():
        return []
    data = json.loads(p.read_text())
    return data.get("hooks", data) if isinstance(data, dict) else data


def _load_tactics(shared_dir: Path) -> list:
    p = shared_dir / "tactics.json"
    if not p.is_file():
        return []
    data = json.loads(p.read_text())
    return data.get("tactics", data) if isinstance(data, dict) else data


def _load_playbook(shared_dir: Path, client_config: dict):
    industry = (client_config.get("industry") or "").lower().replace(" ", "-")
    if not industry:
        return None
    candidates = [
        shared_dir / "playbooks" / f"{industry}.json",
        shared_dir / "playbooks" / f"{industry}-grocery.json",
    ]
    for p in candidates:
        if p.is_file():
            return json.loads(p.read_text())
    return None


def _load_learnings(client_dir: Path, content_type: str) -> str:
    """Concatenate common learnings.md + content-type-specific learnings."""
    parts = []
    base = client_dir / "learnings.md"
    if base.is_file():
        parts.append(base.read_text())
    typed = client_dir / f"learnings-{content_type}.md"
    if typed.is_file():
        parts.append(typed.read_text())
    return "\n\n".join(parts)[:4000]


# ---------------------------------------------------------------------------
# LLM call (reuses writer.py's _call_llm pattern via lazy import to avoid
# circular dep in tests)
# ---------------------------------------------------------------------------

def _call_llm_for_hypotheses(prompt: str) -> str:
    """Call Sonnet to produce the JSON hypothesis array."""
    from writer import _call_llm
    # Hypothesis generation benefits from low temperature — we want diverse but
    # rigorous structural analysis, not creative riffing.
    return _call_llm(prompt, temperature=0.4)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)
_ARRAY_RE = re.compile(r"\[\s*\{[\s\S]*\}\s*\]")


def _parse_hypothesis_json(raw: str) -> list[dict]:
    if not raw:
        return []

    def _coerce(data):
        # Sonnet sometimes returns a single hypothesis dict instead of a list.
        # Wrap it so downstream code can assume list-of-dicts.
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return data
        return None

    # Try direct parse first
    try:
        data = json.loads(raw)
        coerced = _coerce(data)
        if coerced is not None:
            return coerced
    except json.JSONDecodeError:
        pass
    # Strip markdown fences
    m = _JSON_FENCE_RE.search(raw)
    if m:
        try:
            data = json.loads(m.group(1))
            coerced = _coerce(data)
            if coerced is not None:
                return coerced
        except json.JSONDecodeError:
            pass
    # Last-ditch: regex out the array
    m = _ARRAY_RE.search(raw)
    if m:
        try:
            data = json.loads(m.group(0))
            coerced = _coerce(data)
            if coerced is not None:
                return coerced
        except json.JSONDecodeError:
            pass
    return []


# ---------------------------------------------------------------------------
# Deterministic fallback (no-LLM mode + LLM-failure recovery)
# ---------------------------------------------------------------------------

def _fallback_hypotheses(seed_ad: dict, n: int) -> list[dict]:
    """Deterministic hypothesis list. Used when LLM is disabled or fails to
    return parseable JSON. Generic enough to apply to most ads but obviously
    weaker than the LLM-driven variant."""
    base = [
        {
            "id": "H1",
            "claim": "The opening hook is the load-bearing element. Without it the body proof can't earn attention.",
            "load_bearing_element": "scroll_stop_hook",
            "test": "Replace the curiosity-gap opener with a direct declarative statement of the offer.",
            "alternative_hook_seed": "Open with a direct statement of what's being offered, no curiosity gap.",
            "alternative_headline_seed": "Direct headline naming the offer without intrigue.",
            "expected_direction": "performance_drops",
            "confidence_prior": 0.7,
            "knowledge_used": ["hooks/curiosity_gap"],
        },
        {
            "id": "H2",
            "claim": "Identity-level framing (ownership) outperforms transactional framing in CFE pre-campaign copy.",
            "load_bearing_element": "ownership_framing",
            "test": "Replace ownership language with outcome/return language to test which converts.",
            "alternative_hook_seed": "Lead with the benefit / outcome rather than identity / belonging.",
            "alternative_headline_seed": "Outcome-led headline (results, returns) — not 'own a piece' framing.",
            "expected_direction": "performance_drops",
            "confidence_prior": 0.6,
            "knowledge_used": ["learnings", "ownership_framing_rubric"],
        },
        {
            "id": "H3",
            "claim": "Soft / future-tense scarcity is what makes the close-out feel like a queue forming, not a panic.",
            "load_bearing_element": "soft_scarcity",
            "test": "Strip scarcity entirely (no opens-soon language). Test whether neutral pacing converts.",
            "alternative_hook_seed": "Lead with the proof, no scarcity / waitlist framing in the opener.",
            "alternative_headline_seed": "Headline with no urgency or scarcity signal.",
            "expected_direction": "performance_drops",
            "confidence_prior": 0.5,
            "knowledge_used": ["scarcity_register_rubric"],
        },
        {
            "id": "H4",
            "claim": "A statistic-led hook (specific number first) could outperform the curiosity-gap opener.",
            "load_bearing_element": "scroll_stop_hook",
            "test": "Open with a specific number / dollar amount and let the reader infer the angle.",
            "alternative_hook_seed": "Open with a concrete statistic that hints at the offer without explaining it.",
            "alternative_headline_seed": "Number-led headline.",
            "expected_direction": "performance_lifts",
            "confidence_prior": 0.45,
            "knowledge_used": ["hooks/statistic", "benchmarks"],
        },
    ]
    return base[:n]
