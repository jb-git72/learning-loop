#!/usr/bin/env python3
"""
Onboard a new client in ~2 minutes.

Usage:
    python3 scripts/onboard_client.py --name "Brand Name" --slug brand-slug --url https://brand.com \
        --product "One-line product description" --industry grocery --market AU

What it does:
    1. Creates clients/{slug}/ directory
    2. WebFetches the URL to extract brand info
    3. Generates all 5 required files via LLM (config, rules, facts, tone, learnings)
    4. Validates everything (JSON schema, learnings structure, lint, test score)
    5. Generates 3 test ads and scores them
    6. Prints a readiness report

After this, you can immediately run:
    python3 scripts/hill_climb.py {slug} 3
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

# Load .env
env_path = root / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())


# --- Templates ---

CONFIG_TEMPLATE = {
    "content_types": ["meta-ad"],
    "files": {
        "rules": "rules.json",
        "facts": "facts.json",
        "tone": "tone.md",
        "learnings": "learnings.md",
    },
    "rubric": {
        "meta-ad": {
            "weights": {
                "angle_clarity": 1.25,
                "motivation_match": 1.0,
                "tactic_execution": 1.0,
                "specificity": 1.5,
                "objection_preemption": 1.25,
                "receptionist_test": 1.5,
                "scroll_stop_hook": 1.5,
                "cta_clarity": 1.0,
                "platform_fit": 1.0,
                "differentiation": 1.0,
            },
            "max_score": 63.75,
            "thresholds": {
                "production_ready": 51,
                "strong_draft": 44,
                "needs_work": 32,
                "rewrite": 0,
            },
        }
    },
    "composite_weights": {"rubric": 0.5, "rule_compliance": 0.3, "fact_accuracy": 0.2},
    "platform_constraints": {
        "meta-ad": {
            "primary_text_max_chars": 500,
            "headline_max_chars": 40,
            "description_max_chars": 125,
            "platform": "meta",
        }
    },
    "critical_rules": ["no_condescension", "no_commands"],
}

RULES_TEMPLATE = {"extends": "universal", "rules": []}

LEARNINGS_TEMPLATE = """# {brand} — Creative Learnings

## What Works (do more of this)

- [To be filled after first calibration round]
- Structure: customer pain/question → validation → product proof → CTA
- Sentences: 13-18 words. Keep it tight.

## What Fails (never do this)

{never_rules}

## Content Type Rules

- **Meta ads**: Focus on one angle per ad. Don't try to do too much.
"""


def call_llm(prompt: str) -> str:
    """Call Claude API to generate content."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: No ANTHROPIC_API_KEY in .env", file=sys.stderr)
        sys.exit(1)

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def extract_json(raw: str):
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try stripping markdown code fences first
    cleaned = re.sub(r"```json\s*", "", raw)
    cleaned = re.sub(r"```\s*", "", cleaned)
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Try finding JSON object in the text
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return None


def fetch_url(url: str) -> str:
    """Fetch URL content. Returns text."""
    try:
        import urllib.request

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        # Strip HTML tags for a rough text extraction
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:8000]  # Cap at 8K chars
    except Exception as e:
        print(f"WARNING: Could not fetch {url}: {e}", file=sys.stderr)
        return ""


def step_1_create_dir(client_dir: Path):
    """Create the client directory structure."""
    client_dir.mkdir(parents=True, exist_ok=True)
    loop_dir = client_dir / "loop" / "meta-ads"
    loop_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Created {client_dir}/")


def step_2_fetch_website(url: str) -> str:
    """Fetch and extract website content."""
    print(f"  Fetching {url}...")
    text = fetch_url(url)
    if not text:
        print("  WARNING: Could not fetch website. Facts will need manual verification.")
        return "Website could not be fetched. Use manual research."
    print(f"  Extracted {len(text)} chars from website")
    return text


