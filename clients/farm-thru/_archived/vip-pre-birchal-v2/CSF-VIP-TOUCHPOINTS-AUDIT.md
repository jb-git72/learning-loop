# CSF VIP touchpoints audit (Wave 5b)
**Date**: 2026-04-26
**Scope**: learning-loop + sales-skill repos
**Auditor**: Agent (read-only discovery, no code changes)

> ## ⚠️ PRE-PIVOT SNAPSHOT — READ BEFORE USING
>
> This audit was the *trigger* for the Wave 5b rewrite. It captures the state of VIP touchpoints **before** Birchal's response of 2026-04-26. The framings flagged "HIGH severity" below (e.g. "first access to invest", "early access" without disclaimer) were **subsequently approved by Birchal** and the equal-access disclosure was **dropped as no-longer-required**.
>
> Do NOT use this document as a copy spec. Canonical post-pivot copy lives in `CSF-VIP-COPY-PACKAGE.md` and `CSF-VIP-BIRCHAL-SUBMISSION.md` §9. This file is preserved as the audit trail that initiated the rewrite.

## Summary
- Total touchpoints found: 36 (23 production-active, 7 source-of-truth JSON, 6 archive/test)
- Files with banned phrases: 36
- Files missing s738ZG(6) safe-harbour: 36 (NONE of the production VIP touchpoints carry the full s738ZG(6) safe-harbour wording — most carry a generic CSF risk warning at best)
- Files missing equal-access disclosure: 36 (NONE carry "All investors apply on the same terms")
- Files missing refundability ($5 explicit + cutoff): 4 of 23 production touchpoints lack the explicit cutoff/refund-on-request wording

Severity rubric used:
- HIGH = explicit "first access to invest" / "VIP investors get priority" / "Skip the queue. Get first access to invest" framing — the Birchal-prohibited investment-access promise
- MED = "first access" / "priority" framing where the **product** (waitlist, hub) is the noun rather than "invest" — still misleading without disclosures
- LOW = neutral references (badges, button labels, tracking strings) that need a copy refresh once the new framing lands

## Touchpoint inventory (sorted by severity)

### 1. LP — sales-skill production index.html (canonical) — VIP section
- **File**: /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index.html
- **Lines**: 107, 115, 136–148
- **Current copy**:
  > Line 107: `A small refundable deposit secures your spot on the VIP list.`
  > Line 115: `"What does the VIP deposit do?"`
  > Lines 136–148:
  > ```
  > <section class="vip">
  >   <div class="vip__card">
  >     <span class="vip__badge">VIP ACCESS</span>
  >     <h2 class="vip__title">Get first access to invest.</h2>
  >     <p class="vip__text">Place a small refundable deposit to secure VIP status. VIP investors get priority access, exclusive founder updates, and early notice before the campaign opens to the public.</p>
  >     <ul class="vip__perks">
  >       <li class="vip__perk">First access when the campaign opens</li>
  >       <li class="vip__perk">Priority investor updates from the founders</li>
  >       <li class="vip__perk">Exclusive Q&amp;A session with the FarmThru team</li>
  >       <li class="vip__perk">Fully refundable at any time</li>
  >     </ul>
  >     <button class="vip__button" id="vipDepositBtn">Secure VIP Access</button>
  >     <p class="vip__refund">Small, fully refundable deposit. No obligation to invest.</p>
  > ```
- **Banned phrases**: "first access to invest", "priority access" (investor-context), "First access when the campaign opens", "Priority investor updates from the founders"
- **Missing disclosures**: s738ZG(6) safe-harbour, equal-access disclosure, refund-on-request-before-close
- **Severity**: HIGH

### 2. LP — sales-skill index-b.html through index-q.html (15 production variants) — VIP section
- **File(s)** (all production-active):
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-b.html (lines 112, 139–151)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-c.html (lines 152–164)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-d.html (lines 119–131)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-e.html (lines 101, 127–139)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-f.html (lines 103, 130–142)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-g.html (lines 165–177)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-h.html (lines 140–152)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-i.html (lines 154–166)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-j.html (lines 11, 93–105)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-k.html (lines 75, 97, 139–151)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-l.html (lines 155–166)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-m.html (lines 80, 100, 127–139)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-n.html (lines 98, 101, 131–143)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-o.html (lines 14, 77–88)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-p.html (lines 105, 110, 131–143)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index-q.html (lines 70–80)
- **Current copy** (canonical block, repeated verbatim across most):
  > ```
  > <span class="vip__badge">VIP ACCESS</span>
  > <h2 class="vip__title">Get first access to invest.</h2>
  > <p class="vip__text">Place a small refundable deposit to secure VIP status. VIP investors get priority access, exclusive founder updates, and early notice before the campaign opens to the public.</p>
  > ```
  > Per-variant additional offending lines (excerpted):
  > - **index-j.html L11**: `<h1>...143 people signed up this week. VIP spots are limited.</h1>` and L95 `<span class="vip__badge">LIMITED VIP ACCESS</span>` and L97 `VIP members get first access when the campaign opens. Once the raise goes live, VIP spots close. This is your window.`
  > - **index-k.html L142**: `<h2 class="vip__title">Lock in VIP before the crowd.</h2>`
  > - **index-m.html L80**: `327 people have already joined the VIP waitlist. Spots close before we launch.`
  > - **index-n.html L98**: `Want priority access before the campaign goes live? A small refundable amount refundable VIP deposit gets you first access...` and L101 `It puts you at the front of the line.`
  > - **index-o.html L14**: `We're opening investment on Birchal. Join the waitlist for first access.`
  > - **index-q.html L72**: `<h3 class="vip__title">Skip the queue. Get first access.</h3>`
