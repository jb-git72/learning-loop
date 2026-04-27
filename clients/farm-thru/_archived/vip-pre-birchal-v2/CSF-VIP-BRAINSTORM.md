# CSF VIP — brainstorm & decision doc

**UPDATE 2026-04-26**: Q&A dropped from final product spec — bundle is now SMS notification + founder updates email only. Option C and bundle Option 3 below kept as historical analysis.

**Date**: 2026-04-26
**Companion docs**:
- `CSF-VIP-RESEARCH.md` — full regulatory synthesis with verbatim quotes
- `CSF-VIP-RESEARCH-RG261.md` — issuer-side detail (RG 261)
- `CSF-VIP-RESEARCH-RG262.md` — intermediary-side detail (RG 262)

---

## TL;DR

**"First access to invest" is structurally impossible under CSF, not just risky.** Per RG 261.59 + RG 262.151, all applications must go through the intermediary's facility, and the facility is only available while the offer is open. The issuer literally cannot grant earlier access — so claiming to is *false on its face*.

A $5 paid product is fully defensible if the $5 buys a *separate, real service* (founder Q&A, SMS notification, donation-with-thank-you).

---

## Locked constraint (from founder)

- $5 fee stays (real Stripe charge, refundable)
- NO wording about investing earlier
- All money is deducted at the same time when the round opens publicly
- Differentiation is communication-side only (notification, Q&A access, founder updates)

---

## Verdict matrix (6 framings)

| # | Framing | RG 261 | RG 262 | Net verdict |
|---|---|---|---|---|
| A | "Pay $5 for first access to invest" (current FMTH) | RED | RED | **RED — kill immediately** |
| B | "Pay $5 for SMS notification when round opens" | AMBER | AMBER | **AMBER (defensible w/ disclaimers)** |
| C | "Pay $5 for exclusive founder Q&A access" | AMBER → GREEN | GREEN | **GREEN** |
| D | "Pay $5 to be first messaged when round opens" | AMBER | AMBER | **AMBER (defensible)** |
| E | "Pay $5 for queue position on our comms list" | AMBER | AMBER | **AMBER ('queue' is a flag word)** |
| F | "Donation $5 — thank-you SMS" | AMBER | GREEN-AMBER | **GREEN (cleanest re-frame)** |

---

## Phrasings the issuer CAN use

(All paired with the s738ZG(6) safe-harbour line + equal-access disclosure — see "Mandatory additions" below.)

- "Be the first to know when our CSF round opens at Birchal."
- "Get the SMS the moment the round goes live."
- "Pre-register for an exclusive founder Q&A before the round opens."
- "Pay $5 to support our launch marketing — as a thank you, we'll text you when the round goes live."
- "Get priority on our comms list — we'll message you first when the round opens."
- "Founder updates and exclusive Q&A access. Investing happens at Birchal where every investor applies on the same terms."
- "VIP supporters get exclusive founder Q&A access, priority SMS notification, and direct founder updates."

---

## Phrasings the issuer CANNOT use

- "First access to invest"
- "Invest before the public"
- "Beat the queue"
- "Reserve your spot in the round"
- "Lock in your investment early"
- "Limited spots — VIPs go first"
- "Priority allocation"
- "Reserved for VIPs only"
- "VIPs invest first"
- "1,500 VIPs ready to invest" (misleading demand signal — RG 262.119(c))
- "Birchal has approved our VIPs to invest first" (false + drags intermediary into misrepresentation)
- ANY reference to the round without the s738ZG(6) safe-harbour line
- Forecasts of returns or valuation
- Statements attributed to "investors" that are actually the founder's (RG 261.99(c))

---

## Mandatory additions on every VIP touchpoint

Apply to: VIP landing page section, welcome email, Stripe checkout description, mission-control admin descriptions, SMS templates, all VIP-related drip emails.

### 1. s738ZG(6) safe-harbour statement (verbatim required)

> "In deciding whether to apply for shares in the CSF offer, you should consider the CSF offer document and the general risk warning at [Birchal URL]."

Strict liability if missing. **30 penalty units per breach.** Goes on every page/email/SMS that mentions or implies the offer.

