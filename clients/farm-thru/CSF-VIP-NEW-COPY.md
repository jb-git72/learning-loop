# CSF-compliant VIP copy — canonical source

**Issuer**: FarmThru Pty Ltd
**Wave**: 5b — Birchal pre-launch submission
**Owner**: agency on behalf of FarmThru Pty Ltd
**Status**: DRAFT for Birchal review (do not ship until intermediary signs off)
**Date**: 2026-04-26

This is the single source of truth for VIP-related copy across every FarmThru
touchpoint. Every other artefact (LP variants, drip emails, Stripe checkout,
mission-control admin, SMS templates) must mirror what is below.

Implements the locked structure in `CSF-VIP-BIRCHAL-SUBMISSION.md` (Option 2+3
hybrid: $5 supporter charge, two real services, no investment-access framing).

---

## 1. Universal building blocks

### 1.1 Product name
**VIP Supporter** (badge text on LP / thank-you / drip / mission-control).

The legacy badge text "VIP ACCESS" must be replaced everywhere with
"VIP SUPPORTER".

### 1.2 The pitch (one sentence)
> Pay $5 to support FarmThru's launch. As a thank-you, you'll receive a
> priority SMS when our round opens at Birchal, plus updates
> throughout the campaign.

### 1.3 What the $5 buys (the two deliverables)
1. Priority SMS notification when the round goes live at Birchal.
2. Updates email throughout the campaign.

### 1.4 Mandatory disclosures (verbatim — required on every VIP touchpoint that mentions or implies the offer)

- **s738ZG(6) safe-harbour (verbatim)**:
  *"In deciding whether to apply for shares in the CSF offer, you should consider the CSF offer document and the general risk warning at {{birchal_url}}."*

- **Equal-access**:
  *"All investors apply on the same terms when the round opens at Birchal. The VIP Supporter product does not provide earlier or preferential investment access."*

- **Refundability**:
  *"$5 refundable on request before the round closes."*

If `{{birchal_url}}` is not yet wired into a given file, leave the literal
placeholder and flag it as a TODO for the founder.

### 1.5 Banned phrases (NEVER use anywhere in any FMTH surface)

"first access to invest" · "invest before the public" · "beat the queue" ·
"reserve your spot in the round" · "lock in your investment early" ·
"limited spots — VIPs go first" · "priority allocation" · "reserved for
VIPs only" · "VIPs invest first" · "1,500 VIPs ready to invest" (or any
unverified demand-signal claim) · any reference to the round without the
s738ZG(6) safe-harbour line · "first access to the offer" · "head start" ·
"24 hours before the public" / "24-hour head start" · "first to invest" ·
"first group to see the round" · "skip the queue" · "see the offer 24 hours
before the public" · "Birchal link 24 hours before public" · "VIP investor"
· "VIP investors get priority access".

---

## 2. Touchpoint-by-touchpoint copy

### 2.1 Landing page `<section class="vip">` (all variants: index.html + index-b through index-q)

Preserve the `<section class="vip">` wrapper, `vip__card`, `vip__badge`,
`vip__title`, `vip__text`, `vip__perks`, `vip__perk`, `vip__button`,
`vip__refund` classes, and the `id="vipDepositBtn"` attribute on the button.
Rewrite only the visible text.

```html
<section class="vip">
  <div class="vip__card">
    <span class="vip__badge">VIP SUPPORTER</span>
    <h2 class="vip__title">Support FarmThru's launch for $5.</h2>
    <p class="vip__text">Pay $5 to support FarmThru's launch. As a thank-you, you'll receive a priority SMS when our round opens at Birchal, plus updates throughout the campaign.</p>
    <ul class="vip__perks">
      <li class="vip__perk">Priority SMS notification when the round opens at Birchal</li>
      <li class="vip__perk">Updates email throughout the campaign</li>
    </ul>
    <button class="vip__button" id="vipDepositBtn">Support FarmThru — $5</button>
    <p class="vip__refund">$5 refundable on request before the round closes.</p>
    <p class="vip__disclosure" style="font-size: 12px; color: #888; line-height: 1.5; margin-top: 14px;">All investors apply on the same terms when the round opens at Birchal. The VIP Supporter product does not provide earlier or preferential investment access.</p>
    <p class="vip__disclosure" style="font-size: 12px; color: #888; line-height: 1.5; margin-top: 8px;">In deciding whether to apply for shares in the CSF offer, you should consider the CSF offer document and the general risk warning at {{birchal_url}}.</p>
  </div>
</section>
```

Notes:
- "$5" must remain in the button text — the sales-skill `variant_validator.py`
  `check_6_vip_deposit` requires `$5` to appear inside the VIP card.