def step_3_generate_config(args, website_text: str, client_dir: Path) -> dict:
    """Generate config.json using LLM + templates."""
    print("  Generating config.json...")

    prompt = f"""You are generating a config.json for an ad copy scoring engine. Based on the brand info below, generate ONLY the JSON fields listed. Be specific and accurate.

BRAND: {args.name}
PRODUCT: {args.product}
INDUSTRY: {args.industry}
MARKET: {args.market}
WEBSITE TEXT (first 4000 chars): {website_text[:4000]}

Generate these JSON fields:
1. "scoring_context" object with: product (detailed description), brand_positioning (1-2 sentences), tagline (if found), audience (detailed segments), key_motivations (3-5 emotional drivers as array), brand_values (tone description), success_looks_like (what good copy achieves)
2. "angles_in_use" array of 5-8 marketing angle IDs (use kebab-case like "price-value", "quality-craft", "social-proof", "urgency-scarcity", "empathy-founder", "comparison-switching", "transparency-trust", "transformation-story")
3. "approved_ctas" array of 4-6 CTAs appropriate for this brand
4. "receptionist_test_questions" array of 5 questions the ad must answer (What is it? What's included? How much? How is it different? How do I start?)
5. "receptionist_test_patterns" array of [label, regex_pattern] pairs that detect answers to each question in ad copy
6. "objection_preemption_patterns" array of [label, regex_pattern] pairs for 5 common objections this brand should address
7. "brand_names" array of brand names, product names, key people mentioned on the site
8. "prompt_objection_signals" string describing what objection language to include in copy
9. "prompt_rules" object with "meta-ad" key containing rules string for the writer
10. "prompt_extra_rules" object with "meta-ad" key containing extra constraints

IMPORTANT: Use simple regex patterns — lowercase, no word boundaries. For example ["farm.?thru", "regenerative"] not ["\\\\bFarmThru\\\\b"].
Respond with ONLY the JSON object — no markdown code fences, no explanation."""

    raw = call_llm(prompt)
    generated = extract_json(raw)
    if not generated:
        print("  ERROR: Could not parse LLM config output", file=sys.stderr)
        return {}

    # Merge with template
    config = {
        "client_id": args.slug,
        "client_name": args.name,
        "industry": args.industry,
        "product": args.product,
        "currency": "AUD" if args.market == "AU" else "USD",
        "market": args.market,
        **CONFIG_TEMPLATE,
    }

    # Overlay LLM-generated fields
    for key in [
        "scoring_context",
        "angles_in_use",
        "approved_ctas",
        "receptionist_test_questions",
        "receptionist_test_patterns",
        "objection_preemption_patterns",
        "brand_names",
        "prompt_objection_signals",
        "prompt_rules",
        "prompt_extra_rules",
    ]:
        if key in generated:
            config[key] = generated[key]

    # Write
    config_path = client_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    print(f"  Written config.json ({len(json.dumps(config))} chars)")
    return config


