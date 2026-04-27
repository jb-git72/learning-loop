# RG 262 — VIP fee architecture research (intermediary perspective)

**Subject:** Can FarmThru charge $5 at its own marketing site for "VIP early access" benefits ahead of a Birchal-hosted CSF round, without creating problems for Birchal as the AFS-licensed CSF intermediary?

**Source:** ASIC Regulatory Guide 262 — Crowd-sourced funding: Guide for intermediaries (Oct 2018, updated Apr 2026). RG 262 governs the **intermediary** (Birchal). RG 261 covers the issuer (FarmThru) and is being researched in parallel.

**Bottom-line view:** RG 262 contains no concept of paid pre-launch tiers, equal-access of the application facility is implicit (one application facility per offer, available only while open, governed by gatekeeper checks), and any conduct that lets the issuer manufacture the appearance of "first access" or special allocation creates direct, named risks under RG 262.144 (gatekeeper duty to refuse to publish), RG 262.36–.38 (intermediary's own conflicts), RG 262.119(c) (misleading levels of investment) and RG 262.196 (intermediary may be on the hook for issuer pre-offer dishonesty).

---

## 1. Gatekeeper duties (Section C — RG 262.127–.145)

### 1a. Existence and shape of the gatekeeper role

> **RG 262.127** As a CSF intermediary, you have certain specific obligations that apply in recognition of your important role as a 'gatekeeper' for your platform, which include:
> (a) performing certain checks before publishing a CSF offer document on your platform; and
> (b) not publishing, or not continuing to publish, a CSF offer document on your platform in certain circumstances.

**Source:** RG 262.127

**Applies to VIP:** Yes — directly. The intermediary (Birchal) is required to gatekeep the offer. Anything FarmThru does pre-launch that the intermediary later "would have had reason to believe" was misleading or dishonest can trigger a refusal to publish, suspension or close (see RG 262.144 below). The intermediary cannot disown FarmThru's pre-offer marketing once it becomes aware of it.

### 1b. Pre-offer dishonesty is explicitly named as a gatekeeper trigger

> **RG 262.144** ... You have reason to believe the offering company or its directors or other officers have, in relation to the CSF offer, knowingly engaged in conduct that is misleading or deceptive or likely to mislead or deceive | Conduct that is misleading or deceptive, or likely to mislead or deceive, may occur at various stages of the CSF offer—for example: pre-offer—where you have reason to believe that the directors' representations about an offer are dishonest; and during an offer—where you have reason to believe that the directors have knowingly provided misleading information in response to a post on the communication facility.

**Source:** RG 262.144 (Table 3, third row), and the underlying section is s738Q(5)(c).

**Applies to VIP:** This is the load-bearing quote. ASIC explicitly contemplates "**pre-offer**" dishonesty by the issuer as a circumstance that triggers the intermediary's duty NOT to publish. A paid product implying paid investors get a different outcome at the platform when they actually don't (i.e., framing A — "first access to invest") is exactly the kind of dishonest pre-offer representation that ASIC names. Birchal would have a positive duty to refuse to publish the offer if it became aware of this representation and concluded it was knowingly misleading.

### 1c. Strict liability for failure to gatekeep

> **RG 262.142** The consequences of failing to conduct one of the gatekeeper checks, or failing to conduct a check to a reasonable standard, are serious. It is a strict liability offence to not comply with this requirement and if you do not comply you are taken to have knowledge of anything you would have had knowledge of had you conducted the check to a reasonable standard. ...
>
> **RG 262.143** For example, you commit an offence if you continue to publish a CSF offer document where the offering company is not eligible to make a CSF offer, and you would have had reason to believe the company was not eligible had you carried out the relevant gatekeeper check, or carried the check out to a reasonable standard.

**Source:** RG 262.142–.143

**Applies to VIP:** Birchal is taken to have knowledge of anything a reasonable check would have surfaced. If Birchal asks "show me your marketing" during onboarding (which is normal), and FarmThru's pre-launch site mentions a paid VIP product, the intermediary now has actual or constructive knowledge. Failing to act once that knowledge exists is a strict-liability offence on the intermediary.

### 1d. Ongoing checks and the standing duty

> **RG 262.130** The prescribed checks under the CSF regime are a minimum requirement and are not intended to limit the checks conducted, or information that you may wish to seek from an offering company or its officers. If you lead potential clients to believe that you will undertake certain checks or achieve a certain level of quality in CSF offers, it is important that you take the necessary reasonable steps to ensure these expectations are met.

**Source:** RG 262.130

**Applies to VIP:** Birchal's marketing publicly says they vet issuers. They will notice and form a view on FarmThru's pre-launch tactics. They are expected to do more than the bare minimum.

**Framing verdicts (Section 1 / gatekeeper duties):**
- A. "Pay $5 for first access to invest" → **RED.** Pre-offer misrepresentation that everyone's investment access is equal at the platform. Triggers RG 262.144 and a duty to refuse / suspend / close.
- B. "Pay $5 for SMS notification when round opens" → **AMBER.** Notification is not allocation, but the wording "when the round opens" is indistinguishable from "first access" in the public's mind unless heavily qualified. Birchal will want to see the exact copy.
- C. "Pay $5 for exclusive founder Q&A access" → **GREEN/AMBER.** Q&A is a deliverable that doesn't touch the application facility. Risk is only that the Q&A itself contains forward-looking statements / financial product advice that breaches s738ZG (advertising) — see Section 7.
- D. "Pay $5 to be first messaged when the round opens" → **AMBER.** Same as B — the operational outcome (priority comms only, not allocation) is benign, but the wording is easily misread. Must be paired with explicit equal-access disclosure.
- E. "Pay $5 for queue position on our public comms list" → **AMBER.** Cleaner because "comms list" is unambiguously not allocation, but still requires explicit "all investors at the platform are processed equally" disclosure.
- F. "Pay $5 to support FarmThru's marketing — donation framing — VIPs get a thank-you SMS" → **AMBER.** This re-characterises the payment as a gift, removing the implication of investor priority. Lower risk, but the SMS still has to be a benign acknowledgement, not a "you're first" claim.

---

## 2. Application facility — equal access is structural

> **RG 262.151** As a CSF intermediary, you must provide an application facility on your platform to enable people to make applications in response to CSF offers. **All applications must be made through this facility** and you must as soon as practicable reject, and refund any money paid for, any applications made other than through the application facility. Restricting the making of applications to the application facility ensures that applicants are made aware of, and receive, the investor protections under the CSF regime.
>
> **RG 262.152** The application facility must only be available **while the relevant CSF offer is open**—applicants must not be able to make applications while an offer is closed or suspended.

**Source:** RG 262.151–.152

**Applies to VIP:** This is the second load-bearing quote. There is exactly **one** application facility, and it only exists while the offer is open. RG 262 describes no mechanism for early access, allocation tiers, queues, or pre-acceptance of investments. A VIP product cannot be a path around the application facility (any money taken outside it must be refunded).

**Important corollary:** the regime does not contemplate any priority allocation feature at all. Even if the issuer wanted Birchal to gatekeep the VIP scheme (e.g., "use Birchal's API to send the SMS first"), Birchal could not legally let that VIP investor jump the application queue, accept their $X investment before the offer opens, or process their application differently. The $5 product can only buy comms — it cannot buy a different outcome at the platform.

### 2a. Application processing — first-come-first-served / cap / pro-rata?

RG 262 does NOT prescribe the order in which applications inside the open application facility are processed. It does require the offer to close at the earliest of (a) three months after the offer is made, (b) any date specified in the CSF offer document, **(c) when you consider the offer to be fully subscribed**, (d) when the company withdraws, or (e) when the gatekeeper duties require it (RG 262.169). In practice this is first-come-first-served until oversubscription, then the issuer/intermediary decide allocation per the CSF offer document. Crucially:

- The order rules live in the CSF offer document (issuer-controlled, but gatekept by intermediary).
- The retail $10,000-per-issuer-per-12-months cap (RG 262.188) applies regardless of any "VIP" status.
- There is no carve-out for "paid early access" investors.

**Framing verdicts (Section 2 / equal application access):**
- A. **RED** — directly contradicts "all applications must be made through this facility" + "only available while the relevant CSF offer is open."
- B. **GREEN-AMBER** — notification is outside the facility entirely.
- C. **GREEN** — Q&A is outside the facility.
- D. **GREEN-AMBER** — comms only.
- E. **GREEN** — comms only.
- F. **GREEN** — donation, no investment outcome implied.

---

## 3. Equal-treatment / fair-honest-efficient obligations

RG 262 does not use the words "equal" or "all investors must be treated the same" as a standalone obligation. Instead, equal treatment is achieved structurally by (a) one application facility (RG 262.151), (b) one investor cap of $10k per retail client per issuer per 12 months (RG 262.188), and (c) AFS licensee duties of efficiency, honesty and fairness:

> **RG 262.30** When deciding whether to grant an AFS licence authorisation to provide a crowd-funding service, we will assess your capacity and expertise to act as a CSF intermediary in accordance with your obligations as an AFS licensee. For example, we will consider whether you are likely to do all things necessary to carry on the business **efficiently, honestly and fairly**.

> **RG 262.185** As an AFS licensee, you must do all things necessary to ensure that you provide the [cooling-off] method, as part of your financial service, in a manner that is **honest, efficient and fair**. ...

**Source:** RG 262.30, RG 262.185 (the s912A(1)(a) standard, applied to specific functions)

**Applies to VIP:** A VIP scheme that makes the intermediary's processing look unfair (e.g., where some investors think they have priority and others don't) puts Birchal's standing under s912A(1)(a) at risk — it is the central condition of every AFS licence. This is also why intermediaries are typically risk-averse about issuer marketing they didn't approve.

