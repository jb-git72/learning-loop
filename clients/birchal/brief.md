# Birchal — Meta ad copy brief

For invocation of the `direct-response-copy` (DRC) skill. Locks scope, audience, channel, claims, banned phrases. The DRC skill reads this verbatim. Companion file: `clients/birchal/facts.json` (claim register).

Last updated: 2026-05-07. JB-confirmed scope.

## Output target

- **5 Meta ad copy bodies** (primary text + headline + description + CTA each, ~80–120 words primary text)
- **10–20 standalone Meta headlines / hooks** (short-form, max 8 words, sentence case, mix of angles)
- Both go to a Google Sheet for JB approval (one tab each), built via `scripts/build_birchal_approval_sheet.py`.

## DRC brief-intake (12 items)

| # | Item | Value |
|---|---|---|
| 1 | Product / offer | A waitlist for Birchal's own CSF (Crowd-Sourced Funding) campaign. Subscribers receive notification the moment the offer document goes live (26 June 2026), at which point they can read the offer and decide whether to invest in Birchal. The waitlist itself is free, no commitment, no preferential terms. |
| 2 | Price | N/A at waitlist stage. Investment minimums are set in the offer document (not public until 26 June 2026). Do not quote any minimum, e.g. "$X to invest", "from $X" — `BANNED-CSF-PHRASES` blocks this. |
| 3 | Audience | TWO segments, separate ad clusters: (A) **First-time CSF investors** — Australians who have never invested in CSF, may know Birchal as a brand or recognise raises like Naked Life / Our Cow / Medigrowth, but treat startup investing as inaccessible. Likely current users of ETFs / Sharesies / Pearler / Stake. Problem-aware to solution-aware. (B) **Existing Birchal investors** — have made at least one investment on Birchal previously. Receive Birchal newsletters. Most-aware: they understand CSF mechanics and know Birchal as a platform. |
| 4 | Channel & format | Meta ads only (Facebook + Instagram feed primary text). Each ad: primary text (~80–120 words, line breaks for scannability), 1 headline (max 8 words, sentence case), 1 description (1 sentence). |
| 5 | Single conversion action | "Save my spot" — landing on `https://join.birchal.com/` waitlist form. Email capture only. NOT "invest now", NOT "subscribe", NOT "buy". Pre-offer language only (`PREOFFER-VERBS` rule). |
| 6 | Awareness level | Segment A: problem-aware to solution-aware (knows of Birchal, doesn't act on CSF). Segment B: most-aware (has invested on Birchal before). |
| 7 | Sophistication stage | Segment A: stage 2-3 (claim → mechanism). Lead with mechanism reveal — *how* CSF works and why this is unusual access. Segment B: stage 4-5 (better mechanism → identity). Lead with identity — "you've backed Birchal-listed founders, now you can back Birchal itself" — and meta-mechanism: this is the platform doing what it built the rails for. |
| 8 | Competitor + differentiator | Public market alternatives (ETFs, Sharesies, Stake) give exposure to large listed companies but no early-stage equity. Other CSF platforms exist (e.g. Equitise, OnMarket) but Birchal is the dominant platform in the category by volume — 324 raises, $234M+, since 2018. Differentiator: this is the platform that built the rails opening the same opportunity in itself. |
| 9 | Social proof (one piece) | Multiple available, choose by segment. Primary: PLAT-001 (324 companies) + PLAT-002 ($234M+) + PLAT-003 (137,000 investors). Quotes: QUOTE-001 (Dom Pym, founder + investor lens) is strongest single line. QUOTE-002 (Nick Carter) for fund-manager weight. QUOTE-005 (Chris Raleigh, Earthletica $1.1M April 2026) for recency proof. Brand grid: Naked Life $2.95M, Our Cow $2M, Medigrowth $1.59M, Earthletica $1.1M, Aquafab $600K, Pulse Tile $400K, Reckless Brewery $513K (RAISE-001 through RAISE-007). |
| 10 | Risk reversal | Waitlist is free, no commitment. The reader makes no decision until they have read the offer document. Frame this explicitly: "Read the offer document before you decide." |
| 11 | Tone constraints | Australian English. No em-dashes, no en-dashes (commas / colons / full stops). No smart quotes. Sentence case headlines. Confident, specific, conversational. Birchal voice is closer to "Aussie fintech operator" than "VC press release". Match register to segment: Segment A more accessible, Segment B more peer-to-peer. |
| 12 | What we cannot say (regulated) | See `facts.json` `BANNED-CSF-PHRASES` and `PREOFFER-VERBS`. Hard-block: "Be first to invest", "first in line", "Invest from $X", "from as little as $X", "guaranteed return", "secure your allocation", "skip/jump the queue", "invest now", "buy now", "subscribe now". Hard-block: "we will send you the offer document" (`VERBATIM-OFFER-LANGUAGE`). Hard-block social proof: Zero Co, Old Young's (`BRAND-EXCLUDED`, both in administration). Verbatim required: CSF short-form risk warning at end of every primary text, byte-exact (`VERBATIM-CSF-WARNING`). |

## Playbook routing (DRC phase 3)

DRC routing decision tree, applied per segment:

- **Segment A — first-time CSF.** Audience axis: B2C considered ($100+ commitment, days to decide). Awareness: solution-aware. Sophistication: 3 (mechanism). → **Playbook 03 Identity** as primary, **Playbook 04 Long-form sales page elements** as fallback for the longer-bodied ads. Use mechanism reveal as the hook ("how Australian startups actually get funded") to create curiosity, then move to identity ("Australians who back the brands they love").

- **Segment B — existing Birchal investors.** Audience axis: B2C considered, most-aware (have transacted). Lapsed-vs-active: assume mixed, treat as active for default. → **Playbook 11 Promo / launch announcement** with identity and recursion ("the platform you've used is now opening the same opportunity in itself"). Avoid 12 Win-back (assumes lapsed); JB can route lapsed-only sub-audience there in a future pass.

## Volume + angle distribution

5 ad bodies + 14 headlines/hooks. Angle distribution informed by FMTH meta-ad evidence (`clients/farm-thru/learnings-meta-ad.md`):

**FMTH evidence carried over (load-bearing):**
- Curiosity-gap narrow-bound hook beat founder-voice opener by +0.18 composite (PR #125 H3 disconfirmed). Lead with the bound: "never been done", "no idea how", a specific number that creates a gap.
- Ownership framing is load-bearing: removing "own a piece of" dropped composite by -0.19 (PR #125 H2 confirmed). Every ad needs one ownership phrase in first two paragraphs.
- "Belonging" is a tested values-aligned angle ("FarmThru families know who grew their food"). For Birchal, the equivalent slot is community-of-investors: 137,000 Australians who already back Australian brands.
- Soft scarcity only ("opens soon", "first in gets first access" pre-offer-permitted). No hard scarcity ("act now", "last chance") — ACL risk before offer exists.
- Cadence-of-three proof in para 2: e.g. "324 companies. $234M+. 137,000 investors."
- Outcome-stated CTA: "Save my spot, we'll tell you the moment the offer goes live."
- Anti-pattern: no "$X minimum", no transaction verbs (invest now, buy now, subscribe), no Birchal in body of FMTH ads (irrelevant here, but the equivalent for Birchal: no naming the offer doc minimum).

**Community as the dominant non-curiosity angle.** Unlike FMTH, Birchal has a structural community story: the platform exists because 137,000 Australians used it. Recursion-as-community ("the crowd built this; now the crowd is invited to own it") is the strongest community frame because it fuses ownership + belonging + proof in one move. Community appears in 3 of 5 bodies and as social proof inside A1.

**Segment A — first-time CSF (3 ad bodies)**
- **A1: Curiosity-gap mechanism reveal** *(primary, FMTH-validated curiosity hook)*. Hook: "Most Australians have no idea how a startup actually gets funded." Body: reveal the CSF mechanism, drop 137,000 + $234M+ as cadence-of-three proof, recursion punch ("now Birchal is opening its own raise"). Community in the body as social proof, not the lead. Cite PLAT-001/002/003 + OFFER-CONTEXT.
- **A2: Belonging / community-as-identity** *(community angle 1, FMTH belonging-slot equivalent)*. Hook: identity-led, second-person ("Australians who back Aussie brands. This one's for you."). Body: you already vote with your wallet by buying Naked Life / Our Cow products; now you can vote with ownership. 137,000 retail investors have done it; the brand grid is the proof. Community + ownership combined. Cite RAISE-001/002/003 + PLAT-003.
- **A3: Empathy + access + recursion** *(community angle 2)*. Hook: "Backing the next big Aussie brand used to be for VCs and family offices." Body: until Birchal, you couldn't get in this early. 137,000 Australians changed that. Now Birchal is opening itself. Empathy lead, community as proof (137,000), recursion as punch. Cite PLAT-003 + OFFER-CONTEXT.

**Segment B — existing Birchal investors (2 ad bodies)**
- **B1: Community-as-builder / recursion** *(community angle 3, second-person insider voice)*. Hook: cadence-of-three opener ("324 companies. $234M+. 137,000 of you."). Body: the platform is here because of the people on it; now we're opening the platform to the people who built it. "You built this, now you can own it." Cite PLAT-001/002/003 + OFFER-CONTEXT.
- **B2: Investor-validation / peer-decision**. Hook: "The funds backing Birchal." Body: pull quote from QUOTE-001 (Dom Pym) opening "I've looked at Birchal from the founder's seat and the investor's seat..." paired with QUOTE-002 (Nick Carter on dominant platform). Frames the decision as peer-validated for sophisticated readers. Cite QUOTE-001 + QUOTE-002.

**Headlines / hooks — 14 total** (max 8 words, sentence case, AU English, no banned phrases, no em-dashes):

- **5 curiosity-led** (Segment A primary). Lead with a bound, a question, or a number gap. Examples: "How Australian startups actually get funded", "Why 137,000 Australians invested before you", "The platform behind 324 Aussie raises".
- **5 community / belonging-led** (Segments A + B). Lead with identity or co-ownership. Examples: "Built by 137,000 Australians", "Australians who back Aussie brands", "Own the platform you've been part of".
- **2 empathy / access-led** (Segment A). Lead with the gap that's now closed. Examples: "What VCs got, you can get too", "From private capital to public access".
- **2 investor-validation** (Segment B). Verbatim or near-verbatim quote excerpts. Examples: "Founder seat, investor seat, same answer", "Dominant platform in Australian fintech".

All headlines compatible with Meta dynamic creative rotation. Source-labelled by angle in the sheet so JB can tick by angle band.

## Workflow phases (post-DRC)

After the DRC skill produces drafts:

1. **Anti-drift audit** (DRC phase 5, code-only): every empirical claim cites a `[fact:id]` from `clients/birchal/facts.json`; no banned AI words; AU English; no em/en dashes; headline ≤ 8 words; verbatim CSF warning byte-match.
2. **Compliance pass** (`compliance-au` skill): scan every ad against `BANNED-CSF-PHRASES`, `VERBATIM-OFFER-LANGUAGE`, `BRAND-EXCLUDED`, `PREOFFER-VERBS` regex/contradicts_if rules. Resolve every HIGH and MEDIUM finding.
3. **Humaniser** (DRC phase 6): `python3 /Users/jb/Documents/GitHub/marketing-copy/direct-response-copy/scripts/humaniser.py` per ad until clean.
4. **Approval sheet** (`scripts/build_birchal_approval_sheet.py`): two tabs (Bodies, Headlines). Source-label column groups by angle band. Checkbox + comments columns.
5. **JB review** in sheet. Iterate phases 1-3 on rejected rows.
6. **Approved → mark `approved: true` in JSON**. Commit. Hand to media buyer.

## File destinations

- Ad bodies: `clients/birchal/loop/birchal-ad-variants/BIRCHAL-{A1,A2,A3,B1,B2}.json`
- Headlines: `clients/birchal/loop/birchal-headlines.json` (single file, 14 entries)
- Existing `BIRCHAL-DRC-A/B/C.json` from 30 Apr: archive to `birchal-ad-variants/_archived/` (kept for reference) and supersede with the new set, since they precede the fact register and carry the unresolved placeholder.
