# FarmThru VIP scheme — restructure proposals

**Date**: 2026-04-27
**Purpose**: 5 alternative structures (4 in the original brief + a coordinator-requested voucher variant) that resolve Birchal's 4 concerns, ranked by (a) regulatory cleanness, (b) commercial viability, (c) likelihood Birchal approves
**Companion doc**: `birchal-vip-concerns-regulatory-analysis.md` (sister agent — for the regulatory citations: s260A, RG 261.59 / .92 / .95, RG 262.119 / .144 / .151)
**Audit trail**: `../CSF-VIP-RESEARCH.md`, `../CSF-VIP-RESEARCH-RG261.md`, `../CSF-VIP-RESEARCH-RG262.md`, `../CSF-VIP-BIRCHAL-SUBMISSION.md`

---

## Executive summary

- **Top recommendation: Proposal A (Free Insider List).** Drop the $5. Birchal's EOI *already* delivers everything the $5 currently buys — 48hr private access, extended payment terms, early-bird rewards — for free. The $5 is structurally redundant and creates four legal problems for zero upside Birchal recognises.
- **If founder is married to a paid product**, Proposal C (Voucher Bundle — $5 buys a $10 FMTH grocery voucher that must be redeemed before the offer opens) is the strongest paid path. Standalone consumer value, cleanest temporal separation from share application, margin-neutral on CAC basis. Two lawyer points pending: ACL gift-card carve-out + standalone-voucher framing.
- **Proposal D (Founder Pack) and Proposal E (Office Hours) are reserve paid options** if C is rejected. D = strong substance, 8-10 day build. E = cleanest regulatory fit, founder-time bottleneck.
- **Pre-call decision needed**: why does the founder want the $5 — qualified-lead filter, committed-investor signal, or revenue? Different answer → different proposal. See pre-call checklist.
- **Pitch order**: A primary, C fallback, D/E secondary, B reserve. Don't pitch all five.

---

## The constraint set

