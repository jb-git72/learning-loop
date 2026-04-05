# LLM Data Appendix — Creative Benchmarks 2026

All tables are privacy-safe, aggregated only. No row-level or advertiser-identifying data. Suppression rules from the analysis notebook (MIN_ACCOUNTS_FOR_FORMAT = 50, etc.) are applied where applicable.

---

## CH-001: Relationship between weekly ad volume and number of winning creatives

**Type:** Scatter (conceptual); no raw point-level data published to preserve anonymity.

**Summary:** The report describes a positive relationship: as ads launched per week increase, winner count across advertisers increases. No fine-grained scatter table is published in the PDF; the finding is narrative. For replication, see notebook (Creative Volume section).

**Data table:** Not reproduced at point level (would risk identification). Key aggregate: across accounts, higher avgCreativesPerWeek is associated with higher winner count. See SOURCE_MAP.md#CH-001.

---

## CH-002: Spend concentration (spend per ad distribution)

**Type:** Histogram / distribution.

**Summary:** Spend per ad is right-skewed; a small share of ads capture most spend. The PDF references a “Spend per ad distribution” chart (e.g. p90, total ads). Exact bin counts are not reproduced in the PDF text; the narrative states that spend concentrates heavily among a small share of ads.

**Data table:** Distribution is described qualitatively. Dataset-level: 578,750 creatives; $1.29B total spend. Per-creative spend distribution not tabulated here to avoid reconstruction of tail percentiles that could support identification. See SOURCE_MAP.md#CH-002.

---

## CH-003: Spend tier — average testing volume and average hit rate

| Spend tier (per month)     | Average testing volume (per week) | Average hit rate (%) |
|----------------------------|-----------------------------------|------------------------|
| Micro (<$10K)               | 2.8                               | 4.0                   |
| Small ($10K–$50K)          | 4.1                               | 6.4                   |
| Medium ($50K–$200K)        | 6.6                               | 8.1                   |
| Large ($200K–$1M)          | 11.2                              | 8.6                   |
| Enterprise ($1M+)           | 18.8                              | 8.8                   |

**Units:** Testing volume = mean creatives per week per account; hit rate = (winner creatives ÷ total creatives) × 100, unweighted mean across accounts in tier.

---

## CH-004: Hit rate explanation (hypothetical Account A vs Account B)

**Type:** Hypothetical example only.

| Account  | Launches | Winners | Hit rate (%) |
|----------|----------|---------|--------------|
| Account A | 50       | 5       | 10           |
| Account B | 5        | 1       | 20           |

**Note:** No real account data. Used in report to illustrate that hit rate alone does not distinguish testing depth.

---

## CH-005: Portfolio breakdown — % creatives that are losers, mid-range, winners by spend tier

| Spend tier            | Loser (%) | Mid-range (%) | Winner (%) |
|-----------------------|-----------|----------------|------------|
| Micro (<$10K)          | 50.2      | 46.0           | 3.7        |
| Small ($10K–$50K)      | 49.3      | 44.6           | 6.2        |
| Medium ($50K–$200K)    | 52.6      | 40.1           | 7.3        |
| Large ($200K–$1M)      | 53.9      | 38.0           | 8.1        |
| Enterprise ($1M+)       | 52.2      | 39.6           | 8.2        |

**Definitions:** Loser = turned off before 28 days. Mid-range = ≥28 days spend, not winner. Winner = ≥10× account median and ≥$500.

---

## CH-006: Spend allocation — % of spend to losers, mid-range, winners by spend tier

| Spend tier            | Loser (%) | Mid-range (%) | Winner (%) |
|-----------------------|-----------|----------------|------------|
| Micro (<$10K)          | 31.5      | 45.6           | 23.0       |
| Small ($10K–$50K)      | 25.7      | 39.7           | 34.6       |
| Medium ($50K–$200K)    | 18.6      | 28.1           | 53.3       |
| Large ($200K–$1M)      | 17.1      | 26.4           | 56.5       |
| Enterprise ($1M+)       | 13.8      | 22.4           | 63.7       |