### 3a. The communication facility must be open to all who can access the offer document

> **RG 262.156** The communication facility does not need to be open to the general public, but must be accessible to persons that are able to access the CSF offer document. If a person is able to access a CSF offer document once they have registered on your platform, they must be able to make and see posts on the communication facility for the offer on registration.

**Source:** RG 262.156

**Applies to VIP:** Once the offer is open, the platform-hosted Q&A is open to everyone who can see the offer document. So a paid "exclusive founder Q&A" is conceptually fine **only if it happens outside the platform and only as a perk** — not as a substitute for or alternative to the platform-hosted Q&A. If the VIP Q&A becomes the better information channel during the live offer, that creates an information asymmetry that arguably undermines the platform Q&A's purpose.

**Framing verdicts (Section 3 / equal treatment):**
- A. **RED** — explicit unfairness.
- B. **AMBER** — only fair if everyone can see/use the same application facility.
- C. **AMBER** — fine as a perk, risky if it becomes the primary info channel during the live offer.
- D, E. **AMBER** — same as B.
- F. **GREEN** — donation framing avoids unfairness implication.

---

## 4. Anti-hawking duties (s736 / unsolicited offers)

**RG 262 does NOT contain the word "hawking" or any direct reference to s736.** The hawking prohibition (Corporations Act s992A, formerly s736 etc., as updated by the 2022 hawking reforms) sits primarily on the issuer side and is the subject of RG 38 — the parallel agent's RG 261 research will cover it. RG 262 reaches the same territory only obliquely, via:

- The intermediary's general duty under s912A(1)(a) to act efficiently, honestly and fairly (RG 262.30).
- The advertising restrictions under s738ZG (RG 262.113–.117 — see Section 7 below) that apply to anyone who advertises a CSF offer or intended offer.
- The gatekeeper duty to refuse to publish if directors have engaged in pre-offer dishonest conduct (RG 262.144).

**Applies to VIP:** Sending the Birchal investment URL by SMS to a paid pre-purchased list IS plausibly an "unsolicited offer" of a financial product under s992A — the consumer paid $5 to receive marketing for the offer, but they did not initiate the conversation about *the share offer itself*. The exemptions in s992A(3)–(4) (e.g., issuer offers, existing relationship) need to be analysed against RG 38; that analysis sits in the parallel RG 261 work. **From the intermediary's angle**, Birchal will not want its name attached to a campaign that could later be characterised as hawking — this is exactly the kind of pre-offer issuer conduct ASIC has cited in surveillance actions.

**Framing verdicts (Section 4 / anti-hawking):**
- A. **RED** — paid-then-pushed offer is the textbook hawking scenario.
- B. **AMBER** — notification is technically requested by the consumer (they paid for it), but it advertises the live offer; safe-harbour likely depends on the s992A wording.
- C. **GREEN** — Q&A is not an offer.
- D. **AMBER** — same as B.
- E. **AMBER** — same as B/D.
- F. **GREEN-AMBER** — donation + thank-you SMS is the cleanest formulation, but the SMS itself must not include the offer link or solicit investment.