**Regulatory (per sister agent's analysis)**
1. **s260A — financial assistance**: company must not financially assist acquisition of its own shares. $5 cannot be credited toward share purchase or reduce effective share price for VIPs.
2. **RG 261.59 / RG 262.151 — single application facility**: all application money must flow through Birchal while the offer is open. $5 cannot sit in escrow as proto-application-money or net against share price.
3. **RG 261.92 / s738ZG(6)**: strict-liability risk warning on every touchpoint (already enforced).
4. **RG 261.95 — inducement test**: cleaner the $5 is tied to a non-offer service, safer the structure.
5. **RG 261.96–.99**: no false impression of preferential allocation or unapproved structural advantage.
6. **RG 262.144**: any new structure re-submitted to Birchal in writing before launch.

**Birchal's 4 concerns**
1. *"Not clear what someone gets for $5 they wouldn't get by EOI'ing later"* — and Birchal runs extended payment terms.
2. *"Refund process + financial assistance considerations"* — s260A nexus.
3. *"Where funds are held"* — application-money trust + insolvency segregation.
4. *"Risk to investors"* — FMTH late/insolvent/under-delivers.

**FMTH commercial / operational**
- ≤2-week implementation (no custodian setup, no new ASIC license).
- Works with existing stack: **Stripe**, **Mailerlite**, **Cloud Run** mission-control, **manual SMS**. No Birchal API beyond existing link-out.
- Gives founder a meaningful pre-launch commitment signal beyond passive EOIs.
- Doesn't require Birchal to change its facility.

---

## Proposal A: Free Insider List (drop the $5)

**One-line pitch**: Stop charging. Free signup at `join.farmthru.com.au` mirrors Birchal's EOI in everything except platform — captures name + email + mobile, delivers early SMS + founder updates. Tells users to also EOI on Birchal when that campaign opens.

**The $5 buys**: nothing. $5 is gone. Replaced with free signup.

**Refund mechanics / funds held / insolvency protection**: N/A — no charge, no s260A surface area, no investor risk on the pre-launch product (the underlying CSF investment risk remains untouched).

**How this addresses each Birchal concern**:

| # | Birchal concern | How A addresses it |
|---|---|---|
| 1 | What's genuinely additional? | Concedes the point honestly. The Insider List complements (not duplicates) Birchal's EOI with a personal SMS from the founder, a FMTH-controlled drip, and a narrative thread Birchal's platform doesn't carry. Users are told to *also* EOI for structural benefits. |
| 2 | Refund + s260A | Eliminated. |
| 3 | Where funds held | Eliminated. |
| 4 | Investor risk | Eliminated on the pre-launch product. |

**Pros**:
- Regulatory cleanest path. Zero ambiguity on s260A, RG 261.59, RG 262.151.
- 1-2 day implementation. Removes the entire compliance surface area we've been wrestling with for a week.
- Birchal almost certainly approves immediately.
- Founder still gets a hard signal: double opt-in email + SMS opt-in checkbox. SMS opt-in is a real conversion metric.

**Cons**:
- Loses the paid-deposit qualified-lead filter — list quality drops.
- Loses revenue-from-marketing-list framing.
- Loses the "VIP" status-object.
- Sunk cost in Stripe + Cloud Run paid-path code. (Stays in repo behind feature flag — restore in 1 day if Birchal reverses position.)

**Regulatory cleanness (1-5, 5 = trivially clean)**: **5**
**Commercial viability (1-5, 5 = matches current $5 conversion economics)**: **3** (lower-quality list but larger volume — net effect unclear)
**Likelihood Birchal approves (1-5)**: **5**
**Implementation effort**: 1-2 days. Drop Stripe step, change LP copy, batch-refund existing $5 collections, swap Mailerlite trigger from "Stripe payment" to "form submit", update mission-control labels. Re-submit to Birchal in writing.

---

## Proposal B: Donation to a Stated FarmThru Initiative

**One-line pitch**: $5 is an explicit, no-rewards donation to a named FarmThru initiative (e.g., "supports our regenerative farming pilot at Yorke Peninsula" — pick a real line item the founder can defend). Reward-side perks (SMS, founder updates) are free, available to everyone, not framed as consideration.

**The $5 buys**: nothing — explicitly stated as a donation. Page reads as donate-button next to free signup, not paid-product checkout.

**Refund mechanics**: 100% refundable on request, 7 business-day SLA, triggers documented (no-launch, withdrawal, change of mind). Disclosed on donate page + Stripe description.

**Where funds are held**: FMTH operating account. Not segregated as application money because they're not application money. Optional uplift: hold in a labelled internal sub-account with monthly reconciliation — but don't claim trust status we don't have.

**Insolvency protection**: Donations are unsecured. Required disclosure: "FarmThru's $5 donation is not held in trust and is not a deposit. If FarmThru becomes insolvent before refund is requested, donors rank as unsecured creditors."

**How this addresses each Birchal concern**:

| # | Birchal concern | How B addresses it |
|---|---|---|
| 1 | What's genuinely additional? | $5 is genuinely *not* additional — it's a donation, framed honestly. SMS + updates are free, separate. |
| 2 | Refund + s260A | Donation framing breaks s260A nexus (funds operating expenses, not share acquisition). *Needs lawyer sign-off* — substance test; if a court reads donate-button as price-for-perk, s260A reactivates. |
| 3 | Where funds held | FMTH operating account, disclosed. |
| 4 | Investor risk | Disclosed unsecured-creditor status; refund-on-request before round closes. |

**Pros**:
- Preserves Stripe-charge mechanic + revenue line.
- Honest framing — defensible against "what does $5 actually buy" because the answer is "nothing — it's a donation".
- Removes share-acquisition nexus (lawyer-blessed).

**Cons**:
- Donation framing must be **rigorously enforced everywhere** — one slip into "$5 secures your VIP access" collapses the framing.
- Donate-button conversion is lower than paid-product (~1-3% vs 5-15%).
- "Donation funds X" must be true — pick a real, namable initiative.
- Both donors and non-donors must get SMS (otherwise SMS is the consideration, framing collapses).

**Regulatory cleanness (1-5)**: **4** (depends on lawyer-blessed framing; one wording slip degrades to 2)
**Commercial viability (1-5)**: **2.5** (lower conversion, preserves revenue)
**Likelihood Birchal approves (1-5)**: **3** (Birchal will read this carefully; disclosure trio must be airtight)
**Implementation effort**: 4-5 days. Re-write `join.farmthru.com.au` to lead with free signup + secondary donate-button; rewrite Stripe description, all 4 drip emails, Mailerlite triggers; add insolvency + refund disclosures. Re-submit to Birchal.
**Needs lawyer sign-off**: yes (s260A substance-over-form risk).

---

## Proposal C: Voucher Bundle ($5 buys a $10 FarmThru product voucher)

**One-line pitch**: $5 buys a $10 FarmThru store voucher that **must be redeemed on the FarmThru shop before 2026-04-30** (or whichever date is ≥7 days before the offer opens). The pre-launch comms perks (SMS when offer opens + drip emails) are bundled in as a free bonus. Reframed customer-side as: *"Buy a $10 FarmThru voucher for $5. As a thank-you we'll also text you when the round opens."*

**Pre-flight tests** (all pass with caveats):
- **Test 1 — does FMTH have a real shop?** **PASS.** `farmthru.com.au` has an active e-commerce checkout (products with prices, add-to-cart, Brookvale-pickup or Sydney/Central Coast/Wollongong delivery). Voucher infra is real.
- **Test 2 — unredeemed voucher handling.** Adopt sub-option (a): voucher expires, $5 retained, no refund — disclosed upfront. Sub-option (b) "refund if unredeemed" re-introduces the $5-refunded-then-applied-as-shares pattern we're escaping (reject). Sub-option (c) "auto-extend" defeats temporal separation if voucher is still live when offer opens (reject).
- **Test 3 — ACL gift-card 3-year minimum.** ACL requires 3-year minimum expiry from 1 Nov 2019, BUT explicit carve-outs exist for "temporary marketing promotions" (ACCC's example: $100 gift card with a whitegood purchase within a month) and for cards "supplied in connection with the purchase of goods or services" for a limited period. The $10 voucher tied to a pre-launch marketing campaign with a stated end date almost certainly fits. **Lawyer confirmation in writing is the binary risk on this proposal.**
- **Test 4 — does this actually fix s260A?** On its face yes: $5 → voucher → groceries by 2026-04-30 → consumer transaction complete → separately, user applies for shares via Birchal with their own funds. **Substance-over-form risk**: ASIC could read "voucher offer is conditional on being on the VIP investor waitlist" as the financial-assistance link. Mitigation: voucher is sold *standalone* on the FMTH shop, anyone can buy, comms perks (SMS, updates) are an opt-in *checkbox at checkout*, not a gate. The voucher must exist and be marketable independent of the CSF campaign.
- **Test 5 — margin.** At ~50% grocery COGS, a $10 voucher redeemed = $5 product COGS. So $5 ticket - $5 COGS ≈ break-even *before* CAC value of acquired customer. vs current $5 - Stripe fees - refunds ≈ -$1. Voucher variant is margin-positive on CAC basis.
- **Test 6 — framing.** Frame as *"Buy a $10 FarmThru voucher for $5. Bonus: opt in to get an SMS when our round opens."* — consumer transaction headline, VIP perks bonus. NOT *"$5 for the VIP investor list, bonus voucher included"* which inverts and reactivates s260A.

**The $5 buys**: a $10 FMTH store voucher (single-use, expires 2026-04-30, redeemable on `farmthru.com.au`), plus an opt-in checkbox for the (free) Insider List.

**Refund mechanics**: Non-refundable, stated upfront, ACL-compliant (if Test 3 carve-out confirmed). ACL warranty refund applies if FMTH cannot fulfil (shop offline). No refund-on-request — that re-creates the s260A surface area.

**Where funds are held**: $5 immediately becomes deferred revenue (voucher liability on FMTH's balance sheet) until redemption or expiry. Standard accounting treatment for sold-not-yet-redeemed vouchers. Not application money. Not held in trust.

**Insolvency protection**: If FMTH becomes insolvent before voucher redemption, the customer ranks as unsecured creditor for the $5. Disclosed.

**How this addresses each Birchal concern**:

| # | Birchal concern | How C addresses it |
|---|---|---|
| 1 | What's genuinely additional? | A $10 FMTH voucher is concretely additional (worth more than the $5 paid; redeemable for actual groceries; not available via Birchal EOI). |
| 2 | Refund + s260A | The $5 buys a voucher. The voucher is redeemed for product before the offer opens. Consumer transaction is complete and temporally separated from any share application. *Substance test*: voucher must be sold standalone (not gated by VIP-list membership) — see Test 4. *Needs lawyer sign-off* on the standalone-voucher framing specifically. |
| 3 | Where funds held | Deferred revenue on FMTH's balance sheet (voucher liability). Standard accounting. Not application money. |
| 4 | Investor risk | $5 buys a voucher with a 6:1 face-value ratio ($10 for $5). Risk is voucher-non-redemption (mitigated by easy redemption + active shop) or FMTH insolvency (disclosed). No investment-product risk. |

**Pros**:
- Strongest "$10 > $5" answer on "what's genuinely additional" — concrete, monetary, immediately quantifiable.
- Drives traffic to the FMTH shop pre-launch — every $5 voucher buyer becomes a tested first-time customer (real CAC win).
- Preserves Stripe-charge mechanic + a revenue line.
- Margin-positive on a CAC basis if a meaningful share of redeemers come back.
- Clear temporal separation: voucher must be redeemed by 2026-04-30, well before the offer opens.
- Standard ecom infra — Shopify (or whatever runs `farmthru.com.au`) handles voucher codes natively.

**Cons**:
- **Voucher must be sold standalone** to keep s260A clean. This breaks the "exclusive VIP" framing — anyone can buy the voucher whether or not they join the Insider List.
- Margin cost: ~$5 COGS per redeemed voucher. If 1,000 vouchers sell and 80% redeem, that's ~$4,000 of grocery COGS subsidised by the campaign budget.
- ACL gift-card carve-out is a binary lawyer-confirmation question. If carve-out doesn't apply, expiry must be 3 years — which destroys the temporal-separation argument and re-routes back to s260A risk.
- Adds ops burden: voucher codes, redemption tracking, customer-service calls about voucher use.
- Founder loses the "VIP investor list" status-object framing (replaced with "voucher buyer + opted-in for SMS").

**Regulatory cleanness (1-5)**: **3.5** (clean on substance *if* (i) ACL carve-out confirmed, (ii) voucher sold standalone — both lawyer-sign-off points)
**Commercial viability (1-5)**: **4.5** (best of the paid options on a CAC-adjusted basis; ties paid-deposit conversion; adds shop revenue)
**Likelihood Birchal approves (1-5)**: **3.5** (Birchal will scrutinise the standalone-voucher framing carefully; if FMTH can show the voucher is sold to non-investors too, this likely lands; if it reads as a thin veneer over the same scheme, Birchal rejects)
**Implementation effort**: 4-5 days. Set up Shopify voucher code with single-use cap + 2026-04-30 expiry; add voucher product page to `farmthru.com.au` shop; rewrite `join.farmthru.com.au` to lead with voucher purchase + opt-in checkbox for Insider List; rewrite Stripe product description; rewrite drip emails to focus on voucher reminders + bonus SMS; add ACL-required disclosures (expiry, no-refund); add fulfilment workflow. Re-submit to Birchal.
**Needs lawyer sign-off**: yes, on two points — (i) ACL promotional-voucher carve-out applies, (ii) standalone-voucher framing severs s260A nexus.

**Founder follow-up questions** (things you can't confirm in 5 min):
1. **Shopify (or platform) voucher infra**: confirm `farmthru.com.au` has native voucher-code support, single-use cap, and date-based expiry — and that the Stripe → Shopify integration can issue a code on payment. (Most modern Shopify stacks do; verify.)
2. **ACL carve-out — written lawyer opinion**: get this in writing before launch. Ask the lawyer specifically about the *temporary-marketing-promotion exemption* (ACCC has guidance) and whether a 7-30-day voucher tied to a CSF pre-launch campaign qualifies.
3. **Standalone-voucher test**: confirm the voucher product page is buyable by anyone landing on the FMTH shop (not gated by `join.farmthru.com.au`), and that the marketing campaign for the voucher *can* run independently of the CSF campaign (in case Birchal asks).
4. **Voucher cannibalisation**: what's the founder's tolerance for $5 COGS subsidy per voucher buyer, and how many vouchers can FMTH afford to sell? (Sets the campaign cap.)
5. **Existing $5 refund handling**: same question as Proposal A — refund or convert to a voucher? Convert-to-voucher is operationally clean: existing buyers get a $10 voucher emailed, no refund needed, and they end up on the same final structure.
6. **Brookvale hub fulfilment capacity**: if 1,000+ vouchers redeem in a 1-2 week window, can the hub physically handle the picking volume?

---

## Proposal D: Founder Pack (digital content reward)

**One-line pitch**: $5 buys a digital "FarmThru Founder Pack" — a 20-30-page recipe book PDF featuring produce from named FMTH partner farms, plus an optional sticker-pack add. No vouchers (Proposal C handles that path). Pre-launch comms (SMS, updates) bundled in free.

**The $5 buys**: digital recipe book PDF (instant fulfil) + optional sticker pack (Brookvale hub mails, ~$1.50 per send). Bonus: free Insider List opt-in.

**Refund mechanics**: Refund-on-request before the round closes. Recipe book stays with the customer post-refund (content product, can't unsend).

**Where funds are held**: FMTH operating account. Consideration for fulfilment of a real content product. Not application money.

**Insolvency protection**: $5 ranks unsecured. Same disclosure language as Proposal B/C.

**How this addresses each Birchal concern**:

| # | Birchal concern | How D addresses it |
|---|---|---|
| 1 | What's genuinely additional? | Recipe book + sticker pack are concretely additional — not available via Birchal EOI. Comms perks bundled free. |
| 2 | Refund + s260A | $5 buys a content product. Substance test passes — content is the deliverable, not share access. |
| 3 | Where funds are held | Operating account. Standard digital-product accounting. |
| 4 | Investor risk | Risk is product-non-delivery; mitigated by instant-PDF fulfil + refund SLA + unsecured-creditor disclosure. |

**Pros**:
- Strong, defensible substance.
- Preserves Stripe charge + revenue.
- Recipe book is a reusable marketing asset post-campaign (collateral for the FMTH brand long-term).
- No COGS subsidy (unlike Proposal C voucher).

**Cons**:
- **Highest implementation effort** of the five — recipe book is 1-2 weeks of design + photography + farmer interviews.
- Lower perceived value than $10 voucher (Proposal C beats it on quantifiable additionality).
- "Recipe book + SMS bundle" still leaves open the "the SMS is what they really want" reading — copy discipline required.

**Regulatory cleanness (1-5)**: **4** (strong on substance; depends on copy not drifting back to "$5 secures VIP access" framing)
**Commercial viability (1-5)**: **3** (lower conversion than C; no CAC win; founder loves the brand-asset angle)
**Likelihood Birchal approves (1-5)**: **4** (substance is clear; build time is the only cost)
**Implementation effort**: 8-10 working days. Produce recipe book (designer + 3-4 farmer interviews), set up PDF delivery via Stripe + Mailerlite, optionally design + print sticker pack, rewrite touchpoints + drip emails. Re-submit to Birchal.
**Needs lawyer sign-off**: light (substance is clear; copy review only).

---

## Proposal E: Founder Office Hours (paid live access)

**One-line pitch**: $5 buys one ticket to a 30-minute live founder office-hours session (Zoom or in-person at Brookvale hub) — recurring monthly cadence pre-launch. Refundable before session date. Pre-launch comms bundled free.

**The $5 buys**: one ticket to a scheduled live session with founder Rachel. Cap ~25-50 per session.

**Refund mechanics**: Refundable before session date.

**Where funds are held / insolvency**: Operating account, standard service-revenue accounting. Same insolvency disclosure as B/D.

**How this addresses each Birchal concern**:

| # | Birchal concern | How E addresses it |
|---|---|---|
| 1 | What's genuinely additional? | A live founder session — Birchal does not offer this. Separable, time-bounded service. |
| 2 | Refund + s260A | $5 buys access to a meeting, not a share. Nexus broken. |
| 3 | Where funds held | Operating account, service-revenue accounting. |
| 4 | Investor risk | If meeting doesn't happen, refund. Risk contained. |

**Pros**:
- "$5 to ask the founder anything for 30 mins" is a clear consumer value-prop.
- Founder gets unfiltered investor-perspective input.
- Low fulfilment cost (founder time + Zoom).

**Cons**:
- **Founder-time scaling** — 1,500 signups = 30+ sessions. Founder is the bottleneck.
- Lower convert — most paid-deposit buyers don't want to attend a meeting.
- Less natural for FMTH (grocery, not SaaS).

**Regulatory cleanness (1-5)**: **4.5** (service-for-fee is a textbook commercial transaction)
**Commercial viability (1-5)**: **2** (founder-time bottleneck)
**Likelihood Birchal approves (1-5)**: **4.5** (cleanest paid-product structure)
**Implementation effort**: 3-4 days. Zoom + Calendly, LP copy, Stripe description, confirmation + reminder cadence, attendance cap. Re-submit to Birchal.
**Needs lawyer sign-off**: light.

---

## Recommendation

**Pitch order in the call**: Lead with **Proposal A (Free Insider List)** as the primary recommendation. Frame it as "Birchal raised four valid concerns and the cleanest answer is to drop the $5 entirely — Birchal already provides the structural benefits the $5 was supposedly buying, so the $5 is just creating compliance surface for no upside." This is the truthful position and Birchal will respect it.

If the founder cannot accept dropping the $5 entirely (revenue, status-object, qualified-lead-filter reasons), pitch **Proposal C (Voucher Bundle)** as the founder's preferred paid path. It has the strongest *quantifiable* answer to "what's genuinely additional" ($10 voucher > $5 paid), it preserves the Stripe charge, and the $5 → voucher → grocery-redemption → expiry-before-offer-opens flow gives the cleanest temporal separation from any share application. Two lawyer-confirmation points (ACL gift-card carve-out, standalone-voucher framing) — confirm in writing before the call if possible.

If Proposal C is rejected (lawyer can't confirm ACL carve-out, or founder doesn't want the COGS subsidy), fall back to **Proposal D (Founder Pack)** — strongest substance answer at the cost of 8-10 days of build time, or **Proposal E (Office Hours)** for the regulatory-cleanest paid option with the lowest implementation effort.

**Don't pitch Proposal B (Donation) first** — donations require a level of marketing-copy discipline FMTH has already struggled with (the original "first access to invest" framing) and one slip blows the framing. Reserve B as a written fallback if Birchal explicitly asks "is donation framing on the table".

**Critical question to ask Birchal in the call** to disambiguate: *"Of the four concerns you raised, is concern (1) — 'not clear what someone gets for $5' — sufficient on its own to require us to drop the charge, or would a structurally separable, monetary, redeem-before-offer deliverable (e.g., a $10 product voucher) resolve it?"* The answer collapses the decision space immediately.

**Fallback if Birchal rejects all paid options**: Proposal A is non-negotiable as the safety net. The Stripe + Cloud Run code stays in the repo behind a feature flag — restore in 1 day if Birchal's position changes.

---

## Pre-call checklist

1. **Why the $5?** Pin down founder reasoning: (a) qualified-lead filter, (b) committed-investor signal, (c) revenue, (d) status-object. Different reason → different proposal lands.
2. **Paid-vs-free conversion data** — if unknown, the "we lose qualified leads going free" claim is unsupported; be honest.
3. **Existing $5 collections** — refund mechanics for those buyers (`stripe refunds create --charge ch_xxx` per charge, dry-run first; Proposal C lets you convert these to vouchers instead of refunds).
4. **Lawyer pre-brief** — 30-min call covering: (a) substance-over-form on donation framing, (b) ACL gift-card carve-out + standalone-voucher framing for Proposal C, (c) Founder Pack copy review. Get written one-liner: "A/B/C/D/E acceptable as drafted".
5. **Pitch order** — Default: A primary, C fallback, D/E secondary fallback, B reserve.
6. **Post-call re-submission** — draft a re-submission email ready for whichever proposal lands; send within 24 hrs.
7. **Birchal rejects all paid options** — pre-agreed answer is *"we'll drop to free this week and re-engage on a paid structure post-launch"*. Don't negotiate.
8. **Timeline** — when does EOI campaign open? Offer campaign? Runway < 5 days = Proposal A only viable. Runway ≥ 10 days = Proposal C/D in scope.

---

## What NOT to do

- **Don't pitch a "$5 supports our marketing — VIP perks bundled free" structure (the half-donation half-product hybrid)** — it's the worst of both. The substance reads as paid-product, the form pretends to be donation, and one wording slip collapses to whichever Birchal reads it as. Either fully donate (B) or fully product (C/D), not both.
- **Don't propose escrow / hold-in-trust for the $5** — pretending the $5 is "held" creates a representation we'd need to honour, including for s260A purposes if the $5 is later credited toward shares. The simpler answer is: the $5 either is consumer revenue (C/D) or a donation (B), not investment money. Trust framing makes it worse.
- **Don't propose any structure that credits the $5 toward the share purchase price** — this is the bright-line s260A trigger and the bright-line RG 261.59 / RG 262.151 trigger. The $5 must terminate as either (i) revenue for a non-share product/service, (ii) refunded, or (iii) donation. It cannot become application money.
- **Don't propose a tiered VIP scheme ($5 / $20 / $100)** — multiplies every regulatory question by three and creates a "structural advantage" reading the more tiers there are. Single-tier or free.

