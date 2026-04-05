---
title: "Creative Benchmarks 2026 — LLM Edition"
source: "Motion Creative Benchmarks 2026 (final PDF + notebook artifacts)"
inputs:
  pdf_path: "./benchmarks/Benchmarks-Report-2026.pdf"
  notebook_path: "benchmarks/benchmark_2025_4_final.ipynb"
  readme_path: "benchmarks/README.md"
privacy:
  dataset_name: "metrics_tagged_creatives_20260130"
  policy: "Aggregated, anonymous; no advertiser- or creative-identifying outputs"
  suppression_source: "Use the suppression rules as defined in the analysis notebook (do not invent new thresholds)."
data_window:
  start: "2025-09-01"
  end: "2026-01-01"
dataset:
  creatives: 578750
  advertiser_accounts: 6015
  realized_spend_usd: 1290000000
definitions:
  winner:
    spend_multiple_of_account_median: 10
    spend_floor_usd: 500
  mid_range:
    min_days_with_spend: 28
    not_winner: true
  loser:
    turned_off_before_day: 28
spend_tiers:
  - name: "Micro (<$10K)"
    monthly_spend: "<$10,000"
  - name: "Small ($10K–$50K)"
    monthly_spend: "$10,000–$50,000"
  - name: "Medium ($50K–$200K)"
    monthly_spend: "$50,000–$200,000"
  - name: "Large ($200K–$1M)"
    monthly_spend: "$200,000–$1,000,000"
  - name: "Enterprise ($1M+)"
    monthly_spend: "$1,000,000+"
---

# Creative Benchmarks 2026 — LLM Edition

## Table of Contents