- **Banned phrases**: "first access to invest", "VIPs invest first" (paraphrased as "VIP investors get priority access"), "limited spots — VIPs go first" (j: "VIP spots are limited"), "beat the queue" (q: "Skip the queue. Get first access"), "lock in your investment early" (k: "Lock in VIP before the crowd"), "1,500 VIPs ready to invest"-style unverified demand signal (m: "327 people have already joined"; j: "143 people signed up this week"), "priority allocation" (paraphrased)
- **Missing disclosures**: s738ZG(6) safe-harbour (all 16), equal-access (all 16), refund-on-request-before-close (all 16)
- **Severity**: HIGH

### 3. Thank-you template — VIP card (pre-deposit) and confirmed (post-deposit)
- **File**: /Users/jb/Documents/GitHub/sales-skill/web/templates/campaign_thankyou.html
- **Lines**: 59–79, 162–167
- **Current copy**:
  > ```
  > <span class="vip__badge">VIP ACCESS</span>
  > <h2 class="vip__title">Skip the queue. Get first access.</h2>
  > <p class="vip__text">Place a refundable {{ meta.get("deposit_amount", "$5") }} deposit to lock in VIP status. Priority access and early notice before the campaign opens to the public.</p>
  > <ul class="vip__perks">
  >   <li class="vip__perk">First access when the campaign opens</li>
  >   <li class="vip__perk">Priority investor updates from the founders</li>
  >   <li class="vip__perk">Fully refundable at any time</li>
  > </ul>
  > <div class="vip__price">Refundable deposit: <strong>{{ meta.get("deposit_amount", "$5") }}</strong></div>
  > <button class="vip__button" id="vipDepositBtn">Secure VIP Access</button>
  > <p class="vip__refund">100% refundable. No obligation to invest.</p>
  > ```
  > And confirmed state (lines 74–78):
  > ```
  > <h2 class="vip__title">You're a VIP investor.</h2>
  > <p class="vip__text">Your deposit is confirmed. You'll get priority access and exclusive founder updates before anyone else. Check your inbox for your VIP welcome email.</p>
  > ```
- **Banned phrases**: "Skip the queue. Get first access" (== "beat the queue"), "lock in VIP" (== "lock in your investment early"), "Priority investor updates", "First access when the campaign opens", "You're a VIP investor", "priority access and exclusive founder updates before anyone else"
- **Missing disclosures**: s738ZG(6), equal-access, refund-on-request-before-close
- **Severity**: HIGH

### 4. Campaign template — JS-injected VIP CONFIRMED card
- **File**: /Users/jb/Documents/GitHub/sales-skill/web/templates/campaign.html
- **Lines**: 239–252
- **Current copy**:
  > ```
  > if (urlParams.get('vip') === 'success') {
  >   var vipCard = document.querySelector('.vip__card');
  >   if (vipCard) {
  >     vipCard.innerHTML = '<span class="vip__badge" style="background: var(--brand-accent, #2e8b57);">VIP CONFIRMED</span>' +
  >       '<h2 class="vip__title">You\'re a VIP investor.</h2>' +
  >       '<p class="vip__text">Your deposit is confirmed. You\'ll get priority access and exclusive founder updates before anyone else. Check your inbox for your VIP welcome email.</p>';
  >   }
  > ```
- **Banned phrases**: "You're a VIP investor", "priority access ... before anyone else", "exclusive founder updates" (in investor framing)
- **Missing disclosures**: s738ZG(6), equal-access, refund-on-request-before-close
- **Severity**: HIGH

### 5. Stripe checkout — line item product description
- **File**: /Users/jb/Documents/GitHub/sales-skill/web/app.py
- **Lines**: 700–726 (key copy at 708–710)
- **Current copy**:
  > ```python
  > line_items=[
  >   {
  >     "price_data": {
  >       "currency": "aud",
  >       "unit_amount": deposit_cents,
  >       "product_data": {
  >         "name": f"VIP Deposit - {client_name}",
  >         "description": f"Refundable {deposit_display} VIP deposit for priority access.",
  >       },
  >     },
  >     "quantity": 1,
  >   }
  > ],
  > ```