**Note:** Large tier: PDF p.9 showed 26.4, 56.5, 17.1 (column order ambiguous). Table here uses Loser 17.1%, Mid-range 26.4%, Winner 56.5% so winner % increases with tier (Medium 53.3%, Large 56.5%, Enterprise 63.7%). See SOURCE_MAP.md Open Questions.

---

## CH-007: Average weekly testing volume by vertical and spend tier (heatmap)

**Structure:** Rows = industry vertical (brand category); columns = spend tier. Cell = median or mean creatives per week. Vertical list from PDF: Health & Wellness, Other, Finance, Education, Beauty & Personal Care, Home & Lifestyle, Automotive, Professional Services, Technology, Fitness & Sports, Fashion & Apparel, Food & Nutrition, Entertainment & Media, Travel & Hospitality, Parenting & Family, Pets.

**Sample values (from PDF p.10):** Micro column ~2–3; Small ~3–5; Medium ~6–12; Large ~9–19; Enterprise ~14–46 (varies by vertical). Exact cell-by-cell table not fully reconstructed from OCR; notebook can regenerate with same suppression (verticals with <50 accounts → “Other”). See SOURCE_MAP.md#CH-007.

**Abridged reference table (illustrative):**

| Vertical (example)   | Micro | Small | Medium | Large | Enterprise |
|----------------------|-------|-------|--------|-------|------------|
| Health & Wellness    | 3     | 4     | 11     | 19    | 46         |
| Fashion & Apparel    | 3     | 5     | 12     | 18    | 33         |
| Beauty & Personal Care | 3   | 4     | 8      | 15    | 26         |
| Other                | 2     | 3     | 8      | 14    | 14         |

*(Other cells and verticals in PDF; apply MIN_ACCOUNTS_FOR_BRAND_CATEGORY = 50 for “Other” remapping.)*

---

## CH-008: Top 25% vs all accounts — creative volume and winners per month by spend tier

| Spend tier         | All accounts creative vol | Top 25% creative vol | All accounts winners/mo | Top 25% winners/mo |
|--------------------|----------------------------|----------------------|--------------------------|---------------------|
| Micro (<$10K)      | 2.8                        | 4.8                  | 0.0                      | 0.0                 |
| Small ($10K–$50K)  | 4.1                        | 8.0                  | 0.2                      | 0.5                 |
| Medium ($50K–$200K)| 6.6                        | 15.9                 | 0.7                      | 2.0                 |
| Large ($200K–$1M)  | 11.2                       | 31.1                 | 1.7                      | 5.9                 |
| Enterprise ($1M+)   | 18.8                       | 54.6                 | 3.9                      | 10.4                |

**Definitions:** Top 25% = accounts with winner count in the top quartile within that spend tier.

---

## CH-009: Top visual styles — hit rate and spend use ratio

**Hit rate (top formats, from PDF):** Offer-First Banner, Demo, Testimonial, Headline, Montage, Before & After, Listicle, Split Screen, Us vs Them, Unboxing, Feature benefit point, Cinematic b-roll, Grid swap, Screen recording, Problem agitation, Review, How-to, POV, Behind the scene, Founder, Statistic, Influencer endorsement, Collage, Static to video hybrid, Expert explained (with hit rates roughly 5–9% band). **Spend use ratio (top):** Celebrity, Letter, Unconventional text placement, Post-it, Offer-first banner, Unboxing, etc. (ratio band ~0.9–2.1).

**Suppression:** Segments with <50 accounts excluded (MIN_ACCOUNTS_FOR_FORMAT). Full leaderboard in notebook; below is a condensed list consistent with PDF narrative.

| Visual format (sample)   | Winners (count) | Mid-range (count) | Hit rate (%) | % Creative | % Spend | Spend use ratio |
|-------------------------|------------------|-------------------|--------------|------------|---------|-----------------|
| Offer-First Banner      | 1100             | 3944              | 8.6          | 21.9       | 29.3    | 1.3             |
| Demo                    | 556              | 2855              | 8.1          | 12.6       | 12.9    | 1.0             |
| Testimonial             | 507              | 3051              | 6.5          | 13.3       | 13.3    | 1.0             |
| Unboxing                | 136              | 820               | 9.8          | 2.1        | 2.8     | 1.3             |
| Celebrity               | 58               | 335               | 5.9          | 0.8        | 1.8     | 2.1             |

