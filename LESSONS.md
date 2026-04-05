# Lessons Learned

Mistakes made and patterns to avoid. Read this at session start.

---

## 1. Always hill-climb before human review

**Mistake:** Presented 33 items in "needs work" and "rewrite" state for human review. User said: "why are you showing them to me when they are in needs work and rewrite state? that seems like you're not doing your job."

**Rule:** Run the generate-score-iterate loop until ALL items are strong_draft+ (composite >= 0.70) BEFORE presenting for human review. The human reviews polished output, not raw drafts. This is non-negotiable.

**How:** `python3 scripts/hill_climb.py farm-thru 3` — iterates up to 3 times per item, keeps improvements, discards regressions.

---

## 2. Plan mode before multi-agent work

**Mistake:** Launched multiple agents without a plan. Result: agents created conflicting branches (claude/round3-meta-ads, feature/round3-landing-pages-emails), auto-merged PRs that caused merge conflicts, corrupted JSON files, same rule violations fixed 3+ times.

**Rule:** Enter plan mode FIRST for any multi-agent task. Plan must include:
- **Always use git worktrees** (`isolation: "worktree"`) for agents that write code, features, or scripts
- Each agent gets its own branch via worktree — no merge conflicts
- File ownership per agent (no overlapping writes)
- Agents PR back to main when done
- NEVER have multiple agents writing to the same branch without worktrees

---

## 3. Reuse the proven HTML review layout

**Mistake:** Built a new HTML review template from scratch with dropdowns, collapsed cards, and no editable fields. User said: "it was better when you had the buttons" and "I can't see anything here — the previous layout was much easier."

**Rule:** The proven layout has:
- Toggle buttons (not dropdowns) for filters: All | Ads | Pages | Emails | Pending | Approved | Edited | Killed
- Cards expanded by default (not collapsed)
- Two-column layout: primary_text (left), headline + description (right)
- Editable textareas with character counts (434/500)
- Score shown as colored circle (0.71) not plain text
- Compact score summary line: Composite | Rubric | Rules | Facts | Hook
- CTA / Tactic / Funnel tags
- Creative brief in italics
- Save JSON / CSV buttons in toolbar (not at bottom)

Template: `scripts/build_review_html.py`

---

## 4. Verify facts BEFORE generation, not after

**Mistake:** Generated 33 items using unverified facts ("50+ farms", "2,000+ customers", "co-founder Rachel Ward") then had to regenerate everything after verification proved them fabricated.

**Rule:** WebFetch + verify ALL facts.json claims against the client's website BEFORE generating any content. Mark unverified claims before the writer sees them.

---

## 5. writer.py generates rule-violating content

**Mistake:** Hill-climbing loop regenerated variants via writer.py that scored 0.000 (critical FMTH-001 failures) because the writer doesn't know about client rules.

**Rule:** The writer prompt needs the rules context. Current writer.py only passes tone + learnings + facts, not rules. Either:
- Add rules summary to the writer prompt, OR
- Post-process generated variants to fix common violations before scoring

---

## 6. Don't poll background agents

**Mistake:** Repeatedly checked agent output files instead of waiting for completion notification. Wasted turns and context.

**Rule:** Launch background agents and continue with other work. The system notifies you when they complete.

---

## 7. Scorer uses ad_id — landing pages and emails show as "unknown"

**Mistake:** Landing pages (page_id) and emails (email_id) scored as "unknown" in reports because scorer.py hardcodes `ad.get("ad_id", "unknown")`.

**Rule:** When building reports or HTML, resolve the ID from all three fields: `ad.get("ad_id", ad.get("page_id", ad.get("email_id", "unknown")))`. The engine is immutable so this must be handled in scripts.

---

## 8. Feedback loop breaks silently — writer prompt contradicts user feedback

**Mistake:** FarmThru user repeatedly said "no $50, no 'Not financial advice', no Birchal in meta-ads." The feedback was documented in learnings.md. But ads kept containing it across 3+ rounds. Root cause: **7 independent failures** all conspired to break the loop:

1. `writer.py _build_rules_summary()` explicitly told the LLM to ADD "Not financial advice." to descriptions — directly contradicting the user's feedback
2. `learnings.md` truncated to 800 chars — critical feedback at char 1200+, LLM never saw it
3. `FMTH-016` only checked `["primary_text", "headline"]`, not `"description"` — violations in description were invisible
4. `FMTH-001` trigger regexes too narrow — `$50 minimum` missed "From $50"
5. Investment facts intentionally fed to CFE angles via `_select_relevant_facts()` — LLM told "use these facts" AND "don't use these terms"
6. Review JSON feedback was write-only — no script read it back into the system
7. No content-type filtering on angle/fact selection — meta-ads got investment facts

**Rule:** When adding a new client or content type, follow the checklist in CLAUDE.md "Adding a new client." Key guardrails:

