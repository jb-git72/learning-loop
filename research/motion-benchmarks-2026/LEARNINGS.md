# Learnings: Motion Creative Benchmarks 2026

Source: [Motion Creative Benchmarks 2026](https://motionapp.com/thumbstop-pulse/creative-benchmarks-2026)
Dataset: 578K ads, 6K advertisers, $1.3B Meta spend (Sep 2025 – Jan 2026)
Raw data files: `LLM_REPORT.md`, `LLM_DATA_APPENDIX.md`, `SOURCE_MAP.md`, `CHART_SPECS.json`

---

## 1. Hook Taxonomy — Gap Analysis

Our `writer.py` defines 10 hook types. The report ranks 25+ hook/headline tactics by hit rate (% that become winners) and spend use ratio (spend share ÷ creative share). Several high-performing hooks are missing from our taxonomy.

### Our hooks that map cleanly to report winners

| Our hook_type      | Report tactic     | Hit rate rank | Spend use rank | Notes |
|--------------------|-------------------|---------------|----------------|-------|
| `confession`       | Confession        | 9th           | 6th            | Strong on both axes |
| `bold_claim`       | Bold claim        | 14th          | 22nd           | High hit rate, lower spend efficiency |
| `contrarian`       | Contrarian        | 20th          | 14th           | Better at sustaining spend than winning |
| `if_then`          | If then           | 17th          | 16th           | Steady performer |
| `direct_address`   | Direct address    | 23rd          | 23rd           | Common, not differentiated |
| `statistic`        | (implicit in Price anchor) | 3rd  | 2nd            | Price anchor is #2 spend use — our "statistic" hook covers this |
| `story`            | Storytelling      | —             | 24th           | Low spend use; may need tighter framing |

### HIGH-PRIORITY GAPS — hooks we should add

These hooks rank in the **top 10 by hit rate** but have no equivalent in our taxonomy:

| Report tactic          | Hit rate rank | Spend use ratio | Why it matters | Suggested hook_type key |
|------------------------|---------------|-----------------|----------------|-------------------------|
| **Newness**            | 1st           | ~1.0            | Highest hit rate of any hook. "New", "just launched", "introducing". Signals novelty. | `newness` |
| **Sale announcement**  | 2nd           | 21st            | High hit rate but low spend use — great for initial attention in promo contexts | `sale_announcement` |
| **Price anchor**       | 3rd           | 2nd             | Top 3 on BOTH axes. Specific price comparison. Overlaps `statistic` but more focused. | `price_anchor` |
| **Urgency**            | 4th           | 7th             | Deadline/scarcity framing. Strong on both axes. | `urgency` |
| **Offer only**         | 6th           | 5th             | Lead with the deal, no preamble. Pure value prop. | `offer_first` |
| **FOMO**               | 7th           | 9th             | Social proof + scarcity combination. | `fomo` |
| **Exclusivity**        | 10th          | 15th            | "Only for...", "members only", "early access" | `exclusivity` |
| **Curiosity**          | 11th          | 8th             | Open loops, incomplete info. Strong spend use. | `curiosity` |

### MEDIUM-PRIORITY — interesting but situational

| Report tactic          | Hit rate rank | Spend use ratio | Notes |
|------------------------|---------------|-----------------|-------|
| Announcement           | 5th           | 3rd             | Overlaps newness/sale. Could be a variant. |
| Reverse psychology     | 15th          | —               | "Don't buy this if..." Niche but differentiating. |
| Shocking statement     | 16th          | 18th            | Covered by `pattern_interrupt` |
| Warning                | 18th          | 17th            | Partially covered by `contrarian` |
| Wordplay               | 19th          | 10th            | High spend use, hard to generate reliably with LLMs |
| Myth busting           | —             | 12th            | Strong spend sustainer. Overlaps `contrarian`. |

### Recommended additions to HOOK_TEMPLATES

```python
# Priority additions based on Motion Benchmarks 2026
"newness": "Open by announcing something new — a launch, update, or first. Novelty is the hook.",
"urgency": "Open with a time constraint or deadline that creates immediate pressure to act.",
"price_anchor": "Open with two prices side by side — the expensive way vs. your way. Let the gap sell.",
"curiosity": "Open with an incomplete thought or surprising setup that can only be resolved by reading on.",
"offer_first": "Open with the deal. No story, no context — lead with the value proposition immediately.",
"fomo": "Open with what others are already doing or getting. Make inaction feel like missing out.",
"exclusivity": "Open by making the reader feel selected — early access, limited group, insider status.",
```

---

## 2. Visual Format Insights — Scoring Implications

### Top formats by hit rate (% that become 10x winners)

| Format                 | Hit rate | Spend use ratio | Creative share | Spend share |
|------------------------|----------|-----------------|----------------|-------------|
| Unboxing               | 9.8%     | 1.3             | 2.1%           | 2.8%        |
| Offer-First Banner     | 8.6%     | 1.3             | 21.9%          | 29.3%       |
| Demo                   | 8.1%     | 1.0             | 12.6%          | 12.9%       |
| Testimonial            | 6.5%     | 1.0             | 13.3%          | 13.3%       |
| Celebrity              | 5.9%     | 2.1             | 0.8%           | 1.8%        |

### Key insight for text-based ad generation

**Text-forward assets have the HIGHEST hit rate and spend use ratio of any asset type.** From CH-012:
- **Text only**: Highest hit rate (~12%) AND highest spend use ratio (~1.9)
- **Product image with text**: Second highest on both axes
- This directly validates what our engine generates (text-based meta-ads, emails, LPs)

### Scoring implications

The `platform_fit` and `scroll_stop_hook` dimensions already reward clarity and thumb-stopping openers. But the benchmarks suggest we should also reward:

1. **Format-hook alignment** — Offer-first banner + price anchor hook = 8.6% hit rate. The combination matters more than either alone.
2. **Text density in static** — Text-only assets outperform. Our scoring should not penalize "too much text" if it's sharp and specific.
3. **Specificity premium** — Price anchor (#2 spend use), statistic hooks, and offer-first formats all share one trait: they lead with a concrete number or offer. Our `specificity` dimension (weight 1.5) is correctly prioritized.

---

## 3. Visual Formats by Vertical — Industry Playbooks

### Health & Wellness (closest to pet/insurance/wellness clients)

**Hit rate leaders:** Stitch, Reaction video, Unboxing, Celebrity, Founder, Letter, Stop motion, Influencer endorsement, POV, Transformation

**Spend use leaders:** Social post mockup, Letter, Celebrity, Case study, Offer-first banner, Behind the scene, UGC overlay, Founder, Transformation, Billboard

**Takeaway for scoring:** Founder stories and transformation narratives are validated winners in H&W. Our `empathy-founder` angle (Farm Thru) and `story` hook align well. The "Letter" format (founder letter style) is a strong spend sustainer — worth encoding as a format option.

### Fashion & Apparel

**Hit rate:** Post-it, Quiz, Stylized product shot, Meme, ASM, Product shot, Social comment, Podcast, Product showcase, Unconventional text placement

**Spend use:** Podcast, Unconventional text placement, Billboard, Text message, Sign, Celebrity, Slideshow, Post-it, Offer-first banner, Demo

**Takeaway:** Fashion rewards novelty and unconventional presentation. "Meme" and "Quiz" formats suggest playful/interactive hooks outperform in this vertical.

### Food & Nutrition / Pets (relevant for Farm Thru, Best for Pet)

These verticals are listed but detailed breakdowns weren't fully extracted in the LLM appendix. The cross-vertical pattern: **Founder, Transformation, Case study, and Offer-first Banner** appear across most verticals as reliable performers.

---

## 4. Structural Insights for the Scoring Engine

### Hit rate expectations (calibration)

| Spend tier     | Avg hit rate | Top 25% volume/week | All volume/week |
|----------------|-------------|----------------------|-----------------|
| Micro (<$10K)  | 4.0%        | 4.8                  | 2.8             |
| Small          | 6.4%        | 8.0                  | 4.1             |
| Medium         | 8.1%        | 15.9                 | 6.6             |
| Large          | 8.6%        | 31.1                 | 11.2            |
| Enterprise     | 8.8%        | 54.6                 | 18.8            |

**Implication for hill-climbing:** Even at enterprise scale with the best creative teams, only ~9% of ads become winners. Our hill-climb target of composite >= 0.70 before human review is appropriate — we're optimizing for "strong draft" not "guaranteed winner."

### Volume as strategy

The report's #1 finding: more ads tested = more winners found. This validates the hill-climb approach — generating many variants and scoring/filtering is structurally correct. The top 25% of advertisers ship 3x the creative volume of average.

### Mid-range matters

~40% of ads are "mid-range" (not winners, but run 28+ days). These sustain day-to-day performance. Our scoring shouldn't only optimize for scroll-stopping outliers — consistent, solid ads have portfolio value. The `platform_fit` and `receptionist_test` dimensions capture this.

---

## 5. Spend Use Ratio — New Scoring Concept?

The report introduces **spend use ratio** (format's spend share ÷ creative share):
- **>1.0** = punches above weight (gets more spend per creative than average)
- **≈1.0** = as expected
- **<1.0** = overused relative to result

This is analogous to what we measure with hill-climbing: are we generating variants that outperform the average? We don't have a "spend use" equivalent, but the concept maps to: **does this hook/angle combination score above the baseline for the client?**

Potential addition to scoring: a `benchmark_comparison` that compares a variant's hook_type + angle combination against the client's historical average for that combination.

---

## 6. Action Items

### For ad generation (writer.py)
- [ ] Add 7 new hook types to HOOK_TEMPLATES (newness, urgency, price_anchor, curiosity, offer_first, fomo, exclusivity)
- [ ] Update `_dimension_improvement_guidance()` for scroll_stop_hook to reference benchmark-validated hooks
- [ ] Consider vertical-aware hook selection: if client is H&W, weight founder/transformation hooks higher

### For scoring (engine/)
- [ ] Validate that `specificity` dimension properly rewards price anchoring and concrete numbers
- [ ] Consider adding a `hook_type_diversity` meta-score across a batch (not per-ad) — penalize batches that over-index on one hook type
- [ ] Review `scroll_stop_hook` rubric to ensure it recognizes newness, urgency, and FOMO patterns
- [ ] Consider vertical-specific rubric weight profiles (H&W vs Fashion vs Food)

### For client configs
- [ ] Add benchmark-derived angles/hooks to client `config.json` where relevant
- [ ] Update learnings.md files with vertical-specific format insights
- [ ] Use the hit rate × spend use ratio matrix to prioritize which hook/angle combos to test first in hill-climbing
