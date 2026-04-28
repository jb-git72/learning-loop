# Scoring Blindspots — FMTH Meta-Ads Audit

Generated: 2026-04-27 — Audit pass covering PRs #117 (recalibration dimensions) and #123 (phase-aware scoring).

Ads scored: 18 FMTH meta-ads (`clients/farm-thru/loop/meta-ads/`) + live ad test (`LIVE-FMTH-NEVER-DONE`).
All scores are `use_llm=False` (deterministic path only). LLM-judged dims (`angle_clarity`, `motivation_match`, `tactic_execution`) default to heuristic.

---

## Fixed in this audit pass

These were bugs/blindspots that were **corrected** as part of this PR — listed here for traceability.

| ad_id | dim | score before fix | score after fix | root cause |
|---|---|---|---|---|
| ALL 18 meta-ads | `cta_clarity` | 2/5 | 5/5 | Ad JSON files had CTA bucket labels (`brand`, `cfe_campaign`) not actual CTA strings. PR #123 stamped `campaign_phase` but didn't update `cta` field. |
| `LIVE-FMTH-NEVER-DONE` | `objection_preemption` | 2/5 | 3/5 | "Eight NSW farms" not matching provenance pattern. Pattern `named farm\|paddock\|…` missed spelled-out cardinal + state-code form. Both config and hardcoded fallback updated. |
| `LIVE-FMTH-NEVER-DONE`, `CFE-108`, `BR-103` | `emotional_register` | 2/5 | 4/5 | `_classify_register` matched `r'^(?:I \|We )'` (space after "We") — missed contracted "We're/We've" openings. Live $2-lead ad starts with "We're about to open…" → classified "other" (8/19 ads in same category → high saturation → low score). |

---

## Remaining blindspots (not fixed — rationale below)

### BS-001: `motivation_match` is always 2/5 without LLM

- **ad_id**: ALL ads (deterministic path only)
- **my_verdict**: Many FMTH ads tap strong felt motivations (food provenance anxiety, desire to own vs just consume). A human reviewer would score several 4/5.
- **rubric_verdict**: 2/5 for every ad (heuristic fallback checks for literal emotional words: "love", "worry", "fear" — FMTH copy avoids these to stay grounded/founder-voiced).
- **why_disagree**: The heuristic fallback word-list is too narrow. FMTH motivation is encoded structurally ("The store keeps the margin. The farmers at the start of the chain rarely see it.") not in explicit emotion words.
- **dim_responsible**: `motivation_match` (LLM-only dim, heuristic returns 2 if <2 emotional words found)
- **fix recommendation**: Do NOT change weights. Run with `use_llm=True` to get accurate motivation_match scores. The heuristic is correctly conservative (caps at 4, defaults to 2).

---

### BS-002: `objection_preemption` — CFE ads with "Be part of it" closing don't answer "how do I actually join?"