---

## 5. Communication facility — does the platform-hosted Q&A exclude issuer-run pre-launch comms?

> **RG 262.153** As a CSF intermediary, you must provide a communication facility for each CSF offer **while the offer is open or suspended**.
>
> **RG 262.154** The purpose of the communication facility is to allow potential investors, the company making the CSF offer and you to communicate with each other about the offer. The facility must enable a person who accesses the CSF offer document to: (a) make posts about the offer; (b) see posts about the offer; and (c) ask the company making the offer, or the CSF intermediary, questions about the offer.
>
> **RG 262.157** Persons who are officers, employees or agents of the company making a CSF offer (or a related party or associate) or of the CSF intermediary (or an associate), must clearly disclose that fact when posting on the communication facility.

**Source:** RG 262.153–.157

**Applies to VIP:** The mandatory communication facility only exists **while the offer is open or suspended**. RG 262 is silent on issuer-run pre-launch Q&A activity — it does not forbid it, nor does it endorse it. The risks are downstream:

1. If pre-launch Q&A statements become inconsistent with the CSF offer document later filed at Birchal, the document may be defective (RG 262.171) — Birchal must remove and close.
2. Pre-launch Q&A statements that are dishonest trigger RG 262.144 (the pre-offer dishonesty gatekeeper trigger).
3. Once the offer is open, the company can't prefer the paid VIP channel over the platform Q&A — s912A(1)(a) and the communication facility's "frank discussion in good faith" purpose (RG 262.160) make that uncomfortable.

> **RG 262.160** ... keep in mind the purpose of the communication facility to inform investment decisions through frank discussion in good faith.

**Source:** RG 262.160

**Applies to VIP:** Pre-launch Q&A is a perk that doesn't violate this provision if it ends when the offer goes live, or runs in parallel without making the platform Q&A a second-class channel. But the moment the live offer opens, the platform Q&A must be the canonical record.

**Framing verdicts (Section 5 / comms facility):**
- A. **RED**
- B. **GREEN** for the comms layer (notification is not a Q&A)
- C. **AMBER** — fine pre-launch; risky during the live offer if it competes with platform Q&A
- D, E. **GREEN**
- F. **GREEN**

---

## 6. Conflicts of interest — for the intermediary, not the issuer

> **RG 262.36** A key conflict of interest that you are likely to face, and which is specific to CSF intermediaries, is the conflict between your various obligations under the CSF regime and the financial benefits you derive from publishing CSF offers and ensuring the success of those offers. The risk posed by this conflict is heightened by the extent to which your remuneration depends on the success of an offer.
>
> **RG 262.37** Your arrangements to manage conflicts of interest may include, but are not limited to: ... (c) performing checks to the required standard, which may result in you declining to publish certain offers and in turn negatively impact your ability to generate revenue; and (d) reviewing the CSF offer document, which may result in you declining to publish certain offers and in turn negatively impact your revenue.

**Source:** RG 262.36–.37