### 2. Equal-access disclosure

> "All investors apply on the same terms when the round opens at Birchal. The VIP product does not provide earlier or preferential investment access."

### 3. Tell Birchal

Submit the VIP page, confirmation email, and SMS template to Birchal for sign-off **before** launch. RG 262.144 row 2 makes failure to be frank with the intermediary a good-fame trigger — independent of whether the scheme content is OK.

---

## 3 product-structure options to react to

### Option 1 — Pure founder Q&A (cleanest legally)

- **$5 buys**: 30-min founder Q&A session (live or recorded), refundable
- **Marketing angle**: "Get exclusive founder Q&A access. $5, refundable."
- **Side benefits (free, not what's purchased)**: SMS notification when round opens, founder updates email
- **Verdict**: GREEN
- **Trade-off**: lower perceived value at $5; relies on the Q&A actually being a thing customers want

### Option 2 — Donation framing

- **$5 buys**: nothing tangible — explicitly framed as "supporting our launch marketing"
- **Thank-you (free, not what's purchased)**: SMS when round opens, founder updates
- **Marketing angle**: "Help us launch. $5 supports our marketing budget. As a thank-you, we'll text you when the round goes live."
- **Verdict**: GREEN
- **Trade-off**: requires honest framing — can't dress it up as a benefit; conversion may be lower

### Option 3 — Bundle (most marketable, recommended)

- **$5 buys** (three real services):
  1. Exclusive founder Q&A access (live, 30 min, before launch)
  2. Priority SMS notification when the round opens
  3. Founder updates email throughout the campaign
  4. Refundable
- **Marketing angle**: "VIP supporters get exclusive founder Q&A access, priority SMS when our Birchal round opens, and direct founder updates throughout the campaign. $5, refundable. Investing is open to everyone equally when the round goes live at Birchal."
- **Verdict**: GREEN (with disclosures)
- **Trade-off**: needs clean copy execution; "priority SMS" wording must read as messaging-priority not allocation-priority

---

## Decision needed

Pick one (or a hybrid) of Options 1 / 2 / 3 above. Once locked, the next steps are mechanical (see below).

---

## Next steps after the decision is locked

1. **Rewrite VIP copy across all touchpoints** using the chosen framing
   - LP `<section class="vip">` block in every `web/campaigns/FMTH/index*.html`
   - Welcome email VIP section (in `sales-skill` repo `web/campaign_emails.py::_build_campaign_email`)
   - Stripe checkout description
   - Mission-control admin VIP descriptions
   - Add the s738ZG(6) safe-harbour and equal-access disclosure to every one
2. **Author 3-5 new compliance rules** in `shared/regulatory/csf-australia/compliance_rules.json`:
   - VIP-001 — flag "first access to invest" / preferential allocation language
   - VIP-002 — paid product must be a separable real service from investment access
   - VIP-003 — every VIP touchpoint must carry the s738ZG(6) safe-harbour
   - EQUAL-001 — equal-access disclosure required when paid VIP product is mentioned
3. **Author 2-3 fixtures per rule** in `engine/tests/fixtures/compliance/`
4. **Re-run** `scripts/eval_compliance_accuracy.py` — must hit 100% before merging
5. **Build founder Q&A doc** at `clients/farm-thru/VIP-LEGAL-QA.md` — customer-comms backbone + legal defence
6. **Eval against actual FMTH VIP copy** — score the rewritten LP/email/Stripe/admin copy through the full pipeline; report any remaining gaps
7. **Submit to Birchal** for sign-off before going live
8. **PR + merge** the lot, then flip `clients/farm-thru/config.json` `compliance.enabled: true` (combined with Wave 5a re-run)

---

## Open questions to resolve later

- Exact verbatim wording of the s738ZG(6) statement (likely in reg 6D.3A.10 — outside RG 261; ASIC INFO sheets may codify a standard form)
- Birchal's own platform T&Cs on parallel paid issuer products
- ACL / consumer-protection treatment of the $5 if delivery fails (round closes early before SMS sent)
- GST / tax treatment of the $5 inflows
- Refund policy mechanics (currently advertised as refundable — what's the trigger and SLA?)
