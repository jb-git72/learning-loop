# POST-RESEARCH UPDATE — 2026-04-26

**Status**: Birchal (the CSF intermediary) reviewed the VIP product and approved the phrase "early private access to the investment offer" for use in marketing. The mandatory equal-access disclosure was also dropped as not required. See `CSF-VIP-BIRCHAL-SUBMISSION.md` §9 for Birchal's full response.

This means the original regulatory analysis below — which read RG 261.59 + RG 262.151 as a structural bar to "first access" framing — is the agency's pre-Birchal interpretation. Birchal's interpretation is more permissive (their platform supports a real VIP early-access window). The analysis below is preserved as the audit trail of the original reading; the operational compliance posture is set by Birchal's response.

Use the phrasing approved by Birchal. Stop using the equal-access disclosure. Apply the strong VIP card per `CSF-VIP-COPY-PACKAGE.md`.

---

# CSF VIP fee architecture — regulatory research (synthesis)

**Date**: 2026-04-26
**Question**: Can FarmThru charge $5 (real Stripe payment) for a "VIP" tier under ASIC's CSF regime? If so, what can the $5 buy and what wording is allowed?
**Sources**: RG 261 (issuer obligations) + RG 262 (intermediary obligations), in `shared/regulatory/csf-australia/`.
**Detailed per-RG research**: `CSF-VIP-RESEARCH-RG261.md`, `CSF-VIP-RESEARCH-RG262.md`.

---

## Headline finding

The $5 VIP product is **defensible** if the $5 buys a *separate, real service* (founder Q&A access, SMS notification, priority on the comms list, donation-with-thank-you-SMS).

The $5 product is **not defensible** if the $5 buys (or is presented as buying) any of:
- "First access to invest"
- Earlier investment timing
- Preferential allocation
- Reserved shares
- Any kind of investment priority

This is a **structural** constraint, not a wording one. Per RG 261.59 and RG 262.151, all applications must go through the intermediary's facility, and the facility is only available while the offer is open. There is *no place* in the CSF regime to grant earlier access. Marketing that claims this is **structurally false**, not just risky.

---

## The 5 most load-bearing quotes

### 1. RG 261.59 + RG 262.151 — single application facility
> "The hosting agreement … must require all investor applications and all application money to be sent or paid to, and dealt with by, the CSF intermediary."
>
> "All applications must be made through this facility. … The application facility must only be available while the relevant CSF offer is open—applicants must not be able to make applications while an offer is closed or suspended."

**Why it matters**: This is the *structural* reason "first access to invest" is impossible — not just risky. The issuer has no power to grant allocation priority. Every applicant goes through the same facility, only when the facility opens.

### 2. RG 261.95 — the inducement test (s738ZG(3))
> "In determining whether a statement … is reasonably likely to induce investors to apply under an offer, the following three factors must be considered: (a) whether the statement is part of normal advertising directed at maintaining or attracting customers; (b) whether the statement contains information that deals with the affairs of the company; and (c) whether an investor would likely be encouraged to invest in shares **on the basis of the statement rather than the CSF offer document**."

**Why it matters**: This is the test the VIP page would be defended against. The cleaner the $5 is tied to a service that's *not* the offer, the better.

### 3. RG 261.92 + s738ZG(6) — strict-liability prescribed statement
> "Your company may advertise its CSF offer or intended offer … provided that the advertisement or publication includes a statement that investors should consider the offer document and the general risk warning in deciding whether to apply under the offer."

**Why it matters**: Every VIP touchpoint that mentions or implies the offer must carry the s738ZG(6) statement. **Strict liability, 30 penalty units per breach.**

### 4. RG 262.144 — pre-offer dishonesty + good-fame triggers
> "Conduct that is misleading or deceptive, or likely to mislead or deceive, may occur at various stages of the CSF offer—for example: pre-offer—where you have reason to believe that the directors' representations about an offer are dishonest..."
>
> [Row 2, good-fame trigger]: "failure to be frank and honest in dealing with and providing information to the intermediary"

**Why it matters**: The intermediary (Birchal) MUST be told about the VIP scheme. Failure to disclose is itself a compliance failure — independent of whether the scheme's content is OK.

