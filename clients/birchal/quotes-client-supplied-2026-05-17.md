# Birchal — client-supplied quotes (verbatim register)

Supplied by the client (Kirstin Hunter / Birchal) on 2026-05-17 for use in the next ad-copy iteration.

**Integrity rules (read before using any line below):**
- `verbatim_source` = the exact text as supplied/published. Reproduce character-for-character if quoting in full. Do not paraphrase. Do not invent attribution.
- `ad_safe` = the same text with em/en dashes converted to commas and smart quotes straightened, for use in Meta ad copy (AU-English, no-dash rule). This mirrors the existing `facts.json` convention for QUOTE-002 / QUOTE-003 ("Original uses em-dashes; ad copy must not"). Use `ad_safe` in ads; `verbatim_source` is the integrity record.
- Excerpting a contiguous sub-span is allowed; reordering or splicing non-contiguous sentences is not, unless flagged `[excerpt: first + last sentence]` exactly as the existing register does.
- These are CEO / industry-commentary quotes. They are opinion/vision, not statistical claims. They do NOT license any new market-share, valuation, "#1", or "first" numeric claim.
- To be folded into `clients/birchal/facts.json` as `category: verbatim` entries (QUOTE-006..010) by the T3 agent AFTER the V4 create agent finishes (avoids a write race on facts.json).

---

## QUOTE-006 — Aubrey Blanche, on why crowdfunding matters

- **Attribution:** Aubrey Blanche (author, Startup Daily opinion piece)
- **Source:** https://www.startupdaily.net/advice/opinion/why-crowdfunding-is-an-important-part-of-australias-capital-mix/
- **Confidence:** HIGH (client-supplied, published)
- **Use:** third-party validation of the CSF category (Segment A education / belonging). Not a Birchal-specific claim.

**verbatim_source:**
> There are a ton of reasons that crowdfunding is not only a good–but sometimes the best–option for businesses. It can democratise ownership, provide capital without requiring unrealistic growth targets, and is more available to non-traditional founders.
> In short, it's an excellent vehicle to bring more businesses online, which can only be seen as a good thing.
> Crowdfunding–whether through equity, reward, donation, or debt–opens up the ability to invest in excellent businesses to a significantly broader set of investors.

**ad_safe (dashes to commas, for ad use):**
> There are a ton of reasons that crowdfunding is not only a good, but sometimes the best, option for businesses. It can democratise ownership, provide capital without requiring unrealistic growth targets, and is more available to non-traditional founders.
> In short, it's an excellent vehicle to bring more businesses online, which can only be seen as a good thing.
> Crowdfunding, whether through equity, reward, donation, or debt, opens up the ability to invest in excellent businesses to a significantly broader set of investors.

**Short ad excerpt (contiguous, ad_safe):** "Crowdfunding opens up the ability to invest in excellent businesses to a significantly broader set of investors." — Aubrey Blanche

---

## QUOTE-007 — Kirstin Hunter (CEO, Birchal), Forbes: mission beyond numbers

- **Attribution:** Kirstin Hunter, CEO, Birchal
- **Source:** https://www.forbes.com.au/news/leadership/crowdsourcing-our-way-to-economic-growth-and-diversity-in-startups/
- **Confidence:** HIGH (client-supplied, published; client wrote "Forbes quotes from me")
- **Use:** vision / cause-purpose angle (Segment A + B). Pairs with the "Birchal Next" positioning.

**verbatim_source:**
> Birchal's mission goes beyond numbers: it's about fostering an innovation ecosystem where every investor, entrepreneur, and idea can find a place to thrive.
> Crowdsourced funding represents a paradigm shift towards inclusivity and breadth. By empowering a diverse community of investors, Birchal enables founders from all backgrounds – women, people of colour, LGBTQIA+ individuals, migrants, and First Nations people – to draw on the power of the crowd to access capital and realise their entrepreneurial visions.
> Successful crowdsourced funding campaigns result in hundreds, if not thousands, of individual investors putting their money behind ideas they believe in. And when those investments pay off, we see hundreds, if not thousands, of winners.

**ad_safe (dashes to commas, for ad use):**
> Birchal's mission goes beyond numbers: it's about fostering an innovation ecosystem where every investor, entrepreneur, and idea can find a place to thrive.
> Crowdsourced funding represents a paradigm shift towards inclusivity and breadth. By empowering a diverse community of investors, Birchal enables founders from all backgrounds, women, people of colour, LGBTQIA+ individuals, migrants, and First Nations people, to draw on the power of the crowd to access capital and realise their entrepreneurial visions.
> Successful crowdsourced funding campaigns result in hundreds, if not thousands, of individual investors putting their money behind ideas they believe in. And when those investments pay off, we see hundreds, if not thousands, of winners.

