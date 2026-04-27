# Birchal VIP scheme — regulatory analysis (ASIC RG 261/262 + Corps Act)

**Date**: 2026-04-27
**Purpose**: Map Birchal's 4 concerns to specific regulatory provisions, with chapter-and-verse citations, so FarmThru can respond to the "we have a few questions" call from a position of knowledge.
**Status**: Research summary — NOT legal advice. Get a CSF-experienced lawyer to confirm before action.
**Sources**: ASIC RG 261, RG 262 (local copies under `shared/regulatory/csf-australia/`), Corps Act 2001 ss260A–260D, 738Q, 738ZA, 738ZD, 738ZE; Connective Services v Slea [2019] HCA 33; Birchal EOI guidance.

---

## Executive summary

1. **Concerns #3 (where the funds are held) and #4 (risk to investors) are NOT weird** — they are the foundational protections of the CSF regime. The whole point of Pt 6D.3A is that retail investor money sits in an AFSL trust account at the intermediary (RG 262.103, RG 262.164–.165, Corps Act s981B + reg 7.8.01–7.8.03), so the investor is protected if the issuer collapses or the offer is cancelled. FarmThru's $5 sits in FarmThru's own Stripe account — i.e., outside that protection — so Birchal needs to be satisfied (a) the $5 is not application money in substance, and (b) the investor has not been led to believe they are protected when they are not.

2. **Concern #2 (refunds + financial assistance) is the LARGEST single risk.** There is a CSF-specific prohibition on financial assistance — s738ZE — that operates **separately and more strictly than s260A**. RG 261.88–.90 spells it out. If FarmThru refunds the $5 around the time the investor applies for shares (especially on the same Stripe customer / same payment instrument), there is a real argument that the company has provided "financial assistance" to acquire shares, which is a strict prohibition under s738ZE. Penalties hit the directors personally (s79 + s260D + s1311(1)).

3. **Concern #1 ("what's genuinely additional?") is well-founded** because Birchal's standard EOI campaign already provides: early access to the offer, delayed payment terms, early-bird rewards, founder Q&A, company updates and notification — all at zero cost to the investor (Birchal EOI guidance, public). FarmThru charging $5 for items Birchal already provides invites two questions: (i) what is the additional consideration the investor is paying for? and (ii) is the marketing misleading by overstating what is offered (RG 261.96, RG 261.99(a), s1041H)?

4. **The s738ZE financial-assistance prohibition is the strongest single regulatory hook** Birchal could be triggering on. It is strict, captures conduct "before or after" the share acquisition, and personal liability flows to directors. Connective Services v Slea [2019] HCA 33 confirms a broad commercial-substance reading of "financial assistance" — the question is whether the conduct improves the investor's "net balance of financial advantage" in connection with the acquisition.

5. **Birchal's pre-launch dishonesty trigger (RG 262.144) means Birchal cannot proceed if it forms the view the conduct is misleading.** It is a strict-liability gatekeeper offence for Birchal (RG 262.142–.143). That is the institutional reason Birchal is asking these questions hard.

---

## Concern-by-concern map

### 1. "What's genuinely additional?" — equal treatment + intermediary exclusivity

**Birchal's wording**: "Not clear what someone actually gets for their $5 in the pre-EOI period that they wouldn't get by EOI'ing a few weeks later — and Birchal's own facility already offers extended payment terms."

**Why this is not just a commercial quibble**:

- **The CSF regime is structurally one-tier.** RG 261.59 (s738ZA) requires the hosting agreement to "require all investor applications and all application money to be sent or paid to, and dealt with by, the CSF intermediary". RG 262.151: "all applications must be made through this facility and you must as soon as practicable reject, and refund any money paid for, any applications made other than through the application facility." The facility (RG 262.152) "must only be available while the relevant CSF offer is open." No paid pre-launch tiers, no priority allocation, no separate VIP channel.
- **Birchal's standard EOI already provides every "perk" for free.** Per Birchal's own help guide (https://help.birchal.com/en/articles/5018296), EOI subscribers "may also get updates, early access to the CSF offer and be eligible for delayed payment terms and early bird rewards". Notification ("don't miss out"), founder webinar, Q&A and early-bird invitations are all in the free EOI experience.
- **Equal-opportunity principle.** RG 261.322(c) carries forward the takeover principle that "as far as practicable, shareholders all have a reasonable and equal opportunity to participate in any benefits" (s602). ASIC routinely cites it as a fairness baseline.
- **Misleading-or-deceptive risk if marketing overstates what the $5 buys.** RG 261.96, 261.99(a) — "it may be misleading to … overstate or give unbalanced emphasis to the potential benefits". If the only material benefit of the $5 is items Birchal would provide free via EOI, the marketing is structurally susceptible to "misleading by overstatement".
- **Birchal-side problem**: RG 262.119(c) names misleading demand signals as a captured harm. A paid VIP-list count used to signal "demand" replicates that harm.

**Bottom line on concern 1**: Birchal is asking FarmThru to articulate the **non-Birchal-substitutable consideration** for the $5. If the answer is "an SMS plus things Birchal would have given anyway", the marketing overstates value (RG 261.99(a), s1041H). If "extended payment terms additional to Birchal's", that must be documented and compared in writing — Birchal already offers delayed payment terms.

---

### 2. Refund process & s260A / s738ZE financial assistance

**Birchal's wording**: "Refund process (and how it interacts with financial assistance considerations)."

This is the deepest problem. Two parallel financial-assistance prohibitions apply:

#### 2a. s260A — general financial assistance prohibition

**Test (s260A(1)):** "A company may financially assist a person to acquire shares (or units of shares) in the company or a holding company of the company **only if**: (a) giving the assistance does not materially prejudice: (i) the interests of the company or its shareholders; or (ii) the company's ability to pay its creditors; or (b) the assistance is approved by shareholders under section 260B (that section also requires advance notice to ASIC); or (c) the assistance is exempted under section 260C."

**Breadth of "financial assistance" (Connective Services v Slea [2019] HCA 33):** The High Court held that "any action by the company can be financial assistance if it eases the financial burden that would be involved in the process of acquisition or if it improves the person's 'net balance of financial advantage' in relation to the acquisition." On "to acquire": "'To acquire' includes conduct that is in connection with the process of an acquisition of the shares or units of shares and not limited to conduct for the purpose of acquisition." The test is commercial substance, not legal form.

**Application to the $5 + refund mechanic**: If FarmThru refunds the $5 to the investor on or around the time the investor applies for shares at Birchal — and especially if the refund flows back to the same payment instrument the investor uses to fund the share application — the company has, in commercial substance, returned $5 to the person to enable that person to apply for shares. Whether that "improves the person's net balance of financial advantage" in relation to the acquisition is a fact-and-circumstance question, but the answer is plausibly yes if the refund and the application are temporally linked.

**Whitewash exception (s260B):** Available, but expensive and slow — special resolution at 75% (excluding the recipient and their associates) or unanimous agreement of all ordinary shareholders, plus 14-day pre-meeting ASIC lodgement and a further 14-day post-approval ASIC notice before the assistance can be given. Total minimum runway approximately 22 days. Not a practical fix for a $5-per-investor mass-market scheme.

**s260C exemptions:** The relevant general categories (loans by financial institutions, employee share schemes, capital reductions, share buybacks, court-ordered assistance, distributions/discharges on ordinary commercial terms) do not naturally cover a refund-on-share-application scheme. None is an obvious fit.

**Consequences (s260D):**
- **The company is not guilty of an offence** for the s260A breach itself, and the underlying contracts remain valid.
- **BUT s260D(2) is a civil penalty provision** — any person "involved in" the contravention contravenes s260D(2). "Involved in" is defined in s79 (aided, abetted, counselled, procured, induced, was knowingly concerned in or party to, or conspired with others). This catches directors, officers, and arguably the agency that designed the scheme.
- **Civil penalty consequences (s1317E and the post-2019 penalty framework)** for individuals: pecuniary penalties (currently up to the greater of 5,000 penalty units or three times the benefit derived), disqualification orders, compensation orders.
- **Criminal liability if dishonesty involved**: s260D(3) and s1311(1) — maximum penalty for an officer involved dishonestly is 2,000 penalty units or 5 years imprisonment, or both.

#### 2b. s738ZE — CSF-specific financial assistance prohibition (the bigger hammer)

**RG 261.88 (operative): **"Your company, its related parties and the CSF intermediary hosting your company's CSF offer must not provide financial assistance, or arrange for financial assistance to be provided, to a retail investor in connection with your company's offer. For example, your company must not provide a loan (whether or not interest is charged to the borrower) to a retail investor so that the investor can purchase shares under your company's offer."

**RG 261.89:** "A company that financially supports the purchase of its own shares under a CSF offer may seek to artificially inflate investor demand for its shares, inappropriately induce investors to participate in the offer or cause the offer to appear more successful than it actually is."

**RG 261.90:** "This prohibition applies whether the financial assistance is provided **before or after** the investor acquires shares under the CSF offer."

**What makes s738ZE different from s260A:**
- **Applies even if conduct does NOT contravene s260A** — no material-prejudice carve-out, no whitewash, no s260C exemption. Stricter than the general prohibition.
- **Captures the intermediary too**: RG 261.88 binds the company, related parties **and the CSF intermediary**. If Birchal facilitates knowingly, Birchal also breaches.
- **"In connection with your company's offer"** is broader than s260A's "to acquire". A refund at the moment of application is plainly "in connection with" the offer.
- **Penalty: offence under s1311(1).** RG 261.88 Note: non-compliance "will commit an offence."

**Application of s738ZE to the $5 + refund mechanic:**
1. FarmThru charges $5 pre-EOI.
2. Investor later applies for shares at Birchal during the live offer.
3. Investor requests refund of $5 (per the scheme design — refundable on request).
4. FarmThru refunds the $5.

If steps 2 and 3 happen close together, the substance is: "the company has returned $5 to a person who is using FarmThru's account / Birchal application facility to acquire shares in FarmThru, and the return happens in connection with the offer." That is on-its-face capture by RG 261.88 and 261.90 ("before or after the investor acquires shares").

The risk does not depend on intent. RG 261.89 is clear that the harm ASIC sees is "artificially inflate investor demand" and "inappropriately induce investors to participate". Even if the founder's subjective view is "this is a marketing fee, not assistance", ASIC will look at substance.

**Mitigations the founder might propose, and why each is fragile:**
- *"Refundable on request only, requests rare."* The prohibition catches "providing or arranging" assistance — availability on request is plausibly arranging.
- *"It's only $5."* No de minimis carve-out in s738ZE. RG 261.88 captures even a $1 loan.
- *"Refund goes to the original card, not as a credit toward the share purchase."* Connective Services teaches the test is substance — does it improve the investor's net balance of financial advantage in connection with the acquisition?
- *"We refund only if the investor expressly says they don't want to invest."* If refunds are structurally available **only to non-applicants**, the nexus weakens. Conservative position: refunds-only-for-non-applicants is materially safer than refunds-on-request.

**Bottom line on concern 2**: The refund mechanic is the load-bearing risk. The current "$5 refundable on request" structure has a real probability of being characterised as financial assistance under s738ZE, with personal liability for directors under s260D and offence consequences under s1311(1). Birchal would also be exposed and would likely refuse to proceed without legal sign-off.

---

### 3. Where the funds are held

**Birchal's wording**: "Where the funds are held and how they're dealt with in the interim."

Reads strange to non-CSF founders because Stripe/Shopify routinely hold merchant receipts in the merchant's account. CSF inverts that: investor money is the regulator's central protection.

**The CSF rule** (RG 262.103, RG 262.164–.165; s981B + regs 7.8.01–7.8.03):

> **RG 262.103**: "Money you receive from investor clients must be held in an account of the licensee that is kept in accordance with s981B and operated as a trust account in accordance with regs 7.8.01–7.8.03."

> **RG 262.164**: "The client money provisions in Div 2 of Pt 7.8 apply to money that you receive for a CSF offer. Generally, money paid to an AFS licensee to be used to pay an issuer of shares or other financial products to acquire the financial products must be held in a trust account for the paying client."

> **RG 262.165 Table 4**: complete + shares issued → pay to company; closed but not complete → refund applicants; withdrawn under s738T or otherwise rejected → refund applicant.

**RG 261.59** (issuer side): "The hosting agreement … must require all investor applications and all application money to be sent or paid to, and dealt with by, the CSF intermediary".

**Architecture**: All application money in **Birchal's** AFSL trust account. Three permitted exits: to the issuer (offer completes), to the applicant (refund), or fees to Birchal. Bankruptcy-remote from both Birchal and the issuer.

**Where the $5 sits in FarmThru's scheme**: Stripe → FarmThru's bank account, comingled with working capital. Not in trust. If FarmThru becomes insolvent, the $5 is an unsecured trade payable. No segregation, no priority.

**Substance-over-form risk**: If ASIC characterises the $5 as application money in disguise (because the investor understood they were paying as a step toward investing), then it has been received outside the application facility. RG 262.151 requires the intermediary to "reject, and refund any money paid for, any applications made other than through the application facility." Corollary: the issuer cannot lawfully receive application money outside the facility. Marketing pitches the $5 as a gateway to investing earlier — temporal proximity, integrated funnel and framing all support a substance-based characterisation; ASIC's posture per Connective Services is to look at substance.

**Bottom line on concern 3**: Defensible only if the $5 is (a) genuinely for an ancillary product, (b) marketed without reference to share acquisition timing or terms, (c) not characterised by the buyer as "the price of investing earlier", and (d) on a separate Stripe ledger never reconciled with any CSF flow.

---

### 4. Risk to those investors (insolvency)

**Birchal's wording**: "Risk to those investors."

The consumer-protection corollary of concern #3. Even if the $5 is legally a marketing fee, the investor is at commercial risk in three ways CSF structurally protects against:

- **Insolvency before the offer opens.** $5 is in FarmThru's general account; customer is an unsecured creditor. CSF rules expose no investor money to issuer insolvency (RG 262.165 Table 4).
- **Insolvency after the offer opens but before the customer applies.** Same exposure: the $5 is gone. If the offer is closed early or fails (and FarmThru fails), no priority claim.
- **Failure to deliver.** $5 buys "priority SMS + early access + drip emails". If the offer never opens (Birchal closes under RG 262.144), deliverable is impaired. ACL statutory guarantees (ss54, 60, 64A Sch 2 Competition and Consumer Act 2010) bite, but as unsecured trade-creditor claims — not CSF-trust-protected.

The CSF regime *is* the consumer-protection architecture: every dollar an investor pays sits in an AFS licensee's trust, refundable in essentially every failure mode. FarmThru's $5 product breaks that promise — it sits outside CSF protections in the general accounts of a startup. Birchal, whose central AFS duty is to act "efficiently, honestly and fairly" (RG 262.30, s912A(1)(a)), cannot be indifferent.

**Compounding factor — RG 262.144 (gatekeeper duty)**: Birchal must refuse to publish (or suspend/close) where it has "reason to believe" directors have engaged in pre-offer misleading conduct, or are not of "good fame or character". A named factor for the latter is "failure to be frank and honest in dealing with and providing information to the intermediary". So investor-risk is also a can-Birchal-publish question.

**Bottom line on concern 4**: Inseparable from concern #3. The CSF regime is built to eliminate the very insolvency exposure FarmThru's scheme creates, and it implicates Birchal's gatekeeper duties.

---

## Why these aren't weird — founder-readable explanation

The CSF regime's central trick: retail investor money is held in a licensed intermediary's trust account, ring-fenced from the company's bankruptcy estate, until the offer either completes and shares issue or one of the refund triggers fires (cooling-off, non-completion, defective document, withdrawn offer). The investor cannot lose money to issuer collapse during the offer process.

When FarmThru takes $5 into its own account in connection with the CSF round, three central regime protections collide with that move:

1. **The money's not protected.** It's FarmThru's the moment Stripe clears. Birchal asks "where is the money held" because the regime's answer is always "in the intermediary's trust account" — and FarmThru's answer is "in our account", which the regime does not contemplate.

2. **The refund mechanic looks like financial assistance.** When a company gives a person money in connection with that person's purchase of the company's shares, the law calls that "financial assistance". The CSF regime has its own strict ban on it (s738ZE) with no whitewash escape valve. Birchal asks about refund timing because that's the characterisation trigger.

3. **The "what's additional?" question is the misleading-marketing test.** Birchal already provides notification, early access, delayed payment terms and early-bird invites — for free, via standard EOI. If the $5 marketing implies it buys things Birchal would have provided anyway, that overstates benefit (RG 261.99(a), s1041H).

The questions are not weird. They are the regime's three load-bearing protections, asked back to FarmThru as a sanity check.

---

## Strongest regulatory hooks Birchal could be triggering on

Ranked, strongest first:

1. **s738ZE + RG 261.88–.90 (CSF-specific financial assistance ban)** — strict prohibition, captures conduct "before or after" share acquisition, no whitewash, criminal offence under s1311(1), captures intermediary as well as company. **The single strongest hook.**

2. **RG 262.144 (gatekeeper trigger — pre-offer dishonesty)** — Birchal must refuse to publish if it has reason to believe directors have engaged in misleading conduct in connection with the offer. Strict liability for Birchal under RG 262.142–.143. Pulls in directors' "good fame and character" via the same paragraph.

3. **RG 261.96 + RG 261.99(a) + s1041H (misleading or deceptive conduct in advertising)** — applies to all marketing of an "intended offer". Particular risk if the $5 product is marketed with overstated benefits relative to Birchal's free EOI.

4. **RG 261.59 + RG 262.151–.152 + s738ZA (application facility exclusivity / money handling)** — if ASIC characterises the $5 as application money in substance, FarmThru has received it outside the only permitted facility. RG 262.151 requires immediate refund of money paid outside the facility.

5. **s260A + s260D + Connective Services v Slea [2019] HCA 33 (general financial assistance)** — even ignoring s738ZE, the general s260A capture is plausible because the High Court reads "financial assistance" broadly and "to acquire" extends to "conduct in connection with the process of an acquisition". s260D civil penalty exposure for officers; criminal for dishonesty.

6. **s602 / RG 261.322(c) (equal-opportunity principle)** — generalisable from the takeover context; ASIC routinely cites it as a fairness baseline. The CSF regime's structural single-tier design is the operative version of the principle.

7. **RG 262.119(c) (misleading demand signals)** — if the $5 VIP list count is used in launch marketing as if it were "confirmed investor interest", that is a named misleading-conduct example.

8. **s738ZG + RG 261.92, 261.94, 261.95 (advertising of intended CSF offer requires prescribed risk-warning statement)** — strict liability, 30 penalty units per breach. Every $5 product page that "directly or indirectly refers to" or is "reasonably likely to induce" application must carry the s738ZG(6) statement.

---

## Recommended next step

Before the call, get the s738ZE + s260A characterisation of the refund mechanic confirmed by a CSF-experienced lawyer (not a generalist corporate lawyer — the CSF-specific prohibition in s738ZE is the rare-issue point, and it is stricter than s260A in ways generalists routinely miss). The lawyer should be asked three specific questions to test which of Birchal's concerns is load-bearing:

1. **Is the $5 + refund-on-request structure capable of being characterised as financial assistance under s738ZE?** Specifically, does refund availability to a person who has applied for shares at Birchal trigger RG 261.88–.90? Would refund availability *only to non-applicants* materially change the risk?

2. **Is the $5 capable of being characterised as application money in substance under s738ZA / RG 261.59?** What design choices (separate Stripe ledger, no reference to share-acquisition timing, no integrated funnel from $5 receipt to Birchal application) would defeat that characterisation?

3. **Given Birchal's standard EOI already provides notification, early access, delayed payment terms and early-bird invites at no cost — can FarmThru articulate the non-Birchal-substitutable consideration for the $5 in writing, in a way that survives the RG 261.99(a) "overstating benefits" test and the misleading-conduct test in s1041H?**

If the answer to (1) or (2) is "yes, capable of capture", the structure must be redesigned (or scrapped) before launch. If the answer to (3) is "we can't articulate it without overstating", the marketing claim fails irrespective of the underlying mechanic. These are the three questions that determine whether the scheme can ship in any form.

---

## Source map (for the lawyer / advisor)

- **RG 261** (compilation Jun 2020, last refreshed Apr 2026): https://asic.gov.au/regulatory-resources/find-a-document/regulatory-guides/rg-261-crowd-sourced-funding-guide-for-companies/ — operative text in local copy `shared/regulatory/csf-australia/rg261.md`.
- **RG 262** (Oct 2018, refreshed Apr 2026): https://asic.gov.au/regulatory-resources/find-a-document/regulatory-guides/rg-262-crowd-sourced-funding-guide-for-intermediaries/ (PDF: https://download.asic.gov.au/media/kdljjy4d/rg262-published-18-october-2018-20260421.pdf) — operative text in local copy `shared/regulatory/csf-australia/rg262.md`.
- **Corporations Act 2001 ss260A–260D** (Pt 2J.3 financial assistance): https://www.legislation.gov.au/C2004A00818/latest
- **Corporations Act 2001 Pt 6D.3A (CSF regime), particularly ss738Q (gatekeeper), 738ZA (intermediary obligations / application facility / money), 738ZD (cooling-off), 738ZE (CSF-specific financial assistance prohibition), 1311(1) (offence), 1317E (civil penalty declaration)**: introduced by Corporations Amendment (Crowd-Sourced Funding) Act 2017 (No. 17, 2017) Sch 1.
- **Connective Services Pty Ltd v Slea Pty Ltd [2019] HCA 33** — High Court on the breadth of "financial assistance" and "to acquire"; "net balance of financial advantage" test.
- **24-125MR ASIC issues first crowd-sourced funding regime stop order** (Hirehood / VentureCrowd, 13 Jun 2024 interim; 9 Sep 2024 final): https://www.asic.gov.au/about-asic/news-centre/find-a-media-release/2024-releases/24-125mr-asic-issues-first-crowd-sourced-funding-regime-stop-order/ — first use of CSF stop-order powers; concerned share-structure / nominee arrangements (not financial assistance), but illustrates ASIC's willingness to use stop orders in the CSF space.
- **Birchal EOI guidance** (publicly published help articles): https://help.birchal.com/en/articles/5018296 (EOI campaign description — confirms Birchal already offers "early access to the CSF offer", "delayed payment terms", "early bird rewards" at no cost) and https://help.birchal.com/en/articles/6889435 (EOI process — confirms no payment required, non-binding).
- **Local prior research**: `clients/farm-thru/CSF-VIP-RESEARCH-RG261.md` (issuer-side analysis) and `clients/farm-thru/CSF-VIP-RESEARCH-RG262.md` (intermediary-side analysis) — comprehensive paragraph-by-paragraph mapping of the RGs to the VIP-product framings.

**No INFO sheet found**: ASIC does not publish a dedicated INFO sheet on CSF beyond the two RGs. The Pt 6D.3A statutory text plus the two RGs are the canonical sources.

**Caveat**: This analysis cites primary sources where available, with paraphrase where the verbatim text was behind paywalls (some AustLII / Lexology endpoints returned 403 to automated fetch). The s260A test, the s738ZE Note in RG 261.88, the High Court Connective Services formulations and the Birchal EOI public guidance are all confirmed verbatim. The detailed clause-by-clause text of s738ZA(1)–(8), s260B procedure, s260D(2)–(3) and the Sch 1 explanatory memorandum should be confirmed by the lawyer from a primary source before the call.
