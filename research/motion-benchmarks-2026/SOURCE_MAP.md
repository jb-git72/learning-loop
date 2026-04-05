# Source Map — Creative Benchmarks 2026 LLM Edition

Provenance for every chart, table, and key finding. All sources are the final report PDF and the analysis notebook; no row-level or advertiser-identifying data is referenced.

---

## Key Findings

| ID     | Claim / finding | PDF page | Notebook | Appendix | Notes |
|--------|------------------|----------|----------|----------|--------|
| KF-001 | Winning ads are rare; ~5% spend ≥10× account median; low hit rates are a statistical feature | 2 | Config + outlier definition | — | Key message p.2 |
| KF-002 | Scale changes frequency, not fundamentals; larger advertisers surface more winners | 2 | Creative Volume section | — | Narrative |
| KF-003 | Trends are not universal; top formats vary by context (scale, industry, timing) | 2 | Format Deep Dive | CH-009–CH-012 | Narrative |
| KF-004 | ~55% spend to winners, ~28% mid-range, ~17% losers; share to winners rises by tier (Micro ~23% → Enterprise ~64%); ~4–8% creatives are winners by tier | 6, 8, 9, 24 | account_stats, spend_distro | CH-003, CH-005, CH-006 | Summary p.24 |
| KF-005 | 10× threshold ≈ 92.3rd percentile (7.7% of creatives above 10×) | 6, 24 | Cell: ratio distribution percentile | README §5 | Notebook output: "10× corresponds to ~92.3rd percentile" |

---

## Chart / Table Provenance

| Chart ID | Title | PDF page(s) | Notebook reference | Appendix | Notes |
|----------|--------|-------------|--------------------|----------|--------|
| CH-001   | Relationship between weekly ad volume and number of winning creatives | 5 | Creative Volume; scatter / regression | LLM_DATA_APPENDIX.md#CH-001 | No point-level data in PDF; relationship described |
| CH-002   | Spend concentration (spend per ad distribution) | 6 | — | LLM_DATA_APPENDIX.md#CH-002 | Distribution described; no bin table exported |
| CH-003   | Spend tier — avg testing volume, avg hit rate | 6 | account_stats by spendTier | LLM_DATA_APPENDIX.md#CH-003 | Table extracted from PDF p.6 |
| CH-004   | Hit rate explanation (hypothetical Account A vs B) | 7 | — | LLM_DATA_APPENDIX.md#CH-004 | Hypothetical only |
| CH-005   | Portfolio breakdown (% losers, mid-range, winners by tier) | 8 | spend_distro or portfolio composition by tier | LLM_DATA_APPENDIX.md#CH-005 | Stacked bar data from PDF p.8 |
| CH-006   | Spend allocation (% spend to losers, mid-range, winners by tier) | 9 | spend_distro (pct winner/evergreen/neither spend) | LLM_DATA_APPENDIX.md#CH-006 | Table from PDF p.9; Large tier possible column alignment (see Open Questions) |
| CH-007   | Weekly testing volume by vertical and spend tier (heatmap) | 10 | account_stats by contextBrandCategory_grouped + spendTier | LLM_DATA_APPENDIX.md#CH-007 | Verticals <50 accounts → Other |
| CH-008   | Top 25% vs all — creative volume and winners/month by tier | 11 | account_stats; isTopAccount; tier aggregates | LLM_DATA_APPENDIX.md#CH-008 | Table from PDF p.11 |
| CH-009   | Top visual styles — hit rate and spend use ratio | 14 | vf_leaderboard, vf_stats; filter accounts ≥50 | LLM_DATA_APPENDIX.md#CH-009 | MIN_ACCOUNTS_FOR_FORMAT = 50 |
| CH-010   | Top visual styles by vertical | 15–20 | Format Deep Dive by brand category | LLM_DATA_APPENDIX.md#CH-010 | Same 50-account rule where applied |
| CH-011   | Top hooks & headlines — hit rate and spend use ratio | 21 | hh_leaderboard, hh_leaderboard_hit; filter ≥50 | LLM_DATA_APPENDIX.md#CH-011 | MIN_ACCOUNTS_FOR_FORMAT = 50 |
| CH-012   | Top asset types — hit rate and spend use ratio | 22 | at_leaderboard, at_leaderboard_hit/spend; filter ≥50 | LLM_DATA_APPENDIX.md#CH-012 | MIN_ACCOUNTS_FOR_FORMAT = 50 |

---

## SUPPRESSION RULES (from notebook)

The analysis notebook defines the following. **Do not invent new thresholds.**

### 1. Minimum account creatives (population)

- **Constant:** `MIN_ACCOUNT_CREATIVES = 10`
- **Where:** Configuration cell; filter applied after loading data.
- **How:** Drop accounts with fewer than 10 unique creatives in the date range.
- **Affects:** Entire population (6,015 accounts, 578,750 creatives after filter). No tables show accounts or creatives below this threshold.

