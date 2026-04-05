# Learning Loop — Autonomous Ad Copy Scoring & Improvement Engine

Multi-client, multi-content-type scoring engine inspired by Karpathy's autoresearch.

## Architecture

- `engine/` — IMMUTABLE scorer (rule_checker, fact_checker, rubric_scorer, llm_judge, scorer)
- `shared/` — Universal rules, rubric schemas, content-type schemas
- `clients/{slug}/` — Client-specific config (rules, facts, tone, learnings)
- `writer.py` — MUTABLE variant generator (the agent modifies this)
- `program.md` — Agent instructions for autonomous overnight runs
- `run.py` — CLI entry point

## Quick start

```bash
# Score an ad
python3 run.py score --client best-for-pet --ad path/to/ad.json

# Score a batch
python3 run.py batch --client best-for-pet --ads path/to/ads.json

# Validate against human review data
python3 run.py validate --client best-for-pet --review path/to/review.json

# Start overnight loop
claude --dangerously-skip-permissions
# Then: "Read program.md and begin the experiment loop for client best-for-pet with tag apr3"
```

## Adding a new client

**Quick start (2 minutes):**
```bash
python3 scripts/onboard_client.py \
  --name "Brand Name" --slug brand-slug \
  --url https://brand.com \
  --product "One-line product description" \
  --industry grocery --market AU
```

This auto-generates all 5 files, validates them, and runs 3 test ads. Then hill-climb:
```bash
python3 scripts/hill_climb.py brand-slug 3
```

**Manual setup** — create `clients/{slug}/` with these files:
- `config.json` — entry point: weights, thresholds, CTAs, angles, scoring_context
- `rules.json` — client-specific rules (extends universal)
- `facts.json` — structured facts register
- `tone.md` — voice guidelines (prose, for LLM context)
- `learnings.md` — common rules (loaded for ALL content types, max 2000 chars)
- `learnings-meta-ad.md` — meta-ad specific patterns (max 2000 chars)
- `learnings-landing-page.md` — LP specific patterns (max 2000 chars)
- `learnings-email.md` — email specific patterns (max 2000 chars)

Zero code changes to the engine or writer.py. Everything is config-driven.

### New client checklist (follow in order — see LESSONS.md #8-9 for why)

1. **Verify facts before generating** — WebFetch the client website, verify every claim in facts.json. Mark confidence levels. NEVER fabricate stats.
2. **Learnings budget is sacred** — Each learnings file has a 2000-char hard limit. Every word competes for LLM attention. When adding a learning: (a) check if an existing one can be compressed or removed, (b) put it in the right file (common vs content-type), (c) run `python3 scripts/check_learnings.py {slug}` to verify. NEVER let learnings bloat — the LLM ignores rules in long files.
3. **Rules check ALL fields** — every rule must list ALL fields where a violation could appear. Don't omit `description` because you checked `primary_text`. Test: generate 3 sample ads, grep each field for the pattern.
4. **writer.py rules must not contradict learnings** — after editing `_build_rules_summary()`, grep for contradictions: `grep -i "add\|include\|must have" writer.py` vs `grep -i "never\|don't\|no " clients/{slug}/learnings.md`.
5. **Filter facts by content type** — if the client has content types with different rules (e.g., meta-ads vs landing pages), ensure `_select_relevant_facts()` excludes inappropriate fact categories per content type.
6. **Test regex triggers against real copy** — write 3 sample ads, run the scorer. Check for false positives (farming "raises" ≠ financial "raises"). Fix regexes before generating at scale.
7. **Integrate review feedback back** — after each human review round: (a) update learnings.md with new patterns, (b) apply per-ad decisions to content files, (c) verify critical feedback is within the 1600-char truncation window, (d) re-run scorer to confirm fixes land.
8. **Hill-climb to strong_draft+** — only present content scoring >= 0.70 composite. Zero "rewrite" items should reach the user.
9. **Add best-practice rules, not just compliance gates** — BFP's rules enforce what WORKS (e.g., "low_risk_trio_present"). Don't just block violations; encode approved patterns as rules too.

## API key

Store in `.env` (gitignored): `ANTHROPIC_API_KEY=sk-ant-...`
Auto-loaded by `run.py`.