**Applies to VIP:** Birchal is paid based on the success of FarmThru's offer. ASIC explicitly cites this as a conflict the intermediary must manage. A high-momentum pre-launch list (e.g., "1,500 paid VIPs ready to invest in the first hour") makes the offer more attractive to Birchal AND makes Birchal less inclined to gatekeep aggressively. ASIC will look harder at this exact pattern. From Birchal's perspective, being asked to "approve" a VIP-funnel scheme creates a conflict-management headache — they will likely push back if the framing risks ASIC scrutiny.

> **RG 262.119** It may be misleading to: ... (c) quote levels of investment that include investments by you (as the CSF intermediary) or your associates, or associates of the company making the CSF offer, or amounts that are subject to cooling-off withdrawal rights if the reader may be given the impression that the level of investment shows the confirmed level of interest of unassociated public investors.

**Source:** RG 262.119(c)

**Applies to VIP:** A "VIP list of 1,500 ready to invest" claim, used in launch marketing, is exactly the kind of inflated demand-signal RG 262.119(c) warns against. It implies confirmed investor interest that hasn't actually been confirmed (paying $5 isn't paying for shares).

**Framing verdicts (Section 6 / conflicts):**
- A. **RED** — increases Birchal's conflict, increases ASIC attention.
- B. **AMBER** — a notification list is comparable to any other email/SMS list; the risk is in how its size is described in launch advertising.
- C. **GREEN**
- D, E. **AMBER** — same as B.
- F. **GREEN**

---

## 7. Advertising and "no advertising of CSF offers" (s738ZG)

> **RG 262.113** Generally, under s738ZG, you must not:
> (a) advertise a CSF offer or intended offer; or
> (b) publish a statement that:
>   (i) directly or indirectly refers to a CSF offer or intended offer; or
>   (ii) is reasonably likely to induce people to apply for securities under a CSF offer or intended offer.
>
> **RG 262.114** This restriction does not apply where the advertisement or publication states that a person should, in deciding whether to make an application under the CSF offer, consider the CSF offer document and the general risk warning (whether or not the advertisement or publication also contains other material).
>
> **RG 262.115** This requirement applies to CSF intermediaries as well as companies making CSF offers and other persons.

**Source:** RG 262.113–.115

**Applies to VIP:** This is the third load-bearing quote. **Any** statement that directly or indirectly refers to a CSF offer or intended offer — including a paid-product landing page that says "pay $5 to get early access to our investment round" — IS advertising under s738ZG and applies to "CSF intermediaries as well as companies making CSF offers **and other persons**." There is one safe harbour: include the standard "consider the CSF offer document and the general risk warning" disclaimer. This applies whether the offer is "intended" (i.e., before it goes live at Birchal) or live.

> **RG 262.119** It may be misleading to: (a) state success stories of companies raising funds without acknowledging that some or all of the companies have not yet provided any returns to investors under the CSF offers, if that is the case ...; (b) present views about a CSF offer as those of investors or others, if that is not the case; or (c) [as quoted above].

**Source:** RG 262.119

**Applies to VIP:** Pre-launch marketing must follow the same balanced-message rule. "X investors already in" framing is a misleading-conduct trap.

> **RG 262.117** The CSF regime requires advertisements that refer to a CSF offer, including posts on social media that directly or indirectly refer to an offer, to include a statement that investors should consider the offer document and the general risk warning when deciding whether to apply under the offer.

**Source:** RG 262.117

**Applies to VIP:** The VIP landing page, the VIP confirmation email and any VIP SMS that mentions the round (even by implication: "the round is now live") must include the standard CSF-offer-document-and-risk-warning statement.

**Framing verdicts (Section 7 / advertising):**
- A. **RED** — refers to the offer ("first access to invest") AND likely to induce people to apply, without the safe-harbour disclaimer in the marketing micro-funnel that introduces the VIP product.
- B. **AMBER** — refers to the offer ("when the round opens") so s738ZG applies; survivable with the disclaimer.
- C. **GREEN** if Q&A copy stays generic about the company and avoids referencing the CSF offer specifically; **AMBER** if Q&A page mentions the round.
- D, E. **AMBER** — same as B.
- F. **AMBER** — donation framing reduces inducement risk; still, any reference to "the round" or "CSF offer" pulls in s738ZG.