- **Banned phrases**: "VIP deposit for priority access" (== "priority allocation" in Stripe receipts and customer-facing checkout pages — Stripe shows this product description on the hosted Checkout page and on the email receipt)
- **Missing disclosures**: s738ZG(6), equal-access, refundability cutoff (only "Refundable" appears, no "before round closes" qualifier)
- **Severity**: HIGH (Stripe receipt is a permanent transactional record, sent to subscriber email and auditable; ASIC and Birchal can both pull this in a complaint review)

### 6. Welcome email (non-VIP, programmatic) — Reserve VIP CTA
- **File**: /Users/jb/Documents/GitHub/sales-skill/web/campaign_emails.py
- **Lines**: 18–123 (key copy 95, 103, 107)
- **Current copy**:
  > Line 95: `{client_name} is opening a community funding round on 23 June. And right now, for a small refundable deposit, you can reserve a VIP spot and see the offer 24 hours before the public.`
  > Line 103 (CTA button text): `<a href="{referral_url}" ...>Reserve VIP access (refundable)</a>`
  > Line 107 (footer disclosure, only): `<strong>Always consider the general CSF risk warning and offer document before investing.</strong>` Campaign opens {launch_phrase}.`
- **Banned phrases**: "see the offer 24 hours before the public" (== "invest before the public"), "Reserve VIP access" (== "reserve your spot in the round"), "you can reserve a VIP spot" (paraphrase of "reserve your spot in the round")
- **Missing disclosures**: full s738ZG(6) safe-harbour wording (the truncated "Always consider the general CSF risk warning and offer document before investing" is close but does NOT cite the Birchal URL or use the s738ZG(6)-required phrasing), equal-access disclosure, explicit refund-on-request-before-close
- **Severity**: HIGH

### 7. Drip — VIP welcome (HTML template, sent immediately after deposit)
- **File**: /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/emails/drip_vip_welcome.html
- **Lines**: 1, 22, 30, 34, 49 (subject + body excerpts)
- **Current copy**:
  > Line 1 (subject): `<!-- Subject: Your VIP spot is locked. Here's what that means. -->`
  > Line 22: `Someone asked me recently: "What does VIP actually get me?"`
  > Line 30: `On the evening of 22 June, you get an email with your Birchal link. The public round opens 23 June. That 24-hour head start is yours because you committed early, and early investors in community rounds like this often fill the first tranche before most people have even read the announcement.`
  > Line 34 (footer-like): `<strong>Always consider the general CSF risk warning and offer document before investing.</strong>`
- **Banned phrases**: "Your VIP spot is locked" (paraphrase of "lock in your investment early"), "24-hour head start" + "early investors ... often fill the first tranche before most people have even read the announcement" (== "invest before the public" + unverified demand-signal claim that contradicts equal-access), implied "first access to invest"
- **Missing disclosures**: full s738ZG(6) (only the truncated CSF risk warning is present), equal-access (in fact this content directly contradicts equal-access), refund-on-request-before-close
- **Severity**: HIGH

### 8. Drip — VIP drip 1 / 2 / 3 (HTML templates)
- **File(s)**:
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/emails/drip_vip_1.html
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/emails/drip_vip_2.html
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/emails/drip_vip_3.html
- **Lines** (concatenated, key offending lines):
  > **drip_vip_1.html L30**: `You're on the VIP list because you placed a refundable deposit. That means on 22 June 2026, you get the Birchal link 24 hours before it goes public. Day one funding matters. It signals to every farmer we work with that this model has real backing.`
  > **drip_vip_2.html L38**: `Crowdfunding rounds can fill fast, especially when a community has been waiting. VIPs who move on day one lock their position before the public wave arrives.`
  > **drip_vip_2.html L40**: `The refundable deposit you placed is your proof of intent. It's not deducted from your investment. It just held your spot.`
  > **drip_vip_3.html L28**: `23 June 2026. The FarmThru round opens on Birchal, and your VIP link lands in this inbox 24 hours before the public list sees it. Day one funding matters. The investors who move first set the tone for every family and farmer who comes after.`
  > Footer in each: `<strong>Always consider the general CSF risk warning and offer document before investing.</strong>`
- **Banned phrases**: "you get the Birchal link 24 hours before it goes public" (== "invest before the public"), "VIPs who move on day one lock their position before the public wave arrives" (== "lock in your investment early" + "VIPs invest first"), "your VIP link lands in this inbox 24 hours before the public list sees it" (== "invest before the public"), "The investors who move first set the tone" (urgency/scarcity around investment timing without safe-harbour)
- **Missing disclosures**: full s738ZG(6) (truncated CSF risk warning only), equal-access (contradicted directly), refund-on-request-before-close
- **Severity**: HIGH

