# ARCHIVED 2026-04-27 pending Birchal v2 approval

> Status: VIP scheme withdrawn from production on 2026-04-27 after Birchal pushed back on the s738ZE financial-assistance / fund-custody / investor-risk concerns. Replacement v2 proposal at `clients/farm-thru/BIRCHAL-PROPOSAL-V2.md` (decoupled $10 product credit + free CSF waitlist). If Birchal blesses the v1 VIP scheme below, restore via `clients/farm-thru/VIP-ARCHIVE-MANIFEST.md`. Do not reuse this content live until restoration.

# FarmThru VIP — copy package

**Issuer**: FarmThru Pty Ltd · **Date**: 2026-04-26 (revised post-Birchal response)
**Product**: VIP — $5 refundable deposit (real Stripe charge)
**What VIP secures**: early private access to the investment offer at Birchal when our CSF round opens, plus early investor updates from the founders before the campaign opens to the public
**Refundability**: 100% refundable on request before the round closes — no obligation to invest

---

## Mandatory disclosures (on every touchpoint that mentions the offer)

1. **s738ZG(6) safe-harbour (verbatim)**: *"In deciding whether to apply for shares in the CSF offer, you should consider the CSF offer document and the general risk warning at https://www.birchal.com/legal-pages/general-csf-risk-warning."*
2. ~~**Equal-access disclosure**~~ — **Per Birchal 2026-04-26: equal-access disclosure not required.** No longer applied to any touchpoint.
3. **Refundability**: *"$5 refundable on request before the round closes."*

## Banned phrases (revised list)

"beat the queue" · "lock in your investment early" · "limited spots — VIPs go first" · "reserved for VIPs only" · "VIPs invest first" · "1,500 VIPs ready to invest" · ANY round-mention without the s738ZG(6) safe-harbour.

**Globally banned per founder direction**: the word "priority" in any form — includes "priority", "priority SMS", "priority access", "priority allocation", "priority investor updates", "priority notification". Replace every occurrence with "early" or remove entirely. The word "priority" must not appear in any touchpoint copy.

> **Per Birchal 2026-04-26**: "early private access to the investment offer" is approved language; "first access to invest" and "early access" are no longer banned. Per founder direction, "priority" is globally banned in all VIP-related copy — replace with "early" throughout.

---

## Canonical VIP card (apply consistently wherever the VIP product is described)

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

---

## Touchpoint copy

### Landing page — VIP section

**Badge**: VIP ACCESS
**Headline**: Secure early access to invest.
**Sub**: Place a small refundable deposit to secure VIP status. VIP investors get early private access to the investment offer and early notice before the campaign opens to the public.
**Bullets**:
- Early access when the campaign opens
- Early investor updates from the founders
- Fully refundable at any time

**CTA button**: Secure VIP Access
**Footer**: 100% refundable. No obligation to invest.
*(s738ZG(6) safe-harbour appears directly below the card.)*

### Welcome email — VIP section

> **Secure early access to invest in FarmThru.**
>
> Place a small refundable deposit to secure VIP status. VIP investors get early private access to the investment offer when our Birchal round opens, plus early notice and investor updates from the founders. Fully refundable at any time.
>
> - Early access when the campaign opens
> - Early investor updates from the founders
> - Fully refundable at any time

**CTA button**: Secure VIP Access — $5 refundable
*(s738ZG(6) safe-harbour appears in the email body.)*

### Stripe checkout product description (≤250 chars)

> Secure early access to invest in FarmThru. Your $5 refundable deposit secures VIP status — early access when the campaign opens, early investor updates from the founders. 100% refundable.

### SMS — round opens (sent to VIP investors when the offer goes live)

> FarmThru's CSF offer is now live at Birchal: {{birchal_url}} Reply STOP to opt out.

(128 chars with the real URL — fits one SMS segment. The link takes recipients to the general CSF risk warning page; full disclosures appear on every LP / email / Stripe touchpoint they reach after clicking.)

*(SMS sent manually by founder/agency via a manual SMS provider — no automated pipeline.)*

### SMS — purchase confirmation (≤160 chars)

> You're in. VIP early access to FarmThru's CSF offer is secured. We'll text the moment the round opens. Refund anytime: hello@farmthru.com.au

### Drip emails (4 — sent across the campaign, all signed "Rachel")

| Subject | Purpose |
|---|---|
| Your VIP early access is secured | Confirms $5 deposit; recaps early-access framing |
| What I told the farmer on Tuesday | Founder narrative on choosing CSF over VC |
| Your early-access window opens soon | Explains the early-access timing at Birchal; reaffirms refundability |
| Your VIP early-access window opens tomorrow | Sent day before launch; confirms SMS coming with early access |

Each email ends with the s738ZG(6) safe-harbour disclosure.

### Mission-control admin (internal labels in the founder/agency UI)

| Card | Subject |
|---|---|
| VIP Welcome | You're a FarmThru VIP — early access secured. |
| Insider Note (Deposit +3) | What I told the farmer on Tuesday |
| Early Access Window (Deposit +10) | Your early-access window opens soon |
| Round Opens Tomorrow (Launch -1) | Your VIP early-access window opens tomorrow |

---

## FAQ (for sales calls + Birchal questions)

**Q: What does the $5 actually buy?**
A: VIP status, which secures early access to invest in FarmThru when our Birchal round opens, plus early investor updates from the founders. The $5 is a refundable deposit — fully refundable at any time before the round closes.

**Q: Do VIP investors get to invest earlier?**
A: Yes. VIP investors get early private access to the investment offer when our Birchal round opens. Place a small refundable deposit to secure VIP status — Birchal has approved this early-access framing.

**Q: Is this a payment for early investment access?**
A: The $5 deposit secures VIP status, which includes early access to invest at Birchal. The $5 is fully refundable on request before the round closes.

---

## Compliance enforcement (technical safeguard)

Every variant of every touchpoint runs through an automated CSF compliance scorer encoding rules distilled from RG 261 + RG 262. Banned phrases (revised list above) are hard-block rules; the s738ZG(6) safe-harbour is a required-phrase rule on every round-mention. The equal-access disclosure rule was retired per Birchal 2026-04-26. No copy ships without passing.
