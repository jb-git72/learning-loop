# Morning Report — 2026-04-28

## What I did overnight (you went to bed at ~22:00)

### 1. Recalibrated the FMTH meta-ad scorer to learn from the live $2-lead ad
The live ad ("we're about to open something up that's never been done with a grocery store in Australia…") scored only 0.71 on the prior rubric — below our production_ready cut — despite shipping $2 leads. Recalibration encodes its signature levers so future hill-climbs reward similar copy.

**PR #117** — squash-merged to main. https://github.com/jb-git72/learning-loop/pull/117

**4 new deterministic dimensions** (FMTH meta-ad opt-in via explicit weights; `default_weight: 0.0` in schema so other clients are unaffected):
- `ownership_framing` — "own a piece of", "be part of" beats transactional "invest from $X". Investment-context-gated to avoid grocery-share false +ves.
- `scarcity_register` — soft / future-tense scarcity ("opens soon", "first in gets first access") rewarded; hard pressure ("act now", "ends today") penalised.
- `founder_voice` — first-person plural with build-language ("we've built", "we're about to").
- `csf_placement` — CSF as asterisked final-paragraph footnote rewarded; body-blended compliance penalised.

**3 upgraded existing dimensions:**
- `scroll_stop_hook` — detects curiosity-gap hooks ("we're about to", "never been done", "open something up", category+geo-bounded "for the first time")
- `specificity` — counts spelled-out cardinals ("Eight farms", "One hub") + geographies (Northern Beaches, Sydney, Australia) — previously missed both
- `cta_clarity` — funnel-aware approved-list flatten + outcome-stated CTA bonus when body links action to consequence

**Engine bugs surfaced and fixed by code-review agent:**
- `lp_readability` fallthrough was crediting a dummy 3/5 with default_weight 1.0 on every meta-ad → silently inflating composite by ~3.0 weighted points. Now skipped.
- `engine/scorer.py` composite uses dynamic `max_possible` from rubric_result instead of static config `max_score` (which had drifted out of sync). Affects all clients positively — historical scores were inflated.

**Empathy + Social Belonging angles** promoted as first-class in `learnings-meta-ad.md` with seed examples from FMTH's approved sheet ("This food exists. It's just never been easy to get to.", "FarmThru families know who grew their food."). Within 2000-char budget.

**Em-dash rule retained** per your instruction.

### 2. Validation results (calibration-report.md)
| | Prior rubric | New rubric |
|---|---|---|
| Live $2-lead ad | 0.7133 | **0.77–0.88** standalone, **0.7247** cohort, ranked **1st of 6** |
| BR-101 | 0.929 | 0.603 (correctly downgraded — no ownership / founder voice) |
| BR-103 | 0.905 | 0.464 (correctly downgraded — question opener, no curiosity gap) |
| BR-106 | 0.933 | 0.700 |
| BR-109 | 0.937 | 0.689 |
| CFE-108 | 0.944 | **0.000** (contains "$2" — FMTH-NO-DOLLAR-METAAD blocking. Should never have shipped on prior rubric.) |

All 7 deterministic recalibration levers score 5/5 on the live ad. LLM-judge run-to-run variance accounts for ±0.05 on subjective dims (`motivation_match`, `angle_clarity`) — known property, not a recalibration bug.

### 3. Overnight hill-climb (still running when this was written)
- Command: `python3 -u scripts/hill_climb.py farm-thru 8 --type meta-ad --strategy evolutionary --population 4 --workers 4 --target 0.85`
- Log: `clients/farm-thru/loop/hill-climb-overnight-recalibrated.log`
- Started: 22:16
- Target: 0.85 composite per ad
- Population 4 candidates per ad per iteration, 8 iterations max per ad, 4 ads in parallel
- Initial set: 18 meta-ad items in `clients/farm-thru/loop/meta-ads/`

When it finishes I'll either:
- (success) Build a fresh review HTML and link below.
- (crash) Document the failure mode and what to retry.

## To check this morning
1. Open the calibration report: `validation/calibration-report.md`
2. Check the hill-climb log: `tail -100 clients/farm-thru/loop/hill-climb-overnight-recalibrated.log`
3. Look for the review HTML I'll add below if the run completed cleanly.

## Open follow-ups (not in scope tonight)
- LLM-judge variance is real (±0.05 on subjective dims). A future ticket could batch-judge or pin temperature=0 to reduce.
- The em-dash penalty still costs the live ad ~5% composite. Worth a conversation re: scope (headlines only? CFE only?) once we have more high-performer data points.
- Other clients (BFP, Tyroola) get a small composite uplift from the `lp_readability` fallthrough fix — historical scores were inflated. Worth re-running their calibration sets to update baselines.
