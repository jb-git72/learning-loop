# FMTH email fact audit — 2026-04-25 (Phase 4 pass 2)

Per-email claim audit against `facts.json`. Categories:

- **A** = matches a fact exactly (no action)
- **B** = true but not in `facts.json` → add the fact
- **C** = ambiguous wording → rephrase to match canonical fact language
- **D** = risky / unsubstantiated → delete from copy

Source inputs: `clients/farm-thru/loop/scored_emails_rewrite.json` (pass-1 baseline from OVERNIGHT-PLAN-2026-04-24.md) plus a sentence-by-sentence walk of the 8 seeds currently on disk (PR #74 post-rewrite versions). WebFetch of farmthru.com.au 2026-04-24 used to verify partner names and Brookvale address.

Note: Between the OVERNIGHT-PLAN drafting and this pass, PR #74 (`feat(fmth): email rewrite Phase 1`) landed on main with substantially rewritten seed bodies (new subjects, restructured narrative). The audit below is for the **post-PR-#74 seeds** that currently live on disk; the pass-1 fa scores quoted from scored_emails_rewrite.json still apply because that JSON was generated from the pre-#74 copy which was then committed as #74.

---

## Summary — claims driving fact_accuracy down across all 8 emails

Three recurring unverified claims account for ~80% of the loss:

| Claim | Reality | Category | Action |
|---|---|---|---|
| "24 hours" / "24-hour head start" | REAL per founder confirm 2026-04-24, but not yet in facts.json | B | Add new fact `INV-007` with `claim_patterns` covering "24 hours", "24-hour", "head start", "day before" |
| "not financial advice" / "independent financial advice" | Required CSF disclaimer boilerplate (ASIC RG 261) — legitimate but not a marketing claim | B | Add meta fact `LEG-001` tagging the disclaimer as required boilerplate |
| "disclosure document" | Standard Birchal CSF term — legitimate | B | Add to `LEG-001` claim_patterns |
| "400km" | VERIFIED against PQ-006 (MEDIUM) — the fuzzy regex `\d+km` grabs partial matches of "2,400km" | C | Keep as-is; facts.json PQ-006 already absorbs |
| "Bundarra Berkshires" / "heritage" pork | Site lists Bundarra Farm pork products but NOT as Berkshire or heritage (FP-002 note) | D | Remove "Berkshires" / "heritage" language from any seeds where it still appears |

Additional facts worth adding (verified 2026-04-24):
- **Brookvale full address**: "Unit 23, 10-18 Orchard Road, Brookvale NSW 2100" (BM-004 note confirms only one hub)
- **Newly verified named partners**: Mandolé Orchard (Wyangan NSW), Nonie's (Botany NSW)

Rule-compliance losses (FMTH-014 `subscription` / `lock in`) — verify no longer present after PR #74 rewrite.

---

## Per-email audit (post-PR #74 seeds)

The 8 emails currently on disk (subjects from PR #74):

1. **EM-NONVIP-01** "The hub that doesn't exist yet" — product-first, named farms
2. **EM-NONVIP-02** "Why we need to own this ourselves" — cause, equity rationale
3. **EM-NONVIP-03** "The round opens 23 June" — launch countdown
4. **EM-VIP-01** "Something I wouldn't say publicly" — insider founder note
5. **EM-VIP-02** "How the offer will actually work" — mechanism walkthrough
6. **EM-VIP-03** "Your early-access link for tomorrow" — launch-eve
7. **EM-WELCOME-NONVIP** "You're on the FarmThru list" — onboarding
8. **EM-WELCOME-VIP** "You're VIP. Here's what that means" — VIP welcome

All 8 seeds use `24 hours`, `not financial advice`, `disclosure document` — all three phrases are category B (add to facts.json, no copy edit). That's the dominant work.

The PR #74 seeds no longer contain `Bundarra Berkshires`, `lock in`, `subscription`, or `$2 more per kilo` (the problem phrases flagged in pre-#74 audit). They already passed lint_content.py per the PR #74 commit message. So seed-copy edits are **not required** for pass 2 — just the facts expansion.

---

## Aggregate action list

**New facts added to `facts.json`** (5 new entries, worktree `fmth/fact-accuracy-pass2`):

1. **INV-007** — VIP 24-hour head start before public Birchal opens (source: founder confirmation 2026-04-24; HIGH)
2. **LEG-001** — ASIC RG 261 CSF disclaimer boilerplate (source: regulatory requirement; HIGH)
3. **FP-007** — Mandolé Orchard (Wyangan NSW), dates/nuts (source: farmthru.com.au collection page verified 2026-04-24; HIGH)
4. **FP-008** — Nonie's (Botany NSW), artisan sourdough (source: farmthru.com.au; HIGH)
5. **BM-009** — Brookvale hub full address "Unit 23, 10-18 Orchard Road, Brookvale NSW 2100" (source: farmthru.com.au collections page; HIGH)

**Seed edits**: none required for PR #74 versions.

Expected uplift: each email contains ~3 previously-unverified claims (24h head start + disclaimer + disclosure document). All three land as verified after INV-007 + LEG-001. Fact_accuracy should jump from 0.56-0.75 into 0.85-1.00. Avg composite should lift from 0.7627 → ≥0.80 without seed edits.
