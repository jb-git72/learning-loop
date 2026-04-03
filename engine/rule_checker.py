"""
Rule Checker — Axis 1 of the scoring engine.

Loads universal + client rules, runs binary pass/fail checks against ad text.
100% deterministic — no LLM involvement.

Returns: {score, passed, total, failures, critical_failure}
"""

import json
import re
from pathlib import Path


def load_rules(shared_dir: Path, client_dir: Path) -> list[dict]:
    """Load and merge universal + client rules.

    Client rules with "extends": "universal" start with all universal rules,
    then add client-specific rules. Client rules with the same rule_id
    override the universal version.
    """
    # Load universal rules
    universal_path = shared_dir / "rules-universal.json"
    with open(universal_path) as f:
        universal_data = json.load(f)
    universal_rules = universal_data.get("rules", [])

    # Load client rules
    client_rules_path = client_dir / "rules.json"
    if not client_rules_path.exists():
        return _normalize_rules(universal_rules)

    with open(client_rules_path) as f:
        client_data = json.load(f)

    client_rules = client_data.get("rules", [])

    # If client extends universal, start with universal and add/override
    if client_data.get("extends") == "universal":
        merged = {r["rule_id"]: r for r in universal_rules}
        for rule in client_rules:
            merged[rule["rule_id"]] = rule
        return _normalize_rules(list(merged.values()))

    # Otherwise, just use client rules
    return _normalize_rules(client_rules)


def _normalize_rules(rules: list[dict]) -> list[dict]:
    """Normalize rule format differences between universal and client rules.

    Universal uses: check_type, pattern (single string), fields
    Client uses: type, patterns (array), name
    This normalizes everything to a common format.
    """
    normalized = []
    for rule in rules:
        n = {
            "rule_id": rule.get("rule_id", ""),
            "severity": rule.get("severity", "normal"),
            "message": rule.get("message") or rule.get("description", ""),
        }

        # Normalize check type
        n["check_type"] = rule.get("check_type") or rule.get("type", "regex_absent")

        # Normalize patterns — merge single pattern and patterns array
        patterns = []
        if "pattern" in rule:
            patterns.append(rule["pattern"])
        if "patterns" in rule:
            patterns.extend(rule["patterns"])
        n["patterns"] = patterns

        # Normalize fields
        n["fields"] = rule.get("fields", ["primary_text", "headline", "description"])

        # Custom check function name
        if n["check_type"] in ("custom", "custom_check"):
            n["check_type"] = "custom"
            n["function"] = rule.get("function", rule.get("rule_id", "").replace("-", "_"))
            # For custom checks like low_risk_trio, carry extra config
            if "required_phrases" in rule:
                n["required_phrases"] = rule["required_phrases"]
                n["match_mode"] = rule.get("match_mode", "all_required")
                n["case_sensitive"] = rule.get("case_sensitive", False)

        # Length check
        if n["check_type"] == "length_max":
            n["max_value"] = rule.get("max_value", 500)

        # Severity normalization — treat "high" same as "normal" (not critical)
        if n["severity"] not in ("critical", "normal"):
            if n["severity"] == "high":
                n["severity"] = "normal"
            elif n["severity"] == "medium":
                n["severity"] = "normal"

        normalized.append(n)
    return normalized


def check_rules(ad: dict, rules: list[dict], critical_rules: list[str] = None) -> dict:
    """Run all rules against an ad. Returns score report.

    Args:
        ad: Ad in canonical JSON format
        rules: Merged rule list from load_rules()
        critical_rules: Rule IDs from client config that override to critical severity

    Returns:
        {
            "score": 0.0-1.0,
            "passed": int,
            "total": int,
            "failures": [{"rule_id": str, "field": str, "detail": str, "severity": str}],
            "critical_failure": bool
        }
    """
    critical_rules = critical_rules or []
    failures = []
    total = 0
    passed = 0

    for rule in rules:
        rule_id = rule["rule_id"]
        check_type = rule["check_type"]

        # Override severity if rule_id is in client's critical list
        # Map rule names to IDs for matching (e.g., "no_vet_villain" matches "BFP-001" with name "no_vet_villain")
        severity = rule["severity"]
        rule_name = rule.get("name", rule_id)
        if rule_id in critical_rules or rule_name in critical_rules:
            severity = "critical"

        # Skip body-only rules when ad is a hook (no full primary_text)
        primary_text = ad.get("primary_text", "")
        is_hook_only = len(primary_text) < 100
        body_only_rules = {"low_risk_trio_present", "not_insurance_disclaimer", "BFP-005", "BFP-006"}
        if is_hook_only and (rule_id in body_only_rules or rule_name in body_only_rules):
            continue

        if check_type == "custom":
            result = _run_custom_check(rule, ad)
        elif check_type == "length_max":
            result = _run_length_check(rule, ad)
        elif check_type in ("regex_absent", "regex_present"):
            result = _run_regex_check(rule, ad)
        else:
            # Unknown check type — skip
            continue

        total += 1
        if result["passed"]:
            passed += 1
        else:
            failures.append({
                "rule_id": rule_id,
                "field": result.get("field", ""),
                "detail": result.get("detail", rule["message"]),
                "severity": severity,
            })

    # Check for critical failures
    critical_failure = any(f["severity"] == "critical" for f in failures)

    score = passed / total if total > 0 else 1.0

    return {
        "score": round(score, 4),
        "passed": passed,
        "total": total,
        "failures": failures,
        "critical_failure": critical_failure,
    }


