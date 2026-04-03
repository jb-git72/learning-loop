"""Clean investment language from all meta-ad description fields.

Removes: "Not financial advice.", "$50", "$10K", "equity crowdfunding",
"Birchal", and related investment terms from meta-ad descriptions.
Also cleans primary_text of "Not financial advice." lines.
"""

import json
import re
from pathlib import Path

ADS_DIR = Path("clients/farm-thru/loop/meta-ads")

# Patterns to remove from description field
DESC_REMOVALS = [
    r"\s*Not financial advice\.?",
    r"\s*From \$\d+\.?",
    r"\s*\$\d[\d,]*\.?",
    r"\s*Equity crowdfunding[^.]*\.?",
    r"\s*[Ee]quity crowdfunding[^.]*\.?",
    r"\s*[Oo]n Birchal[^.]*\.?",
    r"\s*Birchal[^.]*\.?",
    r"\s*\$5 refundable deposit\.?",
    r"\s*[Mm]inimum investment[^.]*\.?",
    r"\s*[Cc]apped at[^.]*\.?",
]

# Better descriptions for CFE ads (tease opportunity, no investment details)
CFE_DESC_REWRITES = {
    "CFE-101": "Be part of the farm-direct grocery movement. Join the waitlist.",
    "CFE-102": "A farm-direct grocery model that's already working. Be part of what comes next.",
    "CFE-103": "Farm-direct grocery, built by farmers and families. Be part of it.",
    "CFE-104": "Waitlist members get first access. Secure your spot now.",
    "CFE-105": "Honest about the risks, open about the model. See the full picture.",
    "CFE-106": "Own a piece of the farm-direct grocery movement. Be part of it.",
    "CFE-107": "Help build the shorter supply chain. Be part of what comes next.",
    "CFE-108": "Real food from real farms. Be part of what we're building.",
}

def clean_primary_text(text: str) -> str:
    """Remove 'Not financial advice.' line from primary_text."""
    lines = text.split("\n")
    cleaned = [l for l in lines if "Not financial advice" not in l]
    # Remove trailing empty lines
    while cleaned and cleaned[-1].strip() == "":
        cleaned.pop()
    return "\n".join(cleaned)

def clean_description(desc: str, ad_id: str) -> str:
    """Clean investment language from description."""
    # If we have a full rewrite for this CFE ad, use it
    if ad_id in CFE_DESC_REWRITES:
        return CFE_DESC_REWRITES[ad_id]

    # Otherwise, strip investment patterns
    cleaned = desc
    for pattern in DESC_REMOVALS:
        cleaned = re.sub(pattern, "", cleaned)

    # Clean up double spaces, leading/trailing
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"\.\s*\.", ".", cleaned)  # double periods

    return cleaned if cleaned else desc

def main():
    changed = 0
    for f in sorted(ADS_DIR.glob("*.json")):
        with open(f) as fh:
            ad = json.load(fh)

        ad_id = ad.get("ad_id", f.stem)
        original_desc = ad.get("description", "")
        original_pt = ad.get("primary_text", "")

        # Clean description
        new_desc = clean_description(original_desc, ad_id)

        # Clean primary_text
        new_pt = clean_primary_text(original_pt)

        if new_desc != original_desc or new_pt != original_pt:
            ad["description"] = new_desc
            ad["primary_text"] = new_pt
            with open(f, "w") as fh:
                json.dump(ad, fh, indent=2)
                fh.write("\n")

            if new_desc != original_desc:
                print(f"  DESC: {original_desc[:60]}...")
                print(f"    -> {new_desc[:60]}...")
            if new_pt != original_pt:
                print(f"  PT: removed 'Not financial advice' line")
            changed += 1
            print(f"FIXED {ad_id}")
        else:
            print(f"OK    {ad_id}")

    print(f"\n{changed} files updated")

if __name__ == "__main__":
    main()
