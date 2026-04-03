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

Create `clients/{slug}/` with 5 files:
- `config.json` — entry point: weights, thresholds, CTAs, angles, scoring_context
- `rules.json` — client-specific rules (extends universal)
- `facts.json` — structured facts register
- `tone.md` — voice guidelines (prose, for LLM context)
- `learnings.md` — accumulated creative learnings

Zero code changes to the engine or writer.py. Everything is config-driven.

### New client checklist (follow in order — see LESSONS.md #8-9 for why)

1. **Verify facts before generating** — WebFetch the client website, verify every claim in facts.json. Mark confidence levels. NEVER fabricate stats.
2. **Structure learnings.md correctly** — "What Works" first (within 800 chars), "What Fails" second (within 1600 chars). Verify with `head -c 1600 clients/{slug}/learnings.md`.
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

## Workflow: calibration rounds

1. **Verify facts first** — WebFetch client website, update facts.json BEFORE generating
2. **Generate content** — Use writer.py or agents with full rules/facts/tone context
3. **Hill-climb to strong_draft+** — `python3 scripts/hill_climb.py {client}` — NEVER show raw drafts to user
4. **Build HTML review** — `python3 scripts/build_review_html.py scored.json output.html` — uses proven layout
5. **Present for human review** — Only after ALL items score >= 0.70 composite

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