**Short ad excerpt (contiguous, ad_safe):** "Birchal's mission goes beyond numbers: it's about fostering an innovation ecosystem where every investor, entrepreneur, and idea can find a place to thrive." — Kirstin Hunter, CEO, Birchal

---

## QUOTE-008 — Kirstin Hunter, on retail investor power (taking on Birchal CEO role)

- **Attribution:** Kirstin Hunter, CEO, Birchal
- **Source:** https://www.startupdaily.net/topic/people/former-techstars-boss-kirstin-hunter-takes-on-birchal-ceo-role/
- **Confidence:** HIGH (client-supplied, published; client wrote "Me taking on Birchal")
- **Use:** democratisation / empathy-access angle (Segment A). The "she said" is the publication's attribution tag, not part of the quote.

**verbatim_source:**
> What really excites me is crowdsourced equity increases the economic power of retail investors by taking business funding decisions away from a small number of professional investors and placing it in the hands of the community.

(Published with trailing attribution: `," she said.`)

**verbatim_source (CEO-appointment line):**
> As the new CEO of Birchal, I'm thrilled to leverage my experience as co-founder of Future Super combining people and financial power to change the superannuation sector, and more recently shaping the next generation of innovative business leaders as an investor at Techstars Tech Central Sydney Accelerator.

**ad_safe:** identical (no dashes; straighten the apostrophe in "I'm" only if your renderer needs it). Note the published source contains a double space in "my  experience"; ad_safe collapses to a single space: "leverage my experience as co-founder of Future Super".

**Short ad excerpt (contiguous, ad_safe):** "Crowdsourced equity increases the economic power of retail investors by taking business funding decisions away from a small number of professional investors and placing it in the hands of the community." — Kirstin Hunter, CEO, Birchal

---

## QUOTE-009 — Kirstin Hunter, on CSF + the Denholm R&D report

- **Attribution:** Kirstin Hunter, CEO, Birchal
- **Source:** https://www.startupdaily.net/topic/funding/the-denholm-rd-report-made-the-case-for-crowdfunding-reform-so-its-time-for-government-to-act/
- **Confidence:** HIGH (client-supplied, published)
- **Use:** vision / category-building angle (Segment B, sophisticated). Policy framing, no numeric claim.

**verbatim_source:**
> Crowdsourced funding sits at the intersection of two of the report's central ambitions: mobilising more private capital for innovation, and democratising access to that capital. When retail investors – not just wholesale investors and VCs – can back the next generation of Australian deeptech, medtech, and cleantech companies we get a richer, more resilient innovation ecosystem.

**ad_safe (dashes to commas):**
> Crowdsourced funding sits at the intersection of two of the report's central ambitions: mobilising more private capital for innovation, and democratising access to that capital. When retail investors, not just wholesale investors and VCs, can back the next generation of Australian deeptech, medtech, and cleantech companies we get a richer, more resilient innovation ecosystem.

**Short ad excerpt (contiguous, ad_safe):** "When retail investors, not just wholesale investors and VCs, can back the next generation of Australian deeptech, medtech, and cleantech companies we get a richer, more resilient innovation ecosystem." — Kirstin Hunter, CEO, Birchal

---

## REF-001 — Backing female founders (reference link, NOT a quote)

- **Source:** https://www.startupdaily.net/advice/investing/want-more-investment-in-women-founders-here-are-4-you-can-back-for-just-250/
- **Use:** supporting reference for the diversity/inclusion angle (pairs with QUOTE-007). The "$250" in the URL slug is the article's framing, NOT a Birchal offer minimum. Do NOT lift "$250" into ad copy as an investment minimum (`BANNED-CSF-PHRASES` / `brief.md` item 2 prohibit quoting any minimum pre-offer).

---

## Usage guardrails (apply when these go into V_next / T3 batch)

1. Opinion/vision only. None of these license a market-share %, valuation, "#1", "largest", "leading", or "first" claim. The verified numeric spine remains PLAT-001/002/003/004 ($234M+, 324, 137,000, since 2018) only.
2. Use `ad_safe` in ads. Convert any remaining smart quotes/apostrophes to straight. No em/en dashes in shipped copy.
3. Keep attribution exactly: "Kirstin Hunter, CEO, Birchal" and "Aubrey Blanche". Do not add unstated titles.
4. The verbatim CSF risk warning still terminates every Meta primary_text, byte-exact, once.
5. Folded into `facts.json` as QUOTE-006..009 + REF-001 by the T3 create agent (after the V4 create agent completes, to avoid a facts.json write race).