### 9. Drip — non-VIP drip 2 (Upgrade-to-VIP CTA)
- **File**: /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/emails/drip_nonvip_2.html
- **Lines**: 34, 40, 44, 53
- **Current copy**:
  > Line 34: `FarmThru is raising through Birchal, Australia's leading equity crowdfunding platform. The round opens 23 June 2026.`
  > Line 40: `When you invest, you're not donating to a cause. You're owning a piece of the supply chain that pays farmers first.`
  > Line 44: `As a non-VIP waitlist member, you'll get access when the round opens publicly on 23 June. Upgrade to VIP with a small refundable deposit and you'll see the offer 24 hours before everyone else.`
  > Line 53 (CTA): `<a href="{{CAMPAIGN_URL}}" ...>Reserve VIP access (refundable)</a>`
- **Banned phrases**: "you'll see the offer 24 hours before everyone else" (== "invest before the public"), "Reserve VIP access" (== "reserve your spot in the round"), "Upgrade to VIP ... see the offer 24 hours before everyone else" (== "VIPs invest first")
- **Missing disclosures**: full s738ZG(6) (only the truncated CSF risk warning), equal-access (directly contradicted), refund-on-request-before-close
- **Severity**: HIGH

### 10. Drip — non-VIP drip 3 (CTA)
- **File**: /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/emails/drip_nonvip_3.html
- **Lines**: 49
- **Current copy**:
  > `<a href="{{CAMPAIGN_URL}}" ...>Upgrade to VIP (refundable)</a>`
  > Plus footer `<strong>Always consider the general CSF risk warning and offer document before investing.</strong>`
- **Banned phrases**: "Upgrade to VIP" (in immediate context of "the round opens" = pressure to lock in investment access)
- **Missing disclosures**: full s738ZG(6), equal-access, refund-on-request-before-close
- **Severity**: MED (CTA only — but lives next to the "round opens" framing in the body)

### 11. Drip — non-VIP drip 1 (waitlist framing — adjacent risk)
- **File**: /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/emails/drip_nonvip_1.html
- **Lines**: 30, 47
- **Current copy**:
  > Line 30: `We're not open yet. But the farms are ready, the hub is coming, and the waitlist is how you get first access when we do.` (this is **product**-context — first access to the hub product, not the round — but the disclosure is identical)
  > Line 47 (footer): `<strong>Always consider the general CSF risk warning and offer document before investing.</strong>`
- **Banned phrases**: "first access" (in product-context — borderline)
- **Missing disclosures**: full s738ZG(6), equal-access (in case readers conflate hub-product first-access with investment first-access)
- **Severity**: MED

### 12. Mission-control admin dashboard — VIP Track section
- **File**: /Users/jb/Documents/GitHub/sales-skill/web/templates/mission-control.html
- **Lines**: 360–361, 443–500 (key offending lines 449, 450, 452, 459, 472, 484, 495)
- **Current copy**:
  > Line 449: `<span class="mc-section__title">VIP Track</span>`
  > Line 450: `<span class="mc-section__count">{{ meta.get("deposit_amount", "$5") }} deposit</span>`
  > Line 452: `Subscribers who place a {{ meta.get("deposit_amount", "$5") }} refundable deposit`
  > Line 458: `<div class="mc-card__name">VIP Welcome</div>`
  > Line 459: `<div class="mc-card__subject">VIP confirmed. You'll be first to invest.</div>` ← INTERNAL ADMIN COPY THAT CLAIMS "FIRST TO INVEST"
  > Line 472: subject preview `What I told my accountant last Tuesday`
  > Line 483: `<div class="mc-card__subject">Your 24-hour head start: here's exactly how it works</div>`
  > Line 495: `<div class="mc-card__subject">Your link goes live tomorrow</div>`
- **Banned phrases**: "VIP confirmed. You'll be first to invest." (line 459, banned phrase verbatim — it is internal-only but mirrors the banned framing the team is meant to avoid AND can leak via screenshots / Loom recordings)
- **Missing disclosures**: N/A (admin dashboard, not subscriber-facing) — but the framing primes the team to use the same banned language externally
- **Severity**: MED (internal but leaks the banned mental model into team comms)

### 13. Source-of-truth JSON — EM-WELCOME-VIP.json (learning-loop)
- **File**: /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/emails/EM-WELCOME-VIP.json
- **Lines**: 2–17 (subject + body fields)
- **Current copy** (subject + body):
  > Subject (line 10): `Your VIP spot is locked. Here's what that means.`
  > Body (line 12 excerpt): `Your refundable deposit locked your spot in the first group to see the FarmThru equity round. Not the waitlist. Not the queue. The first group. ... On the evening of 22 June, you get an email with your Birchal link. The public round opens 23 June. That 24-hour head start is yours because you committed early, and early investors in community rounds like this often fill the first tranche before most people have even read the announcement.`
  > user_review_note (line 17): `We need to remove anything about investing dollar amounts. No minimum investment, no maximum. We can say that we are going to do a raise, but not those parts. Also, must as the CSF warning. The csf warning is: "Always consider the general CSF risk warning and offer document before investing."` ← founder already flagged this
