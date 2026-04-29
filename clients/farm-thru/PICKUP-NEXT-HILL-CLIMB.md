# Pickup — next FMTH hill-climb

**Last session:** 2026-04-28 evening through 2026-04-29 morning.
**State of main:** clean. 13 PRs merged (#117 → #134).

## What "ready to run" looks like
- All 18 FMTH meta-ads use the canonical asterisked CSF line. Lint 18/18 PASS.
- Live $2-lead ad scores **0.8523 / production_ready** (PR #134 spot-score).
- Rubric weights tuned via PR #132 (`scroll_stop_hook` 2.0; `opening_diversity` / `objection_preemption` / `platform_fit` 0.5).
- ADV-001 lint gate enforces canonical CSF presence (PR #129) — variants without it auto-retry, then auto-append as fallback.
- Random-mode `targeted` routes to `hook_swap` for strong seeds ≥0.65 (PR #130).
- `--hypothesis-driven` mode is reliable post-PR-#131.

## Run the hill-climb

### Recommended (full 18-ad evolutionary run)
```bash
cd /Users/jb/Documents/GitHub/learning-loop
nohup python3 -u scripts/hill_climb.py farm-thru 8 --type meta-ad \
  --strategy evolutionary --population 4 --workers 4 --target 0.85 \
  > clients/farm-thru/loop/hill-climb-$(date +%Y%m%d).log 2>&1 &
echo "PID $!"
```

Monitor: `tail -F clients/farm-thru/loop/hill-climb-$(date +%Y%m%d).log | grep -E "Iteration|ACCEPTED|target|TOURNAMENT"`

Expected wall-clock: ~1 hour for 8 iterations × 18 ads × 4 candidates each.
Expected outcome:
- Live ad stays near 0.85 (it's near-optimal — Phase 3 confirmed all hook-swap variants drop ~0.13).
- Weaker seeds (BR-104 0.67, BR-105 0.68) lift the most.
- New angles surface — Empathy + Social Belonging are now first-class but under-used in current 18.

### Hypothesis-driven on a single seed (surgical)
```bash
python3 scripts/hill_climb_from_seed.py clients/farm-thru/loop/live-ad-test.json \
  --hypothesis-driven --hypotheses 4 --max-variants 4 --max-minutes 10
```
Use this when you want to probe what makes a specific seed work, not when you want to expand the cohort.

### ⚠️ DO NOT use hill_climb_from_seed.py for client-approval variants

Hill-climb modes (improve/mutate/targeted/hook_swap) do small-radius edits — output reads as the same ad reworded ("Own a piece" → "Own a slice" → "Own a share"). Client will reject as "the same ad four times". For approval-sheet variants:

1. **Hand-write 4** against the seed's beat structure (hook → reveal → proof → scarcity → CTA → CSF). Vary only the hook concept.
2. Or **curate from `clients/farm-thru/loop/meta-ads/`** for a separate "explore alternatives" tab — but flag clearly that they're alternatives, not variants of the seed.
3. **Fact-check** against `clients/farm-thru/facts.json` before shipping. Every number, timeline, count, region must be verified. Don't trust the seed — proven ads can carry stale facts (the live $2-lead ad's "Eight NSW farms" needed reconciliation against BM-003 on 2026-04-29).
4. Add the result to the **canonical approval sheet** as a new tab, never a fresh spreadsheet:
   ```bash
   python3 scripts/build_fmth_approval_sheet.py --max-variants 4 \
     --sheet-id 1UrejvBt9m2PtPb0EpCwgwZnUjCtUS3UVDMHxiUVqYs0 \
     --tab-name "<direction> hooks (YYYY-MM-DD)"
   ```

## Post-run steps

1. **Score the new corpus:**
   ```bash
   python3 scripts/score_batch.py farm-thru --type meta-ad \
     > clients/farm-thru/loop/scored-$(date +%Y%m%d).json
   ```

2. **Build the review HTML:**
   ```bash
   python3 scripts/build_review_html.py \
     clients/farm-thru/loop/scored-$(date +%Y%m%d).json \
     clients/farm-thru/loop/review-$(date +%Y%m%d).html
   ```

3. **Build the FMTH approval sheet** (if you want a fresh one):
   ```bash
   python3 scripts/build_fmth_approval_sheet.py \
     --share-with jeremy@launcherlab.com.au
   ```
   The current approval sheet is at https://docs.google.com/spreadsheets/d/1UrejvBt9m2PtPb0EpCwgwZnUjCtUS3UVDMHxiUVqYs0/edit

## Watch for
- **LLM-judge variance ±0.07 composite.** Same ad rescored may differ by ±0.05–0.10. Not a regression.
- **Hook-swap variants will under-perform a strong seed by ~0.13** — that's by-design (Phase 3 finding); the loop is correctly identifying the seed's hook as load-bearing.
- **Time cap.** Each hill-climb attempt ~80s with LLM scoring. Set `--max-minutes` realistically (10 min = ~6–7 attempts).

## Open follow-ups (NOT blockers — only do if you want incremental polish)

1. **N=3 median LLM scoring** to reduce variance to ±0.02. Spec in `validation/THRESHOLD-ANALYSIS-V1.md`.
2. **MISL-001 hint in hypothesis-generator prompt** — one Phase 3 probe tripped it for "first grocery store in Australia". Cheap add: warn the prompt against unbacked superlatives.
3. **Cross-client validation** on BFP / Tyroola — the recalibrated rubric is FMTH-tuned. Default weights should keep other clients inert but no empirical check yet.
4. **Gitignore or snapshot** `clients/farm-thru/loop/live-ad-variants/` (changes every run, currently uncommitted).

## Where things live (so you don't have to hunt)

- **Live $2-lead ad seed:** `clients/farm-thru/loop/live-ad-test.json`
- **Existing FMTH meta-ads:** `clients/farm-thru/loop/meta-ads/` (18 files, all canonical CSF)
- **Last hill-climb output:** `clients/farm-thru/loop/scored-recalibrated.json`
- **Hypothesis dossiers:** `validation/HYPOTHESIS-DOSSIER.md` (v1, pre-fix), `validation/HYPOTHESIS-DOSSIER-V2.md` (v2, post-fix)
- **CFE-AU playbook:** `shared/playbooks/cfe-au.json` + `.md`
- **Hook archetypes:** `shared/hooks.json` (22 hooks; 5 added 2026-04-28)
- **Compliance rules:** `shared/regulatory/csf-australia/compliance_rules.json` (98 rules)
- **FMTH rubric weights:** `clients/farm-thru/config.json` `rubric.meta-ad.weights`
- **Tests:** `engine/tests/` (74 pass)
- **Morning report (full overnight summary):** `clients/farm-thru/MORNING-REPORT-2026-04-29.md`

## Memory pointers (read at session start)

- `project_loop_2026_04_29_autonomous_complete.md` — what shipped overnight + remaining follow-ups
- `project_loop_2026_04_28_three_agents.md` — three-agent run findings (Auditor/DomainExpert/Empiricist)
- `project_fmth_csf_universal.md` — every FMTH ad needs the CSF line; not optional
- `MORNING-REPORT-2026-04-29.md` — composite trajectory + verification commands

## One-paragraph context if you need to brief someone

The FMTH loop has been recalibrated to learn from the live $2-lead ad. The rubric now rewards what makes that ad work (curiosity-gap hook with narrow novelty bound, ownership framing, soft scarcity, founder voice, asterisked CSF placement, outcome-stated CTA). Five real engine bugs were caught and fixed (most consequential: every meta-ad's `cta` field was a bucket label rather than an actual CTA string, scoring everything 2/5 on `cta_clarity` for no reason). A hypothesis-driven hook-swap mode lets you surgically probe what's load-bearing on a strong seed — Phase 3 confirmed the live ad's hook genuinely carries the win, not its body or scarcity. Next hill-climb should produce variants that pass compliance reliably, score against a rubric that actually discriminates, and surface lift on the weaker seeds in the cohort. The live ad itself is near-optimal — don't expect to beat it; the value is in lifting the floor and exploring new angles.
