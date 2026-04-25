#!/usr/bin/env python3
"""Dry-run the CSF compliance gate against existing FMTH content.

Wave 3b validation. Loads:
  - 8 FMTH seed emails  (clients/farm-thru/loop/emails/EM-*.json)
  - 17 LP variants      (../sales-skill/web/campaigns/FMTH/index*.html)
  - 1 deliberately-broken fixture  (built inline)

Runs `check_compliance(text, content_type, applies_to='issuer')` against
each, including llm_judge rules unless --no-llm.

Outputs a Markdown report at the path given by --out (default: stdout).

Use this BEFORE flipping `compliance.enabled: true` in clients/farm-thru/
config.json so we know exactly what would zero out under the new gate.

Usage:
    python3 scripts/dry_run_compliance.py
    python3 scripts/dry_run_compliance.py --no-llm --out report.md
    python3 scripts/dry_run_compliance.py \
        --emails-dir clients/farm-thru/loop/emails \
        --lp-dir /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH \
        --out clients/farm-thru/loop/compliance-dry-run-2026-04-26.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

# Ensure repo root is importable regardless of CWD.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from engine import compliance_checker  # noqa: E402


DEFAULT_EMAILS_DIR = REPO_ROOT / "clients" / "farm-thru" / "loop" / "emails"
DEFAULT_LP_DIR = Path("/Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH")
DEFAULT_OUT = (
    REPO_ROOT / "clients" / "farm-thru" / "loop" / "compliance-dry-run-2026-04-26.md"
)

DELIBERATELY_BROKEN = (
    "Reserve your VIP spot today for just a $5 refundable deposit! "
    "Reply to this email to apply. Minimum $50, maximum $10,000. "
    "FarmThru is the only legitimate grocery investment. "
    "We project 25% returns within 12 months."
)


# -------------------------------------------------------------------------
# Loaders
# -------------------------------------------------------------------------

def load_emails(emails_dir: Path) -> list[dict]:
    items: list[dict] = []
    for p in sorted(emails_dir.glob("EM-*.json")):
        try:
            with open(p) as f:
                ad = json.load(f)
        except Exception as exc:
            print(f"  ! could not load {p.name}: {exc}", file=sys.stderr)
            continue
        text = _email_text(ad)
        items.append({"id": p.stem, "label": p.name, "content_type": "email", "text": text})
    return items


def load_landing_pages(lp_dir: Path) -> list[dict]:
    items: list[dict] = []
    for p in sorted(lp_dir.glob("index*.html")):
        try:
            html = p.read_text(encoding="utf-8")
        except Exception as exc:
            print(f"  ! could not load {p.name}: {exc}", file=sys.stderr)
            continue
        text = _html_to_text(html)
        items.append({"id": p.stem, "label": p.name, "content_type": "landing-page", "text": text})
    return items


def _email_text(ad: dict) -> str:
    """Concatenate the same fields the scorer would feed to check_compliance."""
    parts = [
        ad.get("subject", ""),
        ad.get("preheader", ""),
        ad.get("body", ""),
    ]
    # Some emails store body as nested sections — also fold those in.
    for section in ad.get("sections", []) or []:
        if isinstance(section, dict):
            parts.append(section.get("heading", ""))
            parts.append(section.get("body", ""))
    return "\n".join(p for p in parts if p)


def _html_to_text(html: str) -> str:
    """Crude tag-strip — good enough for compliance scanning of marketing copy."""
    no_scripts = re.sub(r"<script\b.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    no_styles = re.sub(r"<style\b.*?</style>", " ", no_scripts, flags=re.DOTALL | re.IGNORECASE)
    no_tags = re.sub(r"<[^>]+>", " ", no_styles)
    decoded = (
        no_tags.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    return re.sub(r"\s+", " ", decoded).strip()


# -------------------------------------------------------------------------
# Reporting
# -------------------------------------------------------------------------

def evaluate(items: list[dict], enable_llm: bool) -> list[dict]:
    out: list[dict] = []
    for item in items:
        result = compliance_checker.check_compliance(
            text=item["text"],
            content_type=item["content_type"],
            applies_to="issuer",
            enable_llm=enable_llm,
        )
        out.append(
            {
                "id": item["id"],
                "label": item["label"],
                "content_type": item["content_type"],
                "char_count": len(item["text"]),
                "rules_evaluated": result.rules_evaluated,
                "rules_skipped": result.rules_skipped_out_of_scope,
                "passed": result.passed,
                "blocking": [asdict(v) for v in result.blocking_violations],
                "warnings": [asdict(v) for v in result.warnings],
                "advisory": [asdict(v) for v in result.advisory],
            }
        )
    return out


def render_markdown(rows: list[dict], enable_llm: bool) -> str:
    total = len(rows)
    passed = sum(1 for r in rows if r["passed"])
    blocking_count = sum(len(r["blocking"]) for r in rows)
    warning_count = sum(len(r["warnings"]) for r in rows)

    lines: list[str] = []
    lines.append("# CSF compliance dry-run — FMTH")
    lines.append("")
    lines.append(f"- LLM judges: {'ENABLED' if enable_llm else 'disabled (cheap pass)'}")
    lines.append(f"- Total content pieces: {total}")
    lines.append(f"- Passed (zero BLOCKING): {passed} / {total}")
    lines.append(f"- Total BLOCKING violations: {blocking_count}")
    lines.append(f"- Total WARNINGs: {warning_count}")
    lines.append("")
    lines.append("## Per-piece summary")
    lines.append("")
    lines.append("| ID | Type | Eval | Pass | Blocking | Warnings |")
    lines.append("|---|---|---:|:---:|---:|---:|")
    for r in rows:
        gate = "OK" if r["passed"] else "FAIL"
        lines.append(
            f"| {r['id']} | {r['content_type']} | {r['rules_evaluated']} | {gate} "
            f"| {len(r['blocking'])} | {len(r['warnings'])} |"
        )
    lines.append("")

    failing = [r for r in rows if not r["passed"]]
    if failing:
        lines.append("## Failing pieces — BLOCKING violations")
        lines.append("")
        for r in failing:
            lines.append(f"### {r['id']}  ({r['content_type']})")
            for v in r["blocking"]:
                src = "/".join(v["source_ref"])
                lines.append(f"- **[{v['rule_id']}]** ({src}) — {v['fix_message']}")
                if v["matched_text"]:
                    lines.append(f"  - matched: `{v['matched_text']}`")
                if v["line_hint"]:
                    lines.append(f"  - context: `{v['line_hint']}`")
            lines.append("")

    flagged_warnings = [r for r in rows if r["warnings"]]
    if flagged_warnings:
        lines.append("## Pieces with WARNINGs (non-blocking but worth reviewing)")
        lines.append("")
        for r in flagged_warnings:
            lines.append(f"### {r['id']}  ({r['content_type']})")
            for v in r["warnings"]:
                src = "/".join(v["source_ref"])
                lines.append(f"- [{v['rule_id']}] ({src}) — {v['line_hint']}")
            lines.append("")

    return "\n".join(lines)


# -------------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--emails-dir", type=Path, default=DEFAULT_EMAILS_DIR)
    p.add_argument("--lp-dir", type=Path, default=DEFAULT_LP_DIR)
    p.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip llm_judge rules — fast, deterministic, but misses semantic checks.",
    )
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument(
        "--include-broken-fixture",
        action="store_true",
        help="Also score a hand-crafted maximally-broken fixture (sanity check the gate fires).",
    )
    args = p.parse_args(argv)

    items: list[dict] = []
    if args.emails_dir.exists():
        items.extend(load_emails(args.emails_dir))
        print(f"Loaded {sum(1 for i in items if i['content_type']=='email')} emails", file=sys.stderr)
    else:
        print(f"  ! emails dir not found: {args.emails_dir}", file=sys.stderr)

    if args.lp_dir.exists():
        before = len(items)
        items.extend(load_landing_pages(args.lp_dir))
        print(f"Loaded {len(items)-before} landing pages", file=sys.stderr)
    else:
        print(f"  ! lp dir not found: {args.lp_dir}", file=sys.stderr)

    if args.include_broken_fixture:
        items.append(
            {
                "id": "FIXTURE-BROKEN",
                "label": "deliberately-broken-fixture",
                "content_type": "email",
                "text": DELIBERATELY_BROKEN,
            }
        )

    if not items:
        print("No content found.", file=sys.stderr)
        return 1

    enable_llm = not args.no_llm
    print(
        f"Evaluating {len(items)} pieces "
        f"(llm_judge {'enabled' if enable_llm else 'disabled'})...",
        file=sys.stderr,
    )
    rows = evaluate(items, enable_llm=enable_llm)

    md = render_markdown(rows, enable_llm=enable_llm)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(md, encoding="utf-8")
    print(f"Report written to {args.out}", file=sys.stderr)

    blocking_total = sum(len(r["blocking"]) for r in rows)
    failing = sum(1 for r in rows if not r["passed"])
    print(
        f"Summary: {failing}/{len(rows)} pieces failed BLOCKING gate; "
        f"{blocking_total} total BLOCKING violations.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
