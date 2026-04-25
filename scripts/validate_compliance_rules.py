#!/usr/bin/env python3
"""Validate compliance_rules.json schema. Exit 0 if valid, 1 if not.

Usage:
    python3 scripts/validate_compliance_rules.py [path/to/compliance_rules.json]

If no path is given, defaults to:
    shared/regulatory/csf-australia/compliance_rules.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VALID_SEVERITIES = {"BLOCKING", "WARNING", "ADVISORY"}
VALID_CHECK_TYPES = {"required_phrase", "regex_forbidden", "llm_judge"}
VALID_CONTENT_TYPES = {
    "email",
    "landing-page",
    "meta-ad",
    "social-post",
    "offer-document",
}
VALID_APPLIES_TO = {"issuer", "intermediary", "both"}

REQUIRED_TOP_KEYS = ("jurisdiction", "regulations_covered", "rules")
REQUIRED_RULE_KEYS = (
    "rule_id",
    "category",
    "claim",
    "source_ref",
    "severity",
    "scope",
    "check_type",
)


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def _resolve_path(argv: list[str]) -> Path:
    if len(argv) > 1:
        return Path(argv[1])
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "shared" / "regulatory" / "csf-australia" / "compliance_rules.json"


def _validate_top_level(data: dict) -> None:
    for key in REQUIRED_TOP_KEYS:
        if key not in data:
            _fail(f"top-level key missing: {key!r}")
    if not isinstance(data["regulations_covered"], list) or not data["regulations_covered"]:
        _fail("regulations_covered must be a non-empty list")
    if not isinstance(data["rules"], list) or not data["rules"]:
        _fail("rules must be a non-empty list")


def _validate_rule(rule: dict, idx: int, seen_ids: set[str]) -> None:
    where = f"rule[{idx}]"
    if not isinstance(rule, dict):
        _fail(f"{where} is not an object")

    for key in REQUIRED_RULE_KEYS:
        if key not in rule:
            _fail(f"{where} missing required key: {key!r}")

    rule_id = rule["rule_id"]
    if not isinstance(rule_id, str) or not rule_id:
        _fail(f"{where} rule_id must be a non-empty string")
    if rule_id in seen_ids:
        _fail(f"duplicate rule_id: {rule_id!r}")
    seen_ids.add(rule_id)

    where = f"rule {rule_id!r}"

    severity = rule["severity"]
    if severity not in VALID_SEVERITIES:
        _fail(f"{where}: severity must be one of {sorted(VALID_SEVERITIES)} (got {severity!r})")

    check_type = rule["check_type"]
    if check_type not in VALID_CHECK_TYPES:
        _fail(
            f"{where}: check_type must be one of {sorted(VALID_CHECK_TYPES)} (got {check_type!r})"
        )

    if not isinstance(rule.get("source_ref"), list) or not rule["source_ref"]:
        _fail(f"{where}: source_ref must be a non-empty list")

    scope = rule.get("scope", {})
    if not isinstance(scope, dict):
        _fail(f"{where}: scope must be an object")

    content_types = scope.get("content_types", [])
    if not isinstance(content_types, list) or not content_types:
        _fail(f"{where}: scope.content_types must be a non-empty list")
    for ct in content_types:
        if ct not in VALID_CONTENT_TYPES:
            _fail(
                f"{where}: scope.content_types contains invalid type {ct!r} "
                f"(valid: {sorted(VALID_CONTENT_TYPES)})"
            )

    applies_to = scope.get("applies_to", "")
    if applies_to not in VALID_APPLIES_TO:
        _fail(
            f"{where}: scope.applies_to must be one of {sorted(VALID_APPLIES_TO)} "
            f"(got {applies_to!r})"
        )

    # Type-specific payload checks
    if check_type == "required_phrase":
        patterns = rule.get("required_phrase_patterns", [])
        if not isinstance(patterns, list) or not patterns:
            _fail(f"{where}: required_phrase_patterns must be a non-empty list")
        _validate_regex_list(patterns, where, "required_phrase_patterns")

    elif check_type == "regex_forbidden":
        patterns = rule.get("forbidden_patterns", [])
        if not isinstance(patterns, list) or not patterns:
            _fail(f"{where}: forbidden_patterns must be a non-empty list")
        _validate_regex_list(patterns, where, "forbidden_patterns")
        # whitelist_contexts is optional; if present must be a list of strings
        wl = rule.get("whitelist_contexts", [])
        if wl and not (isinstance(wl, list) and all(isinstance(s, str) for s in wl)):
            _fail(f"{where}: whitelist_contexts must be a list of strings if present")

    elif check_type == "llm_judge":
        prompt = rule.get("llm_prompt", "")
        if not isinstance(prompt, str) or not prompt.strip():
            _fail(f"{where}: llm_prompt must be a non-empty string")


def _validate_regex_list(patterns: list, where: str, field_name: str) -> None:
    for i, pat in enumerate(patterns):
        if not isinstance(pat, str) or not pat:
            _fail(f"{where}: {field_name}[{i}] must be a non-empty string")
        try:
            re.compile(pat)
        except re.error as e:
            _fail(f"{where}: {field_name}[{i}] is not a valid regex ({pat!r}): {e}")


def main(argv: list[str]) -> int:
    path = _resolve_path(argv)
    if not path.exists():
        _fail(f"rules file not found: {path}")

    try:
        with open(path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        _fail(f"{path} is not valid JSON: {e}")

    _validate_top_level(data)

    seen: set[str] = set()
    for i, rule in enumerate(data["rules"]):
        _validate_rule(rule, i, seen)

    print(
        f"OK: {path.name} valid — "
        f"{len(data['rules'])} rules across {len(data['regulations_covered'])} regulations"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
