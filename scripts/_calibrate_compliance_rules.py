#!/usr/bin/env python3
"""One-shot calibration: rewrite prompts/scopes for the 5 noisy CSF rules.

Surgical edits informed by the 2026-04-26 FMTH dry-run + agent observations.
Run once; commit the diff; delete.
"""

from __future__ import annotations

import json
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent.parent / "shared" / "regulatory" / "csf-australia" / "compliance_rules.json"


# Rule_id → fields to patch. Only listed fields are modified.
PATCHES: dict[str, dict] = {
    "MISL-001": {
        "llm_prompt": (
            "Read this CSF marketing copy or offer document content. "
            "Identify any statement of present or past fact (revenue, customer count, "
            "partnerships, awards, regulatory approvals, technical capability, market "
            "size, growth metrics) that is presented as definite. For each, assess "
            "whether it is plausible AS WRITTEN or whether it appears: "
            "(a) internally inconsistent with other claims in the same copy; "
            "(b) using vague proxies for harder facts ('thousands of users' where "
            "context implies registrations not active users); "
            "(c) materially time-stale (e.g. presenting a 2-year-old figure as current); "
            "(d) a half-truth (e.g. 'partnered with [BigCo]' where 'partnership' is a "
            "single pilot).\n\n"
            "**On future dates** (today's date is provided above): a stated FUTURE date "
            "for a scheduled event ('the CSF round opens 23 June 2026 on Birchal') is "
            "NOT stale, speculative, or misleading if today's date precedes it AND a "
            "credible operational reference is given (intermediary platform, venue, "
            "registered launch). Treat such dates as legitimate forward scheduling. "
            "Only flag dates if they are internally inconsistent (e.g. company claims "
            "to have launched in 2030 when it's earlier), unverifiable, or stated as "
            "completed events when they are still in the future.\n\n"
            "Pass if all factual claims are concrete, internally consistent, and "
            "plausibly current (or plausibly scheduled, for future references).\n\n"
            "Return JSON: {\"pass\": <bool>, \"evidence\": \"<exact quote if fail>\", "
            "\"reason\": \"<brief>\"}"
        )
    },
    "MISL-004": {
        "llm_prompt": (
            "Read this CSF copy.\n\n"
            "**Step 1 — gate**: Does the copy contain ANY explicit forecast, target, "
            "or projection? A forecast is a forward-looking QUANTITATIVE claim about "
            "future financial outcomes: revenue, profit, customer count, growth %, "
            "valuation, ARR, market share, etc. Marketing language about access "
            "('priority access', 'first access', 'reserve your spot', 'VIP early "
            "access') is process scheduling, NOT a forecast. Operational descriptions "
            "of current state ('15+ partner farms') are not forecasts.\n\n"
            "If no forecast is present in the copy, return immediately: "
            "{\"pass\": true, \"reason\": \"no forecasts present in copy\"}\n\n"
            "**Step 2 — only if a forecast IS present**: For each forecast, does the "
            "copy state nearby (a) the timeframe, (b) the key assumptions, (c) the "
            "methodology or basis (internal model, independent expert report, "
            "contracted revenue, signed LOIs)? Bare numbers ('We will hit $5M ARR') "
            "without basis fail. Numbers with at least timeframe + assumption + method "
            "pass. Speculative forecasts based only on hypotheticals fail under "
            "RG 261.200.\n\n"
            "Return JSON: {\"pass\": <bool>, \"evidence\": \"<exact quote if fail>\", "
            "\"reason\": \"<brief>\"}"
        )
    },
    "ADV-017": {
        # Narrow scope: RG 261.104-105 is about issuer comments on the CSF
        # intermediary's communication facility (Birchal-style Q&A). It does
        # NOT cover landing pages, emails, social posts, or meta ads.
        "scope": {
            "content_types": ["offer-document"],
            "phase": "during-offer",
            "applies_to": "issuer",
        }
    },
    "ADV-006": {
        "llm_prompt": (
            "Read this CSF marketing copy. Does it overstate or give unbalanced "
            "emphasis to potential benefits (returns, growth, upside, traction, "
            "valuation, market size) without comparable prominence given to risks "
            "(loss of capital, illiquidity, early-stage, speculative)?\n\n"
            "**Length-aware threshold**: This rule applies primarily to long-form "
            "copy (landing pages, full-length emails > ~250 words). For short-form "
            "(Meta ads, social posts, brief drip emails < ~250 words), a footer-style "
            "CSF risk warning at the end IS proportionate — these formats can't carry "
            "extended risk discussion without losing all marketing function. Flag "
            "short-form only if the copy makes affirmative benefit claims (returns, "
            "growth, profit) without ANY risk acknowledgement at all.\n\n"
            "**Long-form bar**: 90%+ benefits with only a one-line footer warning is "
            "unbalanced. The body should mention specific risks (capital loss, "
            "illiquidity, speculative early-stage nature) at least once with prose "
            "comparable to any single benefit claim.\n\n"
            "Return JSON: {\"pass\": <bool>, \"evidence\": \"<exact quote if fail>\", "
            "\"reason\": \"<brief explanation of the imbalance>\"}"
        )
    },
    "MISL-002": {
        "llm_prompt": (
            "Read this CSF copy. Are there any statements that disclose only part of "
            "a material fact and thereby create a misleading impression?\n\n"
            "**Common patterns to flag**:\n"
            "- One-off or peak figures presented as current run-rate "
            "(e.g. citing best-quarter revenue as ongoing).\n"
            "- Partnerships named without disclosing the relationship is a single pilot, "
            "expired, terminated, or non-exclusive when context implies otherwise.\n"
            "- 'Profitable' / 'breakeven' for a single quarter without context.\n"
            "- Growth % from a tiny base presented as scaled traction.\n"
            "- **Unstable / approximate numbers presented as definite headline figures** — "
            "e.g. headline says '15+ partner farms' or '15 farms' as a confirmed number, "
            "but body or FAQ admits 'around 15 to 20', 'approximate', 'fluctuates', or "
            "'depending on season'. The headline framing strips uncertainty disclosed "
            "elsewhere in the same copy.\n"
            "- Vague proxies for harder facts ('thousands of users' where context "
            "implies waitlist signups, not paying customers).\n\n"
            "Pass if all material facts are presented with their qualifications and "
            "context. The same numeric claim appearing in two formats with one "
            "qualified and one definite is a fail.\n\n"
            "Return JSON: {\"pass\": <bool>, \"evidence\": \"<exact quote if fail>\", "
            "\"reason\": \"<brief>\"}"
        )
    },
    "ADV-004": {
        "llm_prompt": (
            "Read this marketing copy. Does it contain any FORWARD-LOOKING FINANCIAL "
            "statement (forecast, growth target, expected return, projected revenue, "
            "future valuation, profitability projection, ARR target) WITHOUT stating "
            "supporting assumptions, basis, or evidence?\n\n"
            "**What counts as forward-looking financial**: a quantitative or directional "
            "claim about future FINANCIAL outcomes — revenue, profit, valuation, "
            "growth %, ARR, returns to investors.\n\n"
            "**What does NOT count** (do NOT flag these):\n"
            "- Marketing/operational access language ('priority access', 'first access "
            "to invest', 'VIP early access', 'reserve your spot') — describes process "
            "timing, not a financial outcome.\n"
            "- Descriptive present-state claims ('15+ named farms', 'Brookvale hub "
            "Mon-Fri') — not forward-looking.\n"
            "- Mission/vision statements ('we want to pay farmers fairly') — not "
            "quantitative financial.\n"
            "- Scheduling references ('round opens 23 June 2026') — not a forecast.\n\n"
            "Pass if the copy makes no forward-looking financial claims, OR every such "
            "claim is paired with stated assumptions/basis/evidence.\n\n"
            "Return JSON: {\"pass\": <bool>, \"evidence\": \"<exact quote if fail>\", "
            "\"reason\": \"<brief explanation>\"}"
        )
    },
}


def main() -> int:
    with open(RULES_PATH) as f:
        data = json.load(f)

    rule_index = {r["rule_id"]: r for r in data["rules"]}
    missing = [rid for rid in PATCHES if rid not in rule_index]
    if missing:
        raise SystemExit(f"Patch references missing rule IDs: {missing}")

    for rid, patch in PATCHES.items():
        rule = rule_index[rid]
        for field, value in patch.items():
            rule[field] = value
        print(f"  patched {rid}: fields={sorted(patch.keys())}")

    data["last_updated"] = "2026-04-26"
    with open(RULES_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {RULES_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