- **Banned phrases**: "Your VIP spot is locked" (== "lock in your investment early"), "the first group to see the FarmThru equity round. Not the waitlist. Not the queue. The first group." (== "first access to invest" + "beat the queue"), "24-hour head start" + "early investors ... often fill the first tranche before most people have even read the announcement" (== "invest before the public" + "1,500 VIPs ready to invest"-style unverified demand-signal claim)
- **Missing disclosures**: full s738ZG(6) (only the truncated CSF warning is present), equal-access (directly contradicted), refund-on-request-before-close
- **Severity**: HIGH (this is the source-of-truth that compiles down into the deployed drip_vip_welcome.html)

### 14. Source-of-truth JSON — EM-WELCOME-NONVIP.json (learning-loop)
- **File**: /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/emails/EM-WELCOME-NONVIP.json
- **Lines**: 12, 17
- **Current copy**:
  > Body (line 12 excerpt): `FarmThru is opening a community funding round on 23 June. And right now, for a small refundable deposit, you can lock a VIP spot and see the offer 24 hours before the public.`
  > creative_brief (line 7): `One CTA button: 'Reserve my VIP spot for $5'.`
- **Banned phrases**: "you can lock a VIP spot and see the offer 24 hours before the public" (== "lock in your investment early" + "invest before the public"), "Reserve my VIP spot for $5" (== "reserve your spot in the round" — and "$5" itself per global FMTH no-$ rule)
- **Missing disclosures**: full s738ZG(6), equal-access, refund-on-request-before-close
- **Severity**: HIGH

### 15. Source-of-truth JSON — EM-VIP-01 / EM-VIP-02 / EM-VIP-03 (learning-loop)
- **File(s)**:
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/emails/EM-VIP-01.json
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/emails/EM-VIP-02.json
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/emails/EM-VIP-03.json
- **Lines**: body fields (line 12 in each)
- **Current copy** (key offenders):
  > **EM-VIP-01** body: `You're on the VIP list because you placed a refundable deposit. That means on 22 June 2026, you get the Birchal link 24 hours before it goes public. Day one funding matters. It signals to every farmer we work with that this model has real backing.`
  > **EM-VIP-02** body: `Crowdfunding rounds can fill fast, especially when a community has been waiting. VIPs who move on day one lock their position before the public wave arrives. ... It's not deducted from your investment. It just held your spot.`
  > **EM-VIP-03** preheader (line 11): `Your VIP link goes live 23 June. 24 hours before anyone else sees it.`
  > **EM-VIP-03** body: `23 June 2026. The FarmThru round opens on Birchal, and your VIP link lands in this inbox 24 hours before the public list sees it. Day one funding matters. The investors who move first set the tone for every family and farmer who comes after.`
- **Banned phrases**: "you get the Birchal link 24 hours before it goes public" / "Your VIP link goes live 23 June. 24 hours before anyone else sees it." / "your VIP link lands in this inbox 24 hours before the public list sees it" (all == "invest before the public"), "VIPs who move on day one lock their position before the public wave arrives" (== "VIPs invest first" + "lock in your investment early"), "The investors who move first set the tone" (urgency-around-investment without safe-harbour)
- **Missing disclosures**: full s738ZG(6), equal-access, refund-on-request-before-close
- **Severity**: HIGH (and EM-VIP-01 has an additional founder-flagged issue: the user_review_note (line 17) flags the VC-conversation story as potentially fabricated — separate concern but worth raising)

### 16. Source-of-truth JSON — EM-NONVIP-01 / EM-NONVIP-02 / EM-NONVIP-03 (learning-loop)
- **File(s)**:
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/emails/EM-NONVIP-01.json
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/emails/EM-NONVIP-02.json
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/emails/EM-NONVIP-03.json
- **Lines**: body field (line 12)
- **Current copy** (key offenders):
  > **EM-NONVIP-02** body: `As a non-VIP waitlist member, you'll get access when the round opens publicly on 23 June. Upgrade to VIP with a small refundable deposit and you'll see the offer 24 hours before everyone else.`
  > **EM-NONVIP-01** body: `If you want to go further than just being a customer — if you want to own a piece of the grocery store that pays farmers first — there's a way to do that too. More on that in a few days.`
  > **EM-NONVIP-03** body: `That moment is one week away. 23 June 2026. The FarmThru equity crowdfunding offer opens on Birchal. ... Decide your number — the amount that feels right for you.`
- **Banned phrases**: "you'll see the offer 24 hours before everyone else" (EM-NONVIP-02 == "invest before the public"), "Decide your number — the amount that feels right" (EM-NONVIP-03 — invites investment-amount decision before offer document is provided)
- **Missing disclosures**: full s738ZG(6), equal-access (EM-NONVIP-02 directly contradicts), refund-on-request-before-close
- **Severity**: HIGH (NONVIP-02), MED (NONVIP-01, NONVIP-03)

