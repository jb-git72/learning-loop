#!/usr/bin/env python3
"""Hill-climb all content to strong_draft+ before human review."""

import json
import os
import sys
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

from engine.scorer import load_client, score_ad
from scripts.lint_content import lint
from writer import generate_variant


def main():
    client_id = sys.argv[1] if len(sys.argv) > 1 else "farm-thru"
    max_iterations = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    target_composite = 0.70  # strong_draft threshold

    # Optional --type filter (e.g. --type=meta-ad)
    type_filter = None
    for arg in sys.argv:
        if arg.startswith("--type="):
            type_filter = arg.split("=", 1)[1]

    client_dir = root / "clients" / client_id
    shared_dir = root / "shared"
    client = load_client(client_dir, shared_dir)

    # Collect all content
    loop_dir = client_dir / "loop"
    all_items = []
    for subdir in ["meta-ads", "landing-pages", "emails"]:
        content_dir = loop_dir / subdir
        if not content_dir.exists():
            continue
        for f in sorted(content_dir.iterdir()):
            if f.suffix == ".json" and f.name not in ("test-ad.json", "review-batch.json"):
                with open(f) as fh:
                    ad = json.load(fh)
                all_items.append({"path": f, "ad": ad, "subdir": subdir})

    # Build full ads list for differentiation scoring BEFORE filtering
    all_ads = [item["ad"] for item in all_items]

    if type_filter:
        all_items = [i for i in all_items if i["ad"].get("content_type") == type_filter]
        print(f"Filtered to {len(all_items)} {type_filter} items")

    print(f"Loaded {len(all_items)} items. Target: {target_composite:.2f} (strong_draft)")
    print(f"Max iterations per item: {max_iterations}")
    print()

    # Initial scoring
    for item in all_items:
        report = score_ad(item["ad"], client, existing_ads=all_ads, use_llm=True)
        item["score"] = report["composite"]
        item["verdict"] = report["verdict"]
        item["report"] = report

    below = [i for i in all_items if i["score"] < target_composite]
    above = [i for i in all_items if i["score"] >= target_composite]
    print(f"Initial: {len(above)} at target, {len(below)} below target")
    print()

    # Hill-climb items below target
    recent_failures = []
    improved = 0
    for iteration in range(max_iterations):
        below = [i for i in all_items if i["score"] < target_composite]
        if not below:
            print(f"All items at target after iteration {iteration}!")
            break

        print(f"--- Iteration {iteration + 1}: {len(below)} items below target ---")

        for item in below:
            ad = item["ad"]
            ad_id = ad.get("ad_id", ad.get("page_id", ad.get("email_id", "?")))
            content_type = ad.get("content_type", "meta-ad")
            old_score = item["score"]

            print(f"  {ad_id} ({content_type}): {old_score:.3f} [{item['verdict']}] -> generating...", end=" ", flush=True)

            try:
                new_ad = generate_variant(
                    angle=ad.get("angle", "quality-craft"),
                    tactic=ad.get("tactic", "general"),
                    hook_type=ad.get("hook_type", "story"),
                    funnel=ad.get("funnel", "TOF"),
                    client_dir=client_dir,
                    current_best=ad,
                    recent_failures=recent_failures[-5:],
                    content_type=content_type,
                )

                # Preserve metadata from original
                for key in ["ad_id", "page_id", "email_id", "email_type"]:
                    if key in ad:
                        new_ad[key] = ad[key]

                # Lint gate — catch violations before spending an API call
                lint_result = lint(new_ad, client_dir, shared_dir)
                if not lint_result.passed:
                    details = "; ".join(v["detail"][:60] for v in lint_result.violations[:3])
                    recent_failures.append(f"{ad_id}: lint failed — {details}")
                    print(f"LINT FAIL ({len(lint_result.violations)} critical), skipped scoring")
                    continue

                # Score the new version
                new_report = score_ad(new_ad, client, existing_ads=all_ads, use_llm=True)
                new_score = new_report["composite"]

                if new_score > old_score:
                    # Keep the better version
                    item["ad"] = new_ad
                    item["score"] = new_score
                    item["verdict"] = new_report["verdict"]
                    item["report"] = new_report
                    # Update in all_ads list too
                    idx = all_ads.index(ad)
                    all_ads[idx] = new_ad
                    # Write to disk
                    with open(item["path"], "w") as f:
                        json.dump(new_ad, f, indent=2, ensure_ascii=False)
                        f.write("\n")
                    improved += 1
                    print(f"{new_score:.3f} [{new_report['verdict']}] IMPROVED (+{new_score - old_score:.3f})")
                else:
                    recent_failures.append(f"{ad_id}: tried {new_ad.get('hook_type', '?')} hook, scored {new_score:.3f}")
                    print(f"{new_score:.3f} no improvement, kept original")

            except Exception as e:
                print(f"ERROR: {e}")
                continue

        print()

    # Final summary
    verdicts = {}
    for item in all_items:
        v = item["verdict"]
        verdicts[v] = verdicts.get(v, 0) + 1

    avg = sum(i["score"] for i in all_items) / len(all_items)
    still_below = sum(1 for i in all_items if i["score"] < target_composite)

    print(f"=== HILL-CLIMB COMPLETE ===")
    print(f"Improvements made: {improved}")
    print(f"Avg composite: {avg:.4f}")
    print(f"Still below target: {still_below}")
    for v in ["production_ready", "strong_draft", "needs_work", "rewrite"]:
        print(f"  {v}: {verdicts.get(v, 0)}")


if __name__ == "__main__":
    main()
