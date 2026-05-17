#!/usr/bin/env python3
"""Adversarial independent verification of the Birchal V5 ad batch.

Re-runs the full phase-aware compliance battery from the JSON files. Does NOT
trust any create-agent _compliance_findings_resolved block. Prints a PASS/FAIL
matrix and an itemised findings list.

Run: python3 scripts/verify_birchal_v5_adversarial.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path("/Users/jb/Documents/GitHub/learning-loop")
VAR = ROOT / "clients/birchal/loop/birchal-ad-variants"
LOOP = ROOT / "clients/birchal/loop"
FACTS = ROOT / "clients/birchal/facts.json"
HOOK_AUDIT = "/Users/jb/.claude/skills/direct-response-copy/scripts/hook_audit.py"
HUMANISER = "/Users/jb/Documents/GitHub/marketing-copy/direct-response-copy/scripts/humaniser.py"

W = [f"BIRCHAL-V5-W{i}" for i in range(1, 9)]
E = [f"BIRCHAL-V5-E{i}" for i in range(1, 7)]
L = [f"BIRCHAL-V5-L{i}" for i in range(1, 7)]
ALL_BODIES = W + E + L

# ---------- regex banks ----------
BANNED_CSF = re.compile(
    r"(\bbe first to invest\b|\bfirst in line\b|\binvest from \$|"
    r"\bfrom as little as \$|\bguaranteed return\b|\bsecure your allocation\b|"
    r"\bskip the queue\b|\bjump the queue\b|\binvest now\b|\bbuy now\b|"
    r"\bsubscribe now\b)", re.I)
PREOFFER_VERBS = re.compile(r"\b(invest|buy|subscribe|purchase)\s+(now|today|here)\b", re.I)
VERBATIM_OFFER = re.compile(r"we will send you (the|our) offer", re.I)
BRAND_EXCLUDED = re.compile(r"(Zero Co|Old Young)", re.I)

# EOI-extra (Phase 2)
EOI_EXTRA = [
    (re.compile(r"\bpriority\b", re.I), "priority"),
    (re.compile(r"\ballocat(ion|ed|e)\b", re.I), "allocation/allocated"),
    (re.compile(r"\breserve your (place|spot)\b", re.I), "reserve your place/spot"),
    (re.compile(r"\bfirst in (line|the queue)\b", re.I), "first in line/queue"),
    # $ MINIMUM only: "from $X", "$X a parcel/share/minimum", "as little as $X",
    # "invest $X". NOT the platform-volume proof stat "$234M+" (PLAT-002).
    (re.compile(r"(from \$\d|as little as \$\d|\$\d[\d,.]*\s*(a |per )?(parcel|share|minimum)|invest \$\d|minimum (of )?\$\d)", re.I),
     "$ investment minimum"),
    (re.compile(r"same terms as (institutional|insiders|triple bubble)", re.I),
     "same terms as institutional/insiders/Triple Bubble"),
]

# Live (Phase 3): guarantee-return / brand-excluded / verbatim-offer must be 0
GUARANTEE_RETURN = re.compile(r"\bguaranteed?\b|\bguaranteed return\b", re.I)

# Unsourced-claim grep (shippable strings only)
UNSOURCED = [
    "64%", "70%", "market share", "#1", "largest", "leading CSF", "top 10",
    "top ten", "82,659", "valuation", "$5M", "$1B", "2030", "$250", "$0.50",
    "$50", "from $",
]

# Investor-association names
INVESTOR_NAMES = [
    "Dom Pym", "Triple Bubble", "Nick Carter", "AVPF", "Shayne Gary",
    "Don McKenzie", "Tribe Global", "Australia Venture Partners",
]
ASSOC_OVERCLAIM = re.compile(
    r"(invested in (us|birchal)|backed (this|the|our) raise|"
    r"followed (us )?into the round|anchored our raise|on our cap table|"
    r"\bbacked us\b|\bbacked birchal\b)", re.I)

CSF_WARNING = "*Always consider the general CSF risk warning and offer document before investing."

DASH_CHARS = re.compile(r"[—–“”‘’…]")

RG234_RISK_PATTERNS = [
    re.compile(r"value can fall as well as rise", re.I),
    re.compile(r"every investment carries risk", re.I),
]
RG234_READ_DECIDE = re.compile(r"read the offer document and decide for yourself", re.I)


def load(name):
    return json.loads((VAR / f"{name}.json").read_text())


def shippable_strings(d):
    """Return the shippable strings (what actually renders in the ad)."""
    return {
        "primary_text": d.get("primary_text", ""),
        "headline": d.get("headline", ""),
        "description": d.get("description", ""),
        "cta": d.get("cta", ""),
    }


def run_hook_audit(text, primary=False):
    args = ["python3", HOOK_AUDIT, "--client-facts", str(FACTS)]
    if primary:
        args.append("--primary-text")
    args.append(text)
    r = subprocess.run(args, capture_output=True, text=True)
    # parse "score" from output
    m = re.search(r"score[:\s]+(\d+)", r.stdout, re.I)
    score = int(m.group(1)) if m else None
    return score, r.returncode, r.stdout.strip()


def run_humaniser(path):
    r = subprocess.run(["python3", HUMANISER, str(path)],
                        capture_output=True, text=True)
    err = r.stderr
    m = re.search(r"substitutions=(\d+) word_flags=(\d+) opener_flags=(\d+)", err)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3)), r.stdout
    return None, None, None, r.stdout


def phase_of(name):
    if name in W:
        return "waitlist"
    if name in E:
        return "eoi"
    return "offer-live"


def main():
    facts = json.loads(FACTS.read_text())
    fmap = {f["fact_id"]: f for f in facts["facts"]}
    q1 = fmap["QUOTE-001"]["verbatim_text"]
    q6 = fmap["QUOTE-006"]["ad_safe_text"]
    q9 = fmap["QUOTE-009"]["ad_safe_text"]

    results = {}
    findings = []

    for name in ALL_BODIES:
        d = load(name)
        ph = phase_of(name)
        ship = shippable_strings(d)
        pt = ship["primary_text"]
        joined = " ".join(ship.values())
        row = {}

        # --- 1. hook_audit ---
        score, rc, _ = run_hook_audit(pt, primary=True)
        row["hook"] = score
        if ph == "waitlist":
            row["hook_pass"] = (score is not None and score >= 4)
            if not row["hook_pass"]:
                findings.append(f"[{name}] HOOK FAIL waitlist score={score} (HARD, must be >=4)")
        else:
            row["hook_pass"] = (score is not None and score >= 4)
            if not row["hook_pass"]:
                findings.append(f"[{name}] HOOK <4 ({ph}) score={score} (flag, not silent-accept)")

        # --- 2. banned-phrase scans, phase-aware ---
        banned_hits = []
        for label, rx in [("BANNED-CSF", BANNED_CSF), ("PREOFFER-VERBS", PREOFFER_VERBS),
                          ("VERBATIM-OFFER", VERBATIM_OFFER), ("BRAND-EXCLUDED", BRAND_EXCLUDED)]:
            m = rx.search(joined)
            if m:
                banned_hits.append(f"{label}:'{m.group(0)}'")
        if ph == "eoi":
            for rx, lbl in EOI_EXTRA:
                m = rx.search(joined)
                if m:
                    banned_hits.append(f"EOI-EXTRA[{lbl}]:'{m.group(0)}'")
        if ph == "offer-live":
            # Live: brand-excluded/verbatim-offer/guarantee-return must be 0
            m = GUARANTEE_RETURN.search(joined)
            if m:
                banned_hits.append(f"GUARANTEE-RETURN:'{m.group(0)}'")
            mbx = BRAND_EXCLUDED.search(joined)
            if mbx:
                banned_hits.append(f"BRAND-EXCLUDED:'{mbx.group(0)}'")
            mvo = VERBATIM_OFFER.search(joined)
            if mvo:
                banned_hits.append(f"VERBATIM-OFFER:'{mvo.group(0)}'")
        row["banned"] = "CLEAN" if not banned_hits else ";".join(banned_hits)
        row["banned_pass"] = not banned_hits
        if banned_hits:
            findings.append(f"[{name}] BANNED-PHRASE HARD FAIL ({ph}): {banned_hits}")

        # --- 3. unsourced-claim grep on shippable ---
        uns_hits = []
        for tok in UNSOURCED:
            if tok.lower() in joined.lower():
                uns_hits.append(tok)
        row["unsourced"] = "CLEAN" if not uns_hits else ",".join(uns_hits)
        row["unsourced_pass"] = not uns_hits
        if uns_hits:
            findings.append(f"[{name}] UNSOURCED-CLAIM HARD FAIL shippable: {uns_hits}")

        # --- 4. investor-association defect hunt ---
        assoc_problem = []
        for nm in INVESTOR_NAMES:
            if nm.lower() in joined.lower():
                # look for over-claim verbs near the name
                if ASSOC_OVERCLAIM.search(joined):
                    assoc_problem.append(f"{nm}+overclaim:'{ASSOC_OVERCLAIM.search(joined).group(0)}'")
        row["assoc"] = "CLEAN" if not assoc_problem else ";".join(assoc_problem)
        row["assoc_pass"] = not assoc_problem
        if assoc_problem:
            findings.append(f"[{name}] INVESTOR-ASSOCIATION OVERCLAIM: {assoc_problem}")

        # --- 5. Birchal Next integrity ---
        bn_problem = []
        if "backed by x and y" in joined.lower():
            bn_problem.append("literal 'backed by X and Y'")
        # forward-looking voice if Birchal Next mentioned
        if "birchal next" in joined.lower():
            # must not assert present-state capability ("now has supreme analytics")
            if re.search(r"birchal (now has|has supreme|now offers)", joined, re.I):
                bn_problem.append("present-state capability claim")
        row["birchal_next"] = "CLEAN" if not bn_problem else ";".join(bn_problem)
        row["bn_pass"] = not bn_problem
        if bn_problem:
            findings.append(f"[{name}] BIRCHAL-NEXT integrity: {bn_problem}")

        # --- 6. verbatim CSF warning byte-exact, once, terminal ---
        cnt = pt.count(CSF_WARNING)
        terminal = pt.rstrip().endswith(CSF_WARNING)
        row["csf_warn"] = f"count={cnt},terminal={terminal}"
        row["csf_pass"] = (cnt == 1 and terminal)
        if not row["csf_pass"]:
            findings.append(f"[{name}] CSF-WARNING FAIL count={cnt} terminal={terminal}")

        # --- 7. quote fidelity ---
        qf = []
        if name in ("BIRCHAL-V5-W4", "BIRCHAL-V5-E4", "BIRCHAL-V5-L4"):
            if q1 not in pt:
                qf.append("QUOTE-001 not byte-exact in primary_text")
            if "Dom Pym, Triple Bubble" not in pt:
                qf.append("attribution 'Dom Pym, Triple Bubble' missing")
        if name in ("BIRCHAL-V5-W5", "BIRCHAL-V5-E5", "BIRCHAL-V5-L5"):
            if q6 not in pt:
                qf.append("QUOTE-006 ad_safe not byte-exact in primary_text")
            if "Aubrey Blanche" not in pt:
                qf.append("attribution 'Aubrey Blanche' missing")
        if name == "BIRCHAL-V5-W7":
            if q9 not in pt:
                qf.append("QUOTE-009 ad_safe not byte-exact in primary_text")
            if "Kirstin Hunter, CEO, Birchal" not in pt:
                qf.append("attribution 'Kirstin Hunter, CEO, Birchal' missing")
        row["quote"] = "CLEAN" if not qf else ";".join(qf)
        row["quote_pass"] = not qf
        if qf:
            findings.append(f"[{name}] QUOTE-FIDELITY FAIL: {qf}")

        # --- 8. humaniser ---
        subs, wf, of_, hout = run_humaniser(VAR / f"{name}.json")
        # word_flags inside attributed verbatim are exempt; detect which flagged words
        flagged = re.findall(r"\[FLAG:([^\]]+)\]", hout)
        # only count flags that fall in shippable strings (not _rationale)
        ship_flags = []
        for fw in flagged:
            if fw == "opener":
                continue
            for s in ship.values():
                if re.search(r"\b" + re.escape(fw) + r"\b", s, re.I):
                    ship_flags.append(fw)
                    break
        row["human"] = f"subs={subs},wf={wf},of={of_},ship_flags={ship_flags}"
        # exemption: ecosystem inside QUOTE-009 (W7), seamless inside QUOTE-005, etc.
        exempt = set()
        if name == "BIRCHAL-V5-W7" and "ecosystem" in q9.lower():
            exempt.add("ecosystem")
        real_flags = [f for f in set(ship_flags) if f.lower() not in {e.lower() for e in exempt}]
        row["human_pass"] = (subs == 0 and not real_flags)
        if subs:
            findings.append(f"[{name}] HUMANISER typography subs={subs} (em/en/smart in JSON)")
        if real_flags:
            findings.append(f"[{name}] HUMANISER word flags in shippable (non-exempt): {real_flags}")

        # --- 9. mechanical ---
        mech = []
        for k, s in ship.items():
            if DASH_CHARS.search(s):
                mech.append(f"{k}: em/en/smartquote/ellipsis")
        # headline <=8 words, sentence case
        hl = ship["headline"]
        hwords = len(hl.split())
        if hwords > 8:
            mech.append(f"headline {hwords} words >8")
        wc = d.get("_word_count_primary_text")
        actual_wc = len(pt.replace(CSF_WARNING, "").split())
        # waitlist <=90 (target 65-80); eoi/live <=110
        if ph == "waitlist":
            cap = 90
        else:
            cap = 110
        # count words excluding the verbatim CSF warning line
        body_wc = len([w for w in pt.split() if w])
        # remove the warning's 13 words for the cap check
        warn_wc = len(CSF_WARNING.split())
        eff_wc = body_wc - warn_wc if CSF_WARNING in pt else body_wc
        if eff_wc > cap:
            mech.append(f"primary_text {eff_wc}w >{cap} ({ph})")
        row["mech"] = "CLEAN" if not mech else ";".join(mech)
        row["mech_eff_wc"] = eff_wc
        row["mech_pass"] = not mech
        if mech:
            findings.append(f"[{name}] MECHANICAL: {mech}")

        # --- fact traceability: numbers in shippable must trace ---
        # known-good values
        nums_in = re.findall(r"\$?\d[\d,]*\+?(?:M|K|B)?", joined)
        allowed = {"324", "234", "$234M", "$234M+", "137,000", "2018", "8"}
        bad_nums = []
        for n in nums_in:
            base = n.replace("$", "").replace("+", "").replace("M", "").replace("K", "").replace("B", "").rstrip(",.")
            if n in allowed:
                continue
            if base in {"324", "137,000", "2018", "8", "234"}:
                continue
            if re.fullmatch(r"(19|20)\d{2}", base):
                continue
            bad_nums.append(n)
        row["facttrace"] = "CLEAN" if not bad_nums else ",".join(bad_nums)
        row["facttrace_pass"] = not bad_nums
        if bad_nums:
            findings.append(f"[{name}] FACT-TRACE unexpected number(s): {bad_nums}")

        # --- Live phase RG234 balance test ---
        if ph == "offer-live":
            risk_present = any(rx.search(pt) for rx in RG234_RISK_PATTERNS)
            read_decide = bool(RG234_READ_DECIDE.search(pt))
            row["rg234"] = f"risk={risk_present},read_decide={read_decide}"
            row["rg234_pass"] = (risk_present and read_decide)
            if not row["rg234_pass"]:
                findings.append(f"[{name}] RG234-BALANCE FAIL risk={risk_present} read_decide={read_decide}")
            # transaction verb 'invest' expected here
            row["status_check"] = d.get("status") == "draft-phase-gated" and bool(d.get("compliance_note"))
            if not row["status_check"]:
                findings.append(f"[{name}] LIVE missing status=draft-phase-gated or compliance_note")
        elif ph == "eoi":
            row["status_check"] = d.get("status") == "draft-phase-gated" and bool(d.get("compliance_note"))
            if not row["status_check"]:
                findings.append(f"[{name}] EOI missing status=draft-phase-gated or compliance_note")
        else:
            row["status_check"] = d.get("status") == "ready"

        results[name] = row

    # ---------- headlines ----------
    hl_data = json.loads((LOOP / "birchal-headlines-v5.json").read_text())
    hl_results = {}
    for h in hl_data["headlines"]:
        hid = h["id"]
        txt = h["text"]
        ph = h.get("phase", "waitlist")
        hr = {}
        score, rc, _ = run_hook_audit(txt, primary=False)
        hr["hook"] = score
        hr["hook_pass"] = (score is not None and score >= 4)
        if not hr["hook_pass"]:
            findings.append(f"[HL {hid}] hook score={score} <4")
        # banned
        bh = []
        if BANNED_CSF.search(txt):
            bh.append("BANNED-CSF")
        if ph == "waitlist" and PREOFFER_VERBS.search(txt):
            bh.append("PREOFFER-VERBS")
        if ph == "eoi":
            for rx, lbl in EOI_EXTRA:
                if rx.search(txt):
                    bh.append(f"EOI[{lbl}]")
        hr["banned"] = "CLEAN" if not bh else ";".join(bh)
        hr["banned_pass"] = not bh
        if bh:
            findings.append(f"[HL {hid}] banned: {bh}")
        # unsourced
        uh = [t for t in UNSOURCED if t.lower() in txt.lower()]
        hr["unsourced_pass"] = not uh
        if uh:
            findings.append(f"[HL {hid}] unsourced: {uh}")
        # mechanical
        mh = []
        if DASH_CHARS.search(txt):
            mh.append("dash/smartquote")
        wlen = len(txt.split())
        if wlen > 8 and not (ph == "eoi" and wlen == 9):
            mh.append(f"{wlen} words >8")
        elif wlen > 8:
            mh.append(f"{wlen} words (documented EOI exception)")
        hr["words"] = wlen
        hr["mech"] = "CLEAN" if not mh else ";".join(mh)
        hr["mech_pass"] = not [x for x in mh if "documented" not in x]
        if [x for x in mh if "documented" not in x]:
            findings.append(f"[HL {hid}] mechanical: {mh}")
        hl_results[hid] = hr

    # ---------- output ----------
    print("=" * 100)
    print("BIRCHAL V5 ADVERSARIAL VERIFICATION — BODIES (20)")
    print("=" * 100)
    hdr = f"{'AD':<16}{'PH':<5}{'HOOK':<6}{'BAN':<5}{'UNS':<5}{'ASSC':<5}{'BNXT':<5}{'CSF':<5}{'QUOT':<5}{'HUM':<5}{'MECH':<5}{'FACT':<5}{'RG234':<7}{'STAT':<5}"
    print(hdr)
    print("-" * 100)
    for name in ALL_BODIES:
        r = results[name]
        ph = phase_of(name)[:4]
        def m(k):
            return "PASS" if r.get(k) else "FAIL"
        rg = m("rg234_pass") if "rg234_pass" in r else "n/a"
        print(f"{name:<16}{ph:<5}{str(r['hook']):<6}{m('banned_pass'):<5}{m('unsourced_pass'):<5}"
              f"{m('assoc_pass'):<5}{m('bn_pass'):<5}{m('csf_pass'):<5}{m('quote_pass'):<5}"
              f"{m('human_pass'):<5}{m('mech_pass'):<5}{m('facttrace_pass'):<5}{rg:<7}"
              f"{('PASS' if r.get('status_check') else 'FAIL'):<5}")

    print()
    print("=" * 100)
    print("HEADLINES V5")
    print("=" * 100)
    print(f"{'ID':<16}{'PHASE':<12}{'HOOK':<6}{'W':<4}{'BAN':<5}{'UNS':<5}{'MECH':<5}")
    print("-" * 60)
    for hid, hr in hl_results.items():
        def m(k):
            return "PASS" if hr.get(k) else "FAIL"
        ph = next((h["phase"] for h in hl_data["headlines"] if h["id"] == hid), "?")
        print(f"{hid:<16}{ph:<12}{str(hr['hook']):<6}{hr['words']:<4}"
              f"{m('banned_pass'):<5}{m('unsourced_pass'):<5}{m('mech_pass'):<5}")

    print()
    print("=" * 100)
    print(f"FINDINGS ({len(findings)})")
    print("=" * 100)
    if not findings:
        print("NONE — all checks PASS")
    for f in findings:
        print(" -", f)

    # detailed dump
    print()
    print("=" * 100)
    print("DETAIL (per body)")
    print("=" * 100)
    for name in ALL_BODIES:
        r = results[name]
        print(f"\n--- {name} ({phase_of(name)}) ---")
        for k, v in r.items():
            print(f"  {k}: {v}")

    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
