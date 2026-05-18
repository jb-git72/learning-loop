# Birchal Meta-Ad Learnings

Captured from JB review of V1 (2026-05-07). Apply to every subsequent draft before the row-by-row review.

## What works (carry-over from FMTH evidence)

- Curiosity-gap narrow-bound hook beats founder-voice opener (+0.18 composite, FMTH PR #125 H3).
- Ownership framing in para 2 is load-bearing: removing "own a piece of" dropped composite -0.19 (FMTH PR #125 H2).
- Cadence-of-three proof in para 2: e.g. "324 companies. $234M+. 137,000 of you."
- Soft scarcity only ("opens soon", "the moment it goes live"). Hard scarcity ("act now", "last chance") is ACL-risky pre-offer.
- Outcome-stated CTA: "Save my spot. We will tell you the moment the offer goes live."

## Birchal-specific patterns

### 1. Subject discipline: "Birchal" must mean ONE thing per ad.

The product is structurally confusing. **Birchal is a CSF platform (the venue 324 companies have raised on), AND Birchal is a company doing its own CSF raise.** V1 conflated the two and the reader had to do work.

**Rule.** Adopt first-person Birchal voice (`we` / `our` / `us`) throughout the body. "Birchal" appears at most once or twice as a brand identifier; everywhere else use first person. The platform becomes "our platform" or "the platform we built". The company becomes the implicit `we`.

**Why:** the only "Birchal" in `we` is the corporate entity. The platform-vs-company swap that confused V1 disappears because there's no second referent to swap to.

**How to apply:**
- Bad (V1 A2): "324 companies have raised on Birchal since 2018. ... Birchal is now doing the same for itself."
  Reader has to parse: which Birchal? Same as before? Different? "Itself" referent?
- Good (V2 A2): "Since 2018, Birchal has helped 324 Australian companies raise over $234M. ... Now we're opening our own raise."
  One brand identifier ("Birchal" once, as the helper). Then `we`/`our` = same Birchal, opening its raise. No swap.

**Recursion punch.** When the recursion is the angle ("the platform you've used is now opening up"), make the two referents explicit, not implied:
- Bad: "Now you can back Birchal." (Back the platform? Back the company? Different action.)
- Good: "You've backed a company on our platform. Now you can back the company that runs it."

### 2. Length cap: 65 to 80 words for primary text.

V1 averaged 100 to 115 words. JB flagged it as too long. FMTH's $2-lead ad hits ~110 words but every sentence is load-bearing; V1 had flabby connective tissue ("Australians who used to be locked out of early-stage equity, owning pieces of brands they believed in") that adds wood without lift.

**Rule.** Target 65 to 80 words for Birchal Meta primary text. Refuse to ship anything over 90 words.

**How to apply:**
- Cut "until 2018" preamble unless the date is the hook. Use the dated specifics directly in para 2 if needed.
- Cut clauses that rephrase the prior sentence (e.g. "None of those raises came from VCs alone. They came from 137,000 everyday Australians." -- second sentence repeats the first).
- One brand-grid name list, not two (don't repeat Naked Life / Our Cow across paragraphs).
- Last paragraph max 2 sentences: CTA + waitlist outcome.

### 3. Headlines: avoid ambiguous "it" / "the platform" referents.

Three V1 headlines had subject ambiguity:
- "Built by 137,000 investors. Now opening up." -- *the platform* opening, or *Birchal-the-company* opening its raise?
- "Own a piece of the platform you've used" -- "own a piece of" is correct but reader doesn't immediately map "platform you've used" to "the company that runs it".
- "The crowd built it. Now invited to own it." -- "it" referent shifts mid-line.

**Rule.** When the recursion is the angle, name both subjects explicitly OR pick a single referent and stay there.
- Cleaner: "Built by 137,000 investors. Now we're raising too." (we = Birchal-the-company; "too" makes the recursion implicit).
- Cleaner: "Back the platform you've backed companies on." (the verb stays, but the action is unambiguous: invest in the platform's parent company).
- Cleaner: "Backed by the crowd that built it." (single referent: the company being backed).

## Anti-patterns (do not ship)

- ANY UNSOURCED market-share %, "#1", "largest", "leading", "first in Australia", valuation, or $ minimum. Banned (ASIC RG 234 / BANNED-CSF-PHRASES / brief.md). The verified numeric spine is ONLY: $234M+ raised, 324 raises, 137,000 investors, operating since 2018. SINGLE CARVE-OUT: the registered PLAT-005 stat ("more than 64% of all funds raised through CSF in Australia has been raised on Birchal"), JB-authorised 2026-05-18, used per its facts.json usage rules (at most once per ad, registered wording, "CSF in Australia" scope, never combined with #1/first/largest, citation-pending so not marked live until confirmed). "#1" / "first" / "largest" / "leading" stay fully banned. See #5 compliance carve-out.
- "Birchal is now doing the same for itself" -- "itself" is the problem.
- "the platform it built" with `it = Birchal-the-company` and `platform = Birchal-the-platform` in the same sentence without first-person framing.
- Body copy over 90 words.
- Two paragraphs that re-explain the same proof.
- Brand grid naming the same companies twice across paragraphs.

### 4. Hooks: cadence-of-three numbers + punch line beats statement-then-observation.

V2 openers were informational ("324 Australian companies have raised on Birchal. Most Australians have never invested in one."). Halbert score 3-4. JB flagged as needing more curiosity / epic stats / specificity / benefit.

**Rule.** Lead the first 8 words with at least two of: a specific number, a named entity, a curiosity gap (why/what/how), or a pattern interrupt. Aim for Halbert score 4+. Refuse to ship below 4.

**The four levers, ordered by lift:**

1. **Numbers in the first 8 words.** Cadence-of-three numbers (e.g. "$234M raised. 137,000 investors. None of them VCs.") creates scroll-stop. Specifics imply truth; round numbers imply marketing. [fact:specificity-buzzsumo-numbers] -- numbers lift CTR ~36%.
2. **Punch line that opens a gap.** The third beat of the cadence-of-three carries the curiosity (e.g. "None of them VCs" -- then who?). The reader scrolls to close the loop.
3. **Named entity.** "Triple Bubble's first investment from their new fintech fund: Birchal." -- the specific fund + new-fund framing creates curiosity (why Birchal first?). Named entities outpull generic categories.
4. **Pattern interrupt or news hook.** "Before 2018, only the wealthy could invest in an Australian startup. Now 137,000 Australians have." -- temporal contrast + specific community number = scroll-stop.

**How to apply to Birchal hooks specifically:**

- The strongest hooks for Birchal lean on the platform stats ($234M, 137,000, 324, 8 years) plus one of: a specific named fund (Triple Bubble, AVPF), a verbatim investor quote excerpt (Pym), or a pre-2018 stakes frame.
- Avoid metaphors as openers ("vote with your wallet"). Specificity beats metaphor.
- For headlines: every standalone headline should hit Halbert 4+ on its first 8 words. Statements without a hook ("324 companies. 137,000 investors. One platform.") are V2-grade and need a curiosity gap or recursion punch (V3 fix: "324 raises. $234M raised. Now our own.").

**V3 hook examples that scored 5:**

- A1: "$234M raised. 137,000 investors. None of them VCs." (cadence + punch + curiosity gap)
- A3: "Before 2018, only the wealthy could invest in an Australian startup. Now 137,000 Australians have." (loss frame + community FOMO)
- B1: "You are one of 137,000 investors who built this platform. Now we are raising on it." (personal address + specific number + ownership + recursion)
- B2: "Triple Bubble's first investment from their new fintech fund: Birchal." (news pattern + named fund + curiosity)

**V3 headline examples that scored 5:**

- "$234M, no VCs needed" (5w, specific + pattern interrupt)
- "Why Triple Bubble bet first on Birchal" (Caples Why + named fund)
- "Why most Australians missed the last $234M" (Caples Why + FOMO + specific stat)
- "324 raises. $234M raised. Now our own." (cadence + recursion punch)

### 5. Sentence-level structure: the 2026-05-18 JB-rewrite pattern.

JB rewrote a V5-grade primary text and the edit was almost entirely structural, not factual. The lesson is the *shape of the sentences* and it generalises to every variant. Apply before the hook gate.

**Rule. One idea per sentence. The full stop is the timing device.** Never open with a comma-spliced stat triplet. Open with ONE number as a complete sentence, full stop, then a short second sentence that turns. The hard stop forces the beat that makes the turn land.
- Bad (AI V5): "324 raises, $234M+, and the next CSF offer on Birchal is our own."
- Good (JB): "$234M+ raised on Birchal. And the next crowd-sourced funding offer is our own."

**Rule. The reader is the grammatical subject at the turn and the CTA.** Pivot we->you exactly at the moment of opportunity. The payoff is about the reader's stake, not Birchal's milestone.
- Bad: "Now it is our turn." (subject = Birchal)
- Good: "Now, you can own a piece of the platform." (subject = the reader)

**Rule. No third-party company names in the bridge.** The setup-to-turn paragraph keeps the spotlight on the platform and the reader. Naked Life / Our Cow / Medigrowth steal attention at the exact moment we want the reader thinking about their own stake. Named clients, if used at all, go in a dedicated proof line, never the connective tissue. (Stricter than #2: zero names in the bridge, not just no repeats.)

**Rule. CTA = the literal micro-action, one sentence, with the exchange.** "Leave your email and we will tell you the moment the offer goes live." Beats "Save your spot ..." twice over: (a) it states the real conversion action, the email, matching the FMTH top performer; (b) "spot / place / allocation / secure / reserve" is a CSF place-metaphor smell, "email / notify" is the safe and higher-converting frame. Do not pad the close with separate "it's free / no obligation" sentences; a genuinely small ask defends itself and the disclaimer line carries compliance.

**Rule. One proof point per beat.** At most one number in the hook, one in the bridge, none repeated. Four scattered stats read as a brag; one per beat reads as fact. (Tightens #4: cadence-of-three is a hook device inside one sentence; across the ad, do not re-scatter the same numbers.)

**Observation worth keeping.** "324 raises. The next one is ours." was always the strongest line because it already had this shape: two short sentences, hard stop, turn at the end. JB's body rewrite simply propagated the headline's proven rhythm down into the primary text. When the headline reads well but the body does not, the usual fault is a rhythm mismatch: a punchy headline bolted onto a comma-stacked body. Make the body match the headline's cadence.

**Compliance carve-out (load-bearing, updated 2026-05-18).** JB's rewrite contained "over 64% market share of all crowd-sourced funding raises in Australia" (and the misspelling "acheived"). The *structural slot* it fills (a one-line dominance proof before the turn) is correct. The *claim* was initially treated as a banned unsourced market-share statement. JB has since authorised it (2026-05-18, "it is fact and verifiable"); it is now registered as PLAT-005 (confidence MED, source_status OPEN until the exact public citation is attached). Rule now: that slot MAY be filled with PLAT-005 in its registered wording, at most once per ad, scoped to "CSF in Australia", NEVER combined with #1/first/largest, and not marked live until the citation is confirmed. Every OTHER market-share / #1 / largest / leading / first claim remains banned. The structural lesson is unchanged: adopt the shape; only ever put a registered, sourced number in it.

## Open question for next pass

- For Segment B (existing investors), should the ads call them out as "Birchal investors" explicitly (e.g. "If you've backed a company on our platform...") or stay implicit? V1 used "you backed a Birchal company" which is direct but cold-list-served could feel presumptuous. JB to confirm.
- Possible 6th ad angle: Halbert-style confessional opener. "After 8 years funding other people's companies, we have kept ours private. That is about to change." -- first-person + confession-shape + specific timeframe + curiosity. Reserved for V4 if JB wants to test against the current 5.

## Generation prompt addendum (paste into the DRC primary-text generate + refine step)

Derived from the 2026-05-18 JB rewrite (#5). Each item is a gate, not a preference. Self-check every variant against the checklist before emitting.

1. One idea per sentence. No comma-spliced stat triplets. Open with ONE verified number as a complete sentence, full stop, then a short sentence that turns. The full stop is the hook's timing device; do not replace it with a comma or colon.
2. Hook = one verified number + a turn. Pattern: "[ONE spine stat] [verb] on Birchal. And [the turn]." Spine = $234M+ raised, 324 raises, 137,000 investors, since 2018. The ONLY permitted market-share statement is registered PLAT-005 ("more than 64% of all funds raised through CSF in Australia has been raised on Birchal"), at most once per ad, registered wording, "CSF in Australia" scope, never with #1/first/largest, not marked live until its citation is confirmed. Any OTHER market-share %, "#1", "largest", "leading", "first", valuation, or $ minimum: delete and substitute a spine stat in the same slot.
3. The bridge names no third-party companies. Spotlight on the platform and the reader. Named clients only in a dedicated proof line, never setup-to-turn.
4. The reader is the grammatical subject at the turn and the CTA. "Now, you can own a piece of the platform" / "Leave your email", never "Now it is our turn" / "Save your spot".
5. Plain concrete nouns, not metaphor. "the platform" not "the rails". 5th to 7th grade reading level.
6. CTA = the literal micro-action, one sentence, with the exchange: "Leave your email and we will tell you the moment the offer goes live." No "save your spot / secure / reserve / allocation". No separate "it's free / no obligation" sentence.
7. One proof point per beat. At most one number in the hook, one in the bridge, none repeated.
8. Terminator byte-exact, once: *Always consider the general CSF risk warning and offer document before investing.

Self-check (all must be yes): (a) every sentence one idea; (b) reader is subject at the turn and CTA; (c) no third-party names in the bridge; (d) every number traces to the spine; (e) zero banned phrases incl. market-share / #1 / first / place-metaphor CTA; (f) reads 5th to 7th grade out loud; (g) body cadence matches the headline cadence.