- `id="vipDepositBtn"` and `class="vip__card"` are required by the validator
  and the JS handler in `templates/campaign_thankyou.html` — do not remove.

### 2.2 Thank-you page (`templates/campaign_thankyou.html`) — non-VIP block

Preserve all template structure (`{% if %}` blocks, IDs, classes).

```html
<div class="vip__card" id="vipCard">
  <span class="vip__badge">VIP SUPPORTER</span>
  <h2 class="vip__title">Support FarmThru's launch.</h2>
  <p class="vip__text">Pay {{ meta.get("deposit_amount", "$5") }} to support FarmThru's launch. As a thank-you, you'll receive a priority SMS when our round opens at Birchal, plus updates throughout the campaign.</p>
  <ul class="vip__perks">
    <li class="vip__perk">Priority SMS notification when the round opens at Birchal</li>
    <li class="vip__perk">Updates email throughout the campaign</li>
  </ul>
  <div class="vip__price">Supporter contribution: <strong>{{ meta.get("deposit_amount", "$5") }}</strong></div>
  <button class="vip__button" id="vipDepositBtn">Support FarmThru — {{ meta.get("deposit_amount", "$5") }}</button>
  <p class="vip__refund">{{ meta.get("deposit_amount", "$5") }} refundable on request before the round closes.</p>
  <p class="vip__disclosure" style="font-size: 12px; color: #888; line-height: 1.5; margin-top: 14px;">All investors apply on the same terms when the round opens at Birchal. The VIP Supporter product does not provide earlier or preferential investment access.</p>
  <p class="vip__disclosure" style="font-size: 12px; color: #888; line-height: 1.5; margin-top: 8px;">In deciding whether to apply for shares in the CSF offer, you should consider the CSF offer document and the general risk warning at {{ meta.get("birchal_url", "{{birchal_url}}") }}.</p>
</div>
```

### 2.3 Thank-you page — VIP-confirmed block (post-checkout)

```html
<div class="vip__card" id="vipCard">
  <span class="vip__badge" style="background: var(--brand-accent, #2e8b57);">SUPPORTER CONFIRMED</span>
  <h2 class="vip__title">Thank you for supporting FarmThru.</h2>
  <p class="vip__text">Your $5 supporter contribution is confirmed. Look out for your priority SMS when the round opens at Birchal, plus updates over the coming weeks. Check your inbox for your welcome email.</p>
  <p class="vip__disclosure" style="font-size: 12px; color: #888; line-height: 1.5; margin-top: 14px;">All investors apply on the same terms when the round opens at Birchal. The VIP Supporter product does not provide earlier or preferential investment access.</p>
  <p class="vip__disclosure" style="font-size: 12px; color: #888; line-height: 1.5; margin-top: 8px;">In deciding whether to apply for shares in the CSF offer, you should consider the CSF offer document and the general risk warning at {{ meta.get("birchal_url", "{{birchal_url}}") }}.</p>
</div>
```

### 2.4 Welcome email VIP section (`web/campaign_emails.py::_build_campaign_email`)

Replace only the VIP-related paragraph + button block; preserve the rest of
the email and the wrapper HTML.

VIP paragraph (replaces lines around line 95):

> {client_name} is opening a community funding round on 23 June at Birchal.
> Want to support our launch? For $5 (refundable on request before the round
> closes), you'll get a priority SMS when the round opens at Birchal, plus
> updates throughout the campaign.

Replace the existing CTA copy:
- Old button text: `Reserve VIP access (refundable)`
- New button text: `Support FarmThru — $5`

Add this disclosure paragraph immediately above the existing CSF risk
warning paragraph:

> All investors apply on the same terms when the round opens at Birchal.
> The VIP Supporter product does not provide earlier or preferential
> investment access. In deciding whether to apply for shares in the CSF
> offer, you should consider the CSF offer document and the general risk
> warning at {{birchal_url}}.

(Use `meta.get("birchal_url")` in the f-string; fall back to the literal
placeholder string if not set.)

### 2.5 Stripe checkout (`web/app.py::campaign_vip_checkout`)

Replace only the `product_data` dict copy. Pricing logic ($5 / `deposit_amount_cents`)
must NOT change.

```python
"product_data": {
    "name": f"VIP Supporter - {client_name}",
    "description": (
        f"Pay {deposit_display} to support {client_name}'s launch. "
        f"Thank-you: priority SMS when our round opens at Birchal, "
        f"plus updates. Refundable on request before the round "
        f"closes. VIP Supporter does not provide earlier or preferential "
        f"investment access."
    ),
},
```

