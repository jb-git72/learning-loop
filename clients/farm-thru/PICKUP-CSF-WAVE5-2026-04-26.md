# CSF compliance — Wave 5 pickup (2026-04-26)

Read this first when resuming the CSF compliance work after compact.
Two distinct workstreams to pick up:
1. **Wave 5a** — re-run FMTH dry-run against calibrated rules; compare to baseline.
2. **Wave 5b** — research + codify VIP fee architecture under CSF (the new exploration).

---

## State at handoff

### Shipped this session (PRs all merged to main)
| Wave | PR | What |
|---|---|---|
| 2 | #82 | 91 distilled rules from RG 261 + RG 262 (96 total) |
| 3a | #83 | compliance_checker wired as Gate 0 in scorer.py + writer.py |
| 3b | #84 | first FMTH dry-run + findings doc |
| 4 | #85 | Sonnet 4.6 + calibration → 100% accuracy on 36 fixtures |

### Eval scoreboard (post-Wave 4)
- 36 labeled fixtures, 12 rules covered, 3 fixtures each
- **100% accuracy** (36/36), 0 FP, 0 FN, 0 out-of-scope
- All 12 rules at F1 = 1.00 with Sonnet 4.6 + calibrated prompts
- Per-eval cost: ~$0.40 for 36 fixtures

### Calibrated rules (in `shared/regulatory/csf-australia/compliance_rules.json`)
- **MISL-001** — explicit handling of scheduled future dates (kills the 16x dry-run FPs on '23 June 2026')
- **MISL-002** — explicit "unstable number framing" pattern
- **MISL-004** — gate on forecast presence (PASS if no forecast)
- **ADV-004** — excludes marketing access language ("priority access", "first access to invest")
- **ADV-006** — length-aware carve-out for short Meta ads
- **ADV-017** — scope narrowed to `[offer-document]` only

### Model + config knobs available
- `engine/compliance_checker.py` defaults to `claude-sonnet-4-6`
- Per-rule override via `rule['model']` (use `claude-opus-4-7` for highest stakes)
- Per-client override via `config.compliance.model`
- `config.compliance.enable_llm: false` runs deterministic-only (cheap mode)
- Today's date auto-injected into every llm_judge prompt

### FMTH config — STILL NOT enabled
`clients/farm-thru/config.json` does NOT have a `compliance` section yet.
Don't enable in Wave 5a — first prove the calibrated dry-run is clean.

### Cloud Scheduler `fmth-drip-hourly` — still PAUSED (task #34)

---

## Wave 5a — re-run FMTH dry-run with calibrated rules

### Goal
Repeat the Wave 3b dry-run against the same 26 FMTH pieces but with
Sonnet 4.6 + calibrated rules. Confirm that the 16 MISL-001 + 17
ADV-017 + 13 MISL-004 false positives from 2026-04-26 are gone, and
that only the genuine catches (ADV-007 endorsements, ADV-013
superlatives, ADV-006 imbalance) remain.

### Commands
```bash
cd /Users/jb/Documents/GitHub/learning-loop
set -a && source .env && set +a
python3 scripts/dry_run_compliance.py --include-broken-fixture \
  --out clients/farm-thru/loop/compliance-dry-run-llm-CALIBRATED-2026-04-XX.md
```
Cost: ~$0.50, takes ~5-7 min (200 LLM calls on Sonnet 4.6).

### Expected delta vs 2026-04-26 baseline (`clients/farm-thru/loop/compliance-dry-run-llm-2026-04-26.md`)
- BLOCKING violations: 24 → expect ~5-8 (kill MISL-001 noise; keep ADV-007 sock-puppet catches)
- WARNING violations: 120 → expect ~50-70 (kill ADV-017 + MISL-004 noise; keep ADV-006/ADV-013/MISL-002 catches)
- Pass count: 8/26 → expect 18-22/26 passing

