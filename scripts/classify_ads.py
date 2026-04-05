#!/usr/bin/env python3
"""Classify raw Meta ads into the learning-loop angle×hook taxonomy.

Reads a Meta Ads Manager CSV (with ad text columns), classifies each
unique ad using Haiku, and outputs canonical ad JSON files ready for
scoring with score_batch.py.

Usage:
    python3 scripts/classify_ads.py tyroola --csv clients/tyroola/loop/meta-export.csv
    python3 scripts/classify_ads.py tyroola --csv export.csv --dry-run
"""

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

# Load .env
env_path = root / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# ---------------------------------------------------------------------------
# CSV column aliases — extends staircase.py with ad text columns
# ---------------------------------------------------------------------------

COLUMN_ALIASES = {
    "ad_name": ["Ad name", "Ad Name", "ad_name", "Ad"],
    "body": ["Body", "body", "Ad body", "Primary text", "Text",
             "Primary Text", "Ad Body"],
    "title": ["Creative title", "Title", "title", "Ad title", "Headline",
              "headline", "Ad Title"],
    "ad_description": ["Description", "description", "Ad description",
                       "Link description", "Ad Description"],
    "cta": ["Ad call_to_action type", "Call to action", "CTA", "cta",
            "Call To Action"],
    # Performance columns (for reference/passthrough)
    "impressions": ["Impressions", "impressions", "Impr."],
    "spend": ["Amount spent (AUD)", "Amount spent (USD)", "Amount spent",
              "Spend", "spend", "Cost"],
}


def _resolve_columns(header: list) -> dict:
    clean = [h.strip() for h in header]
    mapping = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in clean:
                mapping[canonical] = clean.index(alias)
                break
    return mapping


# ---------------------------------------------------------------------------
# Hook signal pre-screen (deterministic hints for the LLM)
# ---------------------------------------------------------------------------

def _prescreen_hook(text: str) -> str:
    """Guess the most likely hook type from surface patterns.

    Returns a hint string passed to the LLM, not a final answer.
    """
    if not text:
        return ""
    first_line = text.strip().split("\n")[0].strip()

    if first_line.startswith('"') or first_line.startswith("\u201c"):
        return "quoted_objection"
    if first_line.endswith("?"):
        return "question"
    if re.match(r"^[\$\d]", first_line):
        return "price_anchor or statistic"
    if re.match(r"(?i)^if (you|your|they)", first_line):
        return "if_then"
    if re.search(r"(?i)\b(just launched|introducing|brand new|first time|now available)\b", first_line):
        return "newness"
    if re.search(r"(?i)\b(last chance|hurry|ends|limited time|don.t miss)\b", first_line):
        return "urgency"
    if re.search(r"(?i)\b(I never|I used to|I always thought|confession)\b", first_line):
        return "confession"
    return ""


# ---------------------------------------------------------------------------
# Load hook and angle definitions for the classification prompt
# ---------------------------------------------------------------------------

def _load_hook_definitions() -> list:
    """Load hook id + template from shared/hooks.json."""
    hooks_path = root / "shared" / "hooks.json"
    with open(hooks_path) as f:
        data = json.load(f)
    return [(h["id"], h["template"]) for h in data["hooks"]]


