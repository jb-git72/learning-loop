# FMTH email rewrite plan (2026-04-24)

Written pre-compact. Post-compact, read this first.

## The ask

User: "drips don't seem great — unclear what value they add or how they help increase desire to invest. Reduce to welcome + 3 drips per segment. Use the copy-generation pipeline we used for landing pages + ads."

Data backs the complaint: FMTH emails avg 0.70 composite in `scored_r3_pass8.json`; meta-ads avg 0.93+. Emails under-converge because (a) the pipeline ran fewer hill-climb passes on them, (b) the copy leans on fabricated stats, (c) the sequence tries to sell on every touch instead of building conviction across touches.

## Decisions (confirmed 2026-04-24)

1. **Rachel Ward = co-founder.** Primary framing. Also founder of Rachel's Farm (Kempsey) and a key FarmThru partner/supplier. `facts.json:FP-001` reconciled to lead with co-founder while preserving the Rachel's Farm + partner/supplier context. `tone.md:95` already said "co-founder" and stays.
2. **VIP early access = REAL.** 24-hour head start on the Birchal offer link is a mechanical guarantee, not aspirational. V3 copy may claim it confidently.
3. **Launch date = 2026-06-23.** Already reconciled via PR #73. `facts.json:INV-006` HIGH confidence. Sales-skill must align.

## Strategy summary (from Agent 2)

Replace 6-drip unsegmented sequence with **segmented welcome + 3 drips**:

| Slot | Non-VIP | VIP |
|---|---|---|
| Welcome | Immediate, "you're on the list, here's what's coming, upgrade to VIP for $5 refundable" | Immediate (Stripe webhook), "VIP #X locked, you'll get the offer before the public list" |
| Drip 1 | +3d signup — "the hub that doesn't exist yet" — product-first, name 3-4 real partner farms, CTA = VIP upgrade | +3d deposit — insider note Rachel wouldn't share publicly, soft CTA = "reply with questions" |
| Drip 2 | +10d signup — "why we need to own this ourselves" — CFE mechanism, min/max, honest risk, CTA = VIP upgrade | +10d deposit — "how the offer will work" — Birchal mechanics, timeline, pre-empt decision paralysis |
| Drip 3 | Launch −7d — "the round opens [date]" — calendar prep, pre-commitment | Launch −1d — "your early-access link for tomorrow" — direct Birchal URL, day-1 funding matters |

