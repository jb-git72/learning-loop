# CSF VIP Wave 5b — pre-merge readiness check

**Date**: 2026-04-26
**Mode**: READ-ONLY verification (no PRs merged, no code modified)
**Scope**: 6 PRs (sales-skill #212 #213; learning-loop #87 #88 #89 #90)
**Pivot context**: Birchal response 2026-04-26 (see CSF-VIP-BIRCHAL-SUBMISSION.md §9). Equal-access disclosure NOT required; "early private access" approved; "priority" globally banned per founder direction.

---

## VERDICT: NO — NOT READY FOR PHASE B

**Two blockers** require resolution before merging:

1. **PR #213 (sales-skill / `fix/campaign-html-csf-compliance`)** — adds **pre-pivot copy** to the shared `web/templates/campaign.html` (used by FMTH and every other CFE client). Lines 224, 228, 234, 244, 246, 247 contain banned/dropped phrasing post-Birchal-pivot.

2. **PR #89 (learning-loop / `worktree-agent-acc01fb0c7ba93864`)** — entire `CSF-VIP-NEW-COPY.md` is **pre-pivot**. Specifies "VIP SUPPORTER" badge + "Priority SMS" deliverable + equal-access disclosure as required + bans phrases now Birchal-approved. Merging would inject contradictory canonical-spec into main.

**One soft flag** (not a hard blocker, but should be communicated):

3. **PR #88 (learning-loop / `feature/csf-vip-audit-wave5b`)** — `CSF-VIP-TOUCHPOINTS-AUDIT.md` is a pre-pivot audit; severity rubric and gap calls reference disclosures Birchal has since dropped. Ships fine as historical audit trail, but is misleading without the pivot context.

PRs **#87, #90, #212** all PASS Phase A and are ready to merge.

---

## PASS/FAIL table per PR

| PR | Repo | Branch | Mergeable | Tests | Content grep | Verdict |
|---|---|---|:---:|:---:|:---:|:---|
| 87 | learning-loop | worktree-agent-a0a6be1a58fb5e959 | PASS | 12/12 engine | PASS (priority only in banned-list) | **READY** |
| 88 | learning-loop | feature/csf-vip-audit-wave5b | PASS | 12/12 engine | PASS (priority only in audit context) | **READY w/ FLAG** (pre-pivot audit) |
| 89 | learning-loop | worktree-agent-acc01fb0c7ba93864 | PASS | 12/12 engine | **FAIL** | **BLOCKER** — pre-pivot canonical spec |
| 90 | learning-loop | feat/csf-rules-birchal-pivot | PASS | 16/16 engine (12+4 new) | PASS (priority only in rule defs / fixtures) | **READY** |
| 212 | sales-skill | feature/csf-vip-rewrite-wave5b | PASS | 170 pass / 20 fail (baseline) | PASS (priority only in pivot script + validator regression tests) | **READY** |
| 213 | sales-skill | fix/campaign-html-csf-compliance | PASS | 139 pass / 37 fail (= main baseline) | **FAIL** | **BLOCKER** — pre-pivot customer copy |

---

## TASK 1 — Mergeability

All 6 PRs merge cleanly into `origin/main` with no conflicts (`git merge --no-commit --no-ff origin/main` succeeded for every branch).

| PR | Result |
|---|---|
| #87 | PASS — clean merge |
| #88 | PASS — clean merge |
| #89 | PASS — clean merge |
| #90 | PASS — clean merge |
| #212 | PASS — clean merge |
| #213 | PASS — clean merge |

---

## TASK 2 — Content grep (banned phrases / required phrases)

### Banned phrases — MUST be ZERO matches in customer-facing copy

| PR | "priority" | equal-access disclosure | "Waitlist closes" | "priority allocation" | "beat the queue" | "lock in" | "1,500 VIPs" | "VIP Supporter" |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| #87 | banned-list only (PASS) | banned-list only (PASS) | clean | banned-list only (PASS) | clean | clean | clean | clean |
| #88 | audit context only (PASS) | audit context only (PASS) | clean | audit context only (PASS) | audit context only (PASS) | audit context only (PASS) | audit context only (PASS) | audit context only (PASS) |
| #89 | **CUSTOMER COPY** (FAIL) | **CUSTOMER COPY** (FAIL) | clean | banned-list only (PASS) | clean | clean | banned-list only (PASS) | **CUSTOMER COPY — badge spec** (FAIL) |
| #90 | rule-def + fixtures only (PASS) | rule-def + fixtures only (PASS) | clean | rule-def only (PASS) | clean | clean | clean | clean |
| #212 | pivot-script `OLD_SECTION` + validator regression tests only (PASS) | pivot-script `OLD_SECTION` only (PASS) | pivot-script `OLD_SECTION` only (PASS) | validator regression tests only (PASS) | banned-list `INDEX.md` only (PASS) | banned-list `INDEX.md` only (PASS) | banned-list `INDEX.md` only (PASS) | HTML comments only — `<!-- Send: 3 days after VIP supporter contribution -->` (PASS) |
| #213 | **CUSTOMER COPY — line 246** (FAIL) | **CUSTOMER COPY — line 247** (FAIL) | clean | clean | clean | clean | clean | **CUSTOMER COPY — lines 224/228/234/244** (FAIL) |

### Required phrases — MUST be PRESENT in customer-facing copy

| PR | "early access" / "early private access" | "general risk warning" / s738ZG | "refundable" | "$5" |
|---|:---:|:---:|:---:|:---:|
| #87 | PASS (every section) | PASS (every section that mentions round) | PASS | PASS |
| #88 | n/a (audit doc) | n/a (audit doc) | n/a (audit doc) | n/a (audit doc) |
| #89 | **MISSING** — uses "priority SMS" framing instead | PASS | PASS | PASS |
| #90 | PASS (in fixture + rule rationale) | PASS (in fixture) | PASS | PASS |
| #212 | PASS (variants + REFERENCE.md + welcome email) | PASS (every VIP card disclosure) | PASS | PASS |
| #213 | **MISSING** — uses "supporter contribution" framing instead | PASS (added in disclosure) | PASS | PASS |

### Specific failures — file + line

**PR #213 — `web/templates/campaign.html`** (the customer-facing template used by FMTH and every CFE campaign):

```
L224: vipBtn.textContent = 'Become a VIP Supporter';                                              <- "VIP Supporter" banned
L228: vipBtn.textContent = 'Become a VIP Supporter';                                              <- "VIP Supporter" banned
L234: vipBtn.textContent = 'Become a VIP Supporter';                                              <- "VIP Supporter" banned
L244: vipCard.innerHTML = '<span ...>VIP SUPPORTER CONFIRMED</span>'                              <- "VIP Supporter" banned
L246: '<p ...>Your $5 supporter contribution is confirmed. As a thank-you, you\'ll receive a       <- "priority SMS" banned
       priority SMS notification when the round opens at Birchal, plus updates emails throughout
       the campaign. Check your inbox for your welcome email.</p>'
L247: '<p ...>All investors apply on the same terms when the round opens at Birchal. The VIP       <- equal-access disclosure
       Supporter product does not provide earlier or preferential investment access.                  is Birchal-DROPPED;
       $5 refundable on request before the round closes.</p>'                                         "VIP Supporter" banned
```

Also: `'Become a VIP Supporter'` button text is missing the canonical `"Secure VIP Access"` CTA per `CSF-VIP-COPY-PACKAGE.md`. The success-state card framing ("Thanks for supporting our launch") contradicts the post-pivot canonical ("Secure early access to invest").

**PR #89 — `clients/farm-thru/CSF-VIP-NEW-COPY.md`** (entire file is canonical pre-pivot spec):

```
L23: ## 1.1 Product name
L24: **VIP Supporter** (badge text on LP / thank-you / drip / mission-control).                   <- "VIP Supporter" banned
L26: The legacy badge text "VIP ACCESS" must be replaced everywhere with "VIP SUPPORTER".

L32: > Pay $5 to support FarmThru's launch. As a thank-you, you'll receive a                       <- "priority" banned
L33: > priority SMS when our round opens at Birchal, plus updates throughout the campaign.

L36: 1. Priority SMS notification when the round goes live at Birchal.                             <- "priority" banned

L43: - **Equal-access**: *"All investors apply on the same terms ... does not provide              <- equal-access disclosure
       earlier or preferential investment access."*                                                   is Birchal-DROPPED

L54: "limited spots — VIPs go first" · "priority allocation" · "reserved for VIPs only" ·
L55: "VIPs invest first" · ...
L61: · "VIP investors get priority access".                                                        <- self-contradiction:
                                                                                                       still bans "early access"
                                                                                                       which Birchal approved

L79-82: <span class="vip__badge">VIP SUPPORTER</span>
        <p ...>Pay $5 to support FarmThru's launch. As a thank-you, you'll receive a
        priority SMS ...</p>                                                                       <- pre-pivot HTML spec
```

---

## TASK 3 — Cross-PR consistency

### Canonical VIP card

The canonical post-pivot VIP card (per `CSF-VIP-COPY-PACKAGE.md` and Birchal §9):

```
Badge:    VIP ACCESS
Headline: Secure early access to invest.
Sub:      Place a small refundable deposit to secure VIP status. VIP investors
          get early private access to the investment offer and early notice
          before the campaign opens to the public.
Bullet 1: Early access when the campaign opens
Bullet 2: Early investor updates from the founders
Bullet 3: Fully refundable at any time
CTA:      Secure VIP Access
Footer:   100% refundable. No obligation to invest.
```

Per-PR comparison:

| Source | Match? | Notes |
|---|:---:|---|
| `clients/farm-thru/CSF-VIP-COPY-PACKAGE.md` (main, uncommitted) | reference | Source of truth — already updated for Birchal pivot |
| `clients/farm-thru/CSF-VIP-BIRCHAL-SUBMISSION.md` §9 (main, uncommitted) | reference | Records the pivot |
| **PR #87** `CSF-VIP-MARKETING-COPY.md` | **MATCH** | All five sections (LP, welcome email, drip, FAQ, sales) use canonical phrasing exactly |
| **PR #212** LP variants (16 of 17, plus index-q.html success state) | **MATCH** | `wave5b_vip_pivot.py` script ran successfully; verified by reading actual `index-b.html` etc. — all variants have post-pivot `<section class="vip">` block |
| **PR #212** drip emails (welcome + drip 1/2/3) | **MATCH** | `drip_vip_welcome.html` uses "Early private access to the investment offer" |
| **PR #213** `campaign.html` (customer template) | **NO MATCH** | Uses "VIP Supporter" / "Thanks for supporting" / "priority SMS" / equal-access disclosure |
| **PR #89** `CSF-VIP-NEW-COPY.md` | **NO MATCH** | Specifies "VIP SUPPORTER" badge / "priority SMS" deliverable / equal-access disclosure as canonical |

### "early" vs "priority" usage across all 6 PRs

- PR #87: uses "early" exclusively in customer copy; "priority" only in banned-list section. PASS
- PR #88: uses "priority" only in audit findings (intentional — flagging existing pre-pivot violations). PASS (but note: pre-pivot audit framing)
- PR #89: uses "priority" as the canonical product framing. **FAIL**
- PR #90: uses "priority" only in rule definitions and FAIL fixtures (intended — the rule explicitly bans the word). PASS
- PR #212: uses "early" in customer copy; "priority" only in `wave5b_vip_pivot.py` `OLD_SECTION` constants (find-and-replace anchors) + `variant_validator.py` regression tests. PASS
- PR #213: uses "priority SMS notification" + "VIP Supporter" framing in customer copy. **FAIL**

### Status flags

- **PR #88** (touchpoints audit) — **PRE-PIVOT**. Audit was completed before Birchal's response. Severity rubric (HIGH = "first access to invest" framing) and recommended-fix list (#1: "remove priority access from Stripe description") are now stale. The audit doc has historical value as an audit trail (it's the snapshot that triggered the rewrite work) but reading it without the pivot context would mislead. Two options:
  1. Merge as-is (it's static history; doesn't affect runtime)
  2. Add a 2-line "PIVOT 2026-04-26: this audit pre-dates Birchal's response. See CSF-VIP-BIRCHAL-SUBMISSION.md §9 for the current canonical state." banner before merging
- **PR #89** (canonical in-product copy spec) — **PRE-PIVOT and CONTRADICTORY**. Cannot merge as-is. Either:
  1. Rewrite to match the post-pivot canonical (uses `CSF-VIP-COPY-PACKAGE.md` + PR #87 marketing copy as source of truth)
  2. Drop entirely — `CSF-VIP-COPY-PACKAGE.md` (uncommitted on main) already serves as the canonical in-product copy spec post-pivot

---

## TASK 4 — Tests + eval (learning-loop main)

### `pytest engine/tests/`

```
12 passed in 0.03s
```

PASS — all 12 engine tests green on main.

### `python3 scripts/validate_compliance_rules.py`

```
OK: compliance_rules.json valid — 96 rules across 2 regulations
```

PASS — schema-valid. Note: spec said "97 rules", which is the count AFTER PR #90 lands. Pre-merge: 96. Confirmed PR #90 adds FMTH-PRIORITY-001 to bring it to 97 (verified on PR #90 worktree).

### `python3 scripts/eval_compliance_accuracy.py` (deterministic mode acceptable)

```
--no-llm: Loaded 36 fixtures.
          Accuracy: 9/36 (25.0%) — 0 false positives, 0 false negatives.
```

PASS — deterministic mode shows **0 FP, 0 FN**. The 27 "missed" labels are all `out-of-scope` — fixtures labelling rules that are LLM-judge only (ADV-004/005/006/007/013/017, MISL-001/002/004). The deterministic checker correctly skips them; this is expected behaviour, not a regression.

LLM mode (informational, not required by spec):

```
default: Accuracy: 24/36 (66.7%) — 0 false positives, 12 false negatives.
```

The 12 false negatives are pre-existing on main — the LLM judge is missing some semantic-rule violations on labelled fixtures. This is a calibration gap, **not a Phase A blocker** (spec says deterministic acceptable).

### `python3 scripts/dry_run_compliance.py --include-broken-fixture`

```
Loaded 8 emails
Loaded 17 landing pages
Evaluating 26 pieces (llm_judge enabled)...
Report: clients/farm-thru/loop/compliance-dry-run-CALIBRATED-2026-04-26.md
Summary: 1/26 pieces failed BLOCKING gate; 3 total BLOCKING violations.
```

PASS — only the deliberately-broken fixture failed (sanity check). All 8 emails + all 17 LP variants pass. **Note**: the LP variants currently on sales-skill main use pre-pivot copy ("first access to invest", "priority access") but those phrases are not enforced by the shared CSF rules — they're enforced by the FMTH client-rule `FMTH-PRIORITY-001` introduced in PR #90, which only fires after merge. The dry-run is therefore expected-clean now and would tighten further once PR #90 lands.

---

## TASK 5 — Sales-skill tests

### PR #212

```
170 passed, 20 failed in 0.38s
```

PASS — 20 failures match the spec baseline (17 ASIC disclaimer text mismatches + 3 variant-D structural). All `test_variant_has_vip[*]` (17) PASS — `wave5b_vip_pivot.py` correctly restored `$5` to the VIP card so the validator's `$5` substring check passes.

### PR #213

```
139 passed, 37 failed in 0.40s
```

PASS (relative to main baseline). The 37 failures consist of:
- 17 × `test_variant_has_asic_disclaimer[*]` — pre-existing on main
- 17 × `test_variant_has_vip[*]` — pre-existing on main (caused by PR #211 in main stripping `$5` from variants; the validator's `$5` substring check now fails)
- 3 × `TestVariantD` structural — pre-existing on main

PR #213 introduces **0 new test failures** — same failure set as main HEAD (76d4bdd). However, sales-skill's main baseline has shifted from 20 → 37 failures since the spec was written, due to PR #211's $5-strip. PR #212's pivot script restores those failures (170 pass vs 139 pass) by reintroducing `$5` in the VIP block.

---

## Summary — what to do before Phase B

### MUST FIX

1. **PR #213**: rewrite the changed lines in `web/templates/campaign.html` (lines 224, 228, 234, 244-247) to use the post-pivot canonical:
   - Button text: `'Secure VIP Access'` (not "Become a VIP Supporter")
   - Badge text: `'VIP CONFIRMED'` or `'VIP ACCESS'` (not "VIP SUPPORTER CONFIRMED")
   - Success message: replace the "thank-you/supporter contribution/priority SMS" framing with the post-pivot "Your VIP early access is confirmed. You'll get early private access to the investment offer when the campaign opens at Birchal..." framing
   - Drop the equal-access disclosure paragraph — Birchal explicitly does not require it (per §9 item 1). Keep only the s738ZG(6) safe-harbour and the refund/$5 line.
   - Re-verify with `grep -n "priority\|preferential\|VIP Supporter" web/templates/campaign.html` → should return zero matches.

2. **PR #89**: either:
   - **Option A (rewrite)**: regenerate `CSF-VIP-NEW-COPY.md` against the post-pivot canonical from `CSF-VIP-COPY-PACKAGE.md` + Birchal §9. All "VIP Supporter" → "VIP", all "priority SMS" → "early access", drop the equal-access disclosure section (1.4 second bullet), allow "early access" / "early private access" phrasing.
   - **Option B (drop)**: close PR #89 unmerged. `CSF-VIP-COPY-PACKAGE.md` (currently uncommitted on main, due to be committed in Phase B step 7) serves the canonical-spec role post-pivot, making PR #89's doc redundant.

### SHOULD CLARIFY (soft flag — founder decision)

3. **PR #88**: decide whether to:
   - Merge as-is (it's a historical audit; ships fine as audit trail)
   - Add a 2-line "PIVOT 2026-04-26" banner at the top of `CSF-VIP-TOUCHPOINTS-AUDIT.md` so future readers know the severity rubric and gap calls pre-date Birchal's response

### READY TO MERGE (no changes needed)

- PR #87 — marketing copy doc, fully post-pivot
- PR #90 — compliance rules + fixtures, fully post-pivot
- PR #212 — Wave 5b LP/email rewrite, pivot script applied successfully

### Pre-flight items still pending (per CSF-VIP-GO-LIVE-PLAN.md §Pre-flight)

- Item 5 (variant validator scarcity) — DECISION PENDING
- Item 6 ("early access" compliance gap) — RESOLVED by Birchal pivot (Birchal explicitly approved "early private access to the investment offer" — phrase is no longer banned)

---

## Inventory of failures (quick reference)

| PR | File | Line(s) | Phrase | Why it fails |
|---|---|---|---|---|
| #213 | `web/templates/campaign.html` | 224, 228, 234 | `Become a VIP Supporter` | "VIP Supporter" banned in customer copy |
| #213 | `web/templates/campaign.html` | 244 | `VIP SUPPORTER CONFIRMED` | "VIP Supporter" banned in customer copy |
| #213 | `web/templates/campaign.html` | 246 | `priority SMS notification` | "priority" globally banned (founder direction 2026-04-26) |
| #213 | `web/templates/campaign.html` | 246 | `Your $5 supporter contribution` | Pre-pivot framing — should be "VIP early access" |
| #213 | `web/templates/campaign.html` | 247 | `does not provide earlier or preferential investment access` | Equal-access disclosure DROPPED by Birchal |
| #213 | `web/templates/campaign.html` | 224, 228, 234, 244 | (button text and success state missing canonical "Secure VIP Access" CTA + post-pivot success copy) | Should match `CSF-VIP-COPY-PACKAGE.md` canonical |
| #89 | `clients/farm-thru/CSF-VIP-NEW-COPY.md` | 23-26 | `VIP Supporter` as canonical badge | Pre-pivot canonical spec |
| #89 | `clients/farm-thru/CSF-VIP-NEW-COPY.md` | 32-36 | `priority SMS` as canonical deliverable | Pre-pivot canonical spec |
| #89 | `clients/farm-thru/CSF-VIP-NEW-COPY.md` | 43 | Equal-access disclosure as REQUIRED | Birchal dropped this requirement |
| #89 | `clients/farm-thru/CSF-VIP-NEW-COPY.md` | 54-61 | Bans phrases now Birchal-approved (`first access to the offer`, `head start`, `VIP investor`, `VIP investors get priority access`) | Pre-pivot ban list contradicts Birchal §9 |
| #89 | `clients/farm-thru/CSF-VIP-NEW-COPY.md` | 79-100 | Pre-pivot HTML spec for `<section class="vip">` | Spec contradicts the post-pivot template applied by PR #212's pivot script |

---

## Cleanup notes

- Temporary worktrees created at `/tmp/csf-premerge/{ll-pr*,ss-pr*}` were removed (`git worktree remove --force`)
- Cached PR diffs at `/tmp/csf-premerge/diffs/` retained for reference
- Untracked FMTH compliance fixtures in the local worktree (originally leaked from a prior PR #90 worktree session) were briefly set aside during the eval run and then restored to their original location

---

*This report is read-only. No PRs were merged, no code or rules modified, and no Cloud Scheduler / Stripe / FMTH config changes were made. Phase B and Phase C remain blocked pending the two BLOCKER fixes above.*