def _load_angle_definitions(client_dir: Path) -> list:
    """Load angles_in_use from client config."""
    config_path = client_dir / "config.json"
    if not config_path.exists():
        print(f"ERROR: Client config not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    with open(config_path) as f:
        config = json.load(f)
    return config.get("angles_in_use", [])


# Angle descriptions (brief, for classification context)
ANGLE_DESCRIPTIONS = {
    "price-value": "Cost clarity, savings, value for money, affordability",
    "quality-craft": "Product quality, materials, craftsmanship, premium",
    "outcome-results": "What the customer achieves, before/after, transformation",
    "comparison-switching": "Us vs them, switching from competitor, better alternative",
    "transformation-storytelling": "Personal change narrative, journey, before/after story",
    "simplicity-clarity": "Easy to understand, no complexity, straightforward",
    "safety-risk": "Trust, reliability, risk reduction, guarantees, warranties",
    "empathy-understanding": "We understand your problem, shared frustration",
    "anti-insurance": "Not insurance, objection preemption for insurance confusion",
    "guilt-free": "Relief from guilt, permission to spend",
    "predictability-control": "Known costs, no surprises, budgeting confidence",
    "cause-purpose": "Purpose-driven, mission, social good",
    "transparency-safety": "Know where it comes from, traceability, honesty",
    "urgency-scarcity": "Limited availability, time pressure, act now",
    "social-belonging": "Community, belonging, shared identity",
    "empathy-founder": "Founder's personal story, relatable origin",
    "investment-thesis": "Investment opportunity, ROI, financial upside",
    "convenience-ease": "Easy to buy, fast delivery, hassle-free experience",
    "authority-expertise": "Expert endorsement, professional recommendation",
}


# ---------------------------------------------------------------------------
# LLM classification
# ---------------------------------------------------------------------------

def _classify_ad(ad_text: dict, hooks: list, angles: list,
                 hook_hint: str) -> dict:
    """Classify one ad via Haiku. Returns {angle, hook_type, confidence}."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    # Build hook reference
    hook_ref = "\n".join(f"- {hid}: {template}" for hid, template in hooks)

    # Build angle reference
    angle_ref = "\n".join(
        f"- {a}: {ANGLE_DESCRIPTIONS.get(a, a)}" for a in angles
    )

    # Build ad content block
    parts = []
    if ad_text.get("headline"):
        parts.append(f"HEADLINE: {ad_text['headline']}")
    if ad_text.get("primary_text"):
        parts.append(f"PRIMARY TEXT: {ad_text['primary_text']}")
    if ad_text.get("description"):
        parts.append(f"DESCRIPTION: {ad_text['description']}")
    ad_block = "\n".join(parts)

    hint_line = f"\nDeterministic signal suggests hook might be: {hook_hint}" if hook_hint else ""

    prompt = f"""Classify this Meta ad into the angle and hook_type taxonomy below.

AVAILABLE ANGLES:
{angle_ref}

AVAILABLE HOOKS:
{hook_ref}

AD CONTENT:
{ad_block}
{hint_line}

Pick the single best-matching angle and hook_type. Consider:
- Angle: what strategic proposition does the ad push? (price, quality, empathy, etc.)
- Hook: what technique does the FIRST LINE use to grab attention? (question, story, statistic, etc.)

Respond with ONLY valid JSON (no other text):
{{"angle": "<angle_id>", "hook_type": "<hook_id>", "confidence": <0.0-1.0>}}"""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()

        # Parse JSON from response
        match = re.search(r"\{[^}]+\}", text)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"  LLM error: {e}", file=sys.stderr)

    return {"angle": angles[0] if angles else "unknown",
            "hook_type": "question", "confidence": 0.0}


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------

def parse_ads_csv(csv_path: Path) -> list:
    """Parse Meta CSV, extract unique ads with text + name.

    Returns list of dicts with ad_name, primary_text, headline, description.
    """
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        col_map = _resolve_columns(header)

        if "ad_name" not in col_map:
            print(f"ERROR: No 'Ad name' column found. Columns: {header}",
                  file=sys.stderr)
            sys.exit(1)

        has_text = "body" in col_map or "title" in col_map
        if not has_text:
            print("ERROR: No ad text columns (Body/Title/Description) found.",
                  file=sys.stderr)
            print("Export from Ads Manager with Creative columns added.",
                  file=sys.stderr)
            print(f"Found columns: {header}", file=sys.stderr)
            sys.exit(1)

        seen = {}  # ad_name -> ad dict (deduplicate)
        for row in reader:
            if not row or len(row) < 2:
                continue
            name = row[col_map["ad_name"]].strip()
            if not name or name in seen:
                continue

            ad = {
                "ad_name": name,
                "primary_text": row[col_map["body"]].strip() if "body" in col_map else "",
                "headline": row[col_map["title"]].strip() if "title" in col_map else "",
                "description": row[col_map["ad_description"]].strip() if "ad_description" in col_map else "",
                "cta": row[col_map["cta"]].strip() if "cta" in col_map else "",
            }
            # Skip ads with no text at all
            if ad["primary_text"] or ad["headline"]:
                seen[name] = ad

    return list(seen.values())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Classify raw Meta ads into angle×hook taxonomy")
    parser.add_argument("client", help="Client slug (e.g. tyroola)")
    parser.add_argument("--csv", required=True,
                        help="Path to Meta Ads Manager CSV with ad text columns")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print classifications without writing files")
    parser.add_argument("--no-llm", action="store_true",
                        help="Use deterministic pre-screen only (no API calls)")
    return parser.parse_args()


def main():
    args = parse_args()
    csv_path = Path(args.csv)
    client_dir = root / "clients" / args.client

    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)
    if not client_dir.exists():
        print(f"ERROR: Client not found: {client_dir}", file=sys.stderr)
        print(f"Run: python3 scripts/onboard_client.py --slug {args.client} ...",
              file=sys.stderr)
        sys.exit(1)

    # Load definitions
    hooks = _load_hook_definitions()
    angles = _load_angle_definitions(client_dir)
    print(f"Taxonomy: {len(angles)} angles x {len(hooks)} hooks", file=sys.stderr)

    # Parse CSV
    ads = parse_ads_csv(csv_path)
    print(f"Found {len(ads)} unique ads with text", file=sys.stderr)

    if not ads:
        print("No ads to classify.", file=sys.stderr)
        sys.exit(0)

    # Classify each ad
    output_dir = client_dir / "loop" / "meta-ads"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, ad in enumerate(ads, 1):
        hook_hint = _prescreen_hook(ad["primary_text"] or ad["headline"])

        if args.no_llm:
            classification = {
                "angle": angles[0] if angles else "unknown",
                "hook_type": hook_hint.split(" or ")[0] if hook_hint else "question",
                "confidence": 0.3,
            }
        else:
            classification = _classify_ad(ad, hooks, angles, hook_hint)

        angle = classification["angle"]
        hook = classification["hook_type"]
        conf = classification.get("confidence", 0.0)

        # Build canonical ad JSON
        slug = re.sub(r"[^a-z0-9]+", "-", ad["ad_name"].lower()).strip("-")[:40]
        ad_id = f"{args.client}-{i:03d}"

        canonical = {
            "ad_id": ad_id,
            "original_ad_name": ad["ad_name"],
            "angle": angle,
            "hook_type": hook,
            "funnel": "TOF",
            "primary_text": ad["primary_text"],
            "headline": ad["headline"],
            "description": ad["description"],
            "cta": ad["cta"] or "Learn More",
            "content_type": "meta-ad",
            "source": "classified_from_meta_export",
            "classification_confidence": round(conf, 2),
        }
        results.append(canonical)

        marker = "*" if conf < 0.5 else " "
        print(f"  {marker} {ad_id}  {angle:<25} {hook:<20} "
              f"conf={conf:.2f}  {ad['ad_name'][:40]}")

        if not args.dry_run:
            file_path = output_dir / f"{angle}--{hook}--{slug}.json"
            with open(file_path, "w") as f:
                json.dump(canonical, f, indent=2, ensure_ascii=False)
                f.write("\n")

    # Summary
    print(f"\nClassified {len(results)} ads", file=sys.stderr)
    low_conf = sum(1 for r in results if r["classification_confidence"] < 0.5)
    if low_conf:
        print(f"  {low_conf} ads with low confidence (<0.5) — review manually",
              file=sys.stderr)

    # Print angle×hook distribution
    from collections import Counter
    angle_counts = Counter(r["angle"] for r in results)
    hook_counts = Counter(r["hook_type"] for r in results)
    print(f"\nAngle distribution:", file=sys.stderr)
    for a, c in angle_counts.most_common():
        print(f"  {a}: {c}", file=sys.stderr)
    print(f"\nHook distribution:", file=sys.stderr)
    for h, c in hook_counts.most_common():
        print(f"  {h}: {c}", file=sys.stderr)

    if args.dry_run:
        print(f"\nDry run — no files written. "
              f"Remove --dry-run to write to {output_dir}", file=sys.stderr)
    else:
        print(f"\nWrote {len(results)} files to {output_dir}", file=sys.stderr)

    # Also output JSON summary to stdout for piping
    summary = {
        "client": args.client,
        "total_ads": len(results),
        "low_confidence": low_conf,
        "angle_distribution": dict(angle_counts),
        "hook_distribution": dict(hook_counts),
        "ads": results,
    }
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
