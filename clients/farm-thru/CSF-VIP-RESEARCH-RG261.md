# RG 261 — VIP fee architecture research (issuer perspective)

**Source document**: `shared/regulatory/csf-australia/rg261.md`
**Scope**: Issuer (FarmThru) obligations under ASIC Regulatory Guide 261. Intermediary (Birchal) obligations under RG 262 are covered separately.
**Question**: Is a paid "VIP early access" product (charged $5 by FarmThru on its own marketing site, with the public CSF round opening at Birchal where every investor's money is debited at the same time) compliant under RG 261?

---

## 0. Summary of the regulatory map

RG 261 is the issuer-facing guide. Section C ("How to make a CSF offer") and the cluster RG 261.86–RG 261.117 contain the operative obligations and prohibitions for a company conducting a CSF raise. The relevant clusters for a paid VIP product are:

- **Multiple CSF offers prohibited** — RG 261.87 (s738R)
- **No financial assistance to retail investors** — RG 261.88–RG 261.90 (s738ZE)
- **Inducement / artificial-demand language** — RG 261.89, 261.94(b)(ii), 261.95
- **Advertising rules** — RG 261.91–RG 261.110 (s738ZG); the key directive is the prescribed advertising statement (s738ZG(6))
- **Misleading or deceptive conduct** — RG 261.96–RG 261.101 (s1041E, s1041F, s1041H)
- **Communication facility (only good-faith statements permitted)** — RG 261.102–RG 261.105
- **Offers must be on the platform; hawking prohibition** — RG 261.114–RG 261.117 (s738L, s736)
- **Application money handling — all flows via the intermediary** — RG 261.59 (s738ZA)
- **Investor protections (cap, cooling-off, withdrawal, risk warning)** — RG 261.118–RG 261.119 and Table 10
- **Disclosure of payments to promoters/marketers in offer document** — Table 19 ("Payments to related parties and other persons", RG 261.180)
- **Equal opportunity to participate in benefits** — RG 261.322(c) (general takeover principle, s602)

Critically, RG 261 contains **no explicit "preferential allocation" prohibition** in the issuer guide — this is because allocation is structurally controlled by the intermediary's application facility (everyone applies via Birchal, money is debited together when the offer closes — see RG 261.85 and RG 261.59). The issuer cannot grant preferential allocation even if it wanted to. That structural reality drives most of the analysis below.

---

## 1. Inducements (RG 261.89, 261.94(b)(ii), 261.95)

> **RG 261.89** "A company that financially supports the purchase of its own shares under a CSF offer may seek to artificially inflate investor demand for its shares, inappropriately induce investors to participate in the offer or cause the offer to appear more successful than it actually is."

> **RG 261.94** "Without the inclusion of a statement that investors should consider the CSF offer document and the general risk warning, your company, the CSF intermediary hosting the CSF offer and other persons must not:
> (a) advertise the offer or intended offer; or
> (b) publish a statement that:
> (i) directly or indirectly refers to the offer or intended offer; or
> (ii) is reasonably likely to **induce** people to apply for shares under the offer or intended offer."
> **Note:** See s738ZG(1).

> **RG 261.95** "In determining whether a statement indirectly refers to a CSF offer or intended offer, or is reasonably likely to induce investors to apply under an offer, the following three factors must be considered:
> (a) whether the statement is part of normal advertising directed at maintaining or attracting customers;
> (b) whether the statement contains information that deals with the affairs of the company; and
> (c) whether an investor would likely be encouraged to invest in shares on the basis of the statement rather than the CSF offer document."
> **Note:** See s738ZG(3).

**Source**: RG 261.89, RG 261.94, RG 261.95.

**Applies to VIP**: Strongly. The "inducement" concept here is broad: any statement reasonably likely to induce a person to apply for shares is captured (regardless of whether it explicitly names the offer). A paid VIP product whose sales pitch is "first access to invest" is, on its face, "reasonably likely to induce people to apply for shares". Two distinct risks:

1. **Direct inducement risk (s738ZG)** — if the VIP-product marketing constitutes a "statement reasonably likely to induce people to apply for shares", then the prescribed offer-document/risk-warning statement must accompany every such communication, otherwise it is a strict liability offence (see RG 261.92, Note 1: 30 penalty units).
2. **Artificial demand risk (RG 261.89)** — RG 261.89 sits within the financial-assistance prohibition cluster. While 261.89 itself is reasoning about company-funded share purchases (not relevant to a $5 VIP fee paid *by* the investor), the underlying ASIC concern is generalisable: ASIC dislikes anything that "artificially inflate[s] investor demand" or "cause[s] the offer to appear more successful than it actually is". A VIP-list count being publicly used as a demand-signal ("3,000 VIPs already signed up — be first to invest") leans into the same concern even though it is not a s738ZE breach.

**Framing verdicts**:
- A. "Pay $5 for first access to invest" → **RED**. This is textbook inducement language under 261.95(c) — the investor is encouraged to invest "on the basis of the statement rather than the CSF offer document". Even if mitigated with the prescribed s738ZG(6) statement, the underlying claim ("first access to invest") is materially false because investment access at Birchal is structurally equal.
- B. "Pay $5 for SMS notification when round opens" → **AMBER**. This is a notification product, not an investment product. It is still "reasonably likely to induce" because notification timing is the entire selling point and the only reason a buyer pays $5 is so they can act on the offer. Mitigation: (i) include the s738ZG(6) prescribed statement on every page selling the SMS, (ii) make explicit that all investors compete for allocation on equal footing once the round opens at Birchal.
- C. "Pay $5 for exclusive founder Q&A access" → **AMBER-GREEN**. The Q&A is the deliverable. If the Q&A page does not "deal with the affairs of the company" in a way reasonably likely to induce an investment, and is not promoted as a route to invest, this is far from the inducement core. Mitigation: don't bundle Q&A registration with offer-document/Birchal links inside the same call-to-action; treat it as a content product. Per RG 261.95(b)–(c), if the Q&A content itself becomes "information that deals with the affairs of the company" and is "likely to encourage" investment, the prescribed advertising statement must accompany it.
- D. "Pay $5 to be first messaged when the round opens" → **AMBER**. Substantively identical to (B). Notification timing is the deliverable. Acceptable if (i) the prescribed s738ZG(6) statement appears on the sales page, (ii) the page does not claim or imply preferential allocation, and (iii) the founder accepts that the page is itself an "advertisement" of an "intended offer" within the meaning of RG 261.92.
- E. "Pay $5 for queue position on our public comms list" → **AMBER**. Same analysis as (B)/(D). "Queue position" must be unambiguously about *messaging order*, not *application order* (which is intermediary-controlled). Be wary of the word "queue" — it implies allocation queueing.
- F. "Pay $5 to support FarmThru's marketing costs — donation framing — VIPs get a thank-you SMS" → **AMBER**. The donation framing is a partial mitigation but does not eliminate the inducement test in 261.95: if a buyer reasonably infers the $5 buys access or visibility into the offer, it is captured. Note also: RG 261 Table 19 ("Payments to … any person promoting or marketing the offer") — funds raised under the CSF offer that go to promoters must be disclosed in the offer document. Pre-offer marketing fees raised *outside* the CSF offer are not Table-19 payments, but ASIC will still test the substance.

---

## 2. Preferential allocation / first access / priority

**Direct search of RG 261 returns no hits for "preferential", "priority", "first access", "queue", "VIP" or "early access".**

This is the most important finding. The reason these terms do not appear: RG 261 frames the CSF process so that allocation is structurally controlled by the intermediary's application facility, not by the issuer. The closest text is the equal-opportunity principle (taken from the takeovers context):

> **RG 261.322** "The overall objectives or principles of the takeover rules are to ensure that:
> (a) an acquisition of control of a company takes place in an efficient, competitive and informed market;
> (b) shareholders of a company are given enough time to consider, and information to assess, the merits of the change of control proposal; and
> (c) **as far as practicable, shareholders all have a reasonable and equal opportunity to participate in any benefits through the proposal** (see s602)."

**Source**: RG 261.322(c).

> **RG 261.323** "Even if your company is covered by the exception to the general prohibition in s606, the general principles above will continue to apply to transactions affecting 'control' of your company."

**Source**: RG 261.323.

**Applies to VIP**: Indirectly but powerfully. RG 261.322(c) is technically a takeovers principle, but ASIC consistently invokes "equal opportunity" as a generalisable fairness principle. More directly relevant: the structural equality of allocation in CSF offers comes from the application-facility framework:

> **RG 261.59** "The hosting agreement … (a) must require all investor applications and all application money to be sent or paid to, and dealt with by, the CSF intermediary".

> **RG 261.85** "If the CSF intermediary determines that your company's CSF offer: (a) is complete—your company will be required to issue shares to applicants under the offer and the intermediary will be required to pay the application money to your company (less fees payable to the intermediary under the hosting agreement) following the issue of the shares".

The combined effect: **the issuer cannot grant a preferential allocation even if it wanted to.** All applications and all money flow through the intermediary; the intermediary handles cooling-off, the investor cap, refunds and the close. Therefore any marketing claim of "first access to invest" or "priority allocation" is structurally false (and therefore misleading under s1041H — see Section 4 below).

**Framing verdicts**:
- A. "Pay $5 for first access to invest" → **RED**. False statement: Birchal controls allocation; investment access is equal.
- B. "Pay $5 for SMS notification when round opens" → **GREEN on this axis** (notification is not allocation; it does not falsely claim allocation priority).
- C. "Pay $5 for exclusive founder Q&A access" → **GREEN on this axis**.
- D. "Pay $5 to be first messaged when the round opens" → **GREEN on this axis** (messaging order is at the issuer's discretion; it is not allocation).
- E. "Pay $5 for queue position on our public comms list" → **AMBER on this axis**. The word "queue" risks reader inference of allocation queueing. Recommend "priority on our comms list" or "earlier notification".
- F. Donation framing → **GREEN on this axis** (the $5 is not buying allocation).

---

## 3. Equal treatment / fair / same terms / all investors

The phrase "equal" in RG 261 appears in:

> **RG 261.322(c)** "as far as practicable, shareholders all have a reasonable and equal opportunity to participate in any benefits through the proposal" (see Section 2 above).

The phrase "all investors" appears in operational contexts about refunds and withdrawal rights — these are uniform-treatment rules:

> **RG 261.81** "While the CSF intermediary may close an offer early, if this is done in circumstances where the offer is not yet 'complete', then the intermediary must refund application money to **all investors** who have applied under the offer."

> **RG 261.84** "If a CSF offer is closed for a reason other than the offer period has ended or the offer is fully subscribed … the CSF intermediary must refund application money to **all investors** who have applied under the offer."

> **Section C summary** (RG 261, p.5/106): "If a supplementary or replacement CSF offer document is published to correct a defective offer document, and the defect is materially adverse from the point of view of an investor, **all investors** have 14 days to withdraw their application and be repaid their application money."

The CSF offer itself is on uniform terms (Table 19, "Terms and conditions"):

> **Table 19 — Terms and conditions** (RG 261 Section 3, around RG 261.180): "You must include a description of: the type of shares being offered (i.e. fully-paid ordinary shares); the offer price (i.e. how much investors must pay for shares); the minimum and maximum subscription amounts … and the expected offer period".

**Source**: RG 261.81, RG 261.84, Section C key-questions table, Table 19.

**Applies to VIP**: Reinforces Section 2. The CSF offer is by design a uniform-terms offer (one share class, one price, one offer period, one application facility). There is no mechanism to give VIP investors a different price, allocation, or class of share. Any framing that suggests VIPs "get a better deal on the shares" is false.

**Framing verdicts**:
- A. "First access to invest" → **RED**. Falsely implies non-equal terms.
- B / D / E. Notification framings → **GREEN** if they make clear the *offer terms* are equal and only the *outbound message timing* differs.
- C. Q&A → **GREEN** (Q&A is not an investment term).
- F. Donation → **GREEN** (does not implicate offer terms).

---

## 4. Section C of RG 261 — advertising rules (RG 261.91–RG 261.110)

Section C is "How to make a CSF offer" (starts at line 442 of `rg261.md`); it spans RG 261.53–RG 261.119. The advertising rules sit inside it at RG 261.91–RG 261.110. The two operative provisions are the prescribed-statement rule (s738ZG(6)) and the misleading-or-deceptive rule.

### 4a. Prescribed advertising statement — s738ZG(6)

> **RG 261.91** "We recognise that advertising plays an important role in crowd-sourced funding. We want to ensure that companies, CSF intermediaries and other promoters give clear, accurate and balanced messages when advertising CSF offers."

> **RG 261.92** "Your company may advertise its CSF offer or intended offer, both before and after the CSF offer document is published on the CSF intermediary's platform, provided that the advertisement or publication includes a statement that investors should consider the offer document and the general risk warning in deciding whether to apply under the offer."
> **Note 1:** See s738ZG(6). If this statement is not included (and no other exceptions apply), your company and/or its officers will commit a strict liability offence, punishable by a maximum penalty of 30 penalty units.

> **RG 261.93** "The requirement to include a statement directing investors to the CSF offer document and general risk warning in advertisements for CSF offers aims to alert investors to the information contained in the CSF offer document, before applying for shares under an offer. The requirement applies to all forms of advertising, including advertising on your company's website and on social media (e.g. Twitter, YouTube and Facebook)."

> **RG 261.94** [quoted in Section 1 above]

### 4b. Misleading or deceptive

> **RG 261.96** "Your company and the CSF intermediary must ensure that advertisements for a CSF offer are not misleading or deceptive. Advertising includes information published on the communication facility for the offer and advertising on social media. The obligation not to engage in misleading or deceptive conduct also applies to information on the CSF intermediary's platform."

> **RG 261.99** "In particular, your company and the CSF intermediary should ensure the presentation of information on the intermediary's platform about your company and the CSF offer is not misleading. For example, it may be misleading to:
> (a) overstate or give unbalanced emphasis to the potential benefits (e.g. investment returns) and positive information (e.g. about the company and its management), or create unrealistic expectations by giving undue prominence to the benefits compared with the risks associated with your company's business;
> (b) not clearly or prominently disclose information about the risks facing your company's business or adverse information about your company …;
> (c) present views about the offer as those of investors or unrelated parties, whether on the communication facility, the intermediary's platform or in advertising (including contributions to social media), if these are in fact the views of your company, the intermediary or any associates."

**Source**: RG 261.91–RG 261.99.

**Applies to VIP**: All VIP sales pages, founder updates, SMS messages and emails that "directly or indirectly refer to" the intended CSF offer or are "reasonably likely to induce people to apply" are *advertisements* under s738ZG. They must:

1. Carry the prescribed statement directing the reader to the CSF offer document and the general risk warning (penalty: 30 penalty units, strict liability).
2. Not be misleading or deceptive.
3. Not overstate benefits or under-disclose risks (RG 261.99(a)–(b)).

**Framing verdicts** (advertising-compliance axis only):
- A. "First access to invest" → **RED**. Misleading per RG 261.96/99 (the claim is structurally false — see Section 2). Also captured by 261.94 inducement, requiring the prescribed statement.
- B. "SMS notification when round opens" → **AMBER**. Compliant with the prescribed-statement rule if the page carries the statement; substantively not misleading provided the page makes the equal-allocation point explicit.
- C. "Founder Q&A" → **AMBER**. Page itself can avoid being captured by s738ZG if it carries no offer-related statements. But Q&A *content* will almost certainly become a captured statement (the founder will discuss "the affairs of the company"). Both the page and the Q&A recording must carry the prescribed statement.
- D. "First messaged" → **AMBER**. Same as (B). The word "first" is a flag — be precise that this is messaging-first, not allocation-first.
- E. "Queue position on comms list" → **AMBER**. Same as (B); avoid "queue" language.
- F. "Donation" → **AMBER**. Even a donation page that mentions FarmThru's intended raise is captured by 261.94(b)(i)–(ii). Prescribed statement required.

---

## 5. Section D of RG 261 — communications during the offer

Section D ("Preparing the CSF offer document") begins at RG 261.120 and runs to RG 261.189. It is principally about the *contents* of the offer document published on the intermediary's platform — not about pre-launch issuer communications. The two provisions in Section D most relevant to a paid VIP product are:

### 5a. Disclosure of payments to promoters/marketers (Table 19, Payments to related parties and other persons)

> **Table 19 — Payments to related parties and other persons** (Section 3 of the offer document, around RG 261.180): "You must describe whether any of the funds raised will be paid (directly or indirectly) to: any current or proposed directors or senior managers of your company; any related parties of your company; any person that 'controls' your company or persons who hold more that 20% of the voting rights in the company …; the CSF intermediary publishing the CSF offer or any of the intermediary's related parties; and **any person promoting or marketing the offer**. This includes whether any of the funds will be paid through an interposed entity for the benefit of the person …"

**Source**: RG 261 Table 19 (Section D, "Information about the CSF offer that should be included in the CSF offer document").

**Applies to VIP**: This is a disclosure trigger if (and only if) CSF-raised funds will be paid back to promoters/marketers. The $5 VIP fees are not "funds raised under the CSF offer" — they are pre-offer marketing receipts. So Table 19 likely does *not* apply to the $5 inflows. However, if FarmThru *uses CSF proceeds* to reimburse a marketing agency or pay influencers, Table 19 *does* apply. Document the $5 VIP economics separately.

### 5b. Communication facility — Section 4.2 of the offer document (RG 261.182, Table 20)

> **Table 20 — CSF intermediary's communication facility** (RG 261.182, around line 1235): "A description of the effect of s738ZA(5), which requires the CSF intermediary hosting the CSF offer to provide a communication facility for the offer on its platform. … officers, employees or agents of your company, and related parties or associates of your company or the intermediary, must clearly disclose their relationship to your company and/or the intermediary when making posts on the facility; and that comments on the communication facility must be made in good faith, otherwise the advertising rules may be breached."

**Applies to VIP**: When the round is open at Birchal, founder posts on Birchal's communication facility must be in good faith and not misleading. Cross-promoting "VIP-only Q&A access" inside Birchal's communication facility is risky if it implies non-equal treatment of investors on the platform.

### 5c. Communications by the issuer during the offer (RG 261.102–RG 261.105)

> **RG 261.104** "Your company must ensure that all comments made by its officers and employees on the communication facility are made in good faith. Statements made in good faith on the communication facility for a CSF offer are permitted under the advertising rules. If comments are not made in good faith, then your company may breach the advertising rules."

> **RG 261.105** "You should ensure that all statements made by or on behalf of your company on the communication facility are not misleading or deceptive. This means that statements made by your company must be balanced (focusing on both benefits and risks of the CSF offer), accurately represent your company's business and not create misleading impressions."

**Applies to VIP**: Any "exclusive" founder content (Q&A recordings, behind-the-scenes updates) sent to VIPs while the offer is open at Birchal is itself an advertisement for the offer. It must be balanced, not create misleading impressions, and (if it directly or indirectly refers to the offer or is reasonably likely to induce) must carry the prescribed s738ZG(6) statement.

---

## 6. Anti-hawking — s736 (RG 261.114–RG 261.117)

> **RG 261.114** "CSF offers can only be made via a CSF intermediary's platform. This ensures that investors are not able to apply for shares without receiving the CSF offer document published on the intermediary's platform, which contains the minimum information required to be provided to investors."
> **Note:** See s738L(1). However, your company and the CSF intermediary may advertise the CSF offer and distribute or make available a copy of the CSF offer document (e.g. on the company's website, by email or on social media) provided that this complies with the rules about advertising a CSF offer.

> **RG 261.115** "Your company must not offer shares in the course of, or because of, an unsolicited meeting or telephone call. This includes inviting investors to apply for shares in your company. This is called the prohibition against securities hawking."
> **Note:** See s736. While Pt 6D.3 does not generally apply to offers made under the CSF regime, the securities hawking prohibition in s736 may apply when an offer is made in the course of an unsolicited meeting or telephone call and is not expressed to be made under the CSF regime (meaning it will not be a CSF offer). If a company offering shares expresses the offer to be a CSF offer and the offer is eligible to be made under the CSF regime, the prohibition on securities hawking will not technically apply.

> **RG 261.116** "If your company—or other persons, including officers and employees of your company and the CSF intermediary—makes an unsolicited approach to investors in connection with your company's offer:
> (a) it will contravene the rules for making offers under the CSF regime, because the offer will have been made on the platform other than that of a CSF intermediary; and
> (b) it may contravene the prohibition against securities hawking."

**Source**: RG 261.114–RG 261.116.

**Applies to VIP**: VIP-list SMS messages are *solicited* (the recipient paid $5 and signed up). Sending notifications to a paid, opted-in list is the textbook scenario of a *solicited* contact. Hawking risk is low *for the VIP list itself*. Hawking risk *increases* if FarmThru uses the VIP-list framing to justify cold-outreach (e.g., scraping LinkedIn, cold SMS to people who never opted in). The rule is solid: any contact with someone who did not opt in carries hawking risk.

**Framing verdicts**:
- A–F: hawking-axis verdict for any framing is **GREEN provided the buyer opted in**. AMBER if the channel is repurposed for cold outreach.

---

## 7. The advertising directive — s738ZG (consolidated)

s738ZG is the umbrella section. Key sub-provisions ASIC reads from the statute (per RG 261):

- **s738ZG(1)** — A person must not advertise the offer or publish a statement reasonably likely to induce investment, *without* the prescribed statement (RG 261.94, Note).
- **s738ZG(3)** — Three-factor inducement test for "indirect reference" / "reasonably likely to induce" (RG 261.95).
- **s738ZG(6)** — The prescribed statement requirement; strict liability, 30 penalty units (RG 261.92, Note 1).

The full operative test for whether something is an "advertisement" requiring the prescribed statement is RG 261.95:

> **RG 261.95** [quoted in Section 1 above] "(a) whether the statement is part of normal advertising directed at maintaining or attracting customers; (b) whether the statement contains information that deals with the affairs of the company; and (c) whether an investor would likely be encouraged to invest in shares on the basis of the statement rather than the CSF offer document."

**What an issuer cannot say (under s738ZG)**:

1. Cannot publish *any* statement that directly or indirectly refers to the offer, or is reasonably likely to induce investment, without the prescribed s738ZG(6) statement (RG 261.94).
2. Cannot make a misleading or deceptive statement (RG 261.96).
3. Cannot overstate benefits or fail to give equivalent prominence to risks (RG 261.99(a), (b)).
4. Cannot present views as those of unrelated parties when in fact those views are the company's (RG 261.99(c)).
5. Cannot publish forecasts/projections without a reasonable basis (general M&D principle; cf. RG 234).

**Applies to VIP**: All six framings must comply. Framing A directly fails 261.96/99 (false claim of priority allocation). Framings B, D, E need explicit copy clarifying that allocation is equal at Birchal. Framing C (Q&A) needs careful management of *what is said in the Q&A*, since the Q&A content will almost certainly satisfy 261.95(b)–(c). Framing F (donation) does not escape the inducement test if a buyer infers the $5 buys offer-related access.

---

## 8. Charging fees / accepting payments related to the offer

RG 261 contains **no general prohibition on the issuer charging fees for ancillary products or services**. The financial-assistance prohibition runs the other way (issuer cannot give money to retail investors to help them invest), and the application-money rules require investor *application money* to flow only via the intermediary:

> **RG 261.59** "The hosting arrangement … (a) must require all investor applications and all application money to be sent or paid to, and dealt with by, the CSF intermediary".

> **RG 261.88** "Your company, its related parties and the CSF intermediary hosting your company's CSF offer must not provide financial assistance, or arrange for financial assistance to be provided, to a retail investor in connection with your company's offer. For example, your company must not provide a loan (whether or not interest is charged to the borrower) to a retail investor so that the investor can purchase shares under your company's offer."

> **RG 261.89** [quoted in Section 1 above] — explicitly identifies "artificially inflate investor demand" and "inappropriately induce investors to participate" as the harms ASIC is concerned about.

> **RG 261.90** "This prohibition applies whether the financial assistance is provided before or after the investor acquires shares under the CSF offer."

**Source**: RG 261.59, RG 261.88–RG 261.90.

**Applies to VIP**: Three principles:

1. **The $5 is *not* application money.** It must not flow into the Birchal application facility. It is a separate commercial transaction for a separate product (notification/Q&A/etc). Keep the Stripe receipts and ledger entirely separate from any CSF flows. The $5 is not an investment in shares and must never be characterised as one.
2. **Financial assistance prohibition does not directly apply** because the investor is paying *out* (not receiving money to invest). However, the underlying ASIC concern in 261.89 — *artificially inflating demand* and *inappropriately inducing investors* — generalises. If the VIP product creates the appearance of overwhelming demand (e.g., "5,000 VIPs and counting!"), that may be testable as inappropriate inducement.
3. **No general prohibition on a separate ancillary product**, but the substance test in 261.95 applies. The $5 product cannot be a thin disguise for selling access to the offer.

**Framing verdicts**:
- A. Pay-for-priority-allocation → structurally invalid (no allocation control to sell). **RED**.
- B–E. Pay-for-comms-priority or pay-for-content → not prohibited by RG 261. **AMBER** subject to advertising-rule compliance.
- F. Donation framing → not prohibited; subject to advertising rules; AMBER subject to compliance.

---

## 9. Disclosure obligations re: any benefit being offered alongside the offer

The closest disclosure trigger is Table 19 (Section D, "Payments to related parties and other persons"), quoted above (Section 5a). It requires disclosure inside the offer document of CSF-funds-out-payments to: directors, related parties, controllers, the intermediary, and "any person promoting or marketing the offer" (including via interposed entities).

There is no explicit RG 261 obligation to disclose the existence of a paid pre-launch VIP product *to investors at Birchal*. However, three doctrines bite:

- **RG 261.96** (M&D) — if the existence of a paid VIP list materially affects the investor's understanding of the offer (e.g., creates an impression of demand that does not exist), failure to disclose may be misleading by omission.
- **RG 261.99(c)** — if VIP testimonials, founder Q&A snippets, or VIP-numbers are presented on Birchal as third-party endorsements when they are paid VIPs, that may be misleading per 261.99(c).
- **RG 261.134** — "you should consider if all material information about your company has been included in the CSF offer document, to minimise the risk of it being misleading or deceptive."

> **RG 261.134** "In particular, you should consider if all material information about your company has been included in the CSF offer document, to minimise the risk of it being misleading or deceptive."

**Source**: RG 261.99(c), RG 261.134, Table 19.

**Applies to VIP**: Two operational outputs:

1. If FarmThru does not use CSF proceeds to pay marketing/promoters who are tied to the VIP product, Table 19 disclosure of the VIP economics is not strictly required. But conservative practice is to disclose a one-line summary in Section 3 (Use of funds) or the use-of-funds narrative.
2. Any use of the VIP-list count, VIP testimonials, or paid-VIP "demand" signals in offer-document or Birchal-platform marketing must explicitly disclose that VIPs are paid subscribers (per 261.99(c)).

---

## Cross-cutting analysis

The question reduces to a single substance test from RG 261.95(c): **would an investor likely be encouraged to invest in shares on the basis of the VIP-product statement rather than the CSF offer document?**

- **Framing A** — yes, transparently. "First access to invest" is the entire pitch. **RED**.
- **Framings B, D, E** — yes, partially. The notification/queue product *exists* because the buyer wants to act on the offer. The buyer is paying *because* they intend to invest. So the VIP page is captured by s738ZG and must carry the prescribed statement and avoid misleading claims. With those mitigations, the framing is **AMBER but defensible**.
- **Framing C** — depends entirely on how the Q&A is positioned. If the Q&A is sold as a "founder content" product (educational/relationship-building, not investment-encouraging), the inducement test weakens. If the Q&A *content* is investment-encouraging, the page and the recording become advertisements for the offer (with all that entails). **AMBER**, leaning to GREEN with disciplined positioning.
- **Framing F** — donation framing. Reduces but does not eliminate 261.95 capture. The substance test is what the buyer reasonably understands, not what the merchant calls it. **AMBER**.

**The core principles a defensible VIP product must respect**:

1. The CSF offer terms (price, allocation, class of share, application window, money-handling) are equal for all investors. The VIP product cannot — and must not appear to — alter any of these.
2. The VIP product is a separate commercial transaction, with its own Stripe ledger, clearly described deliverable (notification, Q&A access, etc.), and not characterised as "buying" access to the offer.
3. Every page, email, SMS, social post and Q&A recording that "directly or indirectly refers to" the intended offer or is "reasonably likely to induce" investment must carry the prescribed s738ZG(6) statement.
4. No statement may overstate benefits, under-disclose risks, present company views as third-party views, or claim allocation/timing benefits that are structurally untrue.
5. VIP-list metrics may not be used to artificially inflate apparent demand for the offer (RG 261.89's underlying concern, generalised).

---

## Open questions for further research (RG 262 agent will cover intermediary side)

1. Does Birchal's hosting agreement or platform T&Cs restrict issuer pre-launch paid products? (RG 262 question.)
2. Does Birchal have any "fair access" platform rule that prohibits the issuer from operating a parallel paid access list? (RG 262 / Birchal-specific.)
3. ASIC INFO / staff guidance: are there published examples of CSF issuers running paid pre-launch products? Is there enforcement history? (Not in RG 261; check ASIC INFO sheets and media releases.)
4. Does the prescribed s738ZG(6) statement have an exact prescribed form, or is the substance sufficient? (RG 261 says "investors should consider the offer document and the general risk warning"; check whether reg 6D.3A.10 or s738ZG(6) prescribes exact wording.)
5. For consumer protection (separate from RG 261): does the $5 charge attract Australian Consumer Law refund obligations if FarmThru cannot deliver what was promised (e.g., Birchal closes the round early, no Q&A held)?
6. GST / tax treatment of the $5 — adjacent to compliance but separate question.

---

## Explicit phrasings the issuer CAN use

(All conditional on the page also carrying the prescribed s738ZG(6) statement and not overstating benefits / under-disclosing risks.)

- "Get an SMS notification the moment our Birchal round opens — so you can review the offer document and decide whether to apply on the same terms as everyone else."
- "Be on our priority comms list. We'll message early notification subscribers first when the round opens. Allocation at Birchal is on equal terms — your application is processed by Birchal alongside every other investor's."
- "Join the founder Q&A — a recorded conversation with [founder] about FarmThru's business. (This Q&A is informational only. Investors should consider the CSF offer document and general risk warning before applying.)"
- "Support our pre-launch marketing. As a thank-you, we'll send you a launch SMS the day the round opens at Birchal. The offer terms — price, share class, application process — are the same for every investor under Australian CSF law."

## Explicit phrasings the issuer CANNOT use

- "Get first access to invest." (Falsely implies preferential allocation. RG 261.96/99/322(c).)
- "Pay $5 to invest before the public round." (Same; structurally false. Application access is via Birchal only; RG 261.59.)
- "Skip the queue at Birchal." (False — there is no queue at Birchal in that sense; allocation is structural via the application facility.)
- "VIPs get priority allocation." (False, and a misleading/deceptive statement under s1041H and RG 261.96.)
- "Lock in your shares." (Implies pre-allocation. False per RG 261.85.)
- "Be one of the first investors." (Captures the investor on a misleading basis, since the offer treats all applications received during the offer period equally; the only true "first" is Birchal application timestamp, which is not for sale.)
- "Reserved for VIPs only." (If used for any offer-related allocation framing.)
- "Limited spots available — VIPs go first." (Conflates offer-allocation scarcity with comms priority; misleading.)
- Any of the above phrasings *without* the prescribed s738ZG(6) statement on the same page (strict-liability offence per RG 261.92 Note 1).
- Any quote attributed to an investor or third party that is in fact the founder's view (RG 261.99(c)).
- Any forecast of future returns, valuation upside, or "guaranteed" outcomes (general M&D / RG 234).