---

## 8. Order of application processing (RG 262.169)

> **RG 262.169** You must close a CSF offer at the earliest of the following times:
> (a) three months after the offer is made;
> (b) any date specified in the CSF offer document that the offer will close;
> (c) when you consider the offer to be fully subscribed;
> (d) when the company making the offer withdraws the offer;
> (e) when the gatekeeper obligations require you to remove the CSF offer document from your platform (see RG 262.127–RG 262.145).

**Source:** RG 262.169

**Applies to VIP:** Confirms the structural reality: orders are processed inside the application facility until oversubscribed; allocation rules (if any) live in the CSF offer document. There is **no provision** for paid pre-launch tiers, paid priority allocation, or a separate VIP application channel. RG 262 is silent on first-come-first-served vs pro-rata at the moment of oversubscription — this is left to the offer document. Birchal's standard hosting agreement will dictate this.

**Framing verdicts (Section 8 / order of processing):**
- A. **RED** — implies a different order to "VIPs", which is impossible under the regime.
- B–F. **GREEN** for processing order — none of these touch allocation.

---

## 9. s738Q gatekeeper checks — what triggers them

> **RG 262.144** You must not publish or continue to publish a CSF offer document in four specific circumstances ...
> Source: Section 738Q(5) of the Corporations Act.

**Source:** RG 262.144 (and the underlying s738Q)

The four circumstances:
1. Identity not verified.
2. Reason to believe directors are not of good fame or character.
3. Reason to believe issuer/directors knowingly engaged in pre-offer or in-offer misleading or deceptive conduct.
4. Reason to believe the offer is not an eligible CSF offer.

**Applies to VIP:** Categories 2 and 3 are both live for the VIP question. If the VIP marketing is dishonest about what investors will get, that is "in relation to the CSF offer ... knowingly engaged in conduct that is misleading or deceptive" — circumstance 3. If ASIC or Birchal considers paid-priority-investor schemes to reflect on character, that's circumstance 2 (see Section 11 below).

**Framing verdicts (Section 9 / s738Q triggers):**
- A. **RED** — likely triggers circumstance 3.
- B–E. **AMBER** — risk lies in copy, not the underlying mechanism.
- F. **GREEN-AMBER** — donation framing is safer but still depends on copy.

---

## 10. Intermediary liability for issuer marketing

> **RG 262.111** Advertising by a CSF intermediary may take many forms ... All advertising that you cause or authorise to be communicated must comply with certain requirements, **whether or not it is attributed to you**.
>
> **RG 262.115** This requirement applies to CSF intermediaries as well as companies making CSF offers **and other persons**. A number of exceptions apply.

**Source:** RG 262.111, 262.115

**Applies to VIP:** Two separate liability paths.
- **Direct s738ZG liability** for any advertising the intermediary "causes or authorises" — Birchal is on the hook for content it formally signs off, and arguably for content it knows about and tolerates (though the "causes or authorises" language is the key phrase).
- **Indirect / gatekeeper liability** under s738Q(5)(c) for issuer pre-offer dishonesty (RG 262.144 above) — the intermediary doesn't have to "cause or authorise" the conduct; it just has to have reason to believe it occurred.

> **RG 262.191** As a CSF intermediary, you will commit an offence if you:
> (a) fail to comply with your gatekeeper obligations;
> (b) do not have in place 'adequate arrangements' to ensure you comply with the gatekeeper obligations;
> ...
> (c) publish a CSF offer document or information about a CSF offer that includes a statement or information that is materially misleading and is likely to induce an investor to apply under the offer and you know, or ought reasonably to have known, that the statement or information is materially misleading (see s1041E).

**Source:** RG 262.191