### 17. Source-of-truth JSON — Landing pages LP-A / LP-B / LP-D / LP-E / LP-F / LP-M / LP-N / LP-P (learning-loop)
- **File(s)**:
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/landing-pages/LP-A.json
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/landing-pages/LP-B.json
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/landing-pages/LP-D.json
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/landing-pages/LP-E.json
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/landing-pages/LP-F.json
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/landing-pages/LP-M.json
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/landing-pages/LP-N.json
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/landing-pages/LP-P.json
- **Lines**: hero_copy + section bodies (varies)
- **Current copy** (key offenders, excerpted):
  > **LP-A** body: `Join the waitlist to be first in when the campaign opens. ... Your $5 refundable deposit secures your spot on the VIP list.`
  > **LP-B** body: `Place a $5 refundable deposit to join our VIP waitlist. You'll get early access before the campaign goes live.` (and the disclaimer body line 40 has stronger framing including "The $5 VIP deposit is fully refundable and does not constitute an investment or obligation to invest." — closest to compliant equal-access wording in the corpus)
  > **LP-E** body: `Join the VIP waitlist with a $5 refundable deposit. You get first access to the campaign, priority updates, exclusive Q&A with the founding team`
  > **LP-M** body: `The VIP waitlist gives you first access to invest, priority updates, and an exclusive Q&A with our founding team. It costs $5, fully refundable, no commitment. ... The waitlist closes before launch. Once it's full, it's full. Join now or wait for whatever's left.`
  > **LP-N** body: `A $5 refundable VIP deposit gets you first access, priority updates, and an exclusive Q&A with the founding team. ... The VIP waitlist exists so we can open strong. Your $5 refundable deposit signals intent. It puts you at the front of the line.` AND ALSO declares `Minimum investment is $50. Maximum is $10,000 per investor.` — investment minimums in the LP body, which contradicts founder review note "We need to remove anything about investing dollar amounts."
  > **LP-P** body: `puts you 30x more likely to participate on launch day` (unverified demand-signal claim)
- **Banned phrases**: "first access to invest" (LP-M, LP-N, LP-E paraphrase), "puts you at the front of the line" (LP-N == "beat the queue"), "first in when the campaign opens" (LP-A == "first access to invest"), "early access before the campaign goes live" (LP-B == "invest before the public"), "30x more likely to participate on launch day" (LP-P == unverified demand signal), "Once it's full, it's full" (LP-M == "limited spots — VIPs go first"), "Minimum investment is $50. Maximum is $10,000 per investor" (LP-N — investment-amount references the founder explicitly forbade)
- **Missing disclosures**: full s738ZG(6) (most have a generic ASIC/crowd-sourced funding paragraph but none cite the s738ZG(6) wording verbatim or include the Birchal URL inside the safe-harbour sentence), equal-access (none), refund-on-request-before-close (most say "fully refundable at any time" rather than "before round closes" — close but imprecise)
- **Severity**: HIGH (LP-M, LP-N), MED (LP-A, LP-B, LP-D, LP-E, LP-F, LP-P)

### 18. Source-of-truth JSON — learning-loop FMTH HTML variants (campaigns/variants)
- **File(s)** (mirrors the sales-skill production HTMLs but with `$5` retained instead of `small`):
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/campaigns/variants/index.html
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/campaigns/variants/index-b.html through index-p.html (8 files total in worktree)
- **Lines**: VIP section blocks 130–150 typically
- **Current copy**: matches the sales-skill production text verbatim except `$5` is used instead of `small refundable amount`. Same banned-phrase set as touchpoint 2.
- **Banned phrases**: same as touchpoint 2 (see above)
- **Missing disclosures**: same as touchpoint 2
- **Severity**: HIGH (these source files are what the next regeneration pass would emit if not cleaned first)

### 19. Meta ad — CFE-104 (waitlist priority hook)
- **File**: /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/meta-ads/CFE-104.json
- **Lines**: 3, 10, 12
- **Current copy**:
  > tactic (line 3): `waitlist-priority`
  > primary_text (line 10 excerpt): `We're building something different and the waitlist is how you get first access. Early spots are limited. Once our hub capacity fills, new orders queue behind existing collectors.`
  > description (line 12): `Waitlist members get first access to FarmThru's Brookvale hub. Spots are limited.`
- **Banned phrases**: "first access" + "Early spots are limited" (this one is **product**-context — first access to the **hub product**, NOT investment — but it primes the same audience and framing)
- **Missing disclosures**: equal-access (would be needed if the audience overlaps with the investment audience), s738ZG(6) (not strictly required for product-only ads but advisable as the audience is shared)
- **Severity**: MED (product-context but the audience and framing are the same — confusion risk is real)

### 20. Reference / brand-tracking docs (REFERENCE.md, brand.json, meta.json, smart-money.md)
- **File(s)**:
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/REFERENCE.md (lines 20, 39, 96, 242)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/brand.json (line 20 — only CSS class names referencing `.vip__title`)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/variants/smart-money.md (variant strategy doc — references VIP framing as a planned approach)
- **Current copy**:
  > REFERENCE.md L20: `| VIP deposit | $5 refundable |`
  > REFERENCE.md L39: `- VIP perks: first access, priority updates, exclusive Q&A, fully refundable.`
  > REFERENCE.md L96: `- VIP deposit ($5 refundable): 20-40% conversion to investor vs 1-5% email-only.` (also asserts an unverified ROI claim that needs sourcing)
