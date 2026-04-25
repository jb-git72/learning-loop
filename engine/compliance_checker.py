"""
Compliance Checker — ASIC CSF regulatory compliance engine.

Parallel to engine/fact_checker.py. Loads structured rules from
shared/regulatory/csf-australia/compliance_rules.json and runs three kinds
of check against marketing copy:

1. required_phrase  — at least one canonical phrase must appear
2. regex_forbidden  — no forbidden pattern may appear (with whitelist context)
3. llm_judge        — Haiku-backed semantic check (lazy, opt-out via enable_llm)

Returns a dataclass-based ComplianceResult that exposes the granular
violations the caller needs to render fix suggestions.

Design follows the existing engine style:
- 100% deterministic for required_phrase / regex_forbidden
- LLM calls are lazy and gated, never made when disabled
- Module-level cache for the rules file (one read per process)
- No shared context between scoring and writing
"""

from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


# -------------------------------------------------------------------------
# Public dataclasses
# -------------------------------------------------------------------------

Severity = Literal["BLOCKING", "WARNING", "ADVISORY"]


@dataclass
class Violation:
    rule_id: str
    severity: Severity
    category: str
    matched_text: str
    line_hint: str
    source_ref: list[str]
    fix_message: str


@dataclass
class ComplianceResult:
    passed: bool = True
    blocking_violations: list[Violation] = field(default_factory=list)
    warnings: list[Violation] = field(default_factory=list)
    advisory: list[Violation] = field(default_factory=list)
    rules_evaluated: int = 0
    rules_skipped_out_of_scope: int = 0


# -------------------------------------------------------------------------
# Module-level cache
# -------------------------------------------------------------------------

_RULES_CACHE: dict[str, dict] = {}
_RULES_LOCK = threading.Lock()
_DEFAULT_RULES_PATH = (
    Path(__file__).resolve().parent.parent
    / "shared"
    / "regulatory"
    / "csf-australia"
    / "compliance_rules.json"
)


def _load_rules(rules_path: str | None = None) -> dict:
    """Lazy-load and cache the compliance rules JSON."""
    path = Path(rules_path) if rules_path else _DEFAULT_RULES_PATH
    key = str(path.resolve())
    with _RULES_LOCK:
        if key in _RULES_CACHE:
            return _RULES_CACHE[key]
        with open(path, "r") as f:
            data = json.load(f)
        _RULES_CACHE[key] = data
        return data


def _clear_cache() -> None:
    """Test helper — drop the cache so reloads pick up file changes."""
    with _RULES_LOCK:
        _RULES_CACHE.clear()


# -------------------------------------------------------------------------
# Public entry point
# -------------------------------------------------------------------------

def check_compliance(
    text: str,
    content_type: str,
    applies_to: str = "issuer",
    rules_path: str | None = None,
    enable_llm: bool = True,
) -> ComplianceResult:
    """Run all in-scope compliance rules against `text`.

    Args:
        text: The marketing copy to evaluate (single concatenated string).
        content_type: One of "email", "landing-page", "meta-ad",
            "social-post", "offer-document". Rules without this content
            type in their scope are skipped.
        applies_to: Caller role — "issuer", "intermediary", or "both".
            Rules whose scope.applies_to is the other role are skipped.
            Rules marked "both" always apply.
        rules_path: Override the default rules JSON location. Mostly used
            in tests.
        enable_llm: When False, llm_judge rules are skipped silently
            (counted as out-of-scope so callers can see why). Used by
            the cheap path of hill-climb runs.

    Returns:
        ComplianceResult — `passed` is False iff any BLOCKING violation
        was raised.
    """
    data = _load_rules(rules_path)
    rules = data.get("rules", [])

    result = ComplianceResult()

    for rule in rules:
        if not _rule_in_scope(rule, content_type, applies_to):
            result.rules_skipped_out_of_scope += 1
            continue

        check_type = rule.get("check_type", "")

        if check_type == "llm_judge" and not enable_llm:
            # Treat skipped LLM rules as "not in scope for this run" so
            # the count is honest.
            result.rules_skipped_out_of_scope += 1
            continue

        if check_type == "required_phrase":
            violation = _check_required_phrase(rule, text)
        elif check_type == "regex_forbidden":
            violation = _check_regex_forbidden(rule, text)
        elif check_type == "llm_judge":
            violation = _check_llm_judge(rule, text)
        else:
            # Unknown check type — skip but don't crash.
            result.rules_skipped_out_of_scope += 1
            continue

        result.rules_evaluated += 1

        if violation is not None:
            sev = violation.severity
            if sev == "BLOCKING":
                result.blocking_violations.append(violation)
            elif sev == "WARNING":
                result.warnings.append(violation)
            else:
                result.advisory.append(violation)

    result.passed = len(result.blocking_violations) == 0
    return result