**Applies to VIP:** "Information about a CSF offer" includes the issuer-controlled Birchal page, pre-launch teasers Birchal hosts or links to, and arguably the VIP product page if Birchal is taken to be aware of and authorising it (e.g., sharing investor lists). **Birchal must be told about the VIP scheme before the offer is published.** Hiding it from Birchal is a separate compliance failure for FarmThru and would not protect Birchal once they have constructive knowledge.

> **RG 262.196** This information will help ASIC better understand your business and how it compares to other CSF intermediary businesses ... [data reporting includes]: (c)(i)(B) a brief description of how your gatekeeper obligations brought about that result and/or how the CSF offer document was defective ... (f)(iv) when you had to remove material from the communication facility, for each CSF offer ...

**Source:** RG 262.195–.196

**Applies to VIP:** Anything Birchal does in response to a VIP scheme — refusing the issuer, requiring copy changes, suspending the offer, removing communication facility posts — gets reported to ASIC annually. This means Birchal's incentive is to refuse anything ambiguous rather than risk having to explain it to ASIC later.

**Framing verdicts (Section 10 / intermediary liability):**
- A. **RED** — Birchal will not approve.
- B–E. **AMBER** — Birchal needs to see the copy and approve.
- F. **GREEN-AMBER** — Birchal still needs to see it.

---

## 11. Good fame and character — directors and responsible managers

> **RG 262.144** ... You have reason to believe that any of the directors or other officers are not of good fame or character | The law does not define 'good fame or character' for this purpose, but factors that may give you reason to believe that a person is not of good fame or character include: criminal or civil penalty proceedings or disciplinary action where they were found to have engaged in dishonest or fraudulent activity; insolvency history, depending on the circumstances; bans from managing corporations; bans from providing financial services; and **failure to be frank and honest in dealing with and providing information to the intermediary**.

**Source:** RG 262.144 (Table 3, second row)

**Applies to VIP:** ASIC's named factors centre on dishonesty and concealment in dealings *with the intermediary*. **Failing to disclose a paid-VIP marketing scheme to Birchal during onboarding is itself a "good fame or character" red flag**, even if the underlying scheme wouldn't have been refused. This is the surprise teeth in the regime: the founder's behaviour with Birchal — not just the underlying conduct — matters.

> **RG 262.66** When nominating your responsible managers, you also need to ensure they are of 'good fame and character', as we consider this when we assess an application for an AFS licence.

**Source:** RG 262.66

**Applies to VIP:** Birchal's own directors / responsible managers face this test for their licence. Allowing a borderline-misleading issuer-run VIP scheme could be cited against the intermediary's RM at licence-renewal/surveillance time.

**Framing verdicts (Section 11 / good fame and character):**
- A. **RED** — non-disclosure to Birchal compounds the issue.
- B–F. **GREEN if disclosed; AMBER if hidden.** Always tell Birchal first.

---

## Intermediary liability for issuer marketing (cross-reference summary)

The intermediary, Birchal, is on the hook through three independent doors:
1. **Strict-liability gatekeeper failure** (RG 262.142) — Birchal is taken to know what a reasonable check would have surfaced.
2. **Direct advertising liability** under s738ZG (RG 262.115) — applies to "CSF intermediaries ... and other persons."
3. **Indirect gatekeeper trigger** under s738Q(5)(c) (RG 262.144) — pre-offer dishonest conduct by the issuer requires the intermediary to refuse / suspend / close.

A pre-paid VIP funnel that drives traffic to the Birchal investment URL implicates all three.

## Pre-offer issuer communication constraints (intermediary perspective)

RG 262 does not prohibit issuer pre-launch comms, but it constrains them by:
- s738ZG advertising rules apply to "intended" offers (RG 262.113 — the safe-harbour disclaimer is required even before the offer is live).
- "Conduct that is misleading or deceptive" includes "pre-offer" representations (RG 262.144 Table 3 row 3).
- Once Birchal has reason to believe pre-offer conduct was dishonest, it must refuse / suspend / close.
- Inflated demand signals from a VIP list are a named misleading-conduct example (RG 262.119(c)).
- "Frank discussion in good faith" purpose of the platform Q&A (RG 262.160) means an "exclusive" off-platform Q&A can't replace it during the live offer.