- **Banned phrases**: "first access" + "priority updates" (REFERENCE.md L39); "20-40% conversion to investor" (L96 — unverified investment-conversion claim)
- **Missing disclosures**: N/A (internal docs) — but feeds team mental model
- **Severity**: LOW (internal docs) — but should be updated alongside the production rewrite to avoid drift

### 21. _TEMPLATE drips (template that other future campaigns will inherit)
- **File(s)**:
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/_TEMPLATE/emails/drip_vip_welcome.html
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/_TEMPLATE/emails/drip_vip_1.html (L33: `you'll get your access link 24 hours before the public round opens on {{LAUNCH_DATE_DISPLAY}}. Minimum investment is {{MIN_INVESTMENT}}.`)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/_TEMPLATE/emails/drip_vip_2.html
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/_TEMPLATE/emails/drip_vip_3.html
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/_TEMPLATE/emails/drip_nonvip_1.html
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/_TEMPLATE/emails/drip_nonvip_2.html
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/_TEMPLATE/emails/drip_nonvip_3.html
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/_TEMPLATE/emails/index.json
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/_TEMPLATE/index.html
- **Banned phrases**: same VIP-first-access framing as the FMTH production drips
- **Missing disclosures**: same gaps
- **Severity**: HIGH (these templates propagate the banned framing to every future client onboarded — fix at the template level so the next CFE client inherits compliant copy)

### 22. Validator hard-coded scarcity rule
- **File**: /Users/jb/Documents/GitHub/sales-skill/web/variant_validator.py
- **Lines**: 763 (and 344–352 for the VIP-deposit check)
- **Current copy**:
  > L763: `has_scarcity = any(w in text_lower for w in ["early access", "limited", "spots", "first access"])`
  > L344–352: validator REQUIRES `vipDepositBtn` + `.vip__card` + literal `$5` substring in HTML — meaning any rewrite that drops the `$5` literal will fail this check.
- **Banned phrases**: `"first access"` is allow-listed as a positive scarcity signal (the opposite of what we now want)
- **Missing disclosures**: N/A (validator)
- **Severity**: MED (this validator REWARDS the banned phrasing — it must be updated before the rewrite, otherwise rewritten variants will fail validation)

### 23. Archived drip emails (already ignored at runtime — flagged for cleanup only)
- **File(s)**:
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/emails/_archive_v1/drip_4_product.html (L31: `If you want first access before the campaign opens to everyone, a $5 refundable deposit secures your VIP spot. That means priority access, founder updates, and an exclusive Q&A.`)
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/emails/_archive_v1/drip_5_countdown.html
  - /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/emails/_archive_v1/drip_6_live.html (L39: `VIP perks include first access when we launch mid-2026, priority updates, and exclusive founder Q&As. Your $5 deposit is fully refundable — but VIP access isn't available forever.`)
  - /Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/clients/farm-thru/loop/emails/_archive/EM-005.json
- **Severity**: LOW (archived, not sent — but easier to delete the worst examples than risk accidental re-activation)

## Files searched
Searches run across both repos (excluding `.git/`, `__pycache__`, `node_modules`):

learning-loop worktree (`/Users/jb/Documents/GitHub/learning-loop/.claude/worktrees/agent-a22393ed88c1152b9/`):
- `clients/farm-thru/loop/emails/*.json` (all welcome + drip JSON sources of truth)
- `clients/farm-thru/loop/landing-pages/*.json`
- `clients/farm-thru/loop/meta-ads/*.json`
- `clients/farm-thru/campaigns/variants/index*.html`
- `clients/farm-thru/{config.json,facts.json,rules.json,learnings.md,learnings-*.md,tone.md}`

sales-skill repo (`/Users/jb/Documents/GitHub/sales-skill/`):
- `web/campaigns/FMTH/index*.html` (16 production variants)
- `web/campaigns/FMTH/emails/*.html` (4 active drips + 1 welcome + archives)
- `web/campaigns/FMTH/{REFERENCE.md,brand.json,meta.json,variants/*}`
- `web/campaigns/_TEMPLATE/**` (template inheritance source)
- `web/templates/{campaign.html,campaign_thankyou.html,mission-control.html,admin-leads.html}`
- `web/{app.py,campaign_emails.py,campaign_drip.py,campaign_storage.py,campaign_store.py,campaign_tracking.py,emails.py,qualify.py,slack.py,variant_validator.py}`
- `web/tests/*.py` (cross-checked — only test fixtures, not subscriber-facing)

