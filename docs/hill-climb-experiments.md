# Hill-Climb Experiments — Ideas to Improve Performance

## Tested (Apr 5 2026)

### Wide population > deep iterations
- **Finding**: Pop=10 with 3 iterations outperforms pop=5 with 10 iterations for finding breakthroughs
- **Why**: Extra iterations are exploitation (polishing). Extra population is exploration (new hooks, angles, crossover). Breakthroughs come from diversity, not refinement
- **Evidence**: OR-201 jumped +0.103 in a single iteration via `mutate(story)` — no amount of iterating on the old hook would have found that

### Diversified slot allocation
- **Old**: 1 improve + 1 mutate + 1 targeted + N crossover (all extra slots were crossover)
- **New**: 1 improve + 3 mutate + 3 targeted + 2 crossover + 1 wildcard (pop=10)
- **Why**: 7 crossover slots from the same top-3 donor pool is redundant. Spreading across modes tests more hypotheses per round

### Strategy tracking
- Added JSON tracker logging every candidate attempt with mode, hook, scores, deltas, win/loss
- Enables post-run analysis of which modes and hooks produce the best results

## Speed — reducing total elapsed time

Current bottleneck analysis (20 ads, pop=10, 3 iterations):

```
For each iteration:                    SEQUENTIAL
  For each ad below target:            SEQUENTIAL
    For each candidate (pop=10):       SEQUENTIAL  ← biggest bottleneck
      generate_variant()               API call ~3-5s
      lint()                           local ~10ms
      score_ad()                       local ~50ms + LLM judge ~2-4s
```

Total: ~60-90 min. Almost all of it is waiting on sequential API calls.

### Tier 1: Parallelise candidates within an ad (biggest win)

All 10 candidates for a single ad are independent — different hooks, different modes. No shared state until the "pick winner" step at the end.

- Use `asyncio` with Anthropic's async client, or `concurrent.futures.ThreadPoolExecutor`
- Generate all 10 variants in parallel, lint in parallel, score in parallel
- **Expected speedup**: ~8-10x per ad. A 90-second ad becomes 10 seconds
- **Total run drops from ~70 min to ~7 min**
- Anthropic rate limits are the constraint — but 10 concurrent requests is well within tier limits

### Tier 2: Parallelise ads within an iteration

Ads within an iteration are mostly independent. The exception is crossover, which needs donor scores — but donors come from the *previous* iteration's results (already computed).

- Process all 20 ads concurrently within each iteration
- Batch size limited by API rate limits (~50 req/min on most tiers)
- With 10 candidates × 2 API calls = 20 calls per ad, processing 3-5 ads simultaneously keeps under rate limits
- **Expected speedup**: 3-5x on top of Tier 1
- **Total run drops from ~7 min to ~2 min**

### Tier 3: Remove delay between steps

- **Pre-build all candidate configs** before any API calls. Currently strategy selection (pick hooks, pick donors) is interleaved with generation. Separate planning from execution
- **Pipeline lint with generation** — start scoring the first candidate while the second is still generating
- **Pre-warm the scorer** — load client config, compile regexes, cache fact patterns once, not per-candidate

### Tier 4: Skip expensive work on obvious losers

- **Deterministic pre-screen**: Run the cheap rubric dims (local, ~50ms) before the expensive LLM judge (~3s). If deterministic score is already >0.1 below baseline, skip the LLM call
- **Early winner detection**: If a candidate beats baseline by >0.05, skip remaining low-probability candidates (wildcards, fallback mutations). Saves ~30% of API calls
- **Tradeoff**: Might miss a late-slot surprise. Could make this configurable

### Tier 5: Model selection

- Use Haiku for generation (faster, cheaper) and Opus only for LLM judge scoring
- Generation quality matters less when you have pop=10 — quantity of hypotheses > quality of each
- **Expected speedup**: 3-5x on generation calls (~1s vs ~4s per call)
- **Tradeoff**: Lower individual candidate quality, offset by higher throughput

### Combined estimate

| Change | Time reduction | Cumulative |
|--------|---------------|------------|
| Baseline (current) | — | ~70 min |
| Tier 1: Parallel candidates | ~10x | ~7 min |
| Tier 2: Parallel ads | ~3x | ~2.5 min |
| Tier 3: Pipeline/pre-warm | ~1.3x | ~2 min |
| Tier 4: Skip obvious losers | ~1.5x | ~1.3 min |
| Tier 5: Haiku for generation | ~2x | ~40 sec |

From overnight run to under a minute. Tier 1 alone gets 80% of the win.

## Not yet tested — quality improvements

### Remove target ceiling
- Currently `--target=0.90` stops iterating on ads that hit the threshold
- This leaves improvement on the table — a 0.91 ad might reach 0.95 with the right mutation
- **Experiment**: Run with `--target=1.0` so every ad gets all iterations regardless of score
- **Tradeoff**: Longer runtime (no ads drop out), but maximises peak scores

### Adaptive slot allocation
- Use the strategy tracker data to shift allocation mid-run
- If mutate is winning 3x more than crossover after iteration 1, give mutate more slots in iteration 2
- Bandit-style exploration/exploitation at the meta level

### Temperature scheduling
- Currently: improve=0.7, mutate=0.8, wildcard=0.9, targeted=0.5, crossover=0.6
- **Experiment**: Start hot (all 0.9) in iteration 1 for max diversity, cool down in later iterations
- Mimics simulated annealing — explore wide, then refine

### Hook-specific population
- Some hooks consistently underperform for certain angles (e.g., urgency + anti-insurance)
- **Experiment**: After iteration 1, eliminate hooks that scored >0.1 below baseline and replace with more slots for hooks that showed positive deltas
- Darwinian selection at the hook level, not just the ad level

### Parallel angle mutation
- Current system mutates hooks but keeps the angle fixed
- **Experiment**: Allow angle shifts too (e.g., an empathy ad mutating toward outcome-results)
- Risky — could lose brand coherence. But the scorer would catch that

### Cross-client crossover
- Currently crossover only blends from same-client ads
- **Experiment**: Use high-scoring farm-thru ad structures as donors for best-for-pet
- The structure/rhythm transfers even if the content doesn't. Story arcs are universal

### Ensemble scoring
- Run the same ad through the scorer 3 times, take the median
- LLM scoring has variance — a lucky/unlucky roll can accept or reject borderline candidates
- **Tradeoff**: 3x API cost for scoring. Only worth it for close decisions (delta < 0.02)

### Population decay
- Start with pop=10 in iteration 1, drop to pop=5 in iteration 2, pop=3 in iteration 3
- Front-loads exploration when it matters most, saves compute on refinement rounds
