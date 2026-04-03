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

Zero code changes to the engine.

## API key

Store in `.env` (gitignored): `ANTHROPIC_API_KEY=sk-ant-...`
Auto-loaded by `run.py`.

## Scripts

- `scripts/score_batch.py` — Score all content in a client's loop dir, output JSON
- `scripts/hill_climb.py` — Generate-score-iterate loop to reach strong_draft+
- `scripts/build_review_html.py` — Build interactive HTML review (proven layout with editable textareas, toggle buttons, two-column, char counts)

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