- **ad_id**: `CFE-101`, `CFE-106`, `CFE-108`
- **my_verdict**: These ads end with "Be part of what we're building" — which is an ownership call-to-action, not a clear next step. A prospect who wants to join can't figure out how without clicking. Objection: "I want this, but where do I go?" — not answered.
- **rubric_verdict**: 3–4/5 (hub clarity + no middlemen fires, giving decent score)
- **why_disagree**: The rubric rewards presence of hub clarity ("brookvale"), no-middlemen language, and other signals — but not the fundamental "how do I get started?" clarity that a pre-campaign CFE ad needs. These ads lack "join the waitlist / leave your email" language.
- **dim_responsible**: `objection_preemption` + `cta_clarity` (CTA is now "Join the Waitlist" but the body copy doesn't bridge to it)
- **fix recommendation**: Writer generation prompt should enforce: CFE pre-campaign ads MUST include explicit waitlist-join language in the body (not just the CTA button). Update `prompt_rules` in config.

---

### BS-003: `platform_fit` — "See the general CSF risk warning + offer document" triggers em-dash rule

- **ad_id**: `BR-101` through `BR-110` (not CFE ads which use asterisked format)
- **my_verdict**: Many BR ads end with "See the general CSF risk warning + offer document." which uses `+` not an em-dash — but they still fail `platform_fit` because of other structural issues or the `no_em_dashes` rule_checker catches live-ad `—`.
- **rubric_verdict**: `platform_fit` = 3 for some ads, 5 for others
- **why_disagree**: Not a scoring blindspot per se — the `platform_fit` scorer correctly detects character limit issues. But the interaction between `_score_lp_readability`'s em-dash check and the CSF disclaimer format is worth noting: the rubric correctly rewards "no em dashes" (as a readability signal) while the live $2-lead ad has one em dash in the body ("Leave your email — we'll tell you...") that triggers the `no_em_dashes` rule_checker warning.
- **dim_responsible**: `platform_fit` (correctly fires on constraint violations), `_score_lp_readability` (correctly fires on em dashes)
- **fix recommendation**: No scorer change needed. The live ad's em-dash is a known acceptable stylistic choice for that specific construction; other ads should avoid them.

---

### BS-004: `scroll_stop_hook` — "Be part of what we're building" classified as generic (2/5)

- **ad_id**: `CFE-101`, `CFE-103`, `CFE-106`, `CFE-108` (all end with this phrase, but relevant to ad openings that repeat similar constructions)
- **my_verdict**: Several ads open with community/belonging language that has reasonable emotional pull but no curiosity gap, story, or question → 2/5 is correct for these.
- **rubric_verdict**: 2/5 generic opening for ads like "Be part of an Aussie food revolution" (opening line)
- **why_disagree**: There is no real disagreement — the scorer is right. These openings ARE generic. The blindspot is that the writer loop is generating these openings because the `scroll_stop_hook` dimension's improvement guidance in `_dimension_improvement_guidance` (writer.py) doesn't explicitly tell the writer to avoid belonging-language openers.
- **dim_responsible**: `scroll_stop_hook` (correct) — issue is upstream in writer prompt
- **fix recommendation**: Add "avoid: generic belonging openers like 'Be part of X'" to `prompt_extra_rules.meta-ad` in config, or to `learnings-meta-ad.md`.

---

### BS-005: `differentiation` baseline inflation when comparing to same-angle ads

- **ad_id**: `CFE-101` vs `CFE-102` (both investment-thesis)
- **my_verdict**: CFE-101 and CFE-102 are stylistically similar (both investment-thesis, both use "own a piece" language). A human reader would see them as duplicates in a campaign.
- **rubric_verdict**: Both score 4–5/5 differentiation because bigram Jaccard similarity is low enough (different specific proof points used).
- **why_disagree**: Jaccard similarity at the bigram level misses semantic similarity ("own a piece of it" vs "own a piece of what you believe in"). These are the same frame with slightly different words.
- **dim_responsible**: `differentiation` (correct algorithm, wrong granularity for semantic similarity detection)
- **fix recommendation**: Not worth fixing in deterministic scorer — LLM-judged angle_clarity would catch duplicate angles when `use_llm=True`. Document as known limitation.

---

## Summary table (remaining unfixed blindspots)

| id | ad_id | my_verdict | rubric_verdict | dim_responsible | action |
|---|---|---|---|---|---|
| BS-001 | ALL | varies (4/5 some) | 2/5 | `motivation_match` | Run with LLM |
| BS-002 | CFE-101, 106, 108 | needs how-to-join step | 3–4/5 | `objection_preemption` | Update writer prompt |
| BS-003 | live ad | acceptable em-dash | -3% penalty | `no_em_dashes` rule | Known acceptable |
| BS-004 | CFE-101/103/106/108 openings | 2/5 correct but preventable | 2/5 | `scroll_stop_hook` | Update writer prompt |
| BS-005 | CFE-101 vs CFE-102 | semantic duplicates | 4-5/5 | `differentiation` | Known limitation |