def step_4_generate_facts(args, website_text: str, client_dir: Path):
    """Generate facts.json using LLM."""
    print("  Generating facts.json...")

    prompt = f"""You are building a facts register for an ad copy scoring engine. Extract ONLY verifiable facts from the website text below. Each fact needs a source.

BRAND: {args.name}
PRODUCT: {args.product}
WEBSITE TEXT: {website_text[:5000]}

Generate a JSON object with:
- "client_id": "{args.slug}"
- "last_verified": "{datetime.now().strftime('%Y-%m-%d')}"
- "facts": array of 15-25 fact objects, each with:
  - "fact_id": "CAT-NNN" (e.g., BM-001 for business_model, PQ-001 for product_quality, PR-001 for pricing)
  - "category": one of "business_model", "pricing", "product_quality", "social_proof", "farm_partners", "positioning", "inclusions", "savings", "exclusions", "how_it_works"
  - "claim": the exact claim as it should appear in copy
  - "source": "{args.url}"
  - "confidence": "HIGH" if clearly stated on website, "MEDIUM" if inferred, "LOW" if uncertain
  - "last_verified": "{datetime.now().strftime('%Y-%m-%d')}"

Do NOT include "claim_patterns" — those will be generated automatically.

CRITICAL RULES:
- ONLY include facts you can actually see in the website text
- Mark anything uncertain as LOW confidence
- Never fabricate statistics unless clearly stated on the page
- Include the business model, pricing, key product features, and any social proof visible

Respond with ONLY the JSON object — no markdown code fences, no explanation."""

    for attempt in range(2):
        raw = call_llm(prompt)
        facts = extract_json(raw)
        if facts and "facts" in facts:
            facts_path = client_dir / "facts.json"
            with open(facts_path, "w") as f:
                json.dump(facts, f, indent=2)
                f.write("\n")
            n_facts = len(facts.get("facts", []))
            n_high = sum(1 for ff in facts.get("facts", []) if ff.get("confidence") == "HIGH")
            print(f"  Written facts.json ({n_facts} facts, {n_high} HIGH confidence)")
            return facts
        if attempt == 0:
            print("  Retrying facts generation...")

    print("  ERROR: Could not generate facts.json", file=sys.stderr)
    # Write minimal
    facts = {"client_id": args.slug, "last_verified": datetime.now().strftime("%Y-%m-%d"), "facts": []}
    with open(client_dir / "facts.json", "w") as f:
        json.dump(facts, f, indent=2)
    return facts


def step_5_generate_rules(args, website_text: str, config: dict, client_dir: Path):
    """Generate rules.json using LLM."""
    print("  Generating rules.json...")

    brand_names = config.get("brand_names", [args.name])

    prompt = f"""Generate a rules.json for an ad copy scoring engine. These rules are binary pass/fail checks that zero the score if violated.

BRAND: {args.name}
PRODUCT: {args.product}
INDUSTRY: {args.industry}
BRAND NAMES (never use competitors instead): {json.dumps(brand_names)}

Generate 8-12 rules covering:
1. Competitor naming ban (never name specific competitors — use generic terms instead)
2. Incorrect product/service claims (what the product is NOT)
3. Banned terms or phrases for this industry
4. Headline formatting (sentence case only, never Title Case)
5. Incorrect pricing or stats protection
6. Geographic or service area accuracy (if applicable)
7. Regulatory compliance (if applicable for this industry)

Each rule needs:
- "rule_id": "{args.slug.upper().replace('-','')[:4]}-NNN"
- "name": "descriptive_snake_case"
- "severity": "critical" or "high" or "medium"
- "type": "regex_absent" (patterns that must NOT appear)
- "description": what it prevents
- "fields": ["primary_text", "headline", "description"] (check all by default)
- "patterns": array of regex patterns to block
- "case_sensitive": false
- "rationale": why this matters

Wrap in: {{"extends": "universal", "rules": [...]}}
IMPORTANT: Use simple regex patterns — lowercase, no complex escaping. For example ["woolworths", "coles"] not ["\\bWoolworths\\b"].
Respond with ONLY the JSON object — no markdown code fences, no explanation."""

    for attempt in range(2):
        raw = call_llm(prompt)
        rules = extract_json(raw)
        if rules and "rules" in rules:
            with open(client_dir / "rules.json", "w") as f:
                json.dump(rules, f, indent=2)
                f.write("\n")
            n_rules = len(rules.get("rules", []))
            print(f"  Written rules.json ({n_rules} rules)")
            return rules
        if attempt == 0:
            print("  Retrying rules generation...")

    print("  ERROR: Could not generate rules.json — using empty template", file=sys.stderr)
    with open(client_dir / "rules.json", "w") as f:
        json.dump(RULES_TEMPLATE, f, indent=2)
    return RULES_TEMPLATE