- **writer.py rules must never contradict learnings.md** — after any writer.py edit, grep for contradictions against the client's learnings
- **learnings.md: "what works" first, "what fails" second** — critical rules must fall within the first 1600 chars (the truncation window). BFP's learnings worked because positive patterns were at the top; FarmThru's didn't because problems were at the top
- **Rules must check ALL relevant fields** — when adding a rule, include every field the violation could appear in. Don't assume description is safe because you checked primary_text
- **Regex triggers must match real ad copy patterns** — test patterns against actual generated content, not hypothetical phrases. "raises cattle" ≠ "raises capital"
- **Review JSON must flow back** — after each human review round, integrate feedback into content files AND verify it reaches the LLM prompt
- **Filter facts by content type** — meta-ads should never receive investment category facts. Landing pages and emails can.

---

## 9. Learnings.md structure determines what the LLM sees

**Mistake:** FarmThru's learnings.md was 16,695 chars but writer.py only passes `learnings[:1600]` to the LLM. The file was structured chronologically (Round 1 feedback, Round 2 feedback) instead of by priority. Result: the LLM saw "hub-and-collect, not delivery" problems but never saw "use BFP pattern: customer pain → validation → proof → CTA" or "sentences 13-18 words."

**Rule:** Structure learnings.md by priority, not chronology:

```
# {Client} — Creative Learnings

## What Works (do more of this)        ← MUST be within first 800 chars
- Winning patterns with ad IDs
- Approved phrases and structures
- BFP/reference structure to follow

## What Fails (never do this)          ← MUST be within first 1600 chars
- NEVER rules with specifics
- Banned terms and patterns

## Content Type Rules                  ← Can be past truncation
- Per-type guidance

## Round N Review Details              ← Archive, not critical path
- Chronological review notes
```

**How to verify:** Run `head -c 1600 clients/{slug}/learnings.md` — if the critical "what works" and "what fails" sections aren't fully visible, restructure.

---

## 10. Brand-specific content must live in config, not code

**Mistake:** writer.py and rubric_scorer.py had FarmThru-specific content (compliance disclaimers, sender names, objection signals, scoring patterns) hardcoded in if/else blocks. This caused:
- FarmThru compliance text appearing in all landing page templates (Birchal disclaimer)
- "Rachel & the FarmThru team" hardcoded as email sender for ALL clients
- `_score_objection_preemption` using content-based regex detection to guess which brand — misclassifying ads
- "Collect from Brookvale" objection signal in all meta-ad prompts regardless of client

**Rule:** ALL brand-specific content belongs in `clients/{slug}/config.json`, not in source code. New config keys for each brand:
- `receptionist_test_patterns` — scorer dimension patterns
- `objection_preemption_patterns` — scorer dimension patterns
- `prompt_rules` — per content-type writer rules
- `prompt_extra_rules` — per content-type extra rules
- `prompt_objection_signals` — scoring guide signals
- `email_sender` — email sender name
- `landing_page_compliance` — compliance disclaimer text
- `brand_names` — for specificity scoring

**How to verify for new brands:** Search writer.py and engine/ for any hardcoded references to the brand name. There should be zero. Everything should load from config with a generic fallback.

---

## 11. Greedy hill-climbing converges fast then stalls — use evolutionary strategies

**Mistake:** Pure greedy hill-climbing (1 candidate, same angle/hook, "write something BETTER") converged within 2-3 iterations then stalled. Items stuck at needs_work never improved because the same prompt kept producing similar variants.

**Rule:** Use evolutionary hill-climbing (`--strategy evolutionary`) which generates N candidates per iteration using diverse strategies:

| Strategy | When it helps | Temperature |
|----------|--------------|-------------|
| **improve** | Exploitation — refine what works | 0.7 |
| **mutate** | Rotate hook_type for fresh angles | 0.8 |
| **crossover** | Blend current ad with top-scoring donor — **produced the biggest jumps** | 0.6 |
| **targeted** | Fix the weakest scoring dimension specifically | 0.5 |
| **wildcard** | Ignore current best, try something novel (every 3rd iteration) | 0.9 |

**Key finding from FarmThru:** Crossover was the only strategy that produced meaningful improvements on stuck items (+0.057 by blending CFE-101 with top-scoring BR-109). Pure improve/targeted modes scored ~0.56 avg — barely better than random.

**When items are truly stuck (0 improvements across 50+ candidates):** The bottleneck is structural, not generation quality. Check:
1. Are deterministic scoring patterns (receptionist_test, objection_preemption) rewarding the right content?
2. Are content-type-specific scoring dimensions properly tuned (e.g., emails vs meta-ads)?
3. Does the content need human calibration feedback to break through?

**Usage:** `python3 scripts/hill_climb.py {client} --iterations 5 --population 5 --strategy evolutionary`

---

## 12. Onboard new clients with the script, not manually

**Mistake:** FarmThru onboarding took 2 days of back-and-forth. Facts were fabricated, learnings were mis-structured, scorer patterns were hardcoded, cross-brand contamination went undetected.

**Rule:** Always use the onboarding script for new clients:
```bash
python3 scripts/onboard_client.py --name "Brand" --slug brand-slug \
  --url https://brand.com --product "description" --industry X --market AU
```