1. [Introduction](#introduction)
2. [Key Findings](#key-findings)
3. [Part 1: The Search for Winners](#part-1-the-search-for-winners)
4. [Part 2: The Anatomy of Winning Ads](#part-2-the-anatomy-of-winning-ads)
5. [Methodology & Definitions](#methodology--definitions)
6. [Glossary](#glossary)
7. [How to Use This with an LLM/Agent (Without Misusing It)](#how-to-use-this-with-an-llmagent-without-misusing-it)
8. [Verification](#verification)

---

## Introduction

This report examines what over **$1.3 billion** in ad spend reveals about performance, probability, and creative success. It is based on an anonymized dataset of **550,000+ ads** launched by **6,000+ advertisers**, representing roughly **$1.3 billion** in spend across Facebook and Instagram between **September 2025** and early **January 2026**.

The window spans one of the most competitive promotion cycles of the year: pre-holiday testing, Black Friday and Cyber Monday (BFCM), and the post-holiday reset. Creative turnover is high; competition for attention is higher. The analysis focuses on **spend, outliers (winners), and hit rate** for apples-to-apples comparison. It does **not** tie outcomes to ROAS, revenue, or conversion.

**What this means:** The report is designed for brands that want to see more high-spend “winner” creatives. All data is aggregated and anonymous. No advertiser, campaign, or creative is identifiable.

Source: SOURCE_MAP.md#KF-001

---

## Key Findings

### KF-001: Winning ads are rare

Only a small share of ads — roughly **five percent** — spend at least **10× their account median**. Low hit rates are not necessarily a sign of weak creative; they are a statistical feature of how performance advertising works.

Source: SOURCE_MAP.md#KF-001

### KF-002: Scale changes frequency, not fundamentals

Larger advertisers surface more winning ads because they introduce more variation into the system. Smaller advertisers are not excluded from getting winners but get them less often.

Source: SOURCE_MAP.md#KF-002

### KF-003: Trends are not universal

The most popular ad formats are not always the ones that capture the most spend. Performance shifts with context — scale, industry, timing, and saturation.

Source: SOURCE_MAP.md#KF-003

### KF-004: Spend concentration

- ~**55%** of total spend goes to winning ads; ~**28%** to mid-range; ~**17%** to losing ads.
- Share of spend on winners rises by tier: Micro ~**23%** → Enterprise ~**64%**.
- ~**4–8%** of creatives are winners by tier (Micro ~3.8%, Enterprise ~8.2%); **38–46%** are mid-range; ~**50–53%** are losers (turned off before 28 days).

Source: SOURCE_MAP.md#KF-004

### KF-005: 10× benchmark

The 10× winner threshold corresponds to approximately the **92.3rd percentile** of the ratio-to-median distribution (i.e. about **7.7%** of creatives above 10×). Do not expect more than about **1 in 10–13** creatives to be winners on average.

Source: SOURCE_MAP.md#KF-005

---

## Part 1: The Search for Winners

### Creative volume is a structural advantage

Across industries and budget sizes, one pattern is consistent: advertisers that launch more ads get more winners. This does not mean they are better at predicting what will work; it means they run more tests in an environment where wins are rare.

Ad performance on Meta behaves like probability: roughly half of all ads receive little or no spend, while about **6%** of ads are responsible for the majority of spend in any given account. Each new ad is another chance to find a standout. What separates stronger advertisers is how their testing cadence works — they create enough new ideas to give wins a chance to appear.

**What this means:** Volume helps because it creates more opportunities to get winners. It does not make the average ad better; it increases how often an advertiser runs into something exceptional.

Source: SOURCE_MAP.md#CH-001

---

#### Chart: Relationship between weekly ad volume and number of winning creatives

Chart ID: CH-001  
What it shows: Scatter of testing volume (ads launched per week) vs winner count across advertisers. Winners become more common as volume rises.  
Key takeaways:
- More creatives per week is associated with more winning creatives.
- The relationship holds even when comparing advertisers with similar budgets.

Data table (extracted, privacy-safe): See LLM_DATA_APPENDIX.md#CH-001.  
Definitions/notes: Creative volume = unique creatives launched per week (per account). Winner = ≥10× account median spend and ≥$500.  
Source: SOURCE_MAP.md#CH-001

---

### Winners are rare — and that’s okay

If performance were evenly spread, improving results would mostly be about optimization. The data shows that is not how it works: most ads don’t spend or spend very little, while a small number of ads receive far more spend than the rest. This is not just a holiday effect or a sign of bad creative decisions; it is how performance advertising behaves.

In this report, a **winner** is defined strictly: an ad must spend at least **10×** more than the account’s median ad (and at least **$500**) to be classified as a winner. As accounts get larger, the bar gets higher in absolute terms.

**What this means:** When results are inconsistent, it does not always mean an ad that doesn’t spend is “weak.” Advertisers are better off asking why an ad worked than why it didn’t. Understanding winners has greater impact than interrogating “losing” ads.

Source: SOURCE_MAP.md#CH-002, SOURCE_MAP.md#CH-003

---

#### Chart: Spend concentration (spend per ad distribution)

Chart ID: CH-002  
What it shows: Distribution of spend per ad across the dataset. Spend concentrates heavily among a small share of ads.  
Key takeaways:
- A small fraction of creatives capture the majority of spend.
- p90 spend per ad and total number of ads are represented in the distribution.

Data table (extracted, privacy-safe): See LLM_DATA_APPENDIX.md#CH-002.  
Definitions/notes: Histogram-style distribution; exact bins in appendix.  
Source: SOURCE_MAP.md#CH-002

---

#### Chart: Spend tier — average testing volume and average hit rate

Chart ID: CH-003  
What it shows: By spend tier (monthly ad spend), average testing volume per week and average hit rate as a percentage.  
Key takeaways:
- Testing volume and hit rate both rise with spend tier.
- Enterprise advertisers show the highest volume and hit rate.

Data table (extracted, privacy-safe):

| Spend tier (per month)     | Average testing volume (per week) | Average hit rate (%) |
|----------------------------|-----------------------------------|------------------------|
| Micro (<$10K)               | 2.8                               | 4.0                   |
| Small ($10K–$50K)          | 4.1                               | 6.4                   |
| Medium ($50K–$200K)        | 6.6                               | 8.1                   |
| Large ($200K–$1M)          | 11.2                              | 8.6                   |
| Enterprise ($1M+)           | 18.8                              | 8.8                   |

Definitions/notes: Hit rate = (winner creatives ÷ total creatives) × 100 at account level; unweighted.  
Source: SOURCE_MAP.md#CH-003

---

### Why hit rate can be misleading

Hit rate is often used as a scorecard for creative strategists. A high hit rate can look like proof that a marketer knows what will work. But high hit rates may actually signal that someone is not testing enough to maximize their account’s potential.

Two accounts can have the same hit rate but work very differently: one might launch only a few ads and put most spend behind them; another might test many ads and find a few strong outliers. Hit rates are likely to look lower for the latter despite more testing. So high hit rates need context — they could mean strong judgment or limited testing. Lower hit rates often appear in accounts that test more ideas.

**What this means:** Hit rate is valuable but not a proxy for performance success or efficiency. It tells us how often rare events happen within a certain ad set.

Source: SOURCE_MAP.md#CH-004

---

#### Chart: Hit rate explanation (hypothetical Account A vs Account B)

Chart ID: CH-004  
What it shows: Illustrative comparison of two hypothetical accounts. Account A: 50 launches, 5 winners, hit rate 10%. Account B: 5 launches, 1 winner, hit rate 20%. Same hit rate, different testing behavior.  
Key takeaways:
- Hit rate alone does not distinguish “testing a lot with some winners” from “testing little with one winner.”
- Context (volume, spend allocation) is required to interpret hit rate.

Data table (extracted, privacy-safe): Hypothetical only; no real account data. See LLM_DATA_APPENDIX.md#CH-004.  
Definitions/notes: Example is hypothetical; no identifying information.  
Source: SOURCE_MAP.md#CH-004

---

### Mid-range spenders and portfolio logic

Between winning ads and losing ads sits a third group: **mid-range spenders**. These ads are not big outliers and never become winners, but they keep running, receive steady spend, and in many accounts quietly support day-to-day performance. The charts below show how creatives are split between losers, mid-range, and winners, and how spend is distributed across these groups.

**What this means:** Mid-range ads help keep results stable. Treating them as “second-best” or failed tests is a mistake; in a healthy account they connect testing and scaling.

Source: SOURCE_MAP.md#CH-005, SOURCE_MAP.md#CH-006

---

#### Chart: Portfolio breakdown — % of creatives that are losers, mid-range, winners by spend tier

Chart ID: CH-005  
What it shows: Percentage breakdown of losing ads, mid-range spenders, and winners by monthly ad spend tier.  
Key takeaways:
- Winners make up a small share of portfolios (roughly 4–8% by tier); mid-range and losers make up the majority.
- Mid-range is consistently a large share (about 38–46%); losers about 50–53%.

Data table (extracted, privacy-safe):

| Spend tier            | Loser (%) | Mid-range (%) | Winner (%) |
|-----------------------|-----------|----------------|------------|
| Micro (<$10K)          | 50.2      | 46.0          | 3.7        |
| Small ($10K–$50K)      | 49.3      | 44.6          | 6.2        |
| Medium ($50K–$200K)    | 52.6      | 40.1          | 7.3        |
| Large ($200K–$1M)      | 53.9      | 38.0          | 8.1        |
| Enterprise ($1M+)       | 52.2      | 39.6          | 8.2        |

Definitions/notes: Loser = turned off before 28 days. Mid-range = ≥28 days spend, not winner. Winner = ≥10× median and ≥$500.  
Source: SOURCE_MAP.md#CH-005

---

#### Chart: Spend allocation — % of spend to losers, mid-range, winners by spend tier

Chart ID: CH-006  
What it shows: Percentage of spend going to losing ads, mid-range spenders, and winners by spend tier.  
Key takeaways:
- Spend shifts toward winners as accounts grow. Micro: ~23% to winners; Enterprise: ~64% to winners.
- Mid-range still carries meaningful proportion of spend, especially in smaller accounts.

Data table (extracted, privacy-safe):

| Spend tier            | Loser (%) | Mid-range (%) | Winner (%) |
|-----------------------|-----------|----------------|------------|
| Micro (<$10K)          | 31.5      | 45.6          | 23.0       |
| Small ($10K–$50K)      | 25.7      | 39.7          | 34.6       |
| Medium ($50K–$200K)    | 18.6      | 28.1          | 53.3       |
| Large ($200K–$1M)      | 17.1      | 26.4          | 56.5       |
| Enterprise ($1M+)      | 13.8      | 22.4          | 63.7       |

Definitions/notes: Percentages of total spend within tier. Large tier: column order inferred from narrative (spend shifts toward winners as tier increases); PDF p.9 raw order differed—see SOURCE_MAP.md.  
Source: SOURCE_MAP.md#CH-006

---

### How many ads should you be testing?

There is no universal “best” testing volume for all advertisers. The right volume depends on budget, team size, and how quickly an advertiser can produce new ideas. Below are median testing volumes by vertical and by spend tier.

Source: SOURCE_MAP.md#CH-007

---

#### Chart: Average weekly testing volume by industry vertical and spend tier (heatmap)

Chart ID: CH-007  
What it shows: Heatmap of median (or average) creatives per week by industry vertical (rows) and spend tier (columns).  
Key takeaways:
- Creative output varies widely; larger spend tiers generally show higher testing volume.
- Vertical differences exist; no single number applies to all.

Data table (extracted, privacy-safe): See LLM_DATA_APPENDIX.md#CH-007.  
Definitions/notes: Vertical = brand category (e.g. Health & Wellness, Fashion & Apparel). Suppression: verticals with &lt;50 accounts remapped to “Other” per notebook.  
Source: SOURCE_MAP.md#CH-007

---

### Top advertisers consistently ship more creative than average

Creative volume rises with scale. Within each spend tier, top advertisers (top 25% by winner count within tier) ship materially more creative than the tier average. For smaller advertisers, testing a few ads per week or month may be enough to get winners; for mid-market or growth-stage brands, that level of output is unlikely to produce enough surface area to generate as many winners as they could. At larger scales, conservative testing virtually guarantees that winners will be rare.

**What this means:** The most useful question is: are we shipping enough ads to make winners possible? Creative strategy should be seen as capacity planning as much as optimization.

Source: SOURCE_MAP.md#CH-008

---

#### Chart: Top 25% vs all accounts — creative volume and winners per month by spend tier

Chart ID: CH-008  
What it shows: By spend tier: all accounts’ creative volume and winners/month vs top 25% of accounts (by winner count within tier).  
Key takeaways:
- Top 25% within each tier have higher creative volume and more winners per month.
- Gap is not marginal; top advertisers ship significantly more.

Data table (extracted, privacy-safe):

| Spend tier        | All accounts creative vol | Top 25% creative vol | All accounts winners/mo | Top 25% winners/mo |
|-------------------|----------------------------|----------------------|--------------------------|---------------------|
| Micro (<$10K)     | 2.8                        | 4.8                  | 0.0                      | 0.0                 |
| Small ($10K–$50K) | 4.1                        | 8.0                  | 0.2                      | 0.5                 |
| Medium ($50K–$200K)| 6.6                       | 15.9                 | 0.7                      | 2.0                 |
| Large ($200K–$1M) | 11.2                       | 31.1                 | 1.7                      | 5.9                 |
| Enterprise ($1M+)  | 18.8                       | 54.6                 | 3.9                      | 10.4                |

Definitions/notes: Top 25% = accounts with winnerPercentileInTier ≥ 0.75 within each spend tier.  
Source: SOURCE_MAP.md#CH-008

---

## Part 2: The Anatomy of Winning Ads

### What types of ads should you be testing?

If ad performance works like probability, not all ads have the same odds of success. Some formats, hooks, and asset types become winners more often than others. Two measures used together describe these patterns: **hit rate** and **spend use ratio**.

- **Hit rate:** How often did this format (or hook/asset type) produce a winner?
- **Spend use ratio:** When we use this format, how likely is it to get spend? (A format’s share of total spend ÷ its share of total creative usage.)  
  - **&gt;1.0** → Format punches above its weight  
  - **≈1.0** → Performs as expected  
  - **&lt;1.0** → Overused relative to result  

These are not the same. A format may produce many winners but not spend much relative to use; another may rarely produce winners but receive a lot of consistent mid-range spend. Results are time-bound (e.g. BFCM, gifting season).

Source: SOURCE_MAP.md#CH-009

---

#### Chart: Top visual styles — hit rate and spend use ratio

Chart ID: CH-009  
What it shows: Leaderboards of visual formats by hit rate (%) and by spend use ratio.  
Key takeaways:
- Offer-first banners and demos appear prominently in both tables (scale formats).
- Some formats have high hit rate but lower spend use (e.g. unboxing, POV, behind the scenes, founder ads).
- High-volume formats that receive meaningful spend but become winners less often function as testing/coverage formats.

Data table (extracted, privacy-safe): See LLM_DATA_APPENDIX.md#CH-009.  
Definitions/notes: Only segments with ≥50 accounts (MIN_ACCOUNTS_FOR_FORMAT) per notebook.  
Source: SOURCE_MAP.md#CH-009

---

#### Chart: Top visual styles by vertical

Chart ID: CH-010  
What it shows: Hit rate and spend use ratio for visual formats broken out by vertical (e.g. Health & Wellness, Fashion & Apparel, Home & Lifestyle, Technology, Beauty & Personal Care, Food & Nutrition, Pets, Education, Other, Fitness & Sports, Entertainment & Media, Finance, Travel & Hospitality, Professional Services, Automotive, Parenting & Family).  
Key takeaways:
- Top visual styles differ by vertical; a format strong overall may perform well in one category and barely appear in others.

Data table (extracted, privacy-safe): See LLM_DATA_APPENDIX.md#CH-010.  
Definitions/notes: Same suppression (≥50 accounts) applied per segment where applicable.  
Source: SOURCE_MAP.md#CH-010

---

#### Chart: Top hooks & headlines — hit rate and spend use ratio

Chart ID: CH-011  
What it shows: Leaderboards of hook/headline tactics by hit rate and by spend use ratio.  
Key takeaways:
- Hooks that signal immediacy, clarity, or a concrete reason to act (price framing, offers, urgency, product newness) tend to surface often.
- Curiosity, confessional framing, bold claims, or unexpected statements can interrupt scrolling. Patterns are time-bound (BFCM/holidays).

Data table (extracted, privacy-safe): See LLM_DATA_APPENDIX.md#CH-011.  
Definitions/notes: Hook/headline tactic = coalesced hook and headline dimensions.  
Source: SOURCE_MAP.md#CH-011

---

#### Chart: Top asset types — hit rate and spend use ratio

Chart ID: CH-012  
What it shows: Leaderboards of asset types by hit rate and by spend use ratio.  
Key takeaways:
- Text-forward assets (text-only, product image with text, simple GIFs) appear among winners more often than many teams expect; strength is speed and clarity.
- Higher-production assets play a different role (credibility, quality) but are slower to change. The distinction is between assets that support fast learning and those that require longer cycles.

Data table (extracted, privacy-safe): See LLM_DATA_APPENDIX.md#CH-012.  
Definitions/notes: Same MIN_ACCOUNTS_FOR_FORMAT (50) applied.  
Source: SOURCE_MAP.md#CH-012

---

## Methodology & Definitions

- **Scope:** Creatives launched between **September 1, 2025** and **January 1, 2026**. End date is at least 28 days before the last available data point so all creatives have equal opportunity to be classified as mid-range (avoids end-of-window censoring).
- **Dataset:** 578,750 unique creatives; 6,015 advertiser accounts; **$1.29 billion** in realized spend. Window spans pre-holiday testing, BFCM, and post-holiday reset.
- **Spend as primary success metric:** Performance is evaluated using realized spend, not CTR, CPA, or ROAS. Spend reflects how budget is allocated within accounts. This allows consistent cross-account comparison; it does not mean spend perfectly captures business value.
- **Interpretation:** Definitions describe how creative performance is distributed. Winner classification indicates statistical rarity, not creative excellence in isolation. Hit rate reflects how often rare events occur, not how “good” a team’s ideas are.

Source: SOURCE_MAP.md#METHODOLOGY

---

## Glossary

| Term | Definition |
|------|------------|
| **Creative volume** | Number of unique creatives launched per week at the account level. Treated descriptively, not as a success metric. |
| **Winner (outlier)** | A creative with spend **≥10× the account median** and **≥$500**. Identifies ads that meaningfully outperform the account baseline. |
| **Mid-range creative** | Has **≥28 days** of spend and does **not** meet the winner threshold. Durable, scaled creatives that persist without reaching winner status. |
| **Loser** | Turned off (or never reached) before **28 days**; neither winner nor mid-range. |
| **Hit rate** | At account level: **(Winner creatives ÷ Total creatives) × 100**. Unless specified, hit rates are **unweighted** (each account counts equally). |
| **Spend tiers** | Accounts grouped by average monthly Meta spend: Micro (&lt;$10K), Small ($10K–$50K), Medium ($50K–$200K), Large ($200K–$1M), Enterprise ($1M+). |
| **Spend use ratio** | A format’s share of total spend ÷ its share of total creative usage. &gt;1.0 = punches above weight; ≈1.0 = as expected; &lt;1.0 = overused relative to result. |
| **Top accounts** | Within each spend tier, the **top 25%** of accounts by winner count. |

---

## How to Use This with an LLM/Agent (Without Misusing It)

### Causal claims

- Findings are **associations** (e.g. higher spend with higher hit rate), not proof that changing spend *causes* a change in hit rate.
- Do not claim that “testing more creatives per week causes more winners” in a causal sense. Prefer: “Accounts that spend more tend to have higher hit rates” / “More testing volume is associated with more winners.”

### What the metrics can and cannot support

- **Can:** Compare your account’s testing volume, hit rate, and format mix to these benchmarks. Use tier-level and vertical-level tables to see where you sit relative to aggregated peers.
- **Cannot:** Infer ROAS, revenue, or conversion impact; attribute success to a single format or hook in a causal way; or re-identify any advertiser or creative.

### Safe example prompts (no new results)

- “What is the average hit rate for Medium spend tier in this report?”
- “How is spend allocated between winners, mid-range, and losers for Enterprise accounts?”
- “Which visual formats have the highest spend use ratio in the report?”
- “What is the definition of a winner in Creative Benchmarks 2026?”

### Privacy note

This report is **aggregated and anonymous**. Do not attempt to re-identify any advertiser, account, campaign, or creative from the tables or narrative. No row-level or advertiser-identifying information is included by design.

---

## Verification

- **Accuracy checklist:** Every number in this report appears in LLM_DATA_APPENDIX.md or is directly quoted from the PDF with page reference in SOURCE_MAP.md. Spend tiers, date range, dataset size, and definitions match the methodology. All charts/tables in the PDF are represented.
- **Privacy checklist:** No advertiser names, brands, domains, URLs, or IDs. No row-level examples; only aggregates. No new cross-tabs beyond the public PDF. Tables follow the notebook’s suppression logic (see SOURCE_MAP.md#SUPPRESSION_RULES). Redactions (if any) documented in SOURCE_MAP.md.

**Open Questions / Unresolved conflicts:** See SOURCE_MAP.md (CH-006 Large tier: column order inferred for narrative consistency; CH-002/CH-001: no point-level or bin-level data by design).

✅ Verification complete
