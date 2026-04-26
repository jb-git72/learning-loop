# Variant validator scarcity — discussion doc

**Context for the founder:** the FarmThru landing pages run through an automated quality scorer before they ship. One of the 29 checks is called "authentic scarcity" — it expects the page to communicate that the waitlist is finite ("act now or miss out"). Until last week, that check was passing because the pages used phrases like "first access" and "limited spots". CSF compliance has now banned those phrases. So the check is about to start failing on most variants. We need to decide what (if anything) replaces them.

---

## What `check_28_authentic_scarcity` does

It's an automated test that opens each landing page HTML and checks two things at once:

1. Does the page contain at least one of these four words/phrases anywhere in the HTML: **"early access"**, **"limited"**, **"spots"**, or **"first access"**?
2. Is there a visible countdown timer element on the page (`<div id="countdown">`)?

If both are true, the check passes. If either is missing, it fails. It's marked as a "should-have" item (not mandatory), so failing doesn't block publication — but it lowers the variant's overall validation score and is one of five quality signals we track per page.

The check lives at `/Users/jb/Documents/GitHub/sales-skill/web/variant_validator.py:761-771`.

## Why it matters

The check was designed to enforce a marketing principle: pages that combine **a scarcity signal** (something is finite) with **a deadline cue** (a countdown) convert dramatically better than pages without either. The validator cites OptiMonk research showing **+332% conversion lift** when authentic scarcity is present. The same research is referenced across the codebase:

- `web/docs/CFE-Campaign-Playbook.md:240` — "Limited-time offers: 332% increase in conversion rates (OptiMonk)"
- `web/docs/verified-conversion-stats.md:34` — "Authentic limited-time framing = +332% conversion"
- `web/campaigns/FMTH/variants/urgency-scarcity.md:17` — variant M was built specifically to test this

The principle is loss aversion (Kahneman): people work harder to avoid losing something than to gain the same thing. A waitlist that feels finite ("200 spots, 327 already taken") creates fear of missing out. An open-ended waitlist doesn't.

This check was added because the validator's authors believed the FMTH page should feel finite — that's the whole reason the VIP waitlist concept exists in the first place.

## The conflict

The validator's allow-list of scarcity words overlaps directly with the CSF banned-phrases list in `clients/farm-thru/CSF-VIP-BIRCHAL-SUBMISSION.md` §5:

| Validator's scarcity word | CSF status |
|---------------------------|------------|
| "first access" | **BANNED** ("First access to invest") |
| "early access" | **BANNED** by implication ("invest before the public", same meaning) |
| "limited" | **BANNED** in context ("limited spots — VIPs go first") |
| "spots" | **BANNED** in context ("reserve your spot in the round", "limited spots") |

The reason these were banned: ASIC's CSF rules (RG 261) prohibit any implication that the VIP product grants earlier or preferential investment access. "First access", "limited spots", "reserved for VIPs" all imply that VIPs get to invest before non-VIPs — which is structurally false (everyone applies through the same Birchal facility on the same terms) and a regulatory breach.

**The auditor's high-leverage finding:** the validator was actively *rewarding* the banned phrasing — every page that used "first access" got a green tick on check_28. So compliant variants will now fail a check that non-compliant variants were passing. This is the inversion that needs fixing.

## Current state (post-rewrite)

I scanned all 17 LP variants for the four scarcity words. Here's what's left:

| Variant | "early access" | "first access" | "limited" | "spots" | Has countdown? |
|---------|----------------|----------------|-----------|---------|----------------|
| index.html (A) | 1 | 0 | 0 | 0 | yes |
| b | 1 | 0 | 0 | 0 | yes |
| c | 0 | 0 | 0 | 0 ("Reserve your spot" but not "spots") | yes |
| d, e, f, g, h, i, j, k, l, n, o, p, q | 0 | 0 | 0 | 0 | yes |
| m | 0 | 0 | 0 | 1 ("Spots close before we launch") | yes |

So:

- **2 variants (A and B) currently pass the check, but only by using "early access"** — which is itself a banned phrase. They pass the validator but would fail CSF compliance. These need fixing for compliance regardless.
- **1 variant (M) currently passes legitimately** — "327 people have already joined the VIP waitlist. Spots close before we launch." This is borderline: "spots close" is closer to a deadline statement than a banned-allocation claim, but it's still a single judgment call away from §5.
- **14 variants now fail check_28** — they have a countdown but no scarcity word. Pre-rewrite, several likely passed via "early access" / "first access" / "limited spots".

Sample of what M says today (the only variant with both signals working compliantly):
> "327 people have already joined the VIP waitlist. Spots close before we launch."
> + visible countdown

## Options for CSF-compliant replacement signals

### Option 1 — Update the validator's allow-list to use compliant scarcity words

- **What:** Change line 763 from `["early access", "limited", "spots", "first access"]` to a CSF-safe list, e.g. `["waitlist closes", "closes before", "before we launch", "by [date]", "deadline"]`. Then update existing copy in 1-2 places to use one of these phrasings.
- **Pros:** Keeps the marketing principle (urgency + countdown), removes the regulatory risk, low code change. Validator stops rewarding banned phrasing. M's existing line ("Spots close before we launch") would still pass if we add "closes before" to the list.
- **Cons:** Requires founder/agency to settle on which deadline phrasings are CSF-safe. "Waitlist closes" is about the *waitlist* (a free supporter list), not about the *investment round* (which is the part regulated by ASIC). This is the cleanest framing because it disambiguates the two products.
- **Effort:** ~30 min — edit one line in the validator + add one line to ~2 variants that don't already say "waitlist closes" or equivalent.