def step_6_generate_tone(args, website_text: str, client_dir: Path):
    """Generate tone.md using LLM."""
    print("  Generating tone.md...")

    prompt = f"""Write a tone and voice guide for ad copywriting for this brand. Write in markdown prose (not JSON).

BRAND: {args.name}
PRODUCT: {args.product}
INDUSTRY: {args.industry}
WEBSITE TEXT (for tone reference): {website_text[:3000]}

Structure:
1. Brand Positioning (2-3 sentences)
2. Business Model (how the product/service works — critical for copy accuracy)
3. Voice Pillars (3-5 pillars, each with a name, 1-sentence description, and 2 do/don't examples)
4. Communication Hierarchy (what to lead with vs what comes last)
5. Preferred Terms vs Banned Terms (two columns)

Keep it under 800 words. Be specific to this brand, not generic marketing advice."""

    tone = call_llm(prompt)
    with open(client_dir / "tone.md", "w") as f:
        f.write(tone)
    print(f"  Written tone.md ({len(tone)} chars)")
    return tone


def step_7_generate_learnings(args, config: dict, client_dir: Path):
    """Generate learnings.md with correct priority structure."""
    print("  Generating learnings.md...")

    # Extract never-rules from prompt_rules
    never_rules = []
    prompt_rules = config.get("prompt_rules", {})
    if isinstance(prompt_rules, dict):
        for ct, rules_text in prompt_rules.items():
            for line in rules_text.split("\n"):
                line = line.strip().lstrip("- ")
                if line.upper().startswith("NO ") or line.upper().startswith("NEVER"):
                    never_rules.append(f"- {line}")

    if not never_rules:
        never_rules = [
            f"- Don't fabricate statistics — every number must trace to facts.json",
            f"- Don't use Title Case headlines — sentence case only",
            f"- Don't name competitors directly — use generic terms",
        ]

    learnings = LEARNINGS_TEMPLATE.format(
        brand=args.name, never_rules="\n".join(never_rules)
    )

    with open(client_dir / "learnings.md", "w") as f:
        f.write(learnings)

    # Verify truncation window
    first_1600 = learnings[:1600]
    has_works = "What Works" in first_1600
    has_fails = "What Fails" in first_1600
    print(f"  Written learnings.md ({len(learnings)} chars)")
    print(f"  Truncation check: What Works in first 1600: {'YES' if has_works else 'NO'}, What Fails in first 1600: {'YES' if has_fails else 'NO'}")
    return learnings


