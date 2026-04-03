#!/usr/bin/env python3
"""
Content Linter — Pre-flight gate before scoring.

Three layers:
  1. Rule compliance (reuses engine.rule_checker)
  2. Learnings violations (parses learnings.md "What Fails" section)
  3. Structural validation (field lengths, required fields, hardened blocklist)

Catches violations BEFORE scoring, saving API calls and preventing bad
content from reaching the human reviewer.

Usage:
  python3 scripts/lint_content.py farm-thru                   # lint all content
  python3 scripts/lint_content.py farm-thru --type=meta-ad    # lint only meta-ads
  python3 scripts/lint_content.py farm-thru --file=path.json  # lint single file

Exit code 0 if all pass, 1 if any fail.
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
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

from engine.rule_checker import load_rules, check_rules


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class LintResult:
    passed: bool
    violations: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    summary: str = ""


# ---------------------------------------------------------------------------
# Required fields per content type
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {
    "meta-ad": ["primary_text", "headline", "description", "cta"],
    "landing-page": ["headline", "subhead", "hero_copy", "cta"],
    "email": ["subject", "preheader", "body", "cta"],
}

# Hardened blocklist for investment terms in meta-ads.
# These are terms that should NEVER appear in any meta-ad field.
META_AD_INVESTMENT_BLOCKLIST = [
    r"\$50\b",
    r"\$10[Kk]?\b",
    r"\bequity\s+crowdfunding\b",
    r"\bBirchal\b",
    r"\b[Nn]ot\s+financial\s+advice\b",
    r"\bminimum\s+investment\b",
    r"\$5\s+deposit\b",
]


# ---------------------------------------------------------------------------
# Layer 1 — Rule compliance
# ---------------------------------------------------------------------------

def _check_rule_compliance(ad: dict, rules: list, config: dict) -> list:
    """Run rule_checker against the ad, filtering rules by content_type."""
    content_type = ad.get("content_type", "meta-ad")

    # Pre-filter rules by content_types field if present
    filtered_rules = []
    for rule in rules:
        rule_cts = rule.get("content_types")
        if rule_cts and content_type not in rule_cts:
            continue
        filtered_rules.append(rule)

    critical_rules = config.get("critical_rules", [])
    result = check_rules(ad, filtered_rules, critical_rules)

    violations = []
    for failure in result["failures"]:
        violations.append({
            "layer": "rules",
            "rule_id": failure["rule_id"],
            "field": failure.get("field", ""),
            "detail": failure.get("detail", ""),
            "severity": failure.get("severity", "normal"),
        })
    return violations


# ---------------------------------------------------------------------------
# Layer 2 — Learnings violations
# ---------------------------------------------------------------------------

def _parse_learnings_bans(learnings_text: str) -> list:
    """Parse the 'What Fails' section of learnings.md.

    Extracts lines starting with '- NEVER', '- No ', '- Don't'.
    Pulls quoted terms in double quotes as banned terms, but only
    those appearing in the "ban" part of the sentence, not in the
    "do this instead" part (after 'Say', 'use', 'tease with', etc.).
    """
    bans = []

    # Find the "What Fails" section
    in_section = False
    for line in learnings_text.split("\n"):
        stripped = line.strip()

        # Detect section headers
        if re.match(r"^#+\s+What Fails", stripped, re.IGNORECASE):
            in_section = True
            continue
        if in_section and re.match(r"^#+\s+", stripped) and "What Fails" not in stripped:
            # Hit the next section header — stop
            break

        if not in_section:
            continue

        # Only process lines starting with the target prefixes
        if not re.match(r"^-\s+(NEVER|No\s|Don't\s)", stripped):
            continue

        # Split line into "ban part" vs "alternative part".
        # Alternatives follow: ". Say ", ". Use ", ", tease with ", ", instead "
        alternative_split = re.split(
            r"(?:\.\s+[Ss]ay\s|\.\s+[Uu]se\s|,\s+tease\s+with\s|,\s+instead\s)",
            stripped,
            maxsplit=1,
        )
        ban_part = alternative_split[0]

        # Extract quoted terms only from the ban part
        quoted_terms = re.findall(r'"([^"]+)"', ban_part)

        # Detect content-type scope
        scope = None  # None means all content types
        if "in meta-ad" in stripped.lower() or "in meta ad" in stripped.lower():
            scope = "meta-ad"
        elif "in landing page" in stripped.lower():
            scope = "landing-page"
        elif "in email" in stripped.lower():
            scope = "email"

        bans.append({
            "line": stripped,
            "banned_terms": quoted_terms,
            "scope": scope,
        })

    return bans


def _check_learnings_violations(ad: dict, client_dir: Path) -> list:
    """Check ad text fields against banned patterns from learnings.md."""
    learnings_path = client_dir / "learnings.md"
    if not learnings_path.exists():
        return []

    with open(learnings_path) as f:
        learnings_text = f.read()

    bans = _parse_learnings_bans(learnings_text)
    content_type = ad.get("content_type", "meta-ad")

    # Collect all text fields
    text_fields = _get_text_fields(ad)

    violations = []
    for ban in bans:
        # Skip if this ban doesn't apply to the current content type
        if ban["scope"] and ban["scope"] != content_type:
            continue

        for term in ban["banned_terms"]:
            for field_name, field_text in text_fields.items():
                if not field_text:
                    continue
                if term.lower() in field_text.lower():
                    violations.append({
                        "layer": "learnings",
                        "rule_id": f"learnings-ban:{term[:30]}",
                        "field": field_name,
                        "detail": f'Banned term "{term}" found in {field_name} (from learnings: {ban["line"][:80]})',
                        "severity": "critical" if "NEVER" in ban["line"] else "normal",
                    })

    return violations


# ---------------------------------------------------------------------------
# Layer 3 — Structural validation
# ---------------------------------------------------------------------------

def _check_structural(ad: dict, config: dict) -> list:
    """Check field lengths, required fields, and hardened blocklist."""
    content_type = ad.get("content_type", "meta-ad")
    violations = []
    warnings = []

    # 3a. Required fields
    required = REQUIRED_FIELDS.get(content_type, [])
    for field_name in required:
        value = ad.get(field_name, "")
        if not value or not value.strip():
            violations.append({
                "layer": "structural",
                "rule_id": f"required-field:{field_name}",
                "field": field_name,
                "detail": f"Required field '{field_name}' is empty for content_type={content_type}",
                "severity": "critical",
            })

    # 3b. Field length checks against platform_constraints
    constraints = config.get("platform_constraints", {})
    ct_constraints = constraints.get(content_type, {})
    for key, max_chars in ct_constraints.items():
        if not key.endswith("_max_chars"):
            continue
        field_name = key.replace("_max_chars", "")
        text = ad.get(field_name, "")
        if text and len(text) > max_chars:
            violations.append({
                "layer": "structural",
                "rule_id": f"length:{field_name}",
                "field": field_name,
                "detail": f"{field_name} is {len(text)} chars (max {max_chars})",
                "severity": "normal",
            })

    # For landing pages, check section body lengths
    if content_type == "landing-page":
        section_max = ct_constraints.get("section_body_max_chars", 1000)
        for i, section in enumerate(ad.get("sections", [])):
            if isinstance(section, dict):
                body = section.get("body", "")
                if len(body) > section_max:
                    violations.append({
                        "layer": "structural",
                        "rule_id": f"length:section[{i}].body",
                        "field": f"sections[{i}].body",
                        "detail": f"Section {i} body is {len(body)} chars (max {section_max})",
                        "severity": "normal",
                    })

    # 3c. Hardened investment blocklist for meta-ads
    if content_type == "meta-ad":
        text_fields = _get_text_fields(ad)
        for field_name, field_text in text_fields.items():
            if not field_text:
                continue
            for pattern in META_AD_INVESTMENT_BLOCKLIST:
                match = re.search(pattern, field_text, re.IGNORECASE)
                if match:
                    violations.append({
                        "layer": "structural",
                        "rule_id": "meta-ad-investment-blocklist",
                        "field": field_name,
                        "detail": f'Investment term "{match.group()}" found in meta-ad {field_name}',
                        "severity": "critical",
                    })

    return violations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_text_fields(ad: dict) -> dict:
    """Return a dict of field_name -> text for all text fields in the ad."""
    fields = {}
    for key in [
        "primary_text", "headline", "description",
        "subject", "preheader", "body",
        "hero_copy", "subhead",
    ]:
        text = ad.get(key, "")
        if text:
            fields[key] = text
    # Also include section content for landing pages
    for i, section in enumerate(ad.get("sections", [])):
        if isinstance(section, dict):
            for sub_key in ("heading", "body"):
                text = section.get(sub_key, "")
                if text:
                    fields[f"sections[{i}].{sub_key}"] = text
    return fields


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def lint(ad: dict, client_dir: Path, shared_dir: Path) -> LintResult:
    """Lint a single ad/content item.

    Args:
        ad: Content item in canonical JSON format
        client_dir: Path to client config directory
        shared_dir: Path to shared/ directory

    Returns:
        LintResult with passed, violations, warnings, summary
    """
    config = json.loads((client_dir / "config.json").read_text())
    rules = load_rules(shared_dir, client_dir)

    all_violations = []

    # Layer 1 — Rule compliance
    all_violations.extend(_check_rule_compliance(ad, rules, config))

    # Layer 2 — Learnings violations
    all_violations.extend(_check_learnings_violations(ad, client_dir))

    # Layer 3 — Structural validation
    all_violations.extend(_check_structural(ad, config))

    # Deduplicate by (rule_id, field)
    seen = set()
    unique_violations = []
    for v in all_violations:
        key = (v["rule_id"], v["field"])
        if key not in seen:
            seen.add(key)
            unique_violations.append(v)

    critical = [v for v in unique_violations if v["severity"] == "critical"]
    normal = [v for v in unique_violations if v["severity"] != "critical"]
    passed = len(critical) == 0

    ad_id = ad.get("ad_id", ad.get("page_id", ad.get("email_id", "?")))
    content_type = ad.get("content_type", "meta-ad")
    summary = (
        f"{ad_id} ({content_type}): "
        f"{'PASS' if passed else 'FAIL'} "
        f"({len(critical)} critical, {len(normal)} warnings)"
    )

    return LintResult(
        passed=passed,
        violations=critical,
        warnings=normal,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _collect_items(client_dir: Path, type_filter: str = None, single_file: str = None) -> list:
    """Collect content items to lint."""
    items = []

    if single_file:
        path = Path(single_file)
        if not path.is_absolute():
            path = root / path
        with open(path) as f:
            ad = json.load(f)
        items.append({"path": path, "ad": ad})
        return items

    loop_dir = client_dir / "loop"
    for subdir in ["meta-ads", "landing-pages", "emails"]:
        content_dir = loop_dir / subdir
        if not content_dir.exists():
            continue
        for f in sorted(content_dir.iterdir()):
            if f.suffix == ".json" and f.name not in ("test-ad.json", "review-batch.json"):
                with open(f) as fh:
                    ad = json.load(fh)
                items.append({"path": f, "ad": ad})

    if type_filter:
        items = [i for i in items if i["ad"].get("content_type") == type_filter]

    return items


def main():
    # Parse args
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/lint_content.py <client-id> [--type=meta-ad] [--file=path.json]")
        sys.exit(1)

    client_id = sys.argv[1]
    type_filter = None
    single_file = None
    for arg in sys.argv[2:]:
        if arg.startswith("--type="):
            type_filter = arg.split("=", 1)[1]
        elif arg.startswith("--file="):
            single_file = arg.split("=", 1)[1]

    client_dir = root / "clients" / client_id
    shared_dir = root / "shared"

    if not client_dir.exists():
        print(f"Client directory not found: {client_dir}")
        sys.exit(1)

    items = _collect_items(client_dir, type_filter, single_file)
    if not items:
        print("No content items found to lint.")
        sys.exit(0)

    print(f"Linting {len(items)} items for client '{client_id}'")
    if type_filter:
        print(f"  Filtered to content_type={type_filter}")
    print()

    total_pass = 0
    total_fail = 0
    all_results = []

    for item in items:
        result = lint(item["ad"], client_dir, shared_dir)
        all_results.append((item, result))

        if result.passed:
            total_pass += 1
            print(f"  PASS  {result.summary}")
        else:
            total_fail += 1
            print(f"  FAIL  {result.summary}")
            for v in result.violations:
                print(f"        [{v['layer']}] {v['rule_id']} in {v['field']}: {v['detail']}")
            for w in result.warnings:
                print(f"        [warn] {w['rule_id']} in {w['field']}: {w['detail']}")

    print()
    print(f"=== LINT COMPLETE: {total_pass} passed, {total_fail} failed out of {len(items)} ===")

    if total_fail > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