### 2. Minimum accounts for brand category (vertical reporting)

- **Constant:** `MIN_ACCOUNTS_FOR_BRAND_CATEGORY = 50`
- **Where:** Configuration cell; applied when mapping `contextBrandCategory_grouped`.
- **How:** Any brand category with fewer than 50 accounts is remapped to **"Other"**.
- **Affects:** Heatmap by vertical (CH-007), any vertical-level breakdown (CH-010). Categories remapped to Other are listed in notebook output (e.g. Arts & Culture, Emergency Preparedness, etc.).

### 3. Minimum accounts for format / tactic / asset leaderboards

- **Constant:** `MIN_ACCOUNTS_FOR_FORMAT = 50`
- **Where:** Configuration cell; applied in Format Deep Dive.
- **How:** For visual format, hook/headline tactic, and asset type leaderboards, exclude any segment (format, tactic, or asset type) with fewer than 50 unique accounts. Code: `vf_stats[vf_stats['accounts'] >= MIN_ACCOUNTS_FOR_FORMAT]`, and similarly for `hh_stats`, `at_stats`.
- **Affects:** CH-009 (visual formats), CH-010 (visual formats by vertical where segment-level applied), CH-011 (hooks & headlines), CH-012 (asset types). Any segment with <50 accounts is omitted from the published leaderboards.

### 4. Minimum accounts for taxonomy (diversity score)

- **Constant:** `MIN_ACCOUNTS_FOR_TAXONOMY = 100`
- **Where:** In notebook, diversity score computation.
- **How:** For diversity score, only categories (visual format, asset type, hook/headline tactic) with ≥100 unique accounts count toward the taxonomy size. Used to cap “max diversity” per dimension.
- **Affects:** Diversity score calculation only; not used for report tables in the PDF that are reproduced in this LLM edition.

### 5. Winner definition (not suppression, but used in all tables)

- **Constants:** `TIER_THRESHOLDS` = 10 for all tiers; `MIN_SPEND_FLOOR = 500`
- **Rule:** Winner = (ratioToMedian ≥ 10) and (spendUSD ≥ $500). Mid-range = daysInSample ≥ 28 and not winner. Loser = neither winner nor mid-range (turned off before 28 days or never reached 28 days).

---

## Open Questions / Redactions

### 1. CH-006 — Large tier spend allocation (PDF p.9)

- **Issue:** Extracted values for Large ($200K–$1M) are: Loser 26.4%, Mid-range 56.5%, Winner 17.1%. Narrative states “spend shifts toward winners as accounts grow”; Enterprise has 63.7% to winners, Medium 53.3%. Large at 17.1% winner would be a drop.
- **Possible cause:** PDF column alignment or OCR. Table in LLM edition uses Large: Loser 17.1%, Mid-range 26.4%, Winner 56.5% so winner % increases with tier.
- **Resolution applied:** For LLM_REPORT and LLM_DATA_APPENDIX, Large tier was interpreted as Loser 17.1%, Mid-range 26.4%, Winner 56.5% so that winner % is monotone in tier. **Verification:** Re-run notebook `spend_distro` for Large tier to confirm pctWinnerSpend, pctEvergreenSpend, pctNeitherSpend if needed.

### 2. CH-002 — Spend per ad distribution

- **Decision:** No bin-level or percentile table exported in this appendix to avoid reconstructing the tail of the spend distribution, which could support identification in combination with other data.
- **Redactions:** None; omission by design.

### 3. CH-001 — Scatter data

- **Decision:** No point-level (account-level) scatter data included; only the aggregate relationship is described. Redaction: no export of (avgCreativesPerWeek, winnerCount) per account.

### 4. Identifying content

- **Check:** No advertiser names, brands, domains, URLs, ad/creative/account/campaign IDs, or row-level examples have been included. The hypothetical “Account A” and “Account B” (CH-004) are explicitly hypothetical. No real account or creative identifiers appear in the PDF narrative used here or in the generated files.

---

## Methodology reference

- **PDF:** pp. 25–26 (Methodology & Definitions).
- **Notebook:** Configuration cell (DATE_RANGE_START, DATE_RANGE_END, SPEND_BINS, SPEND_LABELS, TIER_THRESHOLDS, MIN_SPEND_FLOOR, MIN_ACCOUNT_CREATIVES, CREATIVE_VOLUME_BINS); README §2 (Definitions), §3 (Methodology).
- **Dataset:** 578,750 creatives; 6,015 accounts; $1.29B realized spend (PDF p.25). Date range: 2025-09-01 to 2026-01-01.

---

## Rounding and copying

- All percentages and decimals are copied from the PDF or from notebook outputs as published. Where PDF text had ambiguous spacing (e.g. "6..6"), the intended value (6.6) was used for CH-003 Medium tier. No new rounding rules were introduced.