### 2.6 SMS template — round opens (priority SMS sent to VIP supporters)

There is currently no Twilio/SMS sending pipeline in sales-skill (only a
phone-collection input on the LP signup form). Until the founder wires one
up, this is a content spec — the template should live here and in the
mission-control admin docs. When SMS sending lands, this is the canonical text:

```
FarmThru's CSF offer is now live at Birchal: {{birchal_url}} Reply STOP to opt out.
```

Length: 128 chars with the real URL — fits one SMS segment. Trade-off:
the full s738ZG(6) safe-harbour text doesn't fit. The link takes
recipients to the general CSF risk warning page (which references the
offer document). The full mandatory disclosures appear on every other
VIP touchpoint customers reach after clicking (LP, welcome email,
Stripe, drip emails).

### 2.7 Mission-control admin VIP descriptions (`templates/mission-control.html`)

Internal-facing, but treat with the same compliance standards because the
copy is referenced when explaining the funnel to outsiders.

Replacements:

- VIP Welcome card subject line (currently `"VIP confirmed. You'll be first to invest."`):
  → `"You're a FarmThru supporter — thank you."`
- "VIP Track" section header text → keep (internal label)
- VIP Welcome card name → keep `"VIP Welcome"`
- Subject lines in cards (these mirror the actual email subjects — keep
  in sync with §2.8 below):
  - VIP Welcome → `"You're a FarmThru supporter — thank you."`
  - Insider Note (Deposit +3) → `"What I told the farmer on Tuesday"`
    (already CSF-friendly; keep)
  - How The Offer Works (Deposit +10) → `"How our CSF offer works at Birchal"`
  - Head Start Link (Launch -1) → rename card to "Round Opens Tomorrow",
    subject → `"Our Birchal round opens tomorrow"`

### 2.8 Drip emails (`web/campaigns/FMTH/emails/drip_vip_*.html`)

