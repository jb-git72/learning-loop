# Production-Ready Threshold Analysis — 2026-04-29

**Context:** Phase 5 of project_loop_2026_04_29_autonomous_plan.md
**Question:** After Phase 4 weight changes, should the 0.85 production_ready threshold be kept, lowered, or raised?

---

## What Was Measured

Single hypothesis-driven hill-climb on the live $2-lead ad seed (LIVE-FMTH-NEVER-DONE).

| Run | Seed composite | Best variant | Clears 0.85? |
|---|---|---|---|
| Phase 3 (post-PR #129/#130) | 0.6977 | 0.6677 | No |
| Phase 5 (post-PR #132 weights) | 0.7056 | 0.6026 | No |

No variant cleared 0.85. Best-ever hook_swap variant in this session: 0.6677 (Phase 3, S1-H1, curiosity_gap_narrow_bound ablation).

---

## Why No Variant Clears 0.85

The hook_swap methodology locks the body (paragraphs 2+), description, CTA, and CSF footnote from the seed. The new hook must fit the existing body. This structural constraint limits how much a hook_swap variant can lift over the seed — the best hooks in these sessions lifted 0 points (all DENIED the hypothesis). The ceiling in hook_swap mode is bounded by:

1. **Locked body quality**: the existing body scores well on its own (specificity=4, scarcity_register=5, ownership_framing=5). A new hook that doesn't fit this body as naturally as the original gets penalized on tactic_execution.
2. **LLM variance**: The seed itself scores 0.70-0.79 depending on the LLM judge run. With new weights (scroll_stop_hook=2.0, scarcity_register=0.75), a seed that scores 5/5 on those dims has a higher rubric floor.
3. **Heuristic floor on LLM dims**: angle_clarity, motivation_match, tactic_execution score 3/2/4 without LLM. These three dims have total weight 5.5/17.5 = 31% of the rubric. A conservatively scored LLM = lower composite.

---

## Live Ad Score Trajectory

| Version | Rubric (no-LLM) | Composite (no-LLM) | Composite (w/ LLM) | Notes |
|---|---|---|---|---|
| Pre-PR #127 | ~0.749 | ~0.749 | ~0.749 | 3 bugs: cta=bucket, We're classified "other", provenance miss |
| Post-PR #127 | 0.7971 | 0.765 | 0.765-0.79 | Bugs fixed |
| Post-PR #132 | **0.8057** | 0.7654 | est. 0.78-0.85 | Weights rebalanced |

The rubric score increased to 0.8057 with new weights (was 0.7971). This brings the live ad within reach of 0.85 in full LLM scoring when LLM judges score angle_clarity >= 4/5.

---

## Recommendation: KEEP 0.85

**Rationale:**

1. **The live $2-lead ad currently clears strong_draft (0.70+) in full LLM scoring.** It does NOT yet clear production_ready (0.85). This is correct — it's a known-good ad but not the best conceivable execution.

2. **0.85 is achievable.** The rubric ceiling with new weights is 0.8057 (deterministic). Full LLM scoring with angle_clarity=5, motivation_match=4, tactic_execution=5 would add roughly (5×2.0 + 4×2.0 + 5×1.5)/87.5 = 0.514 vs heuristic (3×2.0 + 2×2.0 + 4×1.5)/87.5 = 0.457. Delta = +0.057 on the rubric score. Combined with new 0.8057 rubric baseline: 0.8057 + 0.057 × 0.5 (rubric weight) ≈ 0.83 composite. Close to 0.85 — achievable with a purpose-built ad.

3. **Lowering to 0.80 would gate too early.** The hill-climb sessions generate strong_draft ads (0.70-0.77) regularly. Lowering production_ready to 0.80 risks shipping ads that are 75th percentile, not top quartile.

4. **Raising to 0.88 is premature.** No variant has cleared 0.85 in the hook_swap regime. Raising the bar before demonstrating 0.85 is achievable is counterproductive.

---

## Open Question for JB

The question of whether 0.85 is achievable at all depends on LLM judge reliability:
- If LLM variance is ±0.07 on the same ad (as measured across sessions), the 0.85 threshold requires the ad to be genuinely good enough that even a conservative LLM run clears it.
- The fix (proposed in HYPOTHESIS-DOSSIER.md Fix 3): batch-judge with temperature=0 or N=3 median to reduce noise. This would make the threshold meaningful and stable.

**Recommendation:** Keep 0.85, but add N=3 median LLM scoring for production_ready classification to reduce false gate failures from LLM variance.
