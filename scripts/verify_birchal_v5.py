#!/usr/bin/env python3
"""V5 self-audit: word counts, CSF warning byte-check, dash/quote scan,
banned-phrase + PREOFFER + VERBATIM-OFFER + BRAND-EXCLUDED scan,
hook_audit primary-text score, fact-trace, JSON validity, Birchal-count.

CREATE-only helper. Does NOT push anything. Read-only over the V5 files.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path("/Users/jb/Documents/GitHub/learning-loop")
VAR = ROOT / "clients/birchal/loop/birchal-ad-variants"
FACTS_PATH = ROOT / "clients/birchal/facts.json"
HOOK_AUDIT = "/Users/jb/.claude/skills/direct-response-copy/scripts/hook_audit.py"

CSF_WARNING = "*Always consider the general CSF risk warning and offer document before investing."

# Phase-1 (waitlist) hard-block regex from facts.json BANNED-CSF-PHRASES + task spec
BANNED_WAITLIST = re.compile(
    r"(\bbe first to invest\b|\bfirst in line\b|\binvest from \$|\bfrom as little as \$|"
    r"\bguaranteed return\b|\bsecure your allocation\b|\bskip the queue\b|\bjump the queue\b|"
    r"\binvest now\b|\bbuy now\b|\bsubscribe now\b)",
    re.IGNORECASE,
)
PREOFFER_VERBS = re.compile(r"\b(invest|buy|subscribe|purchase)\s+(now|today|here)\b", re.IGNORECASE)
VERBATIM_OFFER_BAD = re.compile(r"(we will send you (the|our) offer( document)?|we'll send you (the|our) offer)", re.IGNORECASE)
BRAND_EXCLUDED = re.compile(r"\b(Zero Co|Old Young'?s?)\b", re.IGNORECASE)
DASHES = re.compile(r"[—–]")
SMART_QUOTES = re.compile(r"[“”‘’…]")

# Additional EOI hard-blocks (task spec Phase 2)
EOI_EXTRA = re.compile(
    r"(first in line|priority (access|allocation)|"
    r"(secure|reserve) your (allocation|place|spot) in the raise|"
    r"shares allocated to early registrants|"
    r"same terms as (institutional|insiders)|be first in the queue|"
    r"\bfrom \$\d|\$\d+ minimum)",
    re.IGNORECASE,
)
# Offer-Live: waitlist-scoped validator hard-blocks transaction verbs BY DESIGN (expected)
LIVE_EXPECTED_FLAG = re.compile(r"(\binvest\b|\$\{\{OFFER_MIN_TBC\}\}|\bguarantee)", re.IGNORECASE)


def word_count(text):
    # Count words in primary_text EXCLUDING the verbatim CSF warning line
    body = text.replace(CSF_WARNING, "").strip()
    return len(body.split())


def brand_count_outside_quotes(text):
    # crude: count 'Birchal' occurrences NOT inside double-quoted spans
    in_q = False
    out = []
    i = 0
    while i < len(text):
        c = text[i]
        if c == '"':
            in_q = not in_q
        elif not in_q:
            out.append(c)
        i += 1
    return len(re.findall(r"\bBirchal\b", "".join(out)))


def hook_score(primary_text):
    r = subprocess.run(
        ["python3", HOOK_AUDIT, "--client-facts", str(FACTS_PATH), "--primary-text", primary_text],
        capture_output=True, text=True,
    )
    m = re.search(r"score:\s*(\d)/5\s*\((PASS|BLOCK[^)]*)\)", r.stdout)
    return (int(m.group(1)), m.group(2)) if m else (None, r.stdout.strip())


def main():
    files = sorted(VAR.glob("BIRCHAL-V5-*.json"))
    if not files:
        print("NO V5 FILES FOUND")
        return 1
    print(f"{'ad_id':<18} {'phase':<11} {'wc':>3} {'hook':>5} {'B#':>3} {'csf':>4} {'dash':>4} {'sq':>3} {'ban':>4} {'verdict'}")
    print("-" * 90)
    all_ok = True
    for f in files:
        d = json.loads(f.read_text())
        pt = d["primary_text"]
        wc = word_count(pt)
        score, verdict = hook_score(pt)
        bc = brand_count_outside_quotes(pt)
        csf_ok = pt.count(CSF_WARNING) == 1 and pt.rstrip().endswith(CSF_WARNING)
        dash_n = len(DASHES.findall(pt + d["headline"] + d["description"] + d["cta"]))
        sq_n = len(SMART_QUOTES.findall(pt + d["headline"] + d["description"] + d["cta"]))
        phase = d.get("phase", "?")
        joined = pt + " " + d["headline"] + " " + d["description"] + " " + d["cta"]
        ban_hits = []
        if BANNED_WAITLIST.search(joined): ban_hits.append("BANNED-CSF")
        if PREOFFER_VERBS.search(joined): ban_hits.append("PREOFFER")
        if VERBATIM_OFFER_BAD.search(joined): ban_hits.append("VERBATIM-OFFER")
        if BRAND_EXCLUDED.search(joined): ban_hits.append("BRAND-EXCL")
        if phase == "eoi" and EOI_EXTRA.search(joined): ban_hits.append("EOI-EXTRA")
        ban = ",".join(ban_hits) if ban_hits else "0"

        problems = []
        # Waitlist: strict. EOI: no waitlist-extra. Live: transaction verbs expected/phase-gated.
        if phase == "waitlist":
            if score is None or score < 4: problems.append(f"hook<{score}")
            if ban != "0": problems.append(f"ban={ban}")
        elif phase == "eoi":
            if ban != "0": problems.append(f"ban={ban}")
        elif phase == "offer-live":
            # only flag the EXPLICITLY non-expected: banned-csf phrases that are NOT 'invest now' style transaction-by-design
            hard = [h for h in ban_hits if h in ("BRAND-EXCL", "VERBATIM-OFFER")]
            if hard: problems.append(f"ban={','.join(hard)}")
        if not csf_ok: problems.append("CSF-warning")
        if dash_n: problems.append(f"dash={dash_n}")
        if sq_n: problems.append(f"sq={sq_n}")
        if bc > 2: problems.append(f"Birchal>{bc}")
        if wc > 110: problems.append(f"wc>{wc}")
        verdict_s = "OK" if not problems else "FAIL:" + ";".join(problems)
        if problems:
            all_ok = False
        print(f"{d['ad_id']:<18} {phase:<11} {wc:>3} {str(score):>5} {bc:>3} {'Y' if csf_ok else 'N':>4} {dash_n:>4} {sq_n:>3} {ban:>4} {verdict_s}")
    print("-" * 90)
    print("ALL OK" if all_ok else "SOME FAILED (see FAIL rows)")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
