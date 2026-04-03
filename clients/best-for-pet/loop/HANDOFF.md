# Handoff — 2026-04-03 11:43 AEST (Update 2)

## Progress
- **Experiments completed:** 20
- **Kept:** 14 | **Discarded:** 6
- **Unique slots filled:** 12
- **Top scorer:** OR-102 at 0.901 (PRODUCTION_READY)
- **2nd best:** OR-101 at 0.897 (PRODUCTION_READY)

## Current Best Scores by Slot

| Slot | Ad ID | Composite | Verdict |
|---|---|---|---|
| outcome-results--quoted_objection | OR-102 | **0.901** | PRODUCTION_READY |
| outcome-results--story | OR-101 | **0.897** | PRODUCTION_READY |
| simplicity-clarity--question | SC-102 | 0.879 | STRONG_DRAFT |
| empathy-understanding--quoted_objection | EU-101 | 0.863 | STRONG_DRAFT |
| price-value--statistic | PV-102 | 0.859 | STRONG_DRAFT |
| price-value--if_then | PV-101 | 0.857 | STRONG_DRAFT |
| simplicity-clarity--bold_claim | SC-101 | 0.849 | STRONG_DRAFT |
| guilt-free--confession | GF-102 | 0.848 | STRONG_DRAFT |
| predictability-control--bold_claim | PC-102 | 0.848 | STRONG_DRAFT |
| safety-risk--confession | SR-101 | 0.841 | STRONG_DRAFT |
| anti-insurance--contrarian | AI-102 | 0.834 | NEEDS_WORK |
| anti-insurance--confession | AI-101 | 0.824 | NEEDS_WORK |
| guilt-free--story | GF-101 | 0.835 | STRONG_DRAFT |
| predictability-control--question | PC-101 | 0.828 | STRONG_DRAFT |

## What's Working
- **Outcome & Results** angle dominates — 2 PRODUCTION_READY ads (0.90+)
- **Quoted objection + disbelief frame** consistently scores highest
- **Simplicity angle improving** — SC-102 question hook hit 0.879
- **100% rule compliance** achievable when body ≤ 500 chars and no em-dashes
- **Specific cost breakdowns** boost specificity and receptionist test scores
- **Hill-climbing is working** — 3 slots improved on second attempt (SC, GF, PC)

## What's Not Working
- **Empathy angle is sticky at 0.863** — 3 attempts to beat EU-101, all failed
- **Anti-insurance drags on fact accuracy** — competitor prices ($87, $160) unverified
- **OR-102 (0.901) seems near ceiling for --no-llm mode** — 3 attempts to beat it failed
- **Heuristic LLM fallbacks cap angle_clarity and motivation_match at 2-3/5**

## Discarded Experiments (patterns to avoid)
- OR-103: allergy story — too similar to OR-101 (Jaccard overlap)
- EU-102: friend tears story — less specific than EU-101's quoted objection
- EU-103: confession + 76% stat — body 2 chars over limit, lower emotional register
- EU-104: direct address — too generic vs EU-101's quoted specificity
- OR-104: statistic hook $800-1300 — less compelling than quoted objection (OR-102)
- OR-105: if/then two visits — good score (0.872) but still below OR-102

## Next Experiments to Try
1. **Enable LLM scoring** — the 3 heuristic dimensions are capping scores
2. **Try safety-risk with different hooks** — only one slot filled, lots of room
3. **Try empathy--if_then** — "If you've ever put off a vet visit because of cost..."
4. **Pattern interrupt hook** — untested hook type across all angles
5. **Try outcome-results with peer recommendation** — "My friend told me about Best for Pet"
6. **Add competitor prices as MEDIUM facts** — insurance premiums ($87-175) are real data
7. **Try a very short ad** — under 300 chars, see if platform_fit boost offsets lost specificity

## Resume Instructions
1. Read this file
2. Read results.tsv for full experiment history
3. Read best/ directory for current top variants
4. Continue from "Next Experiments to Try"
5. Branch: `adloop/best-for-pet/apr3`
6. To score: `python3 learning-loop/run.py score --client best-for-pet --ad <path> --no-llm`
