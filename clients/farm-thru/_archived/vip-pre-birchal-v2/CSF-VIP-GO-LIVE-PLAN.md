# CSF VIP — Path to Go Live (Wave 5b shipping plan)

**Date written**: 2026-04-26
**Status**: All copy work in PRs, none merged. Birchal submission sent 2026-04-26 (awaiting response). SMS will be sent manually (no Twilio integration). Cloud Scheduler PAUSED. FMTH `compliance.enabled` = false.

---

> ## ⚠️ PIVOT 2026-04-26 — READ FIRST
>
> **Birchal responded** on 2026-04-26 with required changes (NOT silent approval):
> 1. Mandatory disclosure #2 (equal-access) is NOT REQUIRED — drop everywhere
> 2. "Early private access to the investment offer" is APPROVED language
> 3. Founder direction added: NEVER use "priority" — globally banned, replace with "early"
>
> **All three changes have been implemented** across 6 PRs (was 5 — added PR #90 for compliance rules):
> - sales-skill #212 (3 new commits 2026-04-26: 280f552 + f7627eb + c4200cc)
> - learning-loop #87 (commits c0e9f75 + 5b88626)
> - learning-loop #90 NEW (FMTH-PRIORITY-001 + 2 doc rules + 5 fixtures)
> - sales-skill #213, learning-loop #88, learning-loop #89 unchanged
> - Main learning-loop docs (BIRCHAL-SUBMISSION §9 audit trail, COPY-PACKAGE rewritten, RESEARCH POST-RESEARCH UPDATE) updated, uncommitted
>
> **Treat Birchal's response as effective sign-off.** The plan body below is pre-pivot; refer to memory file `project_csf_compliance_engine_plan.md` for current canonical state. Phase A grep checks below MUST be extended to verify priority=0 + equal-access=0 + early-access PRESENT (not absent) across all 6 PRs.
>
> Canonical VIP card and revised disclosure list live in `CSF-VIP-COPY-PACKAGE.md` and `CSF-VIP-BIRCHAL-SUBMISSION.md` §9.

---

## TL;DR

After Birchal signs off + 5 founder decisions resolved, run **3 sequential agents** (~2 hours total) to: merge 5 PRs in order, ship docs, verify production, enable compliance gate, resume scheduler. Each phase has a hard gate — user reviews output before next phase runs.

---

## Pre-flight (founder decisions, BEFORE running agents)

1. **Birchal sign-off** on `CSF-VIP-BIRCHAL-SUBMISSION.md` — **RESOLVED (in flight)**: submission sent to Birchal 2026-04-26, awaiting response. Still a hard gate before merging.
2. **SMS decision** (task #59) — **RESOLVED**: founder will use a MANUAL SMS provider (no Twilio integration). The SMS template stays in the copy package; sends are done by hand from a manual provider tool. The "build Twilio integration" work is dropped.
3. **Birchal offer URL** — **RESOLVED**: `{{birchal_url}}` stays as the general CSF risk warning page (`https://www.birchal.com/legal-pages/general-csf-risk-warning`). The FMTH offer doesn't open until June 2026 so this is fine for now. **Future TODO**: when the offer goes live in June, this should likely swap to the FMTH offer page on Birchal.
4. **Refund SLA** — **RESOLVED**: "within two business days" confirmed by founder.
5. **Variant validator scarcity** (task #61) — **DECISION PENDING**: discussion doc at `clients/farm-thru/CSF-VIP-SCARCITY-DISCUSSION.md`. Agent recommends **Option 3 — reframe scarcity around the WAITLIST** (a separate product from the share offer). *"Waitlist closes before launch"* is true, regulator-safe, keeps the conversion mechanism alive. ~1-2 hrs work. Awaiting founder approval.
6. **"Early access" compliance gap** — **DECISION PENDING**: scarcity agent discovered that 2 of 17 LP variants in sales-skill PR #212 still contain the phrase "early access" — quasi-banned (same regulatory risk profile as "first access to invest"). Either fix as a small follow-up commit on PR #212 (~15 min) OR add to the canonical banned-phrase list and re-run the rewrite agent against just those 2 files. Either way, **must be cleaned before merging PR #212**.

---

## State of the world — PRs to merge

| Repo | PR | Branch | Size | What |
|---|---|---|---|---|
| sales-skill | [#213](https://github.com/jb-git72/sales-skill/pull/213) | `fix/campaign-html-csf-compliance` | 1 file | campaign.html banned-phrase fix |
| sales-skill | [#212](https://github.com/jb-git72/sales-skill/pull/212) | `feature/csf-vip-rewrite-wave5b` | 28+ files | Wave 5b VIP rewrite (LP, emails, Stripe, drips, mission-control, REFERENCE, meta.json Birchal URL, "Updates" rename) |
| learning-loop | [#88](https://github.com/jb-git72/learning-loop/pull/88) | `feature/csf-vip-audit-wave5b` | 1 doc | Touchpoints audit |
| learning-loop | [#87](https://github.com/jb-git72/learning-loop/pull/87) | `worktree-agent-a0a6be1a58fb5e959` | 1 doc | Marketing-comms copy |
| learning-loop | [#89](https://github.com/jb-git72/learning-loop/pull/89) | `worktree-agent-acc01fb0c7ba93864` | 1 doc | Canonical in-product copy spec |

**Plus 8 uncommitted docs** in main learning-loop (`clients/farm-thru/`) — committed in Phase B:
- `CSF-VIP-BIRCHAL-SUBMISSION.md`
- `CSF-VIP-COPY-PACKAGE.md`
- `CSF-VIP-BRAINSTORM.md`
- `CSF-VIP-RESEARCH.md`, `-RG261.md`, `-RG262.md`
- `CSF-VIP-SCARCITY-DISCUSSION.md`
- `CSF-VIP-GO-LIVE-PLAN.md` (this file)

---

## Phase A — Pre-merge readiness (Agent 1, ~30 min)

**Use**: `general-purpose`, `isolation: worktree`. **READ-ONLY** — do NOT merge.

**Tasks**:
1. For each of the 5 PRs: fetch branch, check `git merge --no-commit --no-ff` for conflicts with `origin/main`
2. Run `pytest engine/tests/` against each learning-loop PR branch
3. Run sales-skill test suite (find runner) against #212 + #213
4. grep banned-phrase list (per `CSF-VIP-BIRCHAL-SUBMISSION.md` §5) PLUS the extended set in `CSF-VIP-NEW-COPY.md` §1.5 (head start, 24 hours before, etc.) PLUS explicitly **"early access"** across each PR diff — **ZERO matches required** (Note: pre-flight item 6 must be resolved before this can pass)
5. grep for `s738ZG(6)` safe-harbour + equal-access disclosure presence across every VIP touchpoint per PR
6. Run `python3 scripts/eval_compliance_accuracy.py` — must hit 100% (36/36)
7. Run `python3 scripts/dry_run_compliance.py --include-broken-fixture --out clients/farm-thru/loop/compliance-dry-run-CALIBRATED-2026-04-XX.md` against rewritten FMTH content (this is the Wave 5a re-run, task #50)
8. Output: `clients/farm-thru/CSF-VIP-PREMERGE-CHECK.md` with PASS/FAIL per check

**Gate**: if anything fails → STOP, surface to user, do NOT proceed to Phase B.

---

## Phase B — Merge + ship docs (Agent 2, ~30 min)

**Use**: `general-purpose`, `isolation: worktree`. **Gate**: only after Agent 1 returns all PASS.

**Tasks (exact order)**:
1. `gh pr merge 213 --repo jb-git72/sales-skill --squash --delete-branch`
2. `gh pr merge 212 --repo jb-git72/sales-skill --squash --delete-branch`
3. Verify sales-skill main builds + tests pass post-merge: `cd /Users/jb/Documents/GitHub/sales-skill && git checkout main && git pull && pytest`
4. `gh pr merge 87 --repo jb-git72/learning-loop --squash --delete-branch`
5. `gh pr merge 88 --repo jb-git72/learning-loop --squash --delete-branch`
6. `gh pr merge 89 --repo jb-git72/learning-loop --squash --delete-branch`
7. Commit the 7 uncommitted CSF-VIP-* docs from main learning-loop on new branch `docs/csf-vip-shipping`, push, open PR titled `"docs(vip): ship CSF VIP wave 5b documentation set"`, squash-merge after CI passes

**DO NOT** enable `compliance.enabled` or resume Cloud Scheduler — that's Phase C.

**Gate**: if any merge fails → STOP, surface to user.

---

## Phase C — Production verify + activate (Agent 3, ~45 min)

**Use**: `general-purpose`, `isolation: worktree`. **Gate**: only after Agent 2 returns success.

### Step 1 — Production verification
- WebFetch live URLs: `https://join.farmthru.com.au` and any FMTH variant subpaths
- For each, verify: ZERO banned phrases · s738ZG(6) safe-harbour present · equal-access disclosure present · "VIP Supporter" branding (not bare "VIP")
- Output: `clients/farm-thru/CSF-VIP-LIVE-VERIFICATION.md`

### Step 2 — Manual check flags (surface to user, agent does NOT do these)
- Stripe checkout description (Stripe dashboard)
- Mission-control admin VIP card subject lines

### Step 3 — Enable compliance gate
Edit `clients/farm-thru/config.json` to add:
```jsonc
"compliance": {
  "enabled": true,
  "applies_to": "issuer",
  "enable_llm": true,
  "model": "claude-sonnet-4-6"
}
```
Commit on `feat/fmth-enable-compliance-gate`, PR, squash-merge.

### Step 4 — Resume Cloud Scheduler (REQUIRES user confirmation)
**DO NOT auto-run.** Surface this command for the user to execute manually:
```bash
gcloud scheduler jobs resume fmth-drip-hourly --location=<region>
```

### Step 5 — Post-activation smoke test
After scheduler resumes (~5 min wait), check Cloud Logging for the first `drip_engine` run. Verify clean completion.

---

## Rollback plan

If anything breaks post-merge:
1. Sales-skill: `gh pr revert <pr> --repo jb-git72/sales-skill`
2. learning-loop: same pattern for any docs PR that needs reverting
3. `gcloud scheduler jobs pause fmth-drip-hourly --location=<region>`
4. Revert FMTH `config.json` compliance change
5. Notify Birchal of rollback

---

## Tasks closed by this plan

- #34 Resume Cloud Scheduler → Phase C step 4
- #50 Wave 5a re-run → Phase A step 7
- #52 Rewrite VIP copy → done (PRs #212/#213)
- #56 Birchal sign-off → submitted 2026-04-26, awaiting response (still pre-flight gate)
- #57, #58, #60, #62 → done
- #59 SMS pipeline → resolved: manual SMS provider, no Twilio integration needed
- #61 Variant validator scarcity → still OPEN, separate discussion in flight

---

## Notes for resumption after compact

- All agents use `isolation: worktree`
- All agents use feature branches (no direct main commits except the docs commit, which goes through a PR)
- User reviews each phase output before proceeding to next — three hard gates
- Total estimated time: ~2 hours active + Birchal sign-off lead time
- Read this doc + `CSF-VIP-BIRCHAL-SUBMISSION.md` + project memory `project_csf_compliance_engine_plan.md` to fully resume context post-compact
- All Wave 5b docs live in `clients/farm-thru/CSF-VIP-*.md`