*(Additional rows in PDF/notebook; only segments with ≥50 accounts.)*

---

## CH-010: Top visual styles by vertical

**Structure:** For each vertical, two leaderboards: (1) top visual formats by hit rate (%); (2) top visual formats by spend use ratio. Verticals include Health & Wellness, Fashion & Apparel, Home & Lifestyle, Technology, Beauty & Personal Care, Food & Nutrition, Pets, Education, Other, Fitness & Sports, Entertainment & Media, Finance, Travel & Hospitality, Professional Services, Automotive, Parenting & Family.

**Sample (Health & Wellness, from PDF):** Hit rate top: Stitch, Reaction video, Unboxing, Celebrity, Founder, Letter, Stop motion, Influencer endorsement, POV, Transformation. Spend use: Social post mockup, Letter, Celebrity, Case study, Offer-first banner, Behind the scene, UGC overlay, Founder, Transformation, Billboard.

**Sample (Fashion & Apparel):** Hit rate: Post-it, Quiz, Stylized product shot, Meme, ASM, Product shot, Social comment, Podcast, Product showcase, Unconventional text placement. Spend use: Podcast, Unconventional text placement, Billboard, Text message, Sign, Celebrity, Slideshow, Post-it, Offer-first banner, Demo.

*(Full per-vertical tables in PDF pp.15–20; same MIN_ACCOUNTS_FOR_FORMAT applied. Not all vertical×format cells may meet 50-account threshold; those excluded in notebook.)*

---

## CH-011: Top hooks & headlines — hit rate and spend use ratio

**Hit rate (sample, from PDF):** Newness, Sale announcement, Price anchor, Urgency, Announcement, Offer only, FOMO, New product announcement, Confession, Exclusivity, Curiosity, Giveaway, Event announcement, Bold claim, Reverse psychology, Shocking statement, If then, Warning, Wordplay, Contrarian, Relatability, Contrast, Direct address, Product announcement, Authority (hit rates roughly 6–11%). **Spend use ratio (sample):** Giveaway, Price anchor, Announcement, Event announcement, Offer only, Confession, Urgency, Curiosity, FOMO, Wordplay, Contrast, Myth busting, Call to action first, Contrarian, Exclusivity, If then, Warning, Shocking statement, Authority, Product announcement, Sale announcement, Bold claim, Direct address, Storytelling, Reasons why (ratios ~0.9–2.2).

**Suppression:** Hook/headline segments with <50 accounts excluded. See SOURCE_MAP.md#CH-011.

---

## CH-012: Top asset types — hit rate and spend use ratio

**Hit rate (sample, from PDF):** Text only, Product image with text, Lifestyle-product image, UGC, High production, GIF, Illustration, UGC mashup, Lifestyle-product image with text, Lifestyle image with text, Lifestyle image, Hybrid, Product image, Animation, Carousel (hit rates roughly 4–12%). **Spend use ratio:** Text only, Product image with text, Illustration, UGC, Lifestyle-product image with text, Lifestyle image with text, UGC mashup, Hybrid, Product image, High production, GIF, Lifestyle image, Lifestyle-product image, Animation, Carousel (ratios ~0.5–1.9).

**Suppression:** Asset type segments with <50 accounts excluded. See SOURCE_MAP.md#CH-012.

---

## Methodology summary (Key Benchmarks & Insights Summary, PDF p.24)

- **Creative volume by spend tier (median creatives/week; mean; avg hit rate):** Micro 2.3, 3.4, 4.0; Small 4, 5.6, 6.5; Medium 6.9, 9, 8.1; Large 11.1, 16.8, 8.6; Enterprise 18.2, 29.8, 8.8.
- **10× benchmark:** ~92.3rd percentile of ratio (≈8% of creatives above 10×).
- **Creative longevity:** Mid-range = 28+ days, not winner; Loser = turned off before 28 days. ~50–53% losers; ~38–46% mid-range; ~4–8% winners by tier.
- **Top accounts:** Top 25% of accounts within each spend tier by winner count have higher creative volume than tier median.

All figures aggregated; no advertiser or creative identifiers.
