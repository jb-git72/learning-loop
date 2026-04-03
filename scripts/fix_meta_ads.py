"""
Fix objection preemption signals and scroll-stop hooks in FarmThru meta-ads.

Two fixes:
1. Objection preemption: append missing signals to primary_text
2. Scroll-stop hook: rewrite opening lines for 6 specific ads
"""

import json
import re
from pathlib import Path

ADS_DIR = Path(__file__).resolve().parent.parent / "clients" / "farm-thru" / "loop" / "meta-ads"
MAX_CHARS = 500

# --- Objection preemption signals ---

SIGNAL_PATTERNS = {
    "refundable": re.compile(r"refundable", re.IGNORECASE),
    "cfe_disclosure": re.compile(r"not\s+financial\s+advice|disclosure\s+document", re.IGNORECASE),
    "risk_ack": re.compile(r"don't\s+know|most\s+startups|can't\s+promise|no\s+guarantee", re.IGNORECASE),
    "supply_chain": re.compile(r"no\s+(?:warehouse|wholesaler|middlem)", re.IGNORECASE),
    "delivery_area": re.compile(r"sydney|central\s+coast|wollongong|deliver", re.IGNORECASE),
}

BRAND_APPEND = "\n\nNo middlemen. No commitment. Sydney families collect from the Brookvale hub, Monday to Friday."
CFE_APPEND = "\n\nNo middlemen. Sydney families already collect from the Brookvale hub. We can't promise returns, but we can show you everything."

# --- Scroll-stop hook rewrites ---

HOOK_REWRITES = {
    "CFE-105": '"I thought I could invest in the food system for $50." That\'s what one waitlist member told us.',
    "CFE-107": "Two supply chains feed Sydney families. One takes weeks and thousands of kilometres. The other takes days.",
    "CFE-102": "What if you could own a piece of the grocery store you buy from?",
    "CFE-103": "Rachel Ward was losing money on every kilo of beef she sold through the supermarket supply chain.",
    "BR-103": '"I never used to read the label." That\'s how it starts for most families.',
    "BR-106": "Do you know the name of the farm that raised your last steak?",
}


def check_signals(text: str) -> dict[str, bool]:
    """Return which objection signals are already present."""
    return {name: bool(pat.search(text)) for name, pat in SIGNAL_PATTERNS.items()}


def trim_to_fit(text: str, append_text: str, ad_id: str) -> str:
    """Trim the last paragraph's trailing sentences to make room for append_text."""
    # Split into paragraphs (double-newline separated)
    paragraphs = re.split(r"\n\n", text.rstrip())
    if len(paragraphs) < 2:
        # Single paragraph — trim sentences from the end
        sentences = re.split(r"(?<=[.!?])\s+", paragraphs[0])
        while len(sentences) > 1 and len(" ".join(sentences) + append_text) > MAX_CHARS:
            dropped = sentences.pop()
            print(f"  {ad_id}: dropped sentence: '{dropped[:50]}...'")
        return " ".join(sentences) + append_text

    # Multiple paragraphs — drop last paragraph first, then trim sentences
    while len(paragraphs) > 2 and len("\n\n".join(paragraphs) + append_text) > MAX_CHARS:
        dropped = paragraphs.pop()
        print(f"  {ad_id}: dropped paragraph: '{dropped[:50]}...'")

    candidate = "\n\n".join(paragraphs) + append_text
    if len(candidate) <= MAX_CHARS:
        return candidate

    # Still over — trim sentences from last paragraph
    last_para = paragraphs[-1]
    sentences = re.split(r"(?<=[.!?])\s+", last_para)
    while len(sentences) > 1:
        dropped = sentences.pop()
        paragraphs[-1] = " ".join(sentences)
        candidate = "\n\n".join(paragraphs) + append_text
        print(f"  {ad_id}: dropped sentence: '{dropped[:50]}...'")
        if len(candidate) <= MAX_CHARS:
            return candidate

    return candidate