**Timing rationale:** signup-anchored for drips 1-2 (story/mechanism doesn't need launch context), launch-anchored for drip 3 (every subscriber needs a pointed nudge while the round is actually opening, regardless of when they signed up).

**Separate 3+3, not shared with merge tags.** VIPs and non-VIPs need fundamentally different jobs done (prepare vs convince), not the same copy with conditional branches.

Full strategy brief with subjects, openings, and core beats per email is in this document's git history / agent output — condense into seed JSONs when generating.

## Pipeline readiness (from Agent 1)

- Engine, writer, schemas, rubric — all support content_type=email. No code changes needed.
- FMTH has config.json, facts.json, tone.md, rules.json, learnings.md, learnings-email.md, plus content-type learnings files — all under 2000 char budget.
- Canonical command works: `python3 scripts/hill_climb.py farm-thru 5 --type=email --target=0.75 --strategy=evolutionary --population=5 --workers=4 --use-pairwise`
- ⚠ Do NOT use `--strategy=map-elites` for email — hill_climb.py:763 hardcodes `content_type="meta-ad"` on that path. Evolutionary is fine.

## Execution phases

**Phase 0 — Decisions (blocks everything).** DONE 2026-04-24. See "Decisions" section above.

**Phase 1 — Prep learning-loop (local).** DONE 2026-04-24.
- a. `facts.json:FP-001` reconciled — Rachel = co-founder (primary), + founder of Rachel's Farm, + partner/supplier. `tone.md:95` already aligned.
- b. `clients/farm-thru/learnings-email.md` rewritten: welcome + 3-drip-per-segment structure, signup-anchored drips 1-2, launch-anchored drip 3, Rachel as co-founder voice, truth-claim rules, per-segment jobs. 1987 chars, within 2000-char budget. `check_learnings.py` passes.
- c. Old seeds (EM-001.json..EM-007.json) moved to `clients/farm-thru/loop/emails/_archive/`.
- d. 8 new seed JSONs created (welcome + 3 drips × 2 segments):
  - `EM-WELCOME-NONVIP.json` (segment=nonvip, email_type=welcome, funnel=TOF)
  - `EM-WELCOME-VIP.json` (segment=vip, email_type=welcome, funnel=MOF)
  - `EM-NONVIP-01.json` (segment=nonvip, email_type=nurture, funnel=TOF)
  - `EM-NONVIP-02.json` (segment=nonvip, email_type=nurture, funnel=MOF)
  - `EM-NONVIP-03.json` (segment=nonvip, email_type=countdown, funnel=BOF)
  - `EM-VIP-01.json` (segment=vip, email_type=founder_story, funnel=MOF)
  - `EM-VIP-02.json` (segment=vip, email_type=nurture, funnel=MOF)
  - `EM-VIP-03.json` (segment=vip, email_type=announcement, funnel=BOF)
  All 8 pass `scripts/lint_content.py` with 0 critical + 0 warnings.
- e. Segment encoded in `tactic` field (`segment:{nonvip|vip}|drip-{N}|...`). No rubric schema change. Clean for this run; first-class `segment` field can be added later if needed.

**Phase 2 — Generate + hill-climb (READY TO RUN).**
```
cd /Users/jb/Documents/GitHub/learning-loop
python3 scripts/hill_climb.py farm-thru 5 --type=email --target=0.75 \
    --strategy=evolutionary --population=5 --workers=4 --use-pairwise \
    2>&1 | tee clients/farm-thru/loop/hill-climb-emails-rewrite.log
python3 scripts/score_batch.py farm-thru > clients/farm-thru/loop/scored_emails_rewrite.json
```
Target: all 8 emails score ≥ 0.75 composite. Expect 30-60 min LLM compute.

**Phase 3 — Human review.**
```
python3 scripts/build_review_html.py \
  clients/farm-thru/loop/scored_emails_rewrite.json \
  clients/farm-thru/loop/review_emails_rewrite.html
```
User reviews, flags anything to iterate on, edits in place via the HTML review interface.

**Phase 4 — Iterate (only if Phase 3 surfaces issues).** Update learnings-email.md with feedback patterns, re-run hill-climb on flagged items only.

**Phase 5 — Convert JSON → HTML drip templates in sales-skill.**
- Write 6 new HTML templates (3 nonvip + 3 vip) under `sales-skill/web/campaigns/FMTH/emails/`:
  - `drip_nonvip_1.html`, `drip_nonvip_2.html`, `drip_nonvip_3.html`
  - `drip_vip_1.html`, `drip_vip_2.html`, `drip_vip_3.html`
- Update the 2 welcome sends:
  - Regular welcome: rewrite `campaign_emails.py::_build_campaign_email` with new copy
  - VIP welcome: rewrite `drip_vip_welcome.html`
- Script to convert: extend `scripts/build_fmth_emails.py` (already maps EM-002..EM-007 → drip_1..6) to use the new seed IDs.

**Phase 6 — Code changes in sales-skill.**
- `campaign_drip.py::DRIP_SCHEDULE` → split into `DRIP_SCHEDULE_NONVIP` and `DRIP_SCHEDULE_VIP`:
  ```
  DRIP_SCHEDULE_NONVIP = [
      ("drip_nonvip_1.html", 3, False),
      ("drip_nonvip_2.html", 10, False),
      ("drip_nonvip_3.html", -7, True),  # launch -7
  ]
  DRIP_SCHEDULE_VIP = [
      ("drip_vip_1.html", 3, False),
      ("drip_vip_2.html", 10, False),
      ("drip_vip_3.html", -1, True),  # launch -1
  ]
  ```
- `process_drip_emails` — branch on `signup.get("vip", False)`. Firestore signup docs already get `vip: true` on Stripe webhook (per earlier backfill script / sheet-sync).
- Delete old `drip_1_founder.html..drip_6_live.html` (or move to `_archive/`).
- VIP welcome trigger: already fires on Stripe webhook — template filename stays `drip_vip_welcome.html`, just content changes.

**Phase 7 — Visual QA.** Run `scripts/send_drips_to_email.py --flow nonvip|vip` to blast both new flows to a test inbox. Update the `FLOWS` constants in that script to match the new 4-per-segment structure (welcome + 3 drips).

**Phase 8 — Deploy.**
- Commit learning-loop changes (new seeds, logs, review HTML) on its own branch/PR.
- Commit sales-skill changes (new templates + code) on its own branch/PR.
- Merge both. Run `cd sales-skill/web && ./deploy.sh`.
- Resume the Cloud Scheduler `fmth-drip-hourly` after visual QA passes.

## Ordering + gating

- Phase 0 blocks everything else.
- Phase 1 can start immediately after Phase 0.
- Phase 2-3 are sequential (generate → review).
- Phase 4 loops back to Phase 2 if review says iterate.
- Phase 5-6 can run in parallel (separate repos).
- Phase 7 gates Phase 8 (no deploy without visual QA).

## What gets committed where

- **learning-loop PR**: `clients/farm-thru/learnings-email.md` (trimmed), `clients/farm-thru/tone.md` or `facts.json` (contradiction fix), `clients/farm-thru/loop/emails/_archive/*` (moved old seeds), `clients/farm-thru/loop/emails/EM-*.json` (7 new), `clients/farm-thru/loop/hill-climb-emails-rewrite.log`, `clients/farm-thru/loop/scored_emails_rewrite.json`, `clients/farm-thru/loop/review_emails_rewrite.html`
- **sales-skill PR**: `web/campaigns/FMTH/emails/drip_{nonvip,vip}_{1,2,3}.html` (new), `web/campaigns/FMTH/emails/drip_vip_welcome.html` (updated), `web/campaign_emails.py::_build_campaign_email` (updated), `web/campaign_drip.py` (segmented DRIP_SCHEDULE + VIP branch in process_drip_emails), `scripts/send_drips_to_email.py` (FLOWS update), optional: delete `web/campaigns/FMTH/emails/drip_[1-6]_*.html`

## Compact prep

Save this file (`clients/farm-thru/EMAIL-REWRITE-PLAN.md`) and update MEMORY.md pointer. Post-compact, the plan + the 3 open-question answers are enough to resume.

Agent outputs (full strategy brief + pipeline audit) live in the current session transcript at `/Users/jb/.claude/projects/-Users-jb-Documents-GitHub-learning-loop/d572361f-b829-4db3-817b-3e1a945010ff.jsonl` if needed.