Search terms grepped (case-insensitive): `VIP`, `vip-`, `first access`, `early access`, `priority`, `priority access`, `priority allocation`, `supporter`, `Supporter`, `$5`, `founder Q`, `founder Q&A`, `founder updates`, `reserved`, `reserve your spot`, `lock in`, `beat the queue`, `Skip the queue`, `invest before the public`, `1,500 VIPs`, `limited spots`, `VIPs invest first`, `VIPs go first`, `stripe`, `twilio`, `sms`.

## Files NOT found / unclear (need founder confirmation)

- **SMS template (sent when round opens)** — searched sales-skill for `twilio`, `Twilio`, `sms`, `SMS`, `round opens`, `round_open`, `ROUND OPEN`, `launch_sms`, `sms_template`. **No SMS-sending code or template exists in either repo.** The "priority SMS notification" benefit promised in the locked Birchal product spec has no implementation. Founder needs to confirm: (a) is SMS being sent manually for now, (b) is it on a separate platform (e.g. Klaviyo, ManyChat), or (c) does this need to be built before launch? If it does not exist, the Birchal submission claim is currently aspirational — flag for founder.
- **Founder Q&A delivery mechanism** — searched for `founder Q&A` / `Q&amp;A`. The phrase appears as a perk in 12 LP variants and 4 drip emails, but **no calendar/booking/zoom integration exists in the codebase**. Founder needs to confirm how the Q&A is actually delivered (live event, recorded video, async email thread). Until that's clear, the perk is undeliverable.
- **"Supporter" as the new product name** — zero matches in sales-skill (only matches in REFERENCE files for unrelated content). The new "VIP Supporter" naming is not yet present anywhere in code; the rewrite is a clean greenfield rename of all the "VIP" / "VIP Access" / "VIP investor" strings.
- **Birchal URL** — no canonical Birchal-link constant found in either repo. The drip emails use `{{CAMPAIGN_URL}}` and `{referral_url}`, neither of which routes to a Birchal page. Founder must supply the s738ZG(6)-required Birchal URL string before the safe-harbour disclosure can be templated.
- **CSF-VIP-BIRCHAL-SUBMISSION.md** — referenced in the audit prompt at `clients/farm-thru/CSF-VIP-BIRCHAL-SUBMISSION.md` but this file does **not exist** in the worktree. Confirm whether it lives elsewhere (possibly main branch only, or in `.claude/worktrees/`).

## Recommended fix priority

1. **Stripe checkout description (touchpoint 5)** — fix first. It is the only touchpoint that creates a permanent transactional record (Stripe receipt) auditable by ASIC and Birchal, AND it is a one-line code change. Update `app.py` lines 708–710 to remove "priority access" and to add the equal-access + s738ZG(6) wording in the description field (Stripe limits product-description to 200 chars, so the disclosure may need to live in the success-page footer instead — that is a deliberate design choice the rewrite agent should resolve).
2. **`_TEMPLATE` directory (touchpoint 21)** — fix second. Otherwise every future CFE client inherits the banned framing.
3. **Sales-skill production HTMLs + drip emails (touchpoints 1, 2, 3, 4, 6, 7, 8, 9, 10, 11)** — bulk find-and-replace via the rewrite agent. The canonical block at lines 136–148 is repeated near-verbatim across 16 variants; one canonical replacement string can cover ~80% of the offending content. The thank-you template + JS-injected confirmation card use the same block — update them in lockstep.
4. **`variant_validator.py` (touchpoint 22)** — must be updated **before** the rewrite agent ships, otherwise rewritten variants will fail validation. Update L763 (drop `"first access"` from the scarcity allow-list, add it to a banned-phrase deny-list) and L344–352 (replace the literal `$5` substring check with a softer "deposit-amount mentioned" heuristic that lets the rewrite use words instead of the dollar literal).
5. **Source-of-truth JSON in learning-loop (touchpoints 13, 14, 15, 16, 17, 18)** — update last, but do not skip. If the next regeneration pass runs against today's JSON, it will re-emit all the banned framing into the deployed HTML. The JSON files are the upstream cause of the deployed downstream copy.
6. **Mission-control admin (touchpoint 12)** — single subject-line edit (`mc-card__subject` "VIP confirmed. You'll be first to invest.") + section-title rename. Fast win that prevents internal team from re-introducing the banned framing in future copy drafts.
7. **Meta ad CFE-104 (touchpoint 19)** — clarify product-vs-investment context with a one-line addition; do not delete the ad.
8. **Archived drips + REFERENCE.md (touchpoints 20, 23)** — clean up to prevent accidental re-activation; lowest urgency.

Total estimated copy surface to rewrite: ~16 LP HTMLs + 4 drip HTMLs + 1 welcome-email Python builder + 1 Stripe product description + 8 LP-source JSONs + 6 email-source JSONs + 1 thank-you template + 1 campaign-template JS block + 1 mission-control template + 1 validator file + 9 _TEMPLATE files = **48 files total** (plus the Stripe checkout product registered live with Stripe — verify whether the product is created on each checkout or registered once).