### 5. RG 261.96 + 261.99 — misleading-conduct standard
> "Your company and the CSF intermediary must ensure that advertisements for a CSF offer are not misleading or deceptive … it may be misleading to: (a) overstate or give unbalanced emphasis to the potential benefits … by giving undue prominence to the benefits compared with the risks."

**Why it matters**: "First access to invest" is misleading on its face because the access is structurally equal. Any framing that creates a false impression of allocation priority fails this test.

### Honourable mention: RG 262.113–.115, .117 — s738ZG applies pre-launch and to "other persons"
> "Generally, under s738ZG, you must not: (a) advertise a CSF offer or intended offer; or (b) publish a statement that: (i) directly or indirectly refers to a CSF offer or intended offer; or (ii) is reasonably likely to induce people to apply for securities under a CSF offer or intended offer ... This requirement applies to CSF intermediaries as well as companies making CSF offers and other persons."

**Why it matters**: Pre-launch advertising is captured. The VIP page exists pre-launch. It is captured.

---

## Verdict matrix

| # | Framing | RG 261 | RG 262 | Net |
|---|---|---|---|---|
| A | "Pay $5 for first access to invest" (current FMTH) | RED | RED | **RED — DON'T USE** |
| B | "Pay $5 for SMS notification when round opens" | AMBER | AMBER | **AMBER (defensible w/ disclaimers)** |
| C | "Pay $5 for exclusive founder Q&A access" | AMBER → GREEN | GREEN | **GREEN** |
| D | "Pay $5 to be first messaged when round opens" | AMBER | AMBER | **AMBER (defensible)** |
| E | "Pay $5 for queue position on our comms list" | AMBER | AMBER | **AMBER** |
| F | "Donation $5 — thank-you SMS" | AMBER | GREEN-AMBER | **GREEN (cleanest re-frame)** |

---

## Mandatory copy additions (every VIP page / email / SMS)

1. **s738ZG(6) safe-harbour statement** on every page/email/SMS that touches the offer:
   > "In deciding whether to apply for shares in the CSF offer, you should consider the CSF offer document and the general risk warning at [Birchal URL]."
   Strict liability if missing. 30 penalty units per breach.

2. **Explicit equal-access disclosure** — e.g.:
   > "All investors apply on the same terms when the round opens at Birchal. The VIP product does not provide earlier or preferential investment access."

3. **Tell Birchal** — submit the VIP page, confirmation email, and SMS template to Birchal for sign-off **before** launch. RG 262.144 row 2 makes failure to be frank with the intermediary a good-fame trigger.

---

## Phrasings the issuer CAN use

- "Be the first to know when our CSF round opens at Birchal."
- "Get the SMS the moment the round goes live."
- "Pre-register for an exclusive founder Q&A before the round opens."
- "Pay $5 to support our launch marketing — as a thank you, we'll text you when the round goes live."
- "Get priority on our comms list — we'll message you first when the round opens."
- "Founder updates and exclusive Q&A access. Investing happens at Birchal where every investor applies on the same terms."

(All paired with s738ZG(6) safe-harbour and the equal-access disclosure.)

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
- ANY reference to the round without the s738ZG(6) safe-harbour
- Forecasts of returns / valuation
- Statements attributed to "investors" that are actually the founder's (RG 261.99(c))

---

## Recommended path forward

1. **Drop** all "first access to invest" / "early access" wording immediately.
2. **Bundle** the $5 around three real services: (i) founder Q&A access, (ii) priority SMS notification, (iii) founder updates email. Refundable.
3. **Add** the s738ZG(6) safe-harbour + equal-access disclosure to every VIP touchpoint.
4. **Submit** to Birchal for sign-off before re-launching the VIP page.
5. **Author** VIP-001..EQUAL-001 compliance rules so the scoring engine enforces all of the above on every future variant.

---

## Open questions (need follow-up)

- Exact verbatim wording of the s738ZG(6) statement (likely in reg 6D.3A.10 — outside RG 261; ASIC INFO sheets may codify a standard form).
- Birchal's own platform T&Cs on parallel paid issuer products.
- ACL / consumer-protection treatment of the $5 if delivery fails (e.g. round closes early before SMS sent).
- GST / tax treatment of the $5 inflows.
- Refund policy implications (currently advertised as refundable).