def _run_regex_check(rule: dict, ad: dict) -> dict:
    """Run regex_absent or regex_present check."""
    check_type = rule["check_type"]
    patterns = rule.get("patterns", [])
    fields = rule["fields"]
    case_sensitive = rule.get("case_sensitive", False)

    for field in fields:
        text = ad.get(field, "")
        if not text:
            continue
        for pattern in patterns:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                match = re.search(pattern, text, flags)
            except re.error:
                continue

            if check_type == "regex_absent" and match:
                return {
                    "passed": False,
                    "field": field,
                    "detail": f"Pattern matched in {field}: '{match.group()}' (rule: {rule['rule_id']})",
                }
            elif check_type == "regex_present" and match:
                # Found a match — rule passes (at least one pattern matched)
                return {"passed": True, "field": field}

    # For regex_absent: no pattern matched in any field = pass
    if check_type == "regex_absent":
        return {"passed": True}
    # For regex_present: no pattern matched in any field = fail
    return {
        "passed": False,
        "field": fields[0] if fields else "",
        "detail": f"Required pattern not found in any field (rule: {rule['rule_id']})",
    }


def _run_length_check(rule: dict, ad: dict) -> dict:
    """Run length_max check."""
    max_value = rule.get("max_value", 500)
    fields = rule["fields"]

    for field in fields:
        text = ad.get(field, "")
        if len(text) > max_value:
            return {
                "passed": False,
                "field": field,
                "detail": f"{field} is {len(text)} chars (max {max_value})",
            }
    return {"passed": True}


def _run_custom_check(rule: dict, ad: dict) -> dict:
    """Run custom check functions."""
    func_name = rule.get("function", rule["rule_id"])

    # Route to known custom functions
    if func_name in ("check_lead_with_value_not_price", "lead_with_value_not_price"):
        return _check_lead_with_value_not_price(ad)
    elif func_name in ("check_low_risk_trio", "low_risk_trio_present", "BFP-005"):
        return _check_low_risk_trio(rule, ad)
    elif func_name in ("check_deposit_refundable", "_check_deposit_refundable", "FMTH-010"):
        return _check_deposit_refundable(ad)
    else:
        # Unknown custom function — pass by default
        return {"passed": True}


def _check_lead_with_value_not_price(ad: dict) -> dict:
    """Check that primary_text doesn't open with a dollar amount."""
    text = ad.get("primary_text", "").strip()
    if not text:
        return {"passed": True}

    # Get first non-empty line
    first_line = ""
    for line in text.split("\n"):
        line = line.strip().strip(">").strip()
        if line:
            first_line = line
            break

    if not first_line:
        return {"passed": True}

    # Check if first meaningful token is a dollar amount
    if re.match(r'^\$\d', first_line):
        return {
            "passed": False,
            "field": "primary_text",
            "detail": f"Opens with dollar amount: '{first_line[:40]}...'",
        }
    return {"passed": True}


def _check_low_risk_trio(rule: dict, ad: dict) -> dict:
    """Check that all three low-risk phrases are present."""
    required = rule.get("required_phrases", [
        "no joining fee",
        "no waiting period",
        "cancel anytime",
    ])
    text = ad.get("primary_text", "").lower()

    missing = [phrase for phrase in required if phrase.lower() not in text]

    if missing:
        return {
            "passed": False,
            "field": "primary_text",
            "detail": f"Missing low-risk phrases: {', '.join(missing)}",
        }
    return {"passed": True}


def _check_deposit_refundable(ad: dict) -> dict:
    """Check that when $5 deposit is mentioned, 'refundable' is also present."""
    # Collect all text fields
    fields = [
        "primary_text", "headline", "description",
        "subject", "preheader", "body",
        "hero_copy", "subhead",
    ]
    for field in fields:
        text = ad.get(field, "")
        if not text:
            continue
        text_lower = text.lower()
        # Check if deposit is mentioned
        if re.search(r'\$5\s*(?:deposit|vip|refundable)', text_lower) or "deposit" in text_lower:
            # Must also mention refundable
            if "refundable" not in text_lower:
                return {
                    "passed": False,
                    "field": field,
                    "detail": f"Deposit mentioned in {field} without 'refundable' disclaimer",
                }
    return {"passed": True}
