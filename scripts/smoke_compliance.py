#!/usr/bin/env python3
"""End-to-end smoke test for engine/compliance_checker.py.

Runs three fixture inputs through check_compliance() and prints a
human-readable report. Exits 0 when every fixture produced its expected
result, 1 otherwise. LLM checks are disabled — this is purely the
deterministic path.

Usage:
    python3 scripts/smoke_compliance.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.compliance_checker import check_compliance  # noqa: E402


FIXTURES = [
    {
        "name": "ADV-002 multi-violation (specific $ amounts)",
        "text": "Invest $50 today and receive a $5 refundable VIP deposit!",
        "content_type": "meta-ad",
        "expect_blocking": ["ADV-002"],
        "expect_passed": False,
    },
    {
        "name": "ADV-003 anti-hawking (reply-to-invest)",
        "text": "Reply to this email to apply for shares.",
        "content_type": "email",
        "expect_blocking": ["ADV-003"],
        "expect_passed": False,
    },
    {
        "name": "ADV-001 satisfied (canonical CSF warning present)",
        "text": "Always consider the general CSF risk warning and offer document before investing.",
        "content_type": "email",
        "expect_blocking_excludes": ["ADV-001"],
        "expect_passed": True,
    },
]


def _format_violation(v) -> str:
    return (
        f"      [{v.severity}] {v.rule_id}\n"
        f"        matched: {v.matched_text!r}\n"
        f"        context: {v.line_hint}\n"
        f"        fix:     {v.fix_message}"
    )


def _check_expectations(fixture: dict, result) -> tuple[bool, list[str]]:
    failures: list[str] = []

    blocking_ids = [v.rule_id for v in result.blocking_violations]

    for required in fixture.get("expect_blocking", []):
        if required not in blocking_ids:
            failures.append(
                f"expected BLOCKING violation {required!r} not present "
                f"(got: {blocking_ids})"
            )

    for forbidden in fixture.get("expect_blocking_excludes", []):
        if forbidden in blocking_ids:
            failures.append(
                f"unexpected BLOCKING violation {forbidden!r} present "
                f"(got: {blocking_ids})"
            )

    if fixture["expect_passed"] != result.passed:
        failures.append(
            f"passed={result.passed} but expected passed={fixture['expect_passed']}"
        )

    return (len(failures) == 0, failures)


def main() -> int:
    print("=" * 72)
    print("Compliance checker smoke test (LLM disabled)")
    print("=" * 72)

    overall_pass = True

    for fixture in FIXTURES:
        print()
        print(f"FIXTURE: {fixture['name']}")
        print(f"  content_type: {fixture['content_type']}")
        print(f"  text: {fixture['text']!r}")

        result = check_compliance(
            fixture["text"],
            content_type=fixture["content_type"],
            enable_llm=False,
        )

        print(
            f"  result: passed={result.passed}, "
            f"rules_evaluated={result.rules_evaluated}, "
            f"out_of_scope={result.rules_skipped_out_of_scope}"
        )

        if result.blocking_violations:
            print(f"  blocking ({len(result.blocking_violations)}):")
            for v in result.blocking_violations:
                print(_format_violation(v))
        if result.warnings:
            print(f"  warnings ({len(result.warnings)}):")
            for v in result.warnings:
                print(_format_violation(v))
        if result.advisory:
            print(f"  advisory ({len(result.advisory)}):")
            for v in result.advisory:
                print(_format_violation(v))

        ok, failures = _check_expectations(fixture, result)
        if ok:
            print("  expectation: OK")
        else:
            overall_pass = False
            print("  expectation: FAIL")
            for f in failures:
                print(f"    - {f}")

    print()
    print("=" * 72)
    print("SMOKE TEST: " + ("PASS" if overall_pass else "FAIL"))
    print("=" * 72)
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