These are full HTML emails — they need a careful rewrite to scrub all
banned phrases ("first to invest", "24-hour head start", "fill the first
tranche", "VIP investor", etc.). Each email must end with the s738ZG(6)
safe-harbour line + the equal-access line.

Specific changes:

#### `drip_vip_welcome.html` (subject + body)

- Subject: `Your VIP supporter benefits — what you get`
- Body — replace lines that reference "first group", "head start", "Birchal
  link 24 hours before" with copy that frames the two deliverables only:
  - Confirm $5 supporter contribution received.
  - Recap the two thank-you services.
  - State equal-access disclosure + s738ZG(6) safe-harbour.
  - CTA: link to FarmThru info, NOT a "see the offer first" claim.

Body draft:

> Hi {{FIRST_NAME}},
>
> Thank you for supporting FarmThru's launch. Your $5 contribution is
> confirmed.
>
> As a thank-you, here's what you'll receive over the coming weeks:
>
> 1. A priority SMS the moment our offer goes live at Birchal.
> 2. Updates by email throughout the campaign — what we're
>    building, which farms are joining the hub, and how the offer is structured.
>
> If you change your mind, your $5 is refundable on request before the
> round closes — just reply to this email.
>
> All investors apply on the same terms when the round opens at Birchal.
> The VIP Supporter product does not provide earlier or preferential
> investment access.
>
> In deciding whether to apply for shares in the CSF offer, you should
> consider the CSF offer document and the general risk warning at
> {{BIRCHAL_URL}}.
>
> Rachel

CTA button: `Visit FarmThru` linking to `{{CAMPAIGN_URL}}`.

#### `drip_vip_1.html` (subject + body)

- Subject: `What I told the farmer on Tuesday` (keep — strong narrative)
- Body — strip banned phrases, frame the support relationship not the
  early-access relationship:

> Hi {{FIRST_NAME}},
>
> On Tuesday I was on the phone with one of our partner farmers. He asked
> me straight: "Rachel, why didn't you just take investor money and scale
> fast?"
>
> I told him the truth. Every VC conversation came back to the same
> pressure point. Lift margins, trim the farm gate price, optimise the
> unit economics. Polite language for the same old outcome: farmers
> absorb the cost so the cap table wins.
>
> That's the moment FarmThru stopped being a business plan and became
> something I had to own differently.
>
> So we chose equity crowdfunding on Birchal. The people who believe in
> paying farmers first get to be part of the structure that makes it
> stick, not just customers of it.
>
> Thank you for chipping in $5 to support our launch. Your priority SMS
> and updates are on the way.
>
> If you have questions before our CSF offer opens, just reply to this
> email. I read every one.
>
> All investors apply on the same terms when the round opens at Birchal.
> The VIP Supporter product does not provide earlier or preferential
> investment access.
>
> In deciding whether to apply for shares in the CSF offer, you should
> consider the CSF offer document and the general risk warning at
> {{BIRCHAL_URL}}.
>
> Rachel

CTA button: `Visit FarmThru` → `{{CAMPAIGN_URL}}`.

#### `drip_vip_2.html` (subject + body)

- Subject: `How our CSF offer works at Birchal`
- Body — replace the entire "head start" framing with a simple explanation
  of how the CSF process works. NO claims about VIPs being first, no
  "watching a countdown with everyone else" framing.

> Hi {{FIRST_NAME}},
>
> A supporter asked me last week: "What actually happens when the CSF
> offer opens?"
>
> Here's how it works.
>
> When our CSF offer is live at Birchal, you'll get a priority SMS from
> us with the link. Anyone — supporter or not — applies through the same
> Birchal facility on identical terms. There's no separate VIP line and
> no priority allocation. We can't grant earlier investment access, and
> we wouldn't want to even if we could — Birchal's process treats all
> investors equally and that's the point.
>
> What the $5 supports: our pre-launch work and the two thank-you
> services we promised — the priority SMS and the updates.
>
> If you want to think about whether to apply when the offer opens, the
> Birchal offer document and risk warning are the right places to start.
>
> All investors apply on the same terms when the round opens at Birchal.
> The VIP Supporter product does not provide earlier or preferential
> investment access.
>
> In deciding whether to apply for shares in the CSF offer, you should
> consider the CSF offer document and the general risk warning at
> {{BIRCHAL_URL}}.
>
> Rachel

CTA: `Read the offer document on Birchal` → `{{BIRCHAL_URL}}`.

#### `drip_vip_3.html` (subject + body)

- Subject: `Our Birchal round opens tomorrow`
- Body — strip "VIP link 24 hours before public", "tomorrow is yours",
  "day one funding matters" framing. This goes to all supporters the day
  before the round opens.

> Hi {{FIRST_NAME}},
>
> Tomorrow our CSF offer opens at Birchal.
>
> As promised, you'll get a priority SMS from us when the offer goes
> live. The link will go to the public Birchal page at the same time we
> send the SMS — there's no separate "supporter-only" link.
>
> Whether to apply, and how much, is entirely your call. Take the time
> you need to read the offer document and the general risk warning. Both
> are at Birchal.
>
> Thank you for supporting FarmThru's launch.
>
> All investors apply on the same terms when the round opens at Birchal.
> The VIP Supporter product does not provide earlier or preferential
> investment access.
>
> In deciding whether to apply for shares in the CSF offer, you should
> consider the CSF offer document and the general risk warning at
> {{BIRCHAL_URL}}.
>
> Rachel & the FarmThru team

CTA: `Read the offer document on Birchal` → `{{BIRCHAL_URL}}`.

---

## 3. Implementation order (when applying)

1. LP variants — `<section class="vip">` block in 17 HTML files.
2. Thank-you template — both `{% if not is_vip %}` and `{% else %}` blocks.
3. Welcome email — `web/campaign_emails.py::_build_campaign_email`.
4. Stripe checkout — `web/app.py::campaign_vip_checkout`.
5. Drip emails — 4 files (`drip_vip_welcome.html`, `drip_vip_1.html`,
   `drip_vip_2.html`, `drip_vip_3.html`).
6. Mission-control admin — `templates/mission-control.html` (subject lines
   in VIP track cards).
7. SMS template — content-only spec in §2.6 (no code change yet — pending
   Twilio integration).

## 4. What's NOT being changed

- `web/variant_validator.py` (still requires `$5` + `vipDepositBtn` — both preserved).
- Stripe pricing logic (`deposit_amount_cents = 500`).
- Existing IDs / CSS classes.
- Routing / form handlers / Stripe webhook code.
- Non-VIP drip emails (`drip_nonvip_*`) — out of scope for Wave 5b.
- Underlying funnel structure.

## 5. Open items for the founder

- **Birchal URL placeholder**: `meta.json::birchal_url` is currently empty.
  Either populate it before launch and let the f-strings substitute, or
  ship the literal `{{birchal_url}}` placeholder for Birchal-team manual
  fill at sign-off time.
- **SMS pipeline**: no Twilio integration exists. The SMS template in §2.6
  is a content spec only.
- **Variant validator scarcity check**: `check_28_authentic_scarcity` looks
  for "early access", "limited", "spots", "first access" anywhere in the
  page. If founder wants this to keep passing post-rewrite, the LP must
  retain a non-VIP scarcity signal elsewhere (e.g., countdown timer or
  founder-update cadence).
