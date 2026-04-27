#!/usr/bin/env python3
"""Score all content in a client's loop directory and output JSON results.

Flags:
  --no-llm              Skip the LLM judge (deterministic only)
  --verbose             Print full per-ad reports to stderr
  --type <content_type> Only score items whose content_type matches
                        (e.g. --type email, --type meta-ad, --type landing-page).
                        Accepts both "--type X" and "--type=X" forms.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
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

from engine.scorer import load_client, score_ad, format_report


def _parse_type_flag(argv):
    """Extract --type <value> or --type=<value> from argv.

    Returns the value (str) or None if unset. Does not mutate argv.
    """
    for i, arg in enumerate(argv):
        if arg == "--type" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--type="):
            return arg.split("=", 1)[1]
    return None


def main():
    # Pull positional client id, skipping any known flag values to avoid
    # treating "--type" / "email" as the client id.
    client_id = "farm-thru"
    skip_next = False
    for i, arg in enumerate(sys.argv[1:], start=1):
        if skip_next:
            skip_next = False
            continue
        if arg.startswith("--"):
            # Flags with values: --type; boolean flags: --no-llm, --verbose
            if arg == "--type":
                skip_next = True
            continue
        client_id = arg
        break

    use_llm = "--no-llm" not in sys.argv
    verbose = "--verbose" in sys.argv
    type_filter = _parse_type_flag(sys.argv)

    client_dir = root / "clients" / client_id
    shared_dir = root / "shared"
    client = load_client(client_dir, shared_dir)

    loop_dir = client_dir / "loop"
    all_ads = []           # full corpus — used for cross-type differentiation context
    ads_to_score = []      # subset actually scored (after --type filter)
    all_results = []

    # Collect all content files, honoring --type filter at scan time
    for subdir in ["meta-ads", "landing-pages", "emails", "sms"]:
        content_dir = loop_dir / subdir
        if not content_dir.exists():
            continue
        for f in sorted(content_dir.iterdir()):
            if f.suffix == ".json":
                with open(f) as fh:
                    ad = json.load(fh)
                ad["_file"] = str(f.relative_to(root))
                all_ads.append(ad)
                if type_filter and ad.get("content_type") != type_filter:
                    continue
                ads_to_score.append(ad)

    filter_desc = f", filter=content_type={type_filter}" if type_filter else ""
    print(
        f"Scoring {len(ads_to_score)} items (LLM={'on' if use_llm else 'off'}{filter_desc})...",
        file=sys.stderr,
    )

    for ad in ads_to_score:
        file_path = ad.pop("_file")
        report = score_ad(ad, client, existing_ads=all_ads, use_llm=use_llm)
        # Resolve ID from all possible fields (scorer only checks ad_id)
        resolved_id = ad.get("ad_id", ad.get("page_id", ad.get("email_id", ad.get("sms_id", "unknown"))))
        report["ad_id"] = resolved_id
        report["_file"] = file_path
        report["content_type"] = ad.get("content_type", "meta-ad")
        report["angle"] = ad.get("angle", "")
        report["hook_type"] = ad.get("hook_type", "")
        report["original_ad_name"] = ad.get("original_ad_name", "")
        report["headline"] = ad.get("headline", ad.get("subject", ad.get("purpose", "")))
        report["primary_text"] = ad.get("primary_text", ad.get("body", ad.get("hero_copy", "")))[:200]
        all_results.append(report)

        if verbose:
            print(format_report(report), file=sys.stderr)
            print(file=sys.stderr)

    # Summary
    verdicts = {}
    critical_fails = 0
    for r in all_results:
        v = r["verdict"]
        verdicts[v] = verdicts.get(v, 0) + 1
        if r["overrides"]["critical_rule_failure"] or r["overrides"]["fact_contradiction"]:
            critical_fails += 1

    avg = sum(r["composite"] for r in all_results) / len(all_results) if all_results else 0

    summary = {
        "total": len(all_results),
        "avg_composite": round(avg, 4),
        "verdicts": verdicts,
        "critical_failures": critical_fails,
    }

    print(f"\n=== SUMMARY ===", file=sys.stderr)
    print(f"Total: {summary['total']}", file=sys.stderr)
    print(f"Avg composite: {summary['avg_composite']}", file=sys.stderr)
    print(f"Critical failures: {summary['critical_failures']}", file=sys.stderr)
    for v, c in sorted(verdicts.items()):
        print(f"  {v}: {c}", file=sys.stderr)

    # Output full results as JSON to stdout
    output = {"summary": summary, "results": all_results}
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