### After the re-run
Write a `clients/farm-thru/loop/COMPLIANCE-FINDINGS-CALIBRATED-2026-04-XX.md`
that compares baseline vs calibrated and lists the **genuine** catches
remaining (these are the things to either fix in copy or accept).

### Then decide on FMTH enablement
If the calibrated dry-run is clean enough, ship a small follow-up PR:
```jsonc
// clients/farm-thru/config.json
"compliance": {
  "enabled": true,
  "applies_to": "issuer",
  "enable_llm": true,
  "model": "claude-sonnet-4-6"
}
```
Then resume the scheduler (#34) and let the gate run on every hill-climb.

---

## Wave 5b — VIP fee architecture under CSF (NEW WORK)

### The question
The FMTH VIP scheme charges $5 (real Stripe charge) and grants:
- Priority access when the campaign opens (Birchal link 24h before public list)
- Exclusive founder updates
- Q&A session
- Refundable

ASIC's CSF regime is allergic to anything that looks like:
- **Inducement to invest** (RG 261.99, our ADV-014 rule)
- **Preferential allocation** outside the intermediary's process
- **Unequal investor treatment**
- **Soliciting investments** outside the licensed platform (s738Q gatekeeper, s736 anti-hawking)

### My prior (from end-of-conversation, to verify)
The load-bearing question is **what the $5 actually purchases**.
If $5 buys "first access to invest" → likely problematic (preferential
allocation as a paid product).
If $5 buys "SMS-when-the-round-opens" or "exclusive founder Q&A" or
"queue position on the comms list" → that's a separate, real service,
and earlier visibility of the Birchal link is a side-effect, not what's
being sold. Investment access at the Birchal end remains equal.

### Workstream 5b decomposition

#### 5b-1 — Research (read-only, no code)
Source: `shared/regulatory/csf-australia/rg261.md` + `rg262.md` (already in repo).
Specifically search for:
- Sections C and D of RG 261 — advertising, communications, allocation
- "preferential", "allocation", "premium", "inducement", "first access", "VIP"
- s738Q / s736 / s738ZG / s738ZG(6) / RG 261.99 / RG 261.111
- RG 262 Section C — gatekeeper duties, application form requirements,
  equal-treatment obligations on the intermediary
- "good fame and character" checks on directors (any conflict re: paid VIP?)
- Anti-hawking rules — does charging for "notifications" count as
  hawking when the notification IS the Birchal link?

Existing rules already in our library (don't duplicate):
- ADV-008 — financial assistance (loans/deposits to enable investing)
- ADV-014 — inducements (bonuses, gifts, discounts for investing)
- ADV-009 — single offer at a time
- ADV-010 — one intermediary per offer
- ADV-011 — personalised investment recommendations

Output: a short doc `clients/farm-thru/CSF-VIP-RESEARCH.md` summarising
what the regs say and where the gray zones are.

#### 5b-2 — Architecture decision matrix
Build a 2-axis table:
- Rows: VIP product variants (5-8 hypothetical structures)
  - "Pay $5 for first access to invest" (current framing — probably bad)
  - "Pay $5 for SMS notification when round opens" (probably OK)
  - "Pay $5 for exclusive Q&A access" (probably OK)
  - "Pay $5 to support FarmThru's marketing costs" (donation framing)
  - "Pay $5 for priority customer support post-investment" (post-launch service)
  - "Pay $5 for queue position on the public comms list" (gray)
  - "Pay $5 to buy a $5 voucher redeemable in the FarmThru shop" (gift card / store credit)
  - Combination: $5 buys SMS + Q&A access; investment access is downstream and equal
- Columns:
  - Inducement risk (ADV-014)
  - Preferential allocation risk
  - Anti-hawking risk (s736)
  - Unequal investor treatment risk
  - Verdict: GREEN / AMBER / RED
  - Mitigations needed

#### 5b-3 — New compliance rules (if research uncovers gaps)
Likely additions:
- **VIP-001** — VIP/early-access offerings tied to investment access (RED) —
  llm_judge that flags "pay $X for first access to invest" framing
- **VIP-002** — preferential allocation outside the intermediary's process (RED)
- **VIP-003** — paid product must be a real, separable service from
  investment access (AMBER) — flags vague benefit lists
- **EQUAL-001** — copy must not imply paid investors get better terms or
  more shares than non-paid (RED)

Add via the existing schema. Validate with `validate_compliance_rules.py`.
Author 2-3 fixtures per new rule and add to `engine/tests/fixtures/compliance/`.
Re-run `scripts/eval_compliance_accuracy.py` — must hit 100% before merging.

#### 5b-4 — Q&A artifact for the founder
Build a markdown FAQ at `clients/farm-thru/VIP-LEGAL-QA.md` that the
founder can use as the source-of-truth when explaining the VIP scheme:
- "What does the $5 buy?" (the customer-facing answer)
- "Is this a payment for early investment access?" (NO — explain why)
- "What happens to the $5?" (refundable / charged to revenue / etc.)
- "What does a VIP customer actually get?"
- "What does a non-VIP customer NOT get?"
- "Is this preferential allocation?"
- "How is investment access still equal?"

This is the customer-comms backbone and the legal defence in one doc.

#### 5b-5 — Eval against FMTH VIP copy
Run the full eval pipeline against:
- The current LP VIP section copy (`web/campaigns/FMTH/index*.html` —
  the `<section class="vip">` block)
- The current welcome email's VIP framing
- The Stripe checkout description
- The mission-control admin VIP descriptions

Score against existing rules + new VIP-* rules. Surface specific lines
to rewrite if needed.

### Wave 5b sequence
1. Spawn one agent to do research (5b-1) — output to research doc.
2. While agent runs, build the decision matrix (5b-2) skeleton.
3. After research lands: walk findings, write VIP-001..EQUAL-001 rules.
4. Author fixtures for the new rules; run eval.
5. Generate the Q&A doc.
6. Run eval against actual FMTH VIP copy; report findings.

Estimated cost: ~$2 in LLM calls. Estimated time: ~2-3 hours focused work.

---

## Reference paths

### CSF compliance project
- `engine/compliance_checker.py` — runtime checker
- `engine/scorer.py` — Gate 0 wiring
- `writer.py::_build_rules_summary()` — compliance prompt injection
- `shared/regulatory/csf-australia/`
  - `rg261.md` — verbatim source (264KB)
  - `rg262.md` — verbatim source (111KB)
  - `compliance_rules.json` — 96 rules (calibrated)
- `engine/tests/`
  - `test_compliance_checker.py` — 9 unit tests
  - `test_scorer_compliance_gate.py` — 3 integration tests
  - `fixtures/compliance/` — 36 labeled fixtures + README + 2 reports
- `scripts/`
  - `validate_compliance_rules.py` — schema validator
  - `smoke_compliance.py` — 3-fixture E2E
  - `dry_run_compliance.py` — runner against any client content
  - `eval_compliance_accuracy.py` — fixture-based accuracy eval
  - `_calibrate_compliance_rules.py` — Wave 4 patch script (record)

### FMTH content (for Wave 5a re-run)
- 8 emails: `clients/farm-thru/loop/emails/EM-*.json`
- 17 LP variants: `/Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index*.html`
- Welcome email: hardcoded in `sales-skill/web/campaign_emails.py::_build_campaign_email`
- VIP section selector: `<section class="vip">` block in each LP variant
- Stripe checkout: see `sales-skill` repo `web/payments.py` (or similar)

### Related (not in scope for Wave 5)
- Cloud Scheduler `fmth-drip-hourly` paused since 2026-04-25 (task #34)
- Pass-3 hill-climb on rewritten seeds (task #35)
- Meta-ads variants need CSF + strip-$ treatment (task #36)
- writer.py CSF + no-$ baking (task #37) — partially superseded by Wave 3a wiring
