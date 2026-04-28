# Hypothesis-Driven Validation Dossier — 2026-04-28

**Agent:** THE EMPIRICIST  
**Scope:** 3 FMTH meta-ad seeds, 4 hypotheses each, 12 hypothesis-tests total  
**Method:** `engine/hypothesis_generator.py` + `scripts/hill_climb_from_seed.py` (new — PR #125)  
**Data:** Corpus of 19 FMTH meta-ads scored at deterministic-only, seed 1 also with full LLM scoring

---

## 1. Seeds Selected

| # | Ad ID | Score | Verdict | Angle | Hook | Selection rationale |
|---|---|---|---|---|---|---|
| 1 | LIVE-FMTH-NEVER-DONE | 0.7681–0.7899 | strong_draft | Novelty & First-Mover | Curiosity | Gold-standard $2-lead live ad |
| 2 | BR-105 | 0.6800 | needs_work | social-belonging | question | 2nd highest composite in corpus |
| 3 | BR-104 | 0.6743 | needs_work | cause-purpose | invitation | 3rd highest composite in corpus |

CFE-108 excluded: FMTH-NO-DOLLAR-METAAD critical block (contains "$2").

---

## 2. Hypotheses Generated (all 12)

Hypotheses are ranked by `expected_gain = confidence_prior x score_gap x dim_weight`.

### Seed 1: LIVE-FMTH-NEVER-DONE (score=0.7681)

| # | Dim | LBE | Gap | Prior | ExpGain | Mode |
|---|---|---|---|---|---|---|
| 1.1 | motivation_match | emotional_resonance | 2 | 0.60 | 2.400 | targeted |
| 1.2 | tactic_execution | tactic_pattern | 2 | 0.50 | 1.500 | improve |
| 1.3 | objection_preemption | objection_signals | 3 | 0.60 | 1.350 | targeted |
| 1.4 | sentence_variance | sentence_length_range | 1 | 0.50 | 0.250 | targeted |

### Seed 2: BR-105 (score=0.6800)

| # | Dim | LBE | Gap | Prior | ExpGain | Mode |
|---|---|---|---|---|---|---|
| 2.1 | motivation_match | emotional_resonance | 3 | 0.60 | 3.600 | targeted |
| 2.2 | angle_clarity | single_proposition | 2 | 0.55 | 2.200 | targeted |
| 2.3 | cta_clarity | cta_outcome_statement | 3 | 0.55 | 1.650 | targeted |
| 2.4 | scarcity_register | soft_scarcity_signals | 2 | 0.55 | 0.550 | targeted |

### Seed 3: BR-104 (score=0.6743)

| # | Dim | LBE | Gap | Prior | ExpGain | Mode |
|---|---|---|---|---|---|---|
| 3.1 | motivation_match | emotional_resonance | 3 | 0.60 | 3.600 | targeted |
| 3.2 | angle_clarity | single_proposition | 2 | 0.55 | 2.200 | targeted |
| 3.3 | cta_clarity | cta_outcome_statement | 3 | 0.55 | 1.650 | targeted |
| 3.4 | specificity | concrete_details | 2 | 0.65 | 1.625 | targeted |

---

## 3. Results: All 12 Hypothesis-Tests

### Legend

- **CONFIRMED**: variant moved in predicted direction (>=0.01 delta)
- **DENIED**: variant moved opposite to predicted direction
- **INVALID_PROBE**: lint/compliance failure prevented a valid test

| Test | Dim | Predicted | Variant Score | Delta | Actual | Confirmed |
|---|---|---|---|---|---|---|
| 1.1 | motivation_match | LIFT | 0.0000 | -0.7681 | DROP | **INVALID_PROBE** (ADV-001 compliance block) |
| 1.2 | tactic_execution | LIFT | 0.4629 | -0.3052 | DROP | **no** |
| 1.3 | objection_preemption | LIFT | 0.5391 | -0.2290 | DROP | **no** |
| 1.4 | sentence_variance | LIFT | 0.0000 | -0.7681 | DROP | **INVALID_PROBE** (ADV-001 compliance block) |
| 2.1 | motivation_match | LIFT | 0.0000 | -0.6800 | DROP | **INVALID_PROBE** (ADV-001) |
| 2.2 | angle_clarity | LIFT | 0.0000 | -0.6800 | DROP | **INVALID_PROBE** (ADV-001) |
| 2.3 | cta_clarity | LIFT | 0.0000 | -0.6800 | DROP | **INVALID_PROBE** (ADV-001) |
| 2.4 | scarcity_register | LIFT | 0.0000 | -0.6800 | DROP | **INVALID_PROBE** (ADV-001) |
| 3.1 | motivation_match | LIFT | 0.0000 | -0.6743 | DROP | **INVALID_PROBE** (ADV-001) |
| 3.2 | angle_clarity | LIFT | 0.0000 | -0.6743 | DROP | **INVALID_PROBE** (ADV-001) |
| 3.3 | cta_clarity | LIFT | 0.0000 | -0.6743 | DROP | **INVALID_PROBE** (ADV-001) |
| 3.4 | specificity | LIFT | 0.0000 | -0.6743 | DROP | **INVALID_PROBE** (ADV-001) |

**Summary: 0 confirmed, 2 denied, 10 invalid probes.**

---

## 4. Root Cause: Systemic ADV-001 Compliance Block

**Finding: `generate_variant` does not reliably include the CSF footnote, and `lint_content` does not enforce ADV-001.**

10 of 12 variants failed with `variant_score=0.0` due to `ADV-001` BLOCKING compliance violation ("Always consider the general CSF risk warning and offer document before investing." missing from primary_text).

Reproduction:
- Seeds BR-104 and BR-105 already use an informal CSF note ("See the general CSF risk warning + offer document") — not the canonical asterisked form
- `generate_variant` rewrites the primary_text and does not guarantee the canonical CSF line
- `lint_content` passes variants that lack the CSF note (lint gate does not check ADV-001)
- `score_ad` runs the compliance checker which zeros the composite score via BLOCKING violation

**This is not a rubric problem.** It is a generation pipeline problem:

1. **Lint gap:** `lint_content` does not verify ADV-001 compliance. Proposed fix: add ADV-001 check to `lint_content` layer.
2. **Generation gap:** `generate_variant` should post-hoc append the canonical CSF line if `compliance.enabled=True` and content_type is `meta-ad`.

The 2 non-zero variants (tests 1.2 and 1.3 from seed 1 LLM run) both used a partial CSF phrase ("General CSF risk warning: investing in a CSF offer involves risk...") that is banned by DISC-001 (old wording). They scored 0.54 but dropped from the 0.77 seed score — also confirming that rewriting the primary_text for a single dimension improvement loses other signals.

---

## 5. Load-Bearing Elements: Verdict

From the 2 valid tests (1.2, 1.3) and the corpus variance analysis (19 ads):

| LBE | Test Coverage | Confirmed? | Notes |
|---|---|---|---|
| emotional_resonance | 3 tests (invalid) | inconclusive | ADV-001 block. Most-targeted LBE. |
| single_proposition | 2 tests (invalid) | inconclusive | ADV-001 block. |
| cta_outcome_statement | 2 tests (invalid) | inconclusive | ADV-001 block. |
| tactic_pattern | 1 test (valid) | **no** — DROP | Improvement attempt lost other signals |
| objection_signals | 1 test (valid) | **no** — DROP | Improvement attempt lost other signals |
| concrete_details | 1 test (invalid) | inconclusive | ADV-001 block. |
| soft_scarcity_signals | 1 test (invalid) | inconclusive | ADV-001 block. |
| sentence_length_range | 1 test (invalid) | inconclusive | ADV-001 block. |

**Key observation from valid tests:** When the loop rewrites an ad to improve one dimension (tactic_execution, objection_preemption), it consistently degrades the total composite by 0.2-0.3 because the LOCKED high-scoring dims (scroll_stop_hook=5, founder_voice=5, scarcity_register=5, ownership_framing=5, csf_placement=5) in the seed ad are NOT preserved in the rewrite. This is the "hook_swap isolation" problem: the loop cannot surgically improve one LBE without touching the others.

---

## 6. Rubric Blindspot Analysis

Corpus: 19 FMTH meta-ads, deterministic scoring only (no LLM). Sorted by StdDev ascending.

### 6a. Zero-Variance Dims (LLM heuristic fallback returns constant)

| Dim | Mean | StdDev | Corr(composite) | Weight | Verdict |
|---|---|---|---|---|---|
| angle_clarity | 3.00 | 0.000 | 0.000 | 2.00 | **ZERO-VAR** — LLM-only, heuristic returns constant |
| motivation_match | 2.00 | 0.000 | 0.000 | 2.00 | **ZERO-VAR** — LLM-only, heuristic returns constant |
| tactic_execution | 4.00 | 0.000 | 0.000 | 1.50 | **ZERO-VAR** — LLM-only, heuristic returns constant |

These three are the highest-weighted dimensions in the meta-ad rubric but contribute ZERO discriminating signal in no-LLM mode. This is by design (they're LLM-only), but it means no-LLM hill-climbing cannot optimize for the top 5.5 weighted points (of 87.5 max).

With LLM scoring enabled, angle_clarity shows variance (seed 1 scored 3/5 in one run, 5/5 in another — a 2-point swing). This confirms LLM-judge variance is real and materially affects composite (delta ~0.10).

### 6b. Low-Signal Dims (low variance AND low correlation)

| Dim | Mean | StdDev | Corr(composite) | Weight | Verdict |
|---|---|---|---|---|---|
| csf_placement | 4.05 | 0.229 | +0.283 | 0.50 | **LOW-SIGNAL** — most ads near max; variance from asterisk style |
| platform_fit | 4.89 | 0.459 | -0.283 | 0.75 | **LOW-SIGNAL** — negative correlation; penalizes headlines >40 chars |

`csf_placement` scores 4 or 5 on every ad (either asterisked=5 or present-but-not-asterisked=4). The 1-point range adds almost no discrimination. During hook_swap mode, the body is locked so this dim is always 4 or 5 — adds no signal to variant selection.

`platform_fit` is negatively correlated with composite — better ads tend to have slightly longer headlines (more content = lower platform_fit). This is an inherent trade-off in the platform constraint, not a failure of better ads.

### 6c. Discriminating Dims (std >= 0.5, |corr| > 0.3)

| Dim | Mean | StdDev | Corr(composite) | Weight | Verdict |
|---|---|---|---|---|---|
| scroll_stop_hook | 3.53 | 1.389 | +0.494 | 1.75 | **KEEP / RAISE** — highest corr + variance |
| differentiation | 4.63 | 0.496 | +0.482 | 1.50 | **KEEP** — corr borderline on std; high corr |
| scarcity_register | 3.21 | 0.631 | +0.337 | 0.50 | **RAISE** — strong corr, underweighted (0.5) |
| sentence_variance | 3.00 | 0.577 | +0.337 | 0.50 | **RAISE** — strong corr, underweighted (0.5) |
| specificity | 3.37 | 0.684 | +0.308 | 1.25 | **KEEP** — good corr + variance |

### 6d. Borderline Dims (std OK, corr < 0.3)

| Dim | Mean | StdDev | Corr(composite) | Weight | Current | Recommendation |
|---|---|---|---|---|---|---|
| cta_clarity | 2.16 | 0.688 | +0.283 | 1.00 | 1.00 | **KEEP** — borderline but improving |
| founder_voice | 2.84 | 1.167 | +0.235 | 0.50 | 0.50 | **KEEP** — CFE-specific signal |
| ownership_framing | 3.42 | 0.607 | +0.214 | 0.75 | 0.75 | **MAKE-MODE-AWARE** — only relevant in CFE mode |
| emotional_register | 2.79 | 0.918 | +0.206 | 0.75 | 0.75 | **KEEP** |
| receptionist_test | 4.26 | 0.653 | +0.193 | 0.75 | 0.75 | **KEEP** — compliance gate function |
| opening_diversity | 4.16 | 0.688 | -0.178 | 0.75 | 0.75 | **LOWER** — slight negative corr |
| objection_preemption | 2.84 | 0.834 | -0.037 | 0.75 | 0.75 | **LOWER** — near-zero corr |

---

## 7. Weight-Change Proposals

Data-backed proposals based on variance + correlation evidence. Applies to `clients/farm-thru/config.json`, `rubric.meta-ad.weights`.

| Dim | Current Weight | Proposal | Evidence |
|---|---|---|---|
| scroll_stop_hook | 1.75 | **RAISE to 2.0** | Highest corr (+0.494) + highest std (1.389) in corpus. Most discriminating deterministic dim. |
| scarcity_register | 0.50 | **RAISE to 0.75** | corr=+0.337, std=0.631. Underweighted relative to discriminating power. |
| sentence_variance | 0.50 | **RAISE to 0.75** | corr=+0.337, std=0.577. Same case as scarcity_register. |
| opening_diversity | 0.75 | **LOWER to 0.5** | corr=-0.178 (slight negative). Better ads don't need diverse openers — they need strong openers. |
| objection_preemption | 0.75 | **LOWER to 0.5** | corr=-0.037 (near-zero). High-scoring ads tend NOT to score high here — may conflict with brevity. |
| ownership_framing | 0.75 | **MAKE-MODE-AWARE** | Relevant only in CFE-investment ads. Brand-only ads should not be penalized for missing ownership language. Proposed: weight=0.75 for `cfe_waitlist` phase, 0.0 for `brand` campaign. |
| platform_fit | 0.75 | **LOWER to 0.5** | corr=-0.283. Penalizes better/longer copy. Retain as constraint gate, not quality signal. |
| angle_clarity, motivation_match, tactic_execution | 2.0, 2.0, 1.5 | **KEEP** (no change) | LLM-only dims; zero variance in no-LLM mode but high weighted contribution WITH LLM. Cannot adjust without LLM validation data. |

**Borderline — leave for JB review:**
- `differentiation` (std=0.496, corr=+0.482): correlation is strong but variance is borderline. If you add more diverse ads to the corpus, this may reach KEEP territory.
- `csf_placement` (std=0.229, corr=+0.283): nearly all ads score 4-5. Consider collapsing to pass/fail gate (compliance) instead of weighted rubric dim.

---

## 8. Architecture Recommendations (not weight changes)

### Fix 1: Add ADV-001 to lint gate (HIGH PRIORITY)

The lint gate must check for the canonical CSF footnote. Without this, every hypothesis test that involves rewriting primary_text will be an INVALID_PROBE.

Proposed fix in `scripts/lint_content.py` or `engine/rule_checker.py`:
- Check that `primary_text` ends with a paragraph containing the canonical ADV-001 string
- Return lint violation if missing, severity=BLOCKING
- This prevents the compliance checker from zeroing the score post-generation

### Fix 2: Hypothesis probe isolation (MEDIUM PRIORITY)

The hypothesis loop generates a full variant via `generate_variant`. This replaces the entire primary_text, not just the targeted element. Result: improving `tactic_execution` loses `scroll_stop_hook=5`, `founder_voice=5`, etc.

True hypothesis testing requires surgical changes: swap only the hook, only the CTA, only add specifics — not rewrite the whole ad. Proposed: a `generate_hook_swap_variant` function that preserves the locked body (lines 2+) and only regenerates line 1.

### Fix 3: LLM variance budget in score reports (LOW PRIORITY)

`angle_clarity` scored 3/5 in one LLM run and 5/5 in another for the SAME seed 1 ad. The delta is 2 points at weight=2.0 = 4 weighted points = ~0.046 composite shift. This is non-trivial. Propose: batch-judge with temperature=0 or N=3 median to reduce noise.

---

## 9. Data Files

| File | Contents |
|---|---|
| `validation/seeds-2026-04-28/seed-1-LIVE-FMTH.json` | Seed 1: live $2-lead ad |
| `validation/seeds-2026-04-28/seed-2-BR-105.json` | Seed 2: BR-105 (social-belonging/question) |
| `validation/seeds-2026-04-28/seed-3-BR-104.json` | Seed 3: BR-104 (cause-purpose/invitation) |
| `validation/empiricist-results-2026-04-28/LIVE-FMTH-NEVER-DONE-results.json` | Seed 1 results (LLM-scored) |
| `validation/empiricist-results-2026-04-28/BR-105-results.json` | Seed 2 results (no-LLM) |
| `validation/empiricist-results-2026-04-28/BR-104-results.json` | Seed 3 results (no-LLM) |
| `validation/empiricist-results-2026-04-28/dim-variance-analysis.json` | Corpus variance stats (19 ads) |
| `engine/hypothesis_generator.py` | New: generates testable hypotheses from score reports |
| `scripts/hill_climb_from_seed.py` | New: entry point for hypothesis-driven hill-climb |

---

## 10. Decision: Weight Changes Applied vs. Deferred

**Applied in `clients/farm-thru/config.json`:** None — all changes are borderline or require architectural fixes first (ADV-001 lint gap makes hypothesis confirmation impossible).

**Rationale:** The 10/12 invalid probes mean we have only 2 valid data points (tests 1.2, 1.3 from seed 1). Both DENIED their hypothesis — but this may be because the rewrite lost other signals, not because the LBE is non-causal. With the ADV-001 lint fix in place, a second validation pass would give clean hypothesis-test data. Until then, applying weight changes based on only 2 valid tests + corpus correlations (no causal evidence) is premature.

**Weight proposals documented in Section 7** above for JB review. They are evidence-based but not yet causal-validated.