### Option 2 — Drop the scarcity word requirement; keep just the countdown

- **What:** Change the check to pass if a visible countdown exists. Remove the text-string requirement entirely.
- **Pros:** Simplest fix. Countdown timers are themselves an authentic scarcity signal (visual deadline). No copy edits needed.
- **Cons:** Weakens the check. The original principle was that the *combination* of a deadline cue (countdown) and a scarcity statement (text) is what drives the lift. A countdown alone, without an explanatory line, can read as a stage-prop rather than a real deadline. Also: the "+332% lift" research was specifically about authentic limited-time *framing*, not just a clock.
- **Effort:** ~5 min — change one line in the validator, no copy edits.

### Option 3 — Reframe the scarcity around the *waitlist* (not the investment)

- **What:** Add a non-investment scarcity signal that the validator can detect, e.g. "VIP waitlist closes [date]" or "supporter waitlist limited to 1,000 places". This distinguishes the VIP product (which *can* be limited and time-bound) from the investment round (which can't have any scarcity claim attached). Update validator to look for "waitlist closes", "supporter list", or similar.
- **Pros:** Strongest marketing position — keeps the urgency mechanism alive while staying compliant. The waitlist itself is a separate product, not the share offer, so finite-supply claims on it are fine. Aligns with how the VIP product is structured in §1-3 of the Birchal submission.
- **Cons:** Need to verify the waitlist genuinely is finite. If we say "1,000 supporter places" we have to honour it. "Waitlist closes [date]" is easier — the date is the real launch date, which already exists.
- **Effort:** ~1 hour — settle on one scarcity statement, add it to all 16 variants in a consistent place (e.g. just above the form), update the validator. Could be done as one of the FMTH pass-3 hill-climb iterations.

### Option 4 — Skip the check via `validator-override` and accept the score hit

- **What:** Add `<!-- validator-override: 28 -->` to each variant. The validator already supports this — variants O and Q use it for other checks today.
- **Pros:** Zero code change. Documents the deliberate decision (CSF compliance > scarcity gimmick).
- **Cons:** Loses the conversion mechanism entirely. The +332% lift research is specifically about FMTH's category (a campaign with a deadline). Walking away from this is leaving conversion on the table without a substitute. Also doesn't fix the validator's reward-the-banned-phrase bug — it just hides it.
- **Effort:** ~15 min.

## Recommendation

**Option 3** — reframe the scarcity around the waitlist itself.

The waitlist *is* a finite product (a launch-day SMS list with a closing date), so saying it closes on a specific date is both honest and CSF-safe. It separates cleanly from the share-offer regulation: ASIC bans claims about *who gets to invest first*, not claims about *who's on a free supporter list*. We get to keep the conversion mechanism (urgency + countdown) and we kill the validator's reward-the-banned-phrase bug at the source.

Option 1 is a fine fallback if the founder wants something faster — it's basically Option 3 minus the "consistent line in all 16 variants" step. Option 2 is too weak (countdown without context is wallpaper). Option 4 is a retreat — we'd be giving up on a documented +332% conversion mechanism without trying to recover it in a compliant form.

The waitlist-closes framing also matches the existing M variant ("Spots close before we launch") and the existing N variant ("at the front of the line"), so we're aligning with the strongest variants rather than reinventing.

## Implementation sketch (if recommendation accepted)

**Files to change:**

1. `/Users/jb/Documents/GitHub/sales-skill/web/variant_validator.py:763` — change:
   ```python
   has_scarcity = any(w in text_lower for w in ["early access", "limited", "spots", "first access"])
   ```
   to:
   ```python
   has_scarcity = any(w in text_lower for w in ["waitlist closes", "closes before launch", "closes before we launch", "by launch day", "before [date]"])
   ```
   (exact list to be confirmed — pick 3-4 phrasings that the rewrite agent is allowed to use)

2. `/Users/jb/Documents/GitHub/sales-skill/web/tests/test_variant_validator.py` — update the test fixtures for check_28 to reflect the new allow-list. Add a test that confirms "first access" / "limited spots" do NOT satisfy the check (regression guard against the original bug).

3. `/Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/index*.html` (14 variants missing scarcity text) — add one line in or near the form/VIP section: "Waitlist closes before we launch" (or similar agreed phrasing). Avoid the existing "first access" / "early access" lines in A and B — replace those.

4. `/Users/jb/Documents/GitHub/learning-loop/clients/farm-thru/CSF-VIP-BIRCHAL-SUBMISSION.md` §5 — add a note that "waitlist closes" / launch-date scarcity claims about the supporter list are explicitly OK because they're outside the share-offer regulation perimeter.

5. `/Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/variants/INDEX.md` and `urgency-scarcity.md` — refresh the scarcity-mechanism description to match the compliant phrasing.

**Effort:** ~1-2 hours total, fits inside the existing FMTH pass-3 hill-climb iteration (task #35). Worth pairing with task #61 (which already exists for this exact reconciliation).

**Validation ladder before shipping:**
- Run `python3 web/variant_validator.py web/campaigns/FMTH/` and confirm all 17 variants pass check_28.
- Run the CSF compliance scorer (the one calibrated to 100% accuracy in tasks #47-#49) and confirm zero hits on banned-phrase rules.
- Re-run the variant-validator test suite and confirm the new regression test (banned phrases must NOT satisfy check_28) passes.