## Scripts

- `scripts/score_batch.py` — Score all content in a client's loop dir, output JSON
- `scripts/hill_climb.py` — Generate-score-iterate loop to reach strong_draft+
- `scripts/build_review_html.py` — Build interactive HTML review (proven layout with editable textareas, toggle buttons, two-column, char counts, collapsible cards)
- `scripts/lint_content.py` — Pre-flight content linter (3 layers: rules, learnings, structural). Run before scoring to catch violations early
- `scripts/clean_meta_ads.py` — Clean investment language from meta-ad descriptions
- `scripts/onboard_client.py` — Onboard new client in ~2 min (generates all 5 files + validates)
- `scripts/verify_evolution.py` — Verify evolutionary vs greedy hill-climbing performance
- `scripts/figma_pipeline.py` — Figma API integration: inspect files, export PNGs, set up brand variables, prepare plugin input
- `figma-plugin/` — Figma plugin for injecting ad copy into template frames

## Workflow: calibration rounds

1. **Verify facts first** — WebFetch client website, update facts.json BEFORE generating
2. **Generate content** — Use writer.py or agents with full rules/facts/tone context
3. **Hill-climb to strong_draft+** — use evolutionary strategy for best results:
   ```bash
   python3 scripts/hill_climb.py {client} --iterations 5 --population 5 --strategy evolutionary
   ```
   This uses mutation, crossover, wildcard, and dimension-targeted modes. Crossover with top-scoring ads produces the biggest jumps.
4. **Build HTML review** — `python3 scripts/build_review_html.py scored.json output.html` — collapsible cards, toggle filters
5. **Present for human review** — Only after ALL items score >= 0.70 composite
6. **Integrate feedback** — Update learnings.md (What Works first!), re-run hill-climb

## Learnings architecture (IMPORTANT — read before modifying learnings)

Writer.py loads `learnings.md` (common) + `learnings-{content_type}.md` (type-specific) and passes BOTH to the LLM. There is NO truncation — every character in these files reaches the LLM. This means:

1. **Every word counts** — verbose learnings dilute the LLM's attention. Compress ruthlessly.
2. **2000 chars per file** — hard budget. Run `python3 scripts/check_learnings.py {slug}` after changes.
3. **Common vs type-specific** — put universal rules in `learnings.md`, content-type patterns in split files.
4. **Rules in config too** — `prompt_extra_rules` in config.json is ALWAYS loaded. Put formatting rules there (em dashes, char limits) and creative patterns in learnings.
5. **Scoring must match generation** — if the scorer enforces a rule, the learnings must mention it. If learnings say "never X", a scoring rule should penalize X. These must stay in sync.
6. **When integrating review feedback**: compress the feedback into 1-2 bullet points per pattern. Don't paste raw notes. Trim existing learnings that the new pattern supersedes.

If `check_learnings.py` fails, you MUST trim before committing. The LLM prompt is ~2300 tokens — learnings are ~30% of it. Bloated learnings = ignored rules.

## Git workflow

- **Always use worktrees** for code changes, new features, and scripts: `isolation: "worktree"` in Agent tool calls
- Worktrees give each agent its own branch and repo copy — no merge conflicts between parallel agents
- Main branch stays clean. Agents PR back to main when done.
- Max 2-3 parallel worktree sessions
- Add `.claude/worktrees/` to `.gitignore`

## Critical rules

- `engine/` files are IMMUTABLE — the writer agent cannot modify them
- Rules/facts are pass/fail GATES, not score contributors
- LLM scoring uses separate Haiku API call (no shared context with writer)
- Every number in ad copy must trace to facts.json
- ALWAYS hill-climb before human review — zero "rewrite" or "needs_work" items should reach the user
- Plan mode before multi-agent work — map out worktree assignments, file ownership, merge order
- Use git worktrees for ALL code/feature/script work — never have agents write to the same branch
- Reuse the proven HTML review layout — toggle buttons, editable textareas, two-column, char counts
- ID resolution: use `ad.get("ad_id", ad.get("page_id", ad.get("email_id")))` — scorer only checks ad_id
- Read LESSONS.md at session start