def add_objection_signals(ad_id: str, text: str) -> str:
    """Append missing objection preemption signals based on ad type."""
    is_cfe = ad_id.startswith("CFE")
    signals = check_signals(text)
    append_text = CFE_APPEND if is_cfe else BRAND_APPEND

    # Check which signals the append would add
    append_signals = check_signals(append_text)
    new_signals = {k: v for k, v in append_signals.items() if v and not signals[k]}

    if not new_signals:
        print(f"  {ad_id}: all objection signals already present, skipping append")
        return text

    # Try appending directly
    candidate = text.rstrip() + append_text
    if len(candidate) <= MAX_CHARS:
        print(f"  {ad_id}: appended ({len(candidate)} chars), adds signals: {list(new_signals.keys())}")
        return candidate

    # Over limit — trim then append
    overage = len(candidate) - MAX_CHARS
    print(f"  {ad_id}: over by {overage} chars, trimming to fit")
    candidate = trim_to_fit(text, append_text, ad_id)
    print(f"  {ad_id}: trimmed to {len(candidate)} chars")
    return candidate


def rewrite_first_line(ad_id: str, text: str, new_first_line: str) -> str:
    """Replace the first non-empty line of primary_text.

    If the text has paragraph breaks (\\n\\n or \\n), replace the first line.
    If the text is a single block, replace only the first sentence.
    """
    # Check if text has line breaks
    if "\n" in text:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line.strip():
                old_line = lines[i]
                lines[i] = new_first_line
                print(f"  {ad_id}: hook rewrite (line): '{old_line[:60]}...' -> '{new_first_line[:60]}...'")
                return "\n".join(lines)
        return text

    # Single block — replace the first sentence only
    # Split on sentence boundaries (period/question/exclamation followed by space)
    match = re.match(r"^(.*?[.!?])\s+", text)
    if match:
        old_first = match.group(1)
        rest = text[match.end():]
        print(f"  {ad_id}: hook rewrite (sentence): '{old_first[:60]}...' -> '{new_first_line[:60]}...'")
        return new_first_line + " " + rest

    # Fallback: just prepend
    print(f"  {ad_id}: hook rewrite (prepend): '{text[:40]}...' -> '{new_first_line[:60]}...'")
    return new_first_line + " " + text


def process_ad(filepath: Path) -> None:
    """Process a single ad file."""
    with open(filepath) as f:
        ad = json.load(f)

    ad_id = ad["ad_id"]
    original_text = ad["primary_text"]
    text = original_text

    # Fix 2 first (hook rewrite) so char counting is accurate for Fix 1
    if ad_id in HOOK_REWRITES:
        text = rewrite_first_line(ad_id, text, HOOK_REWRITES[ad_id])

    # Fix 1: objection preemption
    text = add_objection_signals(ad_id, text)

    # Validate
    if len(text) > MAX_CHARS:
        print(f"  WARNING: {ad_id} is {len(text)} chars (over {MAX_CHARS} limit)")

    if text != original_text:
        ad["primary_text"] = text
        with open(filepath, "w") as f:
            json.dump(ad, f, indent=2)
            f.write("\n")
        print(f"  {ad_id}: SAVED ({len(text)} chars)")
    else:
        print(f"  {ad_id}: no changes needed ({len(text)} chars)")


def main():
    print("=== FarmThru Meta-Ad Fix Script ===\n")

    # Process all ads
    for filepath in sorted(ADS_DIR.glob("*.json")):
        print(f"\nProcessing {filepath.name}:")
        process_ad(filepath)

    # Summary: verify signals
    print("\n\n=== Signal Verification ===\n")
    for filepath in sorted(ADS_DIR.glob("*.json")):
        with open(filepath) as f:
            ad = json.load(f)
        signals = check_signals(ad["primary_text"])
        present = [k for k, v in signals.items() if v]
        score = len(present)
        print(f"  {ad['ad_id']}: {score}/5 signals — {present}")

    # Summary: char counts
    print("\n\n=== Char Count Check ===\n")
    over = False
    for filepath in sorted(ADS_DIR.glob("*.json")):
        with open(filepath) as f:
            ad = json.load(f)
        length = len(ad["primary_text"])
        flag = " *** OVER LIMIT ***" if length > MAX_CHARS else ""
        print(f"  {ad['ad_id']}: {length} chars{flag}")
        if length > MAX_CHARS:
            over = True

    if over:
        print("\n  WARNING: Some ads exceed 500 char limit!")
    else:
        print("\n  All ads within 500 char limit.")


if __name__ == "__main__":
    main()
