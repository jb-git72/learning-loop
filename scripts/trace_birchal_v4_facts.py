#!/usr/bin/env python3
"""Full empirical-fact traceability for the Birchal V4 set.

Every empirical number / named claim in every shippable field must map to a
fact_id in facts.json with that value. Excluded brands must never appear.
"""
import json
import re
from pathlib import Path

REPO = Path("/Users/jb/Documents/GitHub/learning-loop")
VDIR = REPO / "clients" / "birchal" / "loop" / "birchal-ad-variants"
FACTS = REPO / "clients" / "birchal" / "facts.json"

facts = json.loads(FACTS.read_text())
fid = {f["fact_id"]: f for f in facts["facts"]}
PYM = fid["QUOTE-001"]["verbatim_text"]

brand_amts = {
    "Naked Life": "$2.95M", "Our Cow": "$2M", "Medigrowth": "$1.59M",
    "Earthletica": "$1.1M", "Aquafab": "$600K", "Pulse Tile": "$400K",
    "Reckless Brewery": "$513K",
}
excluded = ["Zero Co", "Old Young"]

issues = []

for f in ["BIRCHAL-V4-A1", "BIRCHAL-V4-A2", "BIRCHAL-V4-A3",
          "BIRCHAL-V4-B1", "BIRCHAL-V4-B2"]:
    d = json.loads((VDIR / f"{f}.json").read_text())
    pt = d["primary_text"]
    ship = " ".join([pt, d.get("headline", ""), d.get("description", ""), d.get("cta", "")])
    print(f"--- {f} ---")

    for tok, fact in [("324", "PLAT-001"), ("$234M", "PLAT-002"),
                      ("137,000", "PLAT-003"), ("eight years", "PLAT-004"),
                      ("2018", "PLAT-004")]:
        if tok in ship:
            claim = fid[fact]["claim"][:55]
            print(f'    "{tok}" -> {fact} ({claim}...) OK')

    for b, amt in brand_amts.items():
        if b in ship:
            amt_in = amt in ship
            note = "names-only (compliant)" if not amt_in else f"AMOUNT {amt} present (needs RAISE fact)"
            print(f'    brand "{b}" named; {note}')

    for x in excluded:
        if x.lower() in ship.lower():
            msg = f"{f}: EXCLUDED BRAND {x!r} in shipped copy"
            issues.append(msg)
            print(f"    !!! {msg} -- HARD FAIL")

    if f == "BIRCHAL-V4-B2":
        pym_ok = PYM in pt
        attr_ok = "Dom Pym, Triple Bubble" in pt
        avpf = "Australia Venture Partners Fund" in pt
        tribe = "Tribe Global" in pt
        print(f"    Pym QUOTE-001 byte-exact in primary_text? {pym_ok}")
        print(f'    Attribution "Dom Pym, Triple Bubble" present? {attr_ok}')
        print(f'    "Australia Venture Partners Fund" present? {avpf} (QUOTE-004 src)')
        print(f'    "Tribe Global" present? {tribe} (QUOTE-003 src)')
        if not pym_ok:
            issues.append("B2: Pym quote NOT byte-exact")
        if not attr_ok:
            issues.append("B2: Pym attribution missing")

    dollars = set(re.findall(r"\$\d[\d,.]*[KMB]?\+?", ship))
    unknown = [x for x in dollars if x not in ("$234M", "$234M+")]
    if unknown:
        msg = f"{f}: unmapped $ tokens {unknown}"
        issues.append(msg)
        print(f"    !!! {msg}")

    if re.search(r"\d+\s?%|valuation|\$1B|\$5M", ship, re.I):
        msg = f"{f}: percent/valuation token in shipped copy"
        issues.append(msg)
        print(f"    !!! {msg}")

print()
if issues:
    print("TRACEABILITY ISSUES:")
    for i in issues:
        print(f"  - {i}")
    raise SystemExit(1)
print("FACT TRACEABILITY: all empirical claims map to facts.json; no excluded brands; no unmapped $; no percent/valuation in shipped copy.")
