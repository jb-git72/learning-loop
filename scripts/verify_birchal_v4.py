#!/usr/bin/env python3
"""Independent VERIFY pass for the Birchal V4 Meta ad set.

Re-runs the full verification battery from scratch. Does NOT trust the
create agent's self-audit. Prints a PASS/FAIL line for every check.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path("/Users/jb/Documents/GitHub/learning-loop")
VDIR = REPO / "clients" / "birchal" / "loop" / "birchal-ad-variants"
HEADLINES_V4 = REPO / "clients" / "birchal" / "loop" / "birchal-headlines-v4.json"
FACTS = REPO / "clients" / "birchal" / "facts.json"

BODY_IDS = ["BIRCHAL-V4-A1", "BIRCHAL-V4-A2", "BIRCHAL-V4-A3",
            "BIRCHAL-V4-B1", "BIRCHAL-V4-B2"]

VERBATIM_CSF = "*Always consider the general CSF risk warning and offer document before investing."

BANNED = re.compile(
    r"(\bbe first to invest\b|\bfirst in line\b|\binvest from \$|\bfrom as little as \$|"
    r"\bguaranteed return\b|\bsecure your allocation\b|\bskip the queue\b|"
    r"\bjump the queue\b|\binvest now\b|\bbuy now\b|\bsubscribe now\b)", re.I)
PREOFFER_VERBS = re.compile(r"(\b(invest|buy|subscribe|purchase)\s+(now|today|here))", re.I)
VERBATIM_OFFER = re.compile(
    r"(we will send you (the|our) offer document|we'll send you (the|our) offer)", re.I)
BRAND_EXCLUDED = re.compile(r"(Zero Co|Old Young)", re.I)

# Unsourced-claim scan tokens (must be ZERO in shipped copy)
UNSOURCED_TOKENS = [
    "64%", "70%", "market share", "#1", " first CSF", "largest",
    "leading CSF", "top 10", "82,659", "$5M valuation", "valuation",
    "$1B", "2030", "$250", "$0.50", "$50",
]

DASHES = {
    "em-dash U+2014": "—",
    "en-dash U+2013": "–",
    "smart-quote-left U+2018": "‘",
    "smart-quote-right U+2019": "’",
    "smart-dquote-left U+201C": "“",
    "smart-dquote-right U+201D": "”",
    "ellipsis U+2026": "…",
}

results = []  # (item, check_name, status, detail)


def rec(item, check, status, detail=""):
    results.append((item, check, status, detail))


def wc(text: str) -> int:
    return len(text.split())


def main():
    facts = json.loads(FACTS.read_text())
    fact_by_id = {f["fact_id"]: f for f in facts["facts"]}

    bodies = {}
    for bid in BODY_IDS:
        p = VDIR / f"{bid}.json"
        try:
            bodies[bid] = json.loads(p.read_text())
        except Exception as e:
            rec(bid, "JSON parse", "FAIL", f"{p.name}: {e}")
            continue
        rec(bid, "JSON parse", "PASS", "")

    try:
        hl_data = json.loads(HEADLINES_V4.read_text())
        rec("HEADLINES-V4", "JSON parse", "PASS", "")
    except Exception as e:
        rec("HEADLINES-V4", "JSON parse", "FAIL", str(e))
        hl_data = {"headlines": []}
    headlines = hl_data.get("headlines", [])

    # ---- Per-body checks ----
    for bid, ad in bodies.items():
        pt = ad.get("primary_text", "")

        # Check 2: banned phrases (all fields)
        blob = " ".join([pt, ad.get("headline", ""), ad.get("description", ""),
                         ad.get("cta", "")])
        hits = []
        for name, rx in [("BANNED-CSF", BANNED), ("PREOFFER-VERBS", PREOFFER_VERBS),
                         ("VERBATIM-OFFER", VERBATIM_OFFER),
                         ("BRAND-EXCLUDED", BRAND_EXCLUDED)]:
            m = rx.findall(blob)
            if m:
                hits.append(f"{name}={m}")
        rec(bid, "Banned-phrase scan", "PASS" if not hits else "FAIL",
            "; ".join(hits))

        # Check 3: verbatim CSF warning byte-exact, exactly once
        cnt = pt.count(VERBATIM_CSF)
        ends_ok = pt.rstrip().endswith(VERBATIM_CSF)
        if cnt == 1 and ends_ok:
            rec(bid, "Verbatim CSF warning (1x, byte-exact, final)", "PASS", "")
        else:
            rec(bid, "Verbatim CSF warning (1x, byte-exact, final)", "FAIL",
                f"count={cnt} ends_with={ends_ok}")

        # Check 4: unsourced-claim tokens (search the full JSON text of the ad,
        # but the rule is "0 hits in shipped copy" -> check the shippable
        # fields only: primary_text + headline + description + cta)
        ship = " ".join([pt, ad.get("headline", ""), ad.get("description", ""),
                         ad.get("cta", "")])
        bad = []
        for tok in UNSOURCED_TOKENS:
            # whole-token, case-insensitive; '#1' and '$' need literal match
            if tok.lower() in ship.lower():
                bad.append(tok)
        rec(bid, "Unsourced-claim scan (shipped fields)",
            "PASS" if not bad else "FAIL", f"hits={bad}")

        # Check 7: mechanical rules
        w = wc(pt)
        # word count band 65-80 target, 90 hard cap
        wc_status = "PASS" if w <= 90 else "FAIL"
        wc_detail = f"{w} words"
        if w < 65 or w > 80:
            wc_detail += " (outside 65-80 target band but within 90 cap)"
        rec(bid, "Word count (<=90 hard cap)", wc_status, wc_detail)

        # dashes / smart quotes anywhere in shippable fields
        dfound = []
        for label, ch in DASHES.items():
            if ch in ship:
                dfound.append(label)
        rec(bid, "No dashes/smart-quotes/ellipsis", "PASS" if not dfound else "FAIL",
            ",".join(dfound))

        # Check 8: subject discipline -- "Birchal" <=2 outside attributed quotes
        # Strip quoted spans (text inside straight double quotes) then count.
        no_quotes = re.sub(r'"[^"]*"', "", pt)
        birchal_ct = len(re.findall(r"\bBirchal\b", no_quotes))
        # first-person voice present
        fp = bool(re.search(r"\b(we|our|us)\b", pt, re.I))
        anti = []
        if re.search(r"doing the same for itself", pt, re.I):
            anti.append("'doing the same for itself'")
        sd_status = "PASS"
        sd_detail = f"Birchal x{birchal_ct} outside quotes; first-person={fp}"
        if birchal_ct > 2:
            sd_status = "FAIL"
        if not fp:
            sd_status = "FAIL"
            sd_detail += " NO-FIRST-PERSON"
        if anti:
            sd_status = "FAIL"
            sd_detail += " ANTI:" + ",".join(anti)
        rec(bid, "Subject discipline", sd_status, sd_detail)

        # Check 5: fact traceability spot-checks
        trace = []
        if "$234M" in pt and fact_by_id.get("PLAT-002"):
            trace.append("$234M->PLAT-002")
        if "324" in pt and fact_by_id.get("PLAT-001"):
            trace.append("324->PLAT-001")
        if "137,000" in pt and fact_by_id.get("PLAT-003"):
            trace.append("137,000->PLAT-003")
        if ("eight years" in pt or "2018" in pt) and fact_by_id.get("PLAT-004"):
            trace.append("eight-years/2018->PLAT-004")
        rec(bid, "Fact traceability (spot)", "PASS", "; ".join(trace) or "no core numbers")

    # ---- Pym quote byte-exact (B2) ----
    q = fact_by_id["QUOTE-001"]["verbatim_text"]
    b2 = bodies.get("BIRCHAL-V4-B2", {})
    b2pt = b2.get("primary_text", "")
    rec("BIRCHAL-V4-B2", "Pym quote byte-exact (QUOTE-001)",
        "PASS" if q in b2pt else "FAIL",
        "verbatim present" if q in b2pt else f"NOT byte-exact; expected: {q!r}")

    # ---- Per-headline checks ----
    for h in headlines:
        hid = h.get("id", "?")
        txt = h.get("text", "")
        w = len(txt.split())
        # <=8 words
        rec(hid, "Headline <=8 words", "PASS" if w <= 8 else "FAIL", f"{w} words: {txt!r}")
        # sentence case: a mid-sentence word capitalised that is NOT a known
        # proper noun = genuine Title Case. Sentence-start caps are fine.
        # Tokens stripped of non-alpha; "$234M" etc. are not words.
        proper = {"birchal", "australian", "australians", "aussie", "triple",
                  "bubble", "dom", "pym", "vcs", "vc", "australia", "venture",
                  "partners", "tribe", "global"}
        words = txt.split()
        bad_caps = []
        for i, w in enumerate(words):
            if any(c.isdigit() for c in w):
                continue  # $234M / 137,000 / 2018 are amounts, not words
            core = re.sub(r"[^A-Za-z]", "", w)
            if not core:
                continue  # punctuation-only token, not a word
            sent_start = i == 0 or (i > 0 and words[i - 1].rstrip()[-1:] in ".!?")
            if sent_start:
                continue
            if core[0].isupper() and core.lower() not in proper:
                bad_caps.append(w)
        rec(hid, "Sentence case", "FAIL" if bad_caps else "PASS",
            (f"TITLE-CASE tokens {bad_caps}: " if bad_caps else "") + repr(txt))
        # banned phrases + preoffer + dashes
        hb = []
        if BANNED.search(txt):
            hb.append("BANNED")
        if PREOFFER_VERBS.search(txt):
            hb.append("PREOFFER")
        for label, ch in DASHES.items():
            if ch in txt:
                hb.append(label)
        rec(hid, "Headline banned/dash scan", "PASS" if not hb else "FAIL",
            ",".join(hb) + (f" :: {txt!r}" if hb else ""))

    # ---- whole-set unsourced grep (raw file bytes, all 7 V4 files) ----
    set_hits = []
    for p in [VDIR / f"{b}.json" for b in BODY_IDS] + [VDIR / "summary-v4.json", HEADLINES_V4]:
        raw = p.read_text()
        try:
            obj = json.loads(raw)
        except Exception:
            set_hits.append(f"{p.name}: INVALID JSON")
            continue
        # check only shippable string values, not _meta/_changes commentary
        ship_strings = []
        if "primary_text" in obj:
            ship_strings += [obj.get("primary_text", ""), obj.get("headline", ""),
                             obj.get("description", ""), obj.get("cta", "")]
        for hh in obj.get("headlines", []):
            ship_strings.append(hh.get("text", ""))
        joined = " ".join(ship_strings).lower()
        for tok in UNSOURCED_TOKENS:
            if tok.lower() in joined:
                set_hits.append(f"{p.name}: {tok!r}")
    rec("WHOLE-SET", "Unsourced grep (shippable strings, 7 files)",
        "PASS" if not set_hits else "FAIL", "; ".join(set_hits))

    # ---- Print table ----
    print(f"{'ITEM':<22} {'CHECK':<46} {'STATUS':<6} DETAIL")
    print("-" * 120)
    fails = 0
    for item, check, status, detail in results:
        if status == "FAIL":
            fails += 1
        print(f"{item:<22} {check:<46} {status:<6} {detail}")
    print("-" * 120)
    print(f"TOTAL CHECKS: {len(results)}  FAILS: {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
