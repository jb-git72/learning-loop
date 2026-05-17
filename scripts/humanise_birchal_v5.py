#!/usr/bin/env python3
"""Run the humaniser on every V5 primary_text body and report flags.
CREATE-only helper. Read-only over the V5 files. Does NOT push anything.
Exempt: AI-tell words that appear ONLY inside an attributed verbatim quote
(QUOTE-006 Aubrey Blanche, QUOTE-009 Kirstin) per the DRC verbatim-exemption
precedent (same as QUOTE-005 'seamless'). Those are documented, not failures.
"""
import json
import subprocess
import sys
from pathlib import Path

VAR = Path("/Users/jb/Documents/GitHub/learning-loop/clients/birchal/loop/birchal-ad-variants")
HUM = "/Users/jb/Documents/GitHub/marketing-copy/direct-response-copy/scripts/humaniser.py"

any_unexpected = False
for f in sorted(VAR.glob("BIRCHAL-V5-*.json")):
    d = json.loads(f.read_text())
    body = d["primary_text"]
    r = subprocess.run(["python3", HUM], input=body, capture_output=True, text=True)
    stderr = r.stderr.strip()
    # Parse counts
    import re
    m = re.search(r"substitutions=(\d+) word_flags=(\d+) opener_flags=(\d+)", stderr)
    subs, wf, of = (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (-1, -1, -1)
    flagged = re.findall(r"\[FLAG:([^\]]+)\]", r.stdout)
    status = "CLEAN" if (subs == 0 and wf == 0 and of == 0) else f"FLAGS subs={subs} word={wf} opener={of} -> {flagged}"
    # Determine if any flag is unexpected (i.e. NOT inside an attributed verbatim quote)
    note = ""
    if flagged:
        # crude: is the flagged word inside a double-quoted span in the body?
        unexpected = []
        for w in set(flagged):
            # find the word, check if it's between quotes
            in_quote_ok = False
            for mm in re.finditer(re.escape(w), body, re.IGNORECASE):
                before = body[:mm.start()]
                if before.count('"') % 2 == 1:  # odd => inside an open quote
                    in_quote_ok = True
            if not in_quote_ok:
                unexpected.append(w)
        if unexpected:
            note = f"  <<< UNEXPECTED (not in verbatim): {unexpected}"
            any_unexpected = True
        else:
            note = "  (all flags inside attributed verbatim quote -> exempt, documented)"
    print(f"{d['ad_id']:<16} {status}{note}")

print("-" * 70)
print("HUMANISER: all bodies clean OR flags exempt (verbatim)" if not any_unexpected
      else "HUMANISER: UNEXPECTED FLAGS FOUND -- fix required")
sys.exit(1 if any_unexpected else 0)
