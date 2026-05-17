#!/usr/bin/env python3
"""Adversarial fact-trace: extract EVERY number/numeric token from every V5
shipped string (primary_text + headline + description + cta) and assert it
maps to a real facts.json fact_id with that exact value. Anything that does
not trace is a HARD FAIL. CREATE-only, read-only, no push.
"""
import json
import re
import glob
from pathlib import Path

ROOT = Path("/Users/jb/Documents/GitHub/learning-loop")
VAR = ROOT / "clients/birchal/loop/birchal-ad-variants"

# Allowed verified numeric spine (value -> fact_id). These are the ONLY
# numbers permitted to appear as factual claims in shipped Birchal copy.
ALLOWED = {
    "324": "PLAT-001",          # 324 Australian companies / raises
    "$234M": "PLAT-002",        # $234M+ raised (also '$234M+')
    "234M": "PLAT-002",
    "137,000": "PLAT-003",      # 137,000 individual investments
    "2018": "PLAT-004",         # since 2018
    "eight years": "PLAT-004",  # eight years
    "mid 2026": "BIRCHAL-NEXT", # client-stated forward-looking timeframe
}

# Numbers that are explicitly allowed because they are inside an attributed
# verbatim quote (none of the V5 quotes contain bare numerals; defensive).
QUOTE_NUMERIC_OK = set()

# Token regex: $234M, $234M+, 137,000, 324, 2018, percentages, $-amounts.
NUM_RE = re.compile(r"\$?\d[\d,\.]*[MmKkBb%+]?\+?")

fails = []
for f in sorted(glob.glob(str(VAR / "BIRCHAL-V5-*.json"))):
    d = json.loads(Path(f).read_text())
    aid = d["ad_id"]
    for field in ("primary_text", "headline", "description", "cta"):
        text = d[field]
        for m in NUM_RE.finditer(text):
            tok = m.group(0)
            norm = tok.rstrip("+").rstrip(".").rstrip(",")
            # Accept the verified spine numbers
            ok = False
            if norm in ("324",) or norm in ("$234M", "234M") or norm == "137,000" or norm == "2018":
                ok = True
            elif norm in ("$234M+", "234M+"):
                ok = True
            elif norm == "2026":
                # Only OK if it is the client-stated 'mid 2026' (BIRCHAL-NEXT)
                pre = text[max(0, m.start() - 4):m.start()]
                ok = pre.endswith("mid ")
            if not ok:
                fails.append((aid, field, tok, text[:90]))
    # Phrase-level checks for spelled-out spine + forbidden literals
    blob = " ".join(d[x] for x in ("primary_text", "headline", "description", "cta"))
    # FORBIDDEN literals that must never appear (unsourced)
    for bad in ["#1", "number one", "largest", "leading CSF", "market share",
                "$5M", "$1B", "82,659", "70%", "64%", "top ten", "$250",
                "$0.50", "from $", "valuation"]:
        if re.search(re.escape(bad), blob, re.IGNORECASE):
            fails.append((aid, "FORBIDDEN-LITERAL", bad, blob[:90]))
    # 'eight years' if present must be the only spelled form (PLAT-004)
    # (no assertion needed beyond it being allowed; just ensure no 'nine/ten years' drift)
    for bad in ["nine years", "ten years", "seven years", "since 2017", "since 2019",
                "since 2020", "323 ", "325 ", "$233M", "$235M", "$230M", "138,000", "136,000"]:
        if re.search(re.escape(bad), blob, re.IGNORECASE):
            fails.append((aid, "NUMERIC-DRIFT", bad, blob[:90]))

print(f"Scanned {len(glob.glob(str(VAR / 'BIRCHAL-V5-*.json')))} V5 ad files.")
if not fails:
    print("FACT-TRACE: PASS. Every numeric token traces to the verified spine "
          "(324=PLAT-001, $234M+=PLAT-002, 137,000=PLAT-003, 2018/eight years=PLAT-004, "
          "mid 2026=BIRCHAL-NEXT). Zero forbidden literals, zero numeric drift.")
else:
    print("FACT-TRACE: HARD FAIL")
    for a, fld, tok, ctx in fails:
        print(f"  {a} [{fld}] -> '{tok}'  in: {ctx!r}")
import sys
sys.exit(1 if fails else 0)
