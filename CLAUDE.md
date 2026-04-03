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

## Critical rules

- `engine/` files are IMMUTABLE — the writer agent cannot modify them
- Rules/facts are pass/fail GATES, not score contributors
- LLM scoring uses separate Haiku API call (no shared context with writer)
- Every number in ad copy must trace to facts.json
