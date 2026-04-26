#!/usr/bin/env python3
"""Evaluate the compliance checker's per-rule accuracy against labeled fixtures.

For every fixture in `engine/tests/fixtures/compliance/`:
  1. Load text + content_type + applies_to + expected{rule_id: pass|fail}.
  2. Run engine.compliance_checker.check_compliance().
  3. For each rule_id the fixture labels, compare expected vs actual:
       expected=fail, actual=fail   → True Positive  (rule caught it)
       expected=pass, actual=fail   → False Positive (noise)
       expected=fail, actual=pass   → False Negative (missed)
       expected=pass, actual=pass   → True Negative

Reports per-rule precision/recall/F1 + overall accuracy + the specific
fixtures the checker got wrong, with the offending text snippet so
calibration can target the right rule prompts.

Usage:
    python3 scripts/eval_compliance_accuracy.py
    python3 scripts/eval_compliance_accuracy.py --no-llm
    python3 scripts/eval_compliance_accuracy.py --model claude-opus-4-7
    python3 scripts/eval_compliance_accuracy.py --rule MISL-001
    python3 scripts/eval_compliance_accuracy.py --out report.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from engine import compliance_checker  # noqa: E402


DEFAULT_FIXTURES_DIR = REPO_ROOT / "engine" / "tests" / "fixtures" / "compliance"
DEFAULT_OUT = REPO_ROOT / "engine" / "tests" / "fixtures" / "compliance" / "ACCURACY-REPORT.md"


# -------------------------------------------------------------------------
# Data model
# -------------------------------------------------------------------------

@dataclass
class FixtureRow:
    fixture_id: str
    rule_id: str
    expected: str       # "pass" | "fail"
    actual: str         # "pass" | "fail" | "out_of_scope"
    text_snippet: str
    severity: str       # severity from the rule definition


@dataclass
class RuleStats:
    rule_id: str
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0
    out_of_scope: int = 0

    @property
    def total_labeled(self) -> int:
        return self.tp + self.fp + self.tn + self.fn

    @property
    def accuracy(self) -> float:
        n = self.total_labeled
        return (self.tp + self.tn) / n if n else 0.0

    @property
    def precision(self) -> float:
        d = self.tp + self.fp
        return self.tp / d if d else 0.0

    @property
    def recall(self) -> float:
        d = self.tp + self.fn
        return self.tp / d if d else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


# -------------------------------------------------------------------------
# Fixture loader
# -------------------------------------------------------------------------

REQUIRED_FIELDS = {"fixture_id", "text", "content_type", "applies_to", "expected"}


def load_fixtures(fixtures_dir: Path) -> list[dict]:
    out: list[dict] = []
    for p in sorted(fixtures_dir.glob("*.json")):
        try:
            with open(p) as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"  ! {p.name} not valid JSON: {exc}", file=sys.stderr)
            continue
        missing = REQUIRED_FIELDS - data.keys()
        if missing:
            print(f"  ! {p.name} missing fields {missing}; skipping", file=sys.stderr)
            continue
        if not isinstance(data["expected"], dict) or not data["expected"]:
            print(f"  ! {p.name} expected must be non-empty dict; skipping", file=sys.stderr)
            continue
        for rule_id, label in data["expected"].items():
            if label not in {"pass", "fail"}:
                print(
                    f"  ! {p.name} expected[{rule_id}]={label!r} must be 'pass' or 'fail'; "
                    f"skipping fixture",
                    file=sys.stderr,
                )
                break
        else:
            data["_source"] = p.name
            out.append(data)
    return out


# -------------------------------------------------------------------------
# Rule lookup (for severity tagging in report)
# -------------------------------------------------------------------------

def load_rule_index(rules_path: Path | None = None) -> dict[str, dict]:
    data = compliance_checker._load_rules(str(rules_path) if rules_path else None)
    return {r["rule_id"]: r for r in data.get("rules", [])}


# -------------------------------------------------------------------------
# Evaluation core
# -------------------------------------------------------------------------

def evaluate_fixture(
    fixture: dict,
    enable_llm: bool,
    model: str | None,
) -> compliance_checker.ComplianceResult:
    return compliance_checker.check_compliance(
        text=fixture["text"],
        content_type=fixture["content_type"],
        applies_to=fixture["applies_to"],
        enable_llm=enable_llm,
        model=model,
    )


def _actual_label(rule_id: str, result: compliance_checker.ComplianceResult) -> str:
    """Turn a ComplianceResult into 'fail'/'pass'/'out_of_scope' for one rule."""
    fired_ids = (
        {v.rule_id for v in result.blocking_violations}
        | {v.rule_id for v in result.warnings}
        | {v.rule_id for v in result.advisory}
    )
    if rule_id in fired_ids:
        return "fail"
    if rule_id in set(result.evaluated_rule_ids):
        return "pass"
    return "out_of_scope"


def collect_rows(
    fixtures: list[dict],
    enable_llm: bool,
    model: str | None,
    rule_index: dict[str, dict],
    rule_filter: str | None,
) -> list[FixtureRow]:
    rows: list[FixtureRow] = []
    for fx in fixtures:
        result = evaluate_fixture(fx, enable_llm=enable_llm, model=model)
        snippet = fx["text"][:120].replace("\n", " ").strip()
        for rule_id, expected in fx["expected"].items():
            if rule_filter and rule_id != rule_filter:
                continue
            actual = _actual_label(rule_id, result)
            sev = rule_index.get(rule_id, {}).get("severity", "?")
            rows.append(
                FixtureRow(
                    fixture_id=fx["fixture_id"],
                    rule_id=rule_id,
                    expected=expected,
                    actual=actual,
                    text_snippet=snippet,
                    severity=sev,
                )
            )
    return rows


def aggregate(rows: list[FixtureRow]) -> dict[str, RuleStats]:
    stats: dict[str, RuleStats] = {}
    for row in rows:
        s = stats.setdefault(row.rule_id, RuleStats(rule_id=row.rule_id))
        if row.actual == "out_of_scope":
            s.out_of_scope += 1
            continue
        if row.expected == "fail" and row.actual == "fail":
            s.tp += 1
        elif row.expected == "pass" and row.actual == "fail":
            s.fp += 1
        elif row.expected == "pass" and row.actual == "pass":
            s.tn += 1
        elif row.expected == "fail" and row.actual == "pass":
            s.fn += 1
    return stats


# -------------------------------------------------------------------------
# Reporting
# -------------------------------------------------------------------------

def render_report(
    rows: list[FixtureRow],
    stats: dict[str, RuleStats],
    *,
    enable_llm: bool,
    model: str | None,
    n_fixtures: int,
) -> str:
    total_rows = len(rows)
    total_correct = sum(1 for r in rows if r.expected == r.actual)
    overall_acc = total_correct / total_rows if total_rows else 0.0
    out_of_scope = sum(s.out_of_scope for s in stats.values())

    lines: list[str] = []
    lines.append("# Compliance accuracy evaluation")
    lines.append("")
    lines.append(f"- Fixtures loaded: {n_fixtures}")
    lines.append(f"- Total rule labels evaluated: {total_rows}")
    lines.append(f"- LLM mode: {'ENABLED — ' + (model or compliance_checker._DEFAULT_MODEL) if enable_llm else 'disabled'}")
    lines.append(f"- Overall accuracy: **{overall_acc:.1%}** ({total_correct}/{total_rows})")
    lines.append(f"- Labels skipped because rule was out-of-scope for the fixture: {out_of_scope}")
    lines.append("")

    # Per-rule table sorted by F1 descending (worst at the bottom)
    lines.append("## Per-rule scoreboard")
    lines.append("")
    lines.append("| Rule | Sev | Labeled | TP | FP | TN | FN | Acc | Prec | Rec | F1 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    sorted_stats = sorted(
        stats.values(), key=lambda s: (s.f1, s.accuracy), reverse=True
    )
    for s in sorted_stats:
        if s.total_labeled == 0:
            continue
        lines.append(
            f"| {s.rule_id} | {_severity_for(s.rule_id, rows)} | {s.total_labeled} "
            f"| {s.tp} | {s.fp} | {s.tn} | {s.fn} "
            f"| {s.accuracy:.0%} | {s.precision:.0%} | {s.recall:.0%} | {s.f1:.2f} |"
        )
    lines.append("")

    # False positives (noise — calibration target)
    fps = [r for r in rows if r.expected == "pass" and r.actual == "fail"]
    if fps:
        lines.append(f"## False positives ({len(fps)}) — rule fired but should have passed")
        lines.append("")
        for r in fps:
            lines.append(f"- **[{r.rule_id}]** `{r.fixture_id}`")
            lines.append(f"  - text: `{r.text_snippet}...`")
        lines.append("")

    # False negatives (missed catches — accuracy target)
    fns = [r for r in rows if r.expected == "fail" and r.actual == "pass"]
    if fns:
        lines.append(f"## False negatives ({len(fns)}) — rule should have fired but didn't")
        lines.append("")
        for r in fns:
            lines.append(f"- **[{r.rule_id}]** `{r.fixture_id}`")
            lines.append(f"  - text: `{r.text_snippet}...`")
        lines.append("")

    # Out-of-scope fixtures (likely fixture-author error)
    oos = [r for r in rows if r.actual == "out_of_scope"]
    if oos:
        lines.append(f"## Out-of-scope labels ({len(oos)}) — fixture lists a rule its scope filters out")
        lines.append("")
        for r in oos:
            lines.append(f"- [{r.rule_id}] `{r.fixture_id}` (expected={r.expected})")
        lines.append("")

    return "\n".join(lines)


def _severity_for(rule_id: str, rows: list[FixtureRow]) -> str:
    for r in rows:
        if r.rule_id == rule_id:
            return r.severity
    return "?"


# -------------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixtures-dir", type=Path, default=DEFAULT_FIXTURES_DIR)
    p.add_argument("--no-llm", action="store_true",
                   help="Skip llm_judge rules (deterministic-only pass).")
    p.add_argument("--model", type=str, default=None,
                   help=f"Override LLM judge model (default: {compliance_checker._DEFAULT_MODEL}).")
    p.add_argument("--rule", type=str, default=None,
                   help="Filter to a single rule_id (e.g. MISL-001).")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = p.parse_args(argv)

    if not args.fixtures_dir.exists():
        print(f"Fixtures dir not found: {args.fixtures_dir}", file=sys.stderr)
        return 1

    fixtures = load_fixtures(args.fixtures_dir)
    if not fixtures:
        print("No valid fixtures loaded.", file=sys.stderr)
        return 1
    print(f"Loaded {len(fixtures)} fixtures.", file=sys.stderr)

    rule_index = load_rule_index()
    enable_llm = not args.no_llm
    rows = collect_rows(
        fixtures,
        enable_llm=enable_llm,
        model=args.model,
        rule_index=rule_index,
        rule_filter=args.rule,
    )

    stats = aggregate(rows)
    report = render_report(
        rows,
        stats,
        enable_llm=enable_llm,
        model=args.model,
        n_fixtures=len(fixtures),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")

    correct = sum(1 for r in rows if r.expected == r.actual)
    fps = sum(1 for r in rows if r.expected == "pass" and r.actual == "fail")
    fns = sum(1 for r in rows if r.expected == "fail" and r.actual == "pass")
    print(
        f"Accuracy: {correct}/{len(rows)} ({correct/len(rows):.1%}) — "
        f"{fps} false positives, {fns} false negatives. Report: {args.out}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