This generates all 5 files, validates them (18 checks), and runs 3 test ads in ~2 minutes. Then hill-climb immediately:
```bash
python3 scripts/hill_climb.py brand-slug --iterations 5 --population 5
```

**After first human review:** Update learnings.md with "What Works" and "What Fails" from the review, keeping critical sections within the 1600-char truncation window. Then run hill-climbing again.

---

## 13. Learnings files have a 2000-char budget — split by content type

**Mistake:** learnings.md grew to 18K chars. writer.py truncated it to 1600. 91% of learnings were invisible to the LLM. Em dash rules, subhead limits, and LP formatting guidance were all silently discarded. Hit this bug 3 separate times in Round 3.

**Rule:** Learnings are split into 4 files, each with a 2000-char hard budget:
- `learnings.md` — common rules loaded for ALL content types
- `learnings-meta-ad.md` — meta-ad patterns and structure
- `learnings-landing-page.md` — LP formatting, scroll structure, CFE patterns
- `learnings-email.md` — frameworks, subject lines, drip sequence

**How:** `python3 scripts/check_learnings.py {slug}` checks budgets. `--trim` auto-compresses with Haiku while preserving all rules. When adding a learning, compress or remove an existing one first — never just append.

---

## 14. Generation prompt quality beats iteration count

**Mistake:** Ran 120 hill-climbing generations on LPs. Average jump: +0.041 per LP. Generator kept producing em dashes and long subheads because the prompt never mentioned these constraints.

**After fixing 5 prompt gaps:** 40 generations, average jump: +0.108 per LP. 2.6x better results with 3x fewer API calls.

**Rule:** Fix the generation prompt BEFORE running hill-climbing. One prompt fix is worth 100 extra generations. Checklist before hill-climbing:
1. Do learnings mention the constraints the scorer enforces?
2. Do config `prompt_extra_rules` include formatting rules?
3. Does the tone file comply with the rules (no examples that violate them)?
4. Does the config `platform_constraints` match the scoring thresholds?
5. Does `_dimension_improvement_guidance()` in writer.py cover all scored dimensions?

---

## 15. Tone files and examples teach by demonstration

**Mistake:** tone.md had em dashes in example copy ("stone fruit is unreal — juicy"). The LLM learned em dashes were acceptable and used them in every generation.

**Rule:** Every example in tone.md, config.json, and learnings must comply with the active rules. If you ban em dashes, remove them from all examples. If you ban Title Case, don't have Title Case in example headlines.

---

## 16. LP sections must be structured arrays, not markdown strings

**Mistake:** Landing page `sections` field was a markdown string. The rule checker, rubric scorer (`_score_scroll_depth_pull`), and LLM judge (`_format_content_block`) all expect `[{"heading": "...", "body": "..."}]`. With a string, section count returned character count, headings were empty, and compliance text was invisible.

**Rule:** Always convert LP sections to structured arrays. Run `scripts/fix_lp_sections.py` after applying human edits. The `apply_review_edits.py` script writes sections as strings (from the HTML export) — conversion must follow.

---

## 17. Content-check rules produce false positives in LP sections

**Mistake:** FMTH-002 (no_guaranteed_returns) matched "no guaranteed returns" in compliance disclaimers. FMTH-014 matched "no subscription" (saying they DON'T have subscriptions). Both are false positives from negation context.

**Rule:** Content-check rules (banned terms, health claims, delivery claims) should NOT check the `sections` field. Compliance disclaimers live in sections and contain the exact phrases they're disclaiming. Only formatting rules (em dashes) and the custom disclaimer checker (FMTH-001) should check sections.

---

## 18. Chained evolution (crossover then mutate) doesn't improve results

**Tested:** A/B across 24 candidates, 3 approaches:
- Plain crossover: avg 0.685 (winner)
- Single-call combo (crossover + mutation in one prompt): avg 0.608 (worst — confuses the LLM)
- Two-call chain (crossover first, then mutate result): avg 0.673 (mutation degrades good crossovers)

**Finding:** The mutation step acts as regression to the mean — improves bad results but degrades good ones. Tightest range (0.076) but lowest peaks. Keep crossover and mutation as independent population slots.

---

## 19. config.json prompt_extra_rules are always fully loaded

**Key insight:** Unlike learnings (which have a 2000-char budget per file), `config.json -> prompt_extra_rules` is sent in full to the LLM every time. Put hard formatting rules here (em dashes, char limits, structural requirements). Put creative patterns in learnings files.

---

## 20. Pairwise gating catches soulless optimisation

The pairwise LLM comparison (new vs current) catches cases where a variant scores higher on rubrics but reads worse. Example: LP-F got +0.008 on rubric but pairwise scored 2/5 — "loses the powerful personal narrative, replaces intimate storytelling with transactional clarity."

**Rule:** Keep `--use-pairwise` on for evolutionary hill-climbing. One extra Haiku call per accepted candidate prevents accepting technically-correct-but-lifeless rewrites.
