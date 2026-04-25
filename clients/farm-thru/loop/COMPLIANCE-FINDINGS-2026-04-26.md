# FMTH compliance dry-run findings — 2026-04-26

Wave 3b of the CSF compliance project. Dry-runs the new compliance gate against
all live FMTH content, **without** flipping `compliance.enabled` in the FMTH
config. Purpose: surface what the gate would catch before it gates real scoring.

## Inputs scanned

- 8 FMTH seed emails — `clients/farm-thru/loop/emails/EM-*.json`
- 17 FMTH landing-page variants — `sales-skill/web/campaigns/FMTH/index*.html`
- 1 deliberately-broken email fixture (sanity check the gate fires)

## Headline result

| Mode | Pass / Fail | Total BLOCKING | Total WARNING |
|---|---|---:|---:|
| Deterministic only (`--no-llm`) | **25 / 26 pass** (only fixture fails) | 3 | 0 |
| Full LLM judges (`enable_llm=True`) | 8 / 26 pass (18 fail) | 24 | 120 |

The deterministic gate passes cleanly — the founder review work shipped last
night (PRs #210, #211, #78) made every email and every LP variant satisfy:
- ADV-001 (canonical CSF warning present)
- ADV-002 (no `$5/$50/$10K` investment amounts)
- ADV-003 (no anti-hawking patterns)
- DISC-001 (superseded disclaimer removed)

The LLM-judge pass is where the calibration story lives.

## What the LLM judges flagged

### BLOCKING (24 total — would zero composite if gate enabled)

| Rule | Count | Genuine vs noise |
|---|---:|---|
| **MISL-001** false/misleading factual statements | 16 | **Mostly noise** — almost every flag is the LLM mistrusting the future date `23 June 2026` because it has no temporal context. The launch date is real and confirmed. |
| **ADV-007** disguised endorsements / sock-puppet quotes | 5 | **Genuine** — flags Rachel Ward's narrated quotes and the constructed farmer dialogue in EM-VIP-01. Reasonable people will disagree on whether these are sock-puppets, but ASIC tends to read them strictly. |
| ADV-001 / ADV-002 / ADV-003 | 1 each | All fixture-only — confirm gate works. |

### WARNING (120 total — would penalise score 3% each, capped at 15%)

| Rule | Count | Notes |
|---|---:|---|
| **ADV-006** benefits vs risks imbalance | 26 | LLM consistently says "the boilerplate CSF warning at the bottom is not enough — body lacks risk discussion". Probably correct under strict reading of RG 261.99/100. |
| **ADV-004** forward-looking without basis | 18 | Many true positives ("first access to invest", "priority access" framed as guaranteed). Some over-broad. |
| **ADV-013** unsubstantiated superlatives | 18 | Real catches: `"100% Regenerative"`, `"Australia's leading"`, `"farmer pays 30%"` are all flagged for missing methodology/source. |
| **ADV-017** marketing dressed as Q&A | 17 | **Mostly false positive** — the rule is scoped at issuer Q&A on the comms facility, but the LLM judges any LP/email body. Tighten scope. |
| **MISL-002** half-truths / omissions | 15 | Genuine catches around `"15+ farms"` vs `"15-20 partners"`, partnership-vs-pipeline ambiguity. |
| **MISL-004** forecasts missing assumptions | 13 | Mixed — some judge correctly there are no forecasts (passes); others flag `"growing fast"`-style claims. |
| ADV-011 / ADV-005 / ADV-016 | 4 / 4 / 2 | Targeted issues — personalised investment language, founder relationship not disclosed, Rachel Ward consent unclear. |
| MISL-003 | 3 | "100% Regenerative" advertising-strip vs body inconsistency — same root cause as MISL-002. |

## Recommendation for FMTH

**Do NOT enable `compliance.enabled: true` for FMTH yet.** The deterministic
checks would pass cleanly, but turning on `enable_llm` would zero the composite
on 18/26 pieces — most of those zeroes are calibration noise, not real issues.

Three concrete options:

### Option A — ship deterministic-only mode (safe, immediate value)
Add a `compliance.enable_llm: false` config knob that overrides the global
`use_llm`. Then FMTH can opt in today and get reliable BLOCKING enforcement on:
- ADV-001 (canonical CSF warning present)
- ADV-002 (no investment $ amounts)
- ADV-003 (no anti-hawking patterns)
- DISC-001 (no superseded disclaimers)

These are the rules the founder cares about and the rules already shipped in
pass-3. No false positives, no API cost, no surprises.

### Option B — calibrate the LLM judges, then enable
1. **MISL-001** — refactor the rule prompt to inject "today's date" so the LLM
   doesn't flag verifiable future dates as stale. Or downgrade to WARNING.
2. **ADV-017** — narrow the rule scope to `content_type: ["offer-document"]`
   only, so it stops firing on LP/email body.
3. **MISL-004** — refactor prompt so a "no forecasts present" answer counts
   as PASS, not WARNING.
4. Re-run dry-run, check the new noise floor.

This is ~1 hour of work + ~$0.30 of LLM re-runs.

### Option C — review the genuine catches manually, ship A
The non-noise catches in this dry-run are real things the user/founder might
want to fix in the copy:
- The constructed farmer dialogue in EM-VIP-01 (ADV-007)
- The `"100% Regenerative"` claim across 14 LP variants (ADV-013)
- The unbalanced benefits-vs-risks framing (ADV-006) — or accept the
  current "CSF warning at bottom" approach as compliant
- The `"15+ farms"` / `"15-20 partners"` inconsistency (MISL-002, MISL-003)
- Founder relationship disclosure on `index-l`, `index-f` (ADV-005)

These are the things a regulator might raise. Whether to fix is a brand /
legal call, not a tooling call.

## Recommended next move

**Ship Option A in a follow-up PR** — small change to `engine/scorer.py` and
`writer.py` to honour `compliance.enable_llm`. Then enable for FMTH with
deterministic-only mode. That gets the immediate-value wins (gate against the
4 things the founder explicitly directed) without surfacing calibration noise.

The calibration work for Option B becomes a separate, non-urgent project —
mostly LLM-prompt tweaks and rule-scope adjustments.

## Files

- `clients/farm-thru/loop/compliance-dry-run-2026-04-26.md` — full deterministic report (cheap pass)
- `clients/farm-thru/loop/compliance-dry-run-llm-2026-04-26.md` — full LLM-judge report (this drove the analysis above)
- `scripts/dry_run_compliance.py` — reusable dry-runner; pass `--no-llm` for deterministic only
