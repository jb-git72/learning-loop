#!/usr/bin/env python3
"""compliance-au skill applied to Birchal V4 (CSF pre-offer).

Mechanises the CSF checklist from the compliance-au skill:
- s 738G equal terms (preferential-access language)
- INFO 217 pre-offer marketing (offer-like / transaction verbs / return forecasts)
- s 738ZG verbatim risk warning (byte-exact, not paraphrased)
- RG 234 testimonials (genuine, attributed, not implying typical financial outcome)
- ACL s 18 overall-impression / misleading silence
- BRAND-EXCLUDED (companies in administration)
Severity: CRITICAL (HIGH) / WARNING (MEDIUM) / INFO (LOW).
"""
import json
import re
from pathlib import Path

REPO = Path("/Users/jb/Documents/GitHub/learning-loop")
VDIR = REPO / "clients" / "birchal" / "loop" / "birchal-ad-variants"
HL = REPO / "clients" / "birchal" / "loop" / "birchal-headlines-v4.json"
CSF_WARNING = "*Always consider the general CSF risk warning and offer document before investing."

# s 738G preferential-terms language (HIGH if present)
PREFERENTIAL = re.compile(
    r"\b(VIP|exclusive access|first access|priority terms|early[- ]bird|"
    r"founding investor|preferential|reserve your (vip )?spot at better|"
    r"better terms|invest first|priority allocation|early access to (the )?(deal|terms))\b",
    re.I)
# INFO 217 offer-like / transaction verbs as a CTA to the reader (HIGH)
TXN_CTA = re.compile(r"\b(invest|buy|subscribe|purchase)\s+(now|today|here)\b", re.I)
# Return forecasts / projections (HIGH under INFO 217 + RG 234)
RETURN_FORECAST = re.compile(
    r"\b(expected return|projected return|guaranteed return|\d+\s?%\s?(p\.?a\.?|return|yield)|"
    r"returns of|forecast(ed)? (return|yield)|double your|grow your money)\b", re.I)
EXCLUDED = re.compile(r"\b(Zero Co|Old Young)\b", re.I)
# Hard scarcity (ACL risk pre-offer)
HARD_SCARCITY = re.compile(
    r"\b(act now|last chance|don'?t miss out|ending soon|hurry|only \d+ (spots|left)|closing soon)\b",
    re.I)

findings = []  # (item, severity, rule, detail)


def f(item, sev, rule, detail):
    findings.append((item, sev, rule, detail))


def audit_text(item, text, is_headline=False):
    if PREFERENTIAL.search(text):
        f(item, "CRITICAL", "Corps Act s 738G equal terms",
          f"preferential-access language: {PREFERENTIAL.search(text).group(0)!r}")
    if TXN_CTA.search(text):
        f(item, "CRITICAL", "ASIC INFO 217 pre-offer",
          f"transaction-verb CTA: {TXN_CTA.search(text).group(0)!r}")
    if RETURN_FORECAST.search(text):
        f(item, "CRITICAL", "ASIC INFO 217 / RG 234",
          f"return forecast/projection: {RETURN_FORECAST.search(text).group(0)!r}")
    if EXCLUDED.search(text):
        f(item, "CRITICAL", "BRAND-EXCLUDED (in administration)",
          f"excluded brand: {EXCLUDED.search(text).group(0)!r}")
    if HARD_SCARCITY.search(text):
        f(item, "WARNING", "ACL s 18 (hard scarcity pre-offer)",
          f"hard scarcity: {HARD_SCARCITY.search(text).group(0)!r}")


for bid in ["BIRCHAL-V4-A1", "BIRCHAL-V4-A2", "BIRCHAL-V4-A3",
            "BIRCHAL-V4-B1", "BIRCHAL-V4-B2"]:
    d = json.loads((VDIR / f"{bid}.json").read_text())
    pt = d["primary_text"]
    blob = " ".join([pt, d.get("headline", ""), d.get("description", ""), d.get("cta", "")])
    audit_text(bid, blob)

    # s 738ZG verbatim risk warning byte-exact, exactly once, terminal
    cnt = pt.count(CSF_WARNING)
    if cnt != 1:
        f(bid, "CRITICAL", "Corps Act s 738ZG verbatim risk warning",
          f"warning appears {cnt}x (must be exactly 1, byte-exact)")
    elif not pt.rstrip().endswith(CSF_WARNING):
        f(bid, "WARNING", "Corps Act s 738ZG verbatim risk warning",
          "warning present but not the terminal line")

    # RG 234 testimonial rule: B2 carries the Pym quote
    if "\"" in pt:
        # quoted span present -> must be genuine + attributed + no financial-outcome
        # Pym quote is service/credibility, no $ outcome -> LOW
        quoted = re.findall(r'"[^"]+"', pt)
        for qspan in quoted:
            if re.search(r"\$\d|return|profit|made \$|\d+\s?%", qspan, re.I):
                f(bid, "CRITICAL", "RG 234 testimonial (financial outcome)",
                  f"testimonial implies financial outcome: {qspan[:60]!r}")
        # attribution present nearby?
        if "Dom Pym" in pt and "Triple Bubble" in pt:
            f(bid, "INFO", "RG 234 testimonial (attribution OK)",
              "Pym quote attributed 'Dom Pym, Triple Bubble'; service/credibility "
              "claim, no financial-outcome implication. Retain signed consent "
              "(quotes-client-supplied-2026-05-17.md / BIRCH quotes.md, Kirstin 6 May).")

    # ACL s 18 misleading silence: waitlist must be framed as free / no decision
    # until offer document. Look for risk-reversal framing.
    rr = bool(re.search(r"(read the offer|offer document|when (it|the offer) (opens|goes live)|"
                        r"tell you the moment|see the offer)", blob, re.I))
    if not rr:
        f(bid, "WARNING", "ACL s 18 (misleading silence)",
          "no explicit 'read the offer document / when it opens' framing; "
          "reader may infer the waitlist is the investment decision")
    else:
        f(bid, "INFO", "ACL s 18 (risk-reversal present)",
          "waitlist framed as notification-only; decision deferred to offer document")

hl = json.loads(HL.read_text())["headlines"]
for h in hl:
    audit_text(h["id"], h["text"], is_headline=True)

# ---- Report ----
order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
findings.sort(key=lambda x: (order[x[1]], x[0]))
crit = sum(1 for x in findings if x[1] == "CRITICAL")
warn = sum(1 for x in findings if x[1] == "WARNING")
info = sum(1 for x in findings if x[1] == "INFO")

print("COMPLIANCE-AU AUDIT  Birchal V4 (CSF pre-offer)")
print("Regulations: Corps Act Part 6D.3A, s 738G, s 738ZG, ASIC RG 261/262, "
      "INFO 217, ACL s 18, RG 234 testimonials")
print("-" * 110)
for item, sev, rule, detail in findings:
    print(f"[{sev:<8}] {item:<16} {rule}")
    print(f"            -> {detail}")
print("-" * 110)
print(f"CRITICAL(HIGH)={crit}  WARNING(MEDIUM)={warn}  INFO(LOW)={info}")
print()
if crit or warn:
    print("ACTION REQUIRED: resolve every CRITICAL and WARNING before client send.")
    raise SystemExit(1)
print("RESULT: no CRITICAL/HIGH or WARNING/MEDIUM findings. LOW/INFO notes only. "
      "Ad set is compliant for pre-offer CSF release.")
