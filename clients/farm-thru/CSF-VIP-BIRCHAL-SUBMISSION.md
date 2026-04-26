# CSF VIP Supporter product — submission for Birchal review

**Issuer**: FarmThru Pty Ltd
**Date**: 2026-04-26
**Status**: Submitted to Birchal 2026-04-26 — awaiting response
**Purpose**: Pre-launch sign-off for the VIP Supporter product, submitted in advance per RG 262.144 (frank and honest dealing with the intermediary).

---

## 1. The product

- **Name**: VIP Supporter
- **Price**: $5 (real Stripe charge, refundable on request)
- **Sold at**: FarmThru's marketing site — not at Birchal
- **Audience**: anyone who self-selects via the VIP page on FarmThru's site

## 2. What the $5 buys (the deliverable)

> **Note**: This section was updated 2026-04-26 following Birchal's response (see §9). The strong VIP early-access framing is now used; the original "thank-you product" framing is preserved in the audit trail at §8/§9 and CSF-VIP-RESEARCH.md.

The $5 secures VIP status, which delivers:

1. **Early access to invest at Birchal** when the round opens — early private access to the investment offer (Birchal-approved language; see §9)
2. **Early investor updates from the founders** before the campaign opens to the public

The $5 is a refundable deposit. The product is positioned as VIP early access, not a thank-you product.

## 3. What the $5 explicitly does NOT buy

- Reserved shares (allocation is governed by Birchal's facility, not the issuer)
- Any guarantee of investment outcome
- Any waiver of the standard CSF investor protections (cooling-off, etc.)

VIP investors get early private access to the investment offer per Birchal's approval (§9). All other investors apply through Birchal's facility on the standard terms when the round opens publicly.

## 4. Mandatory disclosures on every VIP touchpoint

These appear on the LP VIP section, welcome email, Stripe checkout, SMS template, and any drip referencing VIP:

1. **s738ZG(6) safe-harbour statement (verbatim)**:
   > *"In deciding whether to apply for shares in the CSF offer, you should consider the CSF offer document and the general risk warning at [Birchal URL]."*

2. **Equal-access disclosure** — **DROPPED per Birchal 2026-04-26 — see §9**:
   > ~~*"All investors apply on the same terms when the round opens at Birchal. The VIP Supporter product does not provide earlier or preferential investment access."*~~

3. **Refundability**:
   > *"$5 refundable on request before the round closes."*

## 5. Phrases we will never use

"invest before the public" · "beat the queue" · "reserve your spot in the round" · "lock in your investment early" · "limited spots — VIPs go first" · "reserved for VIPs only" · "VIPs invest first" · "1,500 VIPs ready to invest" (or any unverified demand-signal claim) · any reference to the round without the s738ZG(6) safe-harbour line.

**Globally banned per founder direction**: the word "priority" in any form — includes "priority", "priority SMS", "priority access", "priority allocation", "priority investor updates", "priority notification". Replace every occurrence with "early" or remove entirely.

> **Note (Birchal 2026-04-26 — see §9)**: "early private access to the investment offer" is approved language; "first access to invest" and "early access" are no longer banned.

## 6. Touchpoints (draft copy attached separately for review)

- LP `<section class="vip">` block (across all LP variants)
- Welcome email VIP section
- Stripe checkout product description
- SMS template (sent when round opens)
- Mission-control admin description (internal use, included for completeness)

## 7. Compliance enforcement (technical safeguard)

Every variant of every touchpoint runs through an automated CSF compliance scorer before publication. The scorer encodes 96 rules distilled from RG 261 + RG 262, calibrated to 100% accuracy on labeled fixtures. The banned phrases in §5 are encoded as hard-block rules; the mandatory disclosures in §4 are encoded as required-phrase rules. No copy ships without passing.

## 8. Regulatory grounding

- **RG 261.59 + RG 262.151** — single application facility through the intermediary. This is the structural reason the VIP product cannot grant earlier investment access, and the reason §3 above is enforceable, not aspirational.
- **RG 261.92 + s738ZG(6)** — prescribed statement (disclosure §4.1).
- **RG 261.95** — three-factor inducement test. The VIP product is a separable real service (SMS + updates), not investment access; copy is constructed to fall outside (c).
- **RG 261.96 + 261.99** — misleading-conduct standard. Disclosure §4.2 directly addresses any reader inference of preferential allocation.
- **RG 262.144** — frank and honest dealing with the intermediary. This submission discharges that obligation in advance of launch.

## 10. Ask

1. Please confirm the product structure (§1–§3) is acceptable.
2. Please review the attached draft copy across all touchpoints (§6).
3. The VIP page will not launch and no $5 will be charged until Birchal has signed off.
4. Any future material changes (e.g. pricing, deliverable bundle) will be re-submitted for review.

---

## §9. Birchal Response — 2026-04-26

Birchal reviewed this submission and responded with the following:

1. **Mandatory disclosure #2 (equal-access) is not required.** The disclosure stating "All investors apply on the same terms... does not provide earlier or preferential investment access" can be dropped from all touchpoints.
2. **The phrase "early private access to the investment offer" is approved language.** May be used in landing pages, emails, and other marketing copy.
3. Founder direction following Birchal response: replace "priority" with "early" throughout marketing copy; restore the strong VIP card structure (previously softened in the agency-led rewrite).
4. **Founder direction additionally bans the word "priority" in all VIP-related copy — replace with "early" throughout.** This is a global ban: "priority", "priority SMS", "priority access", "priority allocation", "priority investor updates", and "priority notification" are all prohibited in any touchpoint copy. The earlier "Priority SMS notification" framing in the original submission (§2 / §3 above, since rewritten) is retired.

This response shifts the compliance posture: the VIP product is now positioned as genuinely providing early access to invest at Birchal, not merely a thank-you communications product. All copy and validator rules are updated accordingly. The original regulatory analysis (RG 261.59 + RG 262.151 single-application-facility reading) is preserved in §8 and CSF-VIP-RESEARCH.md as the audit trail.
