#!/usr/bin/env python3
"""Apply human review edits from review decisions JSON to content files."""

import json
import sys
from pathlib import Path

root = Path(__file__).parent.parent

PREFIX_MAP = {
    "BR-": "meta-ads",
    "CFE-": "meta-ads",
    "LP-": "landing-pages",
    "EM-": "emails",
}


def get_subdir(item_id):
    for prefix, subdir in PREFIX_MAP.items():
        if item_id.startswith(prefix):
            return subdir
    return None


def main():
    review_path = sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / "Downloads/review-r3-decisions.json")
    client_slug = sys.argv[2] if len(sys.argv) > 2 else "farm-thru"

    with open(review_path) as f:
        review = json.load(f)

    edits = review.get("edits", {})
    statuses = review.get("statuses", {})

    loop_dir = root / "clients" / client_slug / "loop"
    applied = 0
    skipped = 0
    errors = []

    for item_id, field_edits in sorted(edits.items()):
        if not field_edits:
            skipped += 1
            continue

        subdir = get_subdir(item_id)
        if not subdir:
            errors.append(f"{item_id}: unknown prefix")
            continue

        file_path = loop_dir / subdir / f"{item_id}.json"
        if not file_path.exists():
            errors.append(f"{item_id}: file not found at {file_path}")
            continue

        with open(file_path) as f:
            content = json.load(f)

        changed_fields = []
        for field, new_value in field_edits.items():
            old_value = content.get(field, "")
            if old_value != new_value:
                content[field] = new_value
                changed_fields.append(field)

        if changed_fields:
            with open(file_path, "w") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
                f.write("\n")
            status = statuses.get(item_id, "no-status")
            print(f"  {item_id} [{status}]: updated {', '.join(changed_fields)}")
            applied += 1
        else:
            skipped += 1

    print(f"\nApplied: {applied}, Skipped (no changes): {skipped}")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors:
            print(f"  {e}")


if __name__ == "__main__":
    main()