def step_8_validate(args, client_dir: Path) -> dict:
    """Run validation suite on the generated client."""
    print("\n--- VALIDATION ---")
    results = {"passed": 0, "failed": 0, "warnings": 0}

    # 1. JSON validation
    for fname in ["config.json", "rules.json", "facts.json"]:
        fpath = client_dir / fname
        try:
            with open(fpath) as f:
                json.load(f)
            print(f"  [PASS] {fname} is valid JSON")
            results["passed"] += 1
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"  [FAIL] {fname}: {e}")
            results["failed"] += 1

    # 2. Config required keys
    with open(client_dir / "config.json") as f:
        config = json.load(f)

    required_keys = [
        "client_id", "client_name", "product", "scoring_context",
        "rubric", "platform_constraints", "approved_ctas",
    ]
    for key in required_keys:
        if key in config:
            results["passed"] += 1
        else:
            print(f"  [FAIL] config.json missing required key: {key}")
            results["failed"] += 1

    scorer_keys = [
        "receptionist_test_patterns", "objection_preemption_patterns",
        "prompt_rules", "brand_names",
    ]
    for key in scorer_keys:
        if key in config:
            results["passed"] += 1
        else:
            print(f"  [WARN] config.json missing recommended key: {key}")
            results["warnings"] += 1

    # 3. Learnings truncation
    learnings_path = client_dir / "learnings.md"
    if learnings_path.exists():
        text = learnings_path.read_text()
        first_1600 = text[:1600]
        if "What Works" in first_1600 and "What Fails" in first_1600:
            print("  [PASS] learnings.md: critical sections within 1600-char window")
            results["passed"] += 1
        else:
            print("  [FAIL] learnings.md: critical sections NOT within 1600-char window")
            results["failed"] += 1

    # 4. Facts confidence check
    facts_path = client_dir / "facts.json"
    if facts_path.exists():
        with open(facts_path) as f:
            facts = json.load(f)
        n_facts = len(facts.get("facts", []))
        n_high = sum(1 for f in facts.get("facts", []) if f.get("confidence") == "HIGH")
        if n_facts >= 5:
            print(f"  [PASS] facts.json: {n_facts} facts ({n_high} HIGH confidence)")
            results["passed"] += 1
        else:
            print(f"  [WARN] facts.json: only {n_facts} facts — consider adding more")
            results["warnings"] += 1

    # 5. Rules check
    rules_path = client_dir / "rules.json"
    if rules_path.exists():
        with open(rules_path) as f:
            rules = json.load(f)
        n_rules = len(rules.get("rules", []))
        if n_rules >= 3:
            print(f"  [PASS] rules.json: {n_rules} client-specific rules")
            results["passed"] += 1
        else:
            print(f"  [WARN] rules.json: only {n_rules} rules — consider adding more")
            results["warnings"] += 1

    # 6. Try loading in scorer
    try:
        from engine.scorer import load_client
        client = load_client(client_dir, root / "shared")
        print("  [PASS] Scorer loads client successfully")
        results["passed"] += 1
    except Exception as e:
        print(f"  [FAIL] Scorer cannot load client: {e}")
        results["failed"] += 1

    return results


def step_9_test_generate(args, client_dir: Path) -> dict:
    """Generate 3 test ads and score them."""
    print("\n--- TEST GENERATION ---")

    try:
        from engine.scorer import load_client, score_ad
        from writer import generate_variant

        client = load_client(client_dir, root / "shared")
        config = client["config"]
        angles = config.get("angles_in_use", ["quality-craft"])
        hook_types = ["question", "story", "statistic"]

        scores = []
        for i, hook in enumerate(hook_types[:3]):
            angle = angles[i % len(angles)]
            print(f"  Generating test ad {i+1}/3 (angle={angle}, hook={hook})...")

            try:
                ad = generate_variant(
                    angle=angle,
                    tactic="test",
                    hook_type=hook,
                    funnel="TOF",
                    client_dir=client_dir,
                    content_type="meta-ad",
                )

                if ad.get("ad_id") == "ERROR":
                    print(f"    [WARN] Generation failed: {ad.get('error', 'unknown')}")
                    continue

                # Score it
                result = score_ad(ad, client, use_llm=False)
                composite = result["composite"]
                verdict = result["verdict"]
                scores.append(composite)

                # Save test ad
                ad_path = client_dir / "loop" / "meta-ads" / f"TEST-{i+1:03d}.json"
                with open(ad_path, "w") as f:
                    json.dump(ad, f, indent=2)

                print(f"    Score: {composite:.3f} ({verdict}) — {ad.get('headline', '')[:50]}")

                # Check for critical failures
                if result.get("overrides", {}).get("critical_rule_failure"):
                    failures = result.get("rule_compliance", {}).get("failures", [])
                    for fail in failures[:3]:
                        print(f"    [WARN] Rule failure: {fail.get('rule_id', '?')} — {fail.get('detail', '')[:80]}")

            except Exception as e:
                print(f"    [FAIL] Error generating test ad: {e}")

        if scores:
            avg = sum(scores) / len(scores)
            print(f"\n  Avg test score: {avg:.3f}")
            return {"avg_score": avg, "scores": scores}
        else:
            print("\n  No test ads generated successfully")
            return {"avg_score": 0, "scores": []}

    except Exception as e:
        print(f"  [FAIL] Could not run test generation: {e}")
        return {"avg_score": 0, "scores": []}