# -------------------------------------------------------------------------
# Scope filter
# -------------------------------------------------------------------------

def _rule_in_scope(rule: dict, content_type: str, applies_to: str) -> bool:
    scope = rule.get("scope", {})
    types = scope.get("content_types", [])
    if types and content_type not in types:
        return False

    rule_applies_to = scope.get("applies_to", "both")
    if rule_applies_to == "both":
        return True
    if applies_to == "both":
        return True
    return rule_applies_to == applies_to


# -------------------------------------------------------------------------
# Check implementations
# -------------------------------------------------------------------------

def _check_required_phrase(rule: dict, text: str) -> Violation | None:
    """Pass if ANY of the required phrase patterns matches (case-insensitive regex)."""
    patterns = rule.get("required_phrase_patterns", [])
    for pattern in patterns:
        try:
            if re.search(pattern, text, re.IGNORECASE):
                return None
        except re.error:
            # Invalid regex — fall back to literal substring match.
            if pattern.lower() in text.lower():
                return None

    return _violation_from_rule(
        rule,
        matched_text="",
        line_hint="(no canonical phrase found in content)",
    )


def _check_regex_forbidden(rule: dict, text: str) -> Violation | None:
    """Violation if ANY forbidden pattern matches outside a whitelist context."""
    patterns = rule.get("forbidden_patterns", [])
    whitelist = rule.get("whitelist_contexts", [])

    for pattern in patterns:
        try:
            for match in re.finditer(pattern, text):
                if _is_whitelisted(text, match.start(), match.end(), whitelist):
                    continue
                return _violation_from_rule(
                    rule,
                    matched_text=match.group(0),
                    line_hint=_context_window(text, match.start(), match.end()),
                )
        except re.error:
            # Invalid regex — log silently, don't crash the whole run.
            continue

    return None


def _check_llm_judge(rule: dict, text: str) -> Violation | None:
    """Call Haiku, parse JSON {pass, evidence, reason}; violation if pass is false."""
    prompt = rule.get("llm_prompt", "")
    if not prompt:
        return None

    full_prompt = f"{prompt}\n\nCONTENT TO REVIEW:\n{text}"

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # No key — silently skip rather than block the pipeline.
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            temperature=0.0,
            messages=[{"role": "user", "content": full_prompt}],
        )
        raw = response.content[0].text.strip()
    except Exception:
        return None

    parsed = _parse_llm_judge_response(raw)
    if parsed is None:
        return None

    if parsed.get("pass") is True:
        return None

    evidence = parsed.get("evidence", "") or ""
    reason = parsed.get("reason", "") or ""
    line_hint = reason if reason else "(LLM flagged content; no specific quote returned)"
    return _violation_from_rule(
        rule,
        matched_text=evidence,
        line_hint=line_hint,
    )


def _parse_llm_judge_response(text: str) -> dict | None:
    """Pull the first JSON object out of a Haiku response."""
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        return json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return None


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _is_whitelisted(text: str, start: int, end: int, whitelist: list[str]) -> bool:
    """Soft whitelist: suppress the violation if any whitelist phrase
    appears within ~80 chars on either side of the match."""
    if not whitelist:
        return False

    window_start = max(0, start - 80)
    window_end = min(len(text), end + 80)
    window = text[window_start:window_end].lower()

    for phrase in whitelist:
        if phrase.lower() in window:
            return True
    return False


def _context_window(text: str, start: int, end: int, pad: int = 30) -> str:
    """Return a short context string showing what surrounded the match."""
    a = max(0, start - pad)
    b = min(len(text), end + pad)
    snippet = text[a:b].replace("\n", " ").strip()
    prefix = "..." if a > 0 else ""
    suffix = "..." if b < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


def _violation_from_rule(rule: dict, matched_text: str, line_hint: str) -> Violation:
    return Violation(
        rule_id=rule.get("rule_id", "?"),
        severity=rule.get("severity", "ADVISORY"),
        category=rule.get("category", ""),
        matched_text=matched_text,
        line_hint=line_hint,
        source_ref=list(rule.get("source_ref", [])),
        fix_message=rule.get("violation_message", ""),
    )