## Cross-cutting analysis — what's the real risk for FarmThru's $5 product?

1. **Frame matters more than mechanism.** The $5 VIP product itself isn't prohibited — what is prohibited is a frame that (a) implies a different investment outcome, (b) misstates demand, (c) advertises the round without the safe-harbour disclaimer, or (d) tries to push the Birchal URL on a list that didn't ask for *that*.

2. **Notification + Q&A + thank-you = legitimate.** Allocation, "first access to invest", or "queue for the round" framing = not legitimate.

3. **Birchal must be told.** Treating Birchal as a partner is non-negotiable. Failing to disclose hits the "good fame and character" door (RG 262.144 row 2).

4. **The $5 amount is irrelevant** to the regulatory analysis. Whether it's $0, $5, or $50 doesn't change the framing risk.

5. **The donation/marketing-support framing (F) is the safest re-characterisation** because it defangs the "you bought priority access" misread. But the SMS deliverable still has to be a benign acknowledgement, not the offer URL.

6. **Birchal will likely require copy approval** for the VIP landing page, the email confirmation and the SMS, given they have reason to believe they will be associated with the funnel. Build that into the VIP product roadmap.

## Open questions

1. **Does Birchal have a published VIP/pre-launch policy?** Some intermediaries explicitly forbid issuer-run paid products; others tolerate them with sign-off. Ask Birchal directly. (Out of scope for RG 262.)

2. **s992A hawking analysis.** The detailed hawking carve-outs sit in the parallel RG 261 / RG 38 research — that work needs to confirm whether a pre-paid SMS list is "unsolicited" given the consumer's $5 act.

3. **What does Birchal's hosting agreement say about issuer marketing?** Standard CSF hosting agreements reserve the intermediary's right to require copy changes. The VIP product needs to be allowed under that agreement.

4. **What does Birchal's CSF offer document template say about allocation / oversubscription?** If FarmThru's offer document doesn't carve out anything for "VIPs" (and it can't, lawfully), the risk of misalignment between the VIP marketing promise and the offer document reality is acute.

## Explicit phrasings the issuer CAN use (under RG 262)

- "Be the first to know when our CSF round opens at Birchal." *(B / D — notification framing)*
- "Get the SMS the moment the round goes live." *(B — same)*
- "Pre-register for an exclusive founder Q&A before the round opens. Investing is at Birchal — every investor is processed equally when the round opens publicly." *(C, with explicit equal-access disclosure)*
- "Pay $5 to support our launch marketing. As a thank you, we'll text you when the round goes live and invite you to a founder Q&A." *(F — cleanest framing)*
- Add the s738ZG safe-harbour line wherever the round is referenced: *"In deciding whether to apply for shares in the CSF offer, you should consider the CSF offer document and the general risk warning at [Birchal URL]."* (per RG 262.114, RG 262.117).
- Disclose anywhere the VIP list is described publicly: *"VIPs receive earlier marketing communications; investing happens at Birchal where every investor is processed equally."*

## Explicit phrasings the issuer CANNOT use (under RG 262)

- "Pay $5 for first access to invest." *(A — RG 262.144 + RG 262.151 + s738ZG)*
- "VIPs invest before the public." *(A)*
- "Beat the queue / jump the queue / priority allocation." *(A, RG 262.151–.152)*
- "Reserve your spot in the round for $5." *(A — implies share allocation)*
- "Lock in your investment early." *(A — implies pre-acceptance of money)*
- "1,500 VIPs are ready to invest" *(RG 262.119(c) — misleading demand signal)*
- "Birchal has approved our VIPs to invest first." *(False, plus dragging the intermediary into the misrepresentation)*
- Any campaign asset that mentions "the round" or "investment" without the s738ZG safe-harbour disclaimer.
- Any VIP SMS that operationally pushes the Birchal investment URL without the consumer first being clearly told this is a financial-product offer (the s992A hawking issue — confirm with RG 261 work).