def print_report(args, validation: dict, test_results: dict):
    """Print final readiness report."""
    print("\n" + "=" * 60)
    print(f"  ONBOARDING REPORT: {args.name}")
    print("=" * 60)
    print(f"  Client dir:  clients/{args.slug}/")
    print(f"  Validation:  {validation['passed']} passed, {validation['failed']} failed, {validation['warnings']} warnings")

    if test_results.get("scores"):
        avg = test_results["avg_score"]
        print(f"  Test scores: {', '.join(f'{s:.3f}' for s in test_results['scores'])} (avg {avg:.3f})")
    else:
        print("  Test scores: No test ads generated")

    print()

    if validation["failed"] == 0:
        print("  STATUS: READY FOR CALIBRATION")
        print()
        print("  Next steps:")
        print(f"    1. Review and verify facts:  cat clients/{args.slug}/facts.json")
        print(f"    2. Hill-climb to improve:    python3 scripts/hill_climb.py {args.slug} 3")
        print(f"    3. Build review HTML:         python3 scripts/build_review_html.py scored.json review.html")
        print(f"    4. Run with LLM scoring:     python3 scripts/score_batch.py {args.slug}")
    else:
        print("  STATUS: NEEDS FIXES")
        print(f"  Fix the {validation['failed']} failed checks above, then re-run this script.")

    print()


def main():
    parser = argparse.ArgumentParser(description="Onboard a new client")
    parser.add_argument("--name", required=True, help="Brand name (e.g., 'FarmThru')")
    parser.add_argument("--slug", required=True, help="URL-safe slug (e.g., 'farm-thru')")
    parser.add_argument("--url", required=True, help="Brand website URL")
    parser.add_argument("--product", required=True, help="One-line product description")
    parser.add_argument("--industry", default="general", help="Industry (e.g., grocery, pet-care, fintech)")
    parser.add_argument("--market", default="AU", help="Market (e.g., AU, US, UK)")
    parser.add_argument("--skip-generate", action="store_true", help="Skip LLM generation (validate existing)")
    args = parser.parse_args()

    client_dir = root / "clients" / args.slug

    if client_dir.exists() and not args.skip_generate:
        print(f"WARNING: {client_dir} already exists. Use --skip-generate to validate existing.")
        confirm = input("Overwrite? (y/N): ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    print(f"\nOnboarding: {args.name} ({args.slug})")
    print(f"URL: {args.url}")
    print(f"Product: {args.product}")
    print(f"Industry: {args.industry} | Market: {args.market}")
    print()

    if not args.skip_generate:
        # Step 1: Create directory
        print("Step 1/7: Create directory")
        step_1_create_dir(client_dir)

        # Step 2: Fetch website
        print("Step 2/7: Fetch website")
        website_text = step_2_fetch_website(args.url)

        # Step 3: Generate config
        print("Step 3/7: Generate config.json")
        config = step_3_generate_config(args, website_text, client_dir)

        # Step 4: Generate facts
        print("Step 4/7: Generate facts.json")
        step_4_generate_facts(args, website_text, client_dir)

        # Step 5: Generate rules
        print("Step 5/7: Generate rules.json")
        step_5_generate_rules(args, website_text, config, client_dir)

        # Step 6: Generate tone
        print("Step 6/7: Generate tone.md")
        step_6_generate_tone(args, website_text, client_dir)

        # Step 7: Generate learnings
        print("Step 7/7: Generate learnings.md")
        step_7_generate_learnings(args, config, client_dir)

    # Step 8: Validate
    validation = step_8_validate(args, client_dir)

    # Step 9: Test generate
    test_results = step_9_test_generate(args, client_dir)

    # Report
    print_report(args, validation, test_results)


if __name__ == "__main__":
    main()
