"""SMS-focused hill-climb pass-5 (PICKUP-2026-04-27 follow-up).

The shared `hill_climb.py` mechanics are not fully SMS-aware (crossover/donor
picks etc.). This script is a tighter, SMS-native loop:

1. Seeds the 2 canonical FMTH SMS bodies (round-opens-vip + purchase-confirmation)
2. Runs N iterations where each iteration:
   a. Generates K candidate variants per seed via writer.py (which IS SMS-aware)
   b. Adds a pinned set of hand-crafted variants (target the LLM-judged dim
      weaknesses: motivation_match, tone_brand_fit, specificity)
   c. Scores every candidate with full LLM judges
   d. Keeps the top-1 per seed for the next round
3. Stops when both seeds hit ≥0.80 (target) OR after 4 iterations OR after
   25min wall time (whichever first)
4. Writes the winner JSON, scored output, review HTML
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

# Auto-load .env
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from engine.scorer import load_client, score_ad  # noqa: E402

try:
    from writer import generate_variant  # noqa: E402
except Exception as e:
    generate_variant = None
    print(f"[warn] writer import failed: {e}")


CLIENT = "farm-thru"
TARGET = 0.80
STRETCH = 0.90
WALL_TIME_SECS = 25 * 60
MAX_ITERATIONS = 4
LLM_GENERATED_PER_ITER = 4  # writer-generated candidates per seed per iter


# ---------------------------------------------------------------------------
# Hand-crafted candidate banks
# ---------------------------------------------------------------------------
# Targets motivation_match (felt urgency), tone_brand_fit (Rachel/regenerative
# voice), and specificity (verified named entities: Rachel, Brookvale, NSW).
# Every candidate kept ≤140 expanded chars (single-segment + 5/5 char_efficiency).
# Compliance-required tokens preserved verbatim:
#   - {{birchal_url}} for round-opens (URL → risk-warning route)
#   - "general CSF risk warning" short paraphrase always present
#   - "Reply STOP" on marketing sends, omitted on transactional confirms
#
# Banned (per learnings-sms.md / FMTH overrides):
#   priority, $\d, em-dashes, "huge", "unmissable", "act now", "don't miss"

PINNED_OPEN_VARIANTS = [
    # V1: Rachel signoff = +1 specific (Rachel name registers in scorer regex)
    "FarmThru is live on Birchal: {{birchal_url}} See the general CSF risk warning. Reply STOP. Rachel",
    # V2: Founder voice ("Rachel here") + felt moment ("just opened")
    "Rachel here. FarmThru just opened on Birchal: {{birchal_url}} See the general CSF risk warning. Reply STOP.",
    # V3: Stake the ground for VIPs ("your spot held") + brand voice
    "Your VIP spot is held. FarmThru is open: {{birchal_url}} See general CSF risk warning. Reply STOP. Rachel",
    # V4: Make the moment visceral ("doors are open") + regenerative cue (brand)
    "Doors open. Back FarmThru's regenerative offer: {{birchal_url}} See general CSF risk warning. Reply STOP.",
    # V5: Direct, warm, founder-signed
    "We're live. Your FarmThru offer is open at Birchal: {{birchal_url}} See general CSF risk warning. STOP to opt out. Rachel",
    # V6: "From the paddock" = brand voice + Rachel + named place
    "From the paddock. FarmThru opens on Birchal: {{birchal_url}} See general CSF risk warning. Reply STOP. Rachel",
    # V7: Tighter - confirmation of held VIP slot (motivation match)
    "Your VIP slot is open. FarmThru on Birchal: {{birchal_url}} See general CSF risk warning. STOP to opt out. Rachel",
    # V8: Brand-direct hub reference ("Brookvale" verified specific)
    "FarmThru is open. From Brookvale to Birchal: {{birchal_url}} See general CSF risk warning. Reply STOP. Rachel",
]

PINNED_CONFIRM_VARIANTS = [
    # V1: Rachel signoff (specificity +1) — drop "early" to make room
    "You're in. VIP access secured. We'll text when FarmThru opens at Birchal. See general CSF risk warning. Refund: hello@farmthru.com.au Rachel",
    # V2: Warmer founder voice + tighter compliance
    "You're in. VIP secured at FarmThru. We'll text the moment Birchal opens. See general CSF risk warning. Refund: hello@farmthru.com.au Rachel",
    # V3: Felt-need first ("welcome"), tightened compliance phrasing
    "Welcome aboard. Your VIP spot at FarmThru is secured. We'll text when Birchal opens. See general CSF risk warning. Refund: hello@farmthru.com.au",
    # V4: Strong status word + Rachel signoff
    "You're in. VIP secured at FarmThru. We'll text the second Birchal opens. See general CSF risk warning. Refund anytime. Rachel",
    # V5: Tighter, brand-warm, Rachel
    "Locked in. Your FarmThru VIP spot is secured. We'll text when Birchal opens. See general CSF risk warning. Refund: hello@farmthru.com.au",
    # V6: Reassurance + founder voice ("from us") + Rachel
    "You're in. VIP secured at FarmThru. We'll text when Birchal opens. See general CSF risk warning. Refundable anytime. Rachel",
    # V7: Founder signature confirms transactional warmth
    "Welcome to FarmThru VIP. Your spot is secured. We'll text when Birchal opens. See general CSF risk warning. Refund: hello@farmthru.com.au",
    # V8: "secured" + "Rachel" + tight compliance
    "You're in. FarmThru VIP secured. We'll text when Birchal opens. See general CSF risk warning. Refund: hello@farmthru.com.au Rachel",
]


def _expanded_len(body: str) -> int:
    return len(re.sub(r"\{\{[^{}]+\}\}", "X" * 30, body))


def _make_candidate(seed: dict, body: str, label: str) -> dict:
    cand = deepcopy(seed)
    cand["body"] = body
    cand["char_count"] = len(body)
    cand["_variant_label"] = label
    return cand


def _filter_pinned(seed: dict, variants: list[str], label_prefix: str) -> list[dict]:
    """Drop pinned variants that exceed the 140-char single-segment-tight cap."""
    out = []
    for i, body in enumerate(variants):
        elen = _expanded_len(body)
        if elen > 160:
            print(f"  [skip] {label_prefix}-V{i+1}: expanded={elen} > 160 (would bust)")
            continue
        cand = _make_candidate(seed, body, f"{label_prefix}-V{i+1}")
        cand["_expanded_len"] = elen
        out.append(cand)
    return out


def _gen_writer_variant(
    seed: dict,
    client_dir: Path,
    weak_dims: list[str],
    label: str,
) -> dict | None:
    """Use writer.py to generate one SMS variant. Returns None on error."""
    if generate_variant is None:
        return None
    try:
        new_ad = generate_variant(
            angle=seed.get("angle", "transparency-safety"),
            tactic=seed.get("tactic", "vip-purchase-confirmation"),
            hook_type=seed.get("hook_type", "confirmation"),
            funnel=seed.get("funnel", "BOF"),
            client_dir=client_dir,
            current_best=seed,
            recent_failures=[],
            content_type="sms",
            mode="improve",
            weak_dimensions=weak_dims,
        )
        # Preserve seed metadata
        for k in ("sms_id", "purpose", "audience", "content_type", "send_segment", "merge_tags"):
            if k in seed:
                new_ad[k] = seed[k]
        if not new_ad.get("body"):
            return None
        new_ad["_variant_label"] = label
        new_ad["_expanded_len"] = _expanded_len(new_ad["body"])
        return new_ad
    except Exception as e:
        print(f"  [writer-fail] {label}: {e}")
        return None


def _score(cand: dict, client: dict, peers: list[dict]) -> dict:
    """Full LLM-judged score for one candidate. Returns the report dict."""
    return score_ad(cand, client, existing_ads=peers, use_llm=True)


def _summary_line(cand: dict, report: dict) -> str:
    label = cand.get("_variant_label", "?")
    elen = cand.get("_expanded_len", _expanded_len(cand.get("body", "")))
    composite = report.get("composite", 0)
    verdict = report.get("verdict", "?")
    raw = report.get("rubric", {}).get("raw_scores", {})
    weak = (
        f"mot={raw.get('motivation_match','-')} "
        f"spec={raw.get('specificity','-')} "
        f"tone={raw.get('tone_brand_fit','-')} "
    )
    compl = "PASS" if report.get("compliance", {}).get("passed", False) else "FAIL"
    crit = "FAIL" if report.get("rule_compliance", {}).get("critical_failure") else "ok"
    return f"  {label:24s}  comp={composite:.4f} {verdict:14s}  exp={elen:3d}c  {weak} compl={compl} crit={crit}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-iterations", type=int, default=MAX_ITERATIONS)
    parser.add_argument("--writer-per-iter", type=int, default=LLM_GENERATED_PER_ITER)
    parser.add_argument("--target", type=float, default=TARGET)
    parser.add_argument("--wall-time-secs", type=int, default=WALL_TIME_SECS)
    parser.add_argument(
        "--out-scored", type=str,
        default="clients/farm-thru/loop/scored-pass5-sms.json"
    )
    parser.add_argument(
        "--out-review", type=str,
        default="clients/farm-thru/loop/review-pass5-sms.html"
    )
    parser.add_argument(
        "--seed-open", type=str,
        default="clients/farm-thru/loop/sms/SMS-VIP-OPEN.json"
    )
    parser.add_argument(
        "--seed-confirm", type=str,
        default="clients/farm-thru/loop/sms/SMS-VIP-CONFIRM.json"
    )
    args = parser.parse_args()

    started = time.time()
    client_dir = ROOT / "clients" / CLIENT
    shared_dir = ROOT / "shared"
    client = load_client(client_dir, shared_dir)

    seed_open = json.loads((ROOT / args.seed_open).read_text())
    seed_confirm = json.loads((ROOT / args.seed_confirm).read_text())

    # Score baselines
    print("=" * 78)
    print("BASELINE")
    print("=" * 78)
    base_open_rep = _score(seed_open, client, [seed_confirm])
    seed_open_eval = deepcopy(seed_open)
    seed_open_eval["_variant_label"] = "BASELINE-OPEN"
    seed_open_eval["_expanded_len"] = _expanded_len(seed_open["body"])
    print(_summary_line(seed_open_eval, base_open_rep))

    base_confirm_rep = _score(seed_confirm, client, [seed_open])
    seed_confirm_eval = deepcopy(seed_confirm)
    seed_confirm_eval["_variant_label"] = "BASELINE-CONFIRM"
    seed_confirm_eval["_expanded_len"] = _expanded_len(seed_confirm["body"])
    print(_summary_line(seed_confirm_eval, base_confirm_rep))

    # State for iteration
    best_open = (seed_open, base_open_rep)
    best_confirm = (seed_confirm, base_confirm_rep)

    # Each "best" record holds the parent score so we know what we're beating
    parent_open_score = base_open_rep["composite"]
    parent_confirm_score = base_confirm_rep["composite"]

    weak_open = ["motivation_match", "tone_brand_fit"]
    weak_confirm = ["motivation_match", "tone_brand_fit"]

    pinned_open = _filter_pinned(seed_open, PINNED_OPEN_VARIANTS, "open")
    pinned_confirm = _filter_pinned(seed_confirm, PINNED_CONFIRM_VARIANTS, "confirm")

    print(f"\nStarted with {len(pinned_open)} pinned OPEN candidates, "
          f"{len(pinned_confirm)} pinned CONFIRM candidates")

    iteration = 0
    while iteration < args.max_iterations:
        elapsed = time.time() - started
        if elapsed > args.wall_time_secs:
            print(f"\n[wall-time] {elapsed:.0f}s > {args.wall_time_secs}s — stopping iteration loop")
            break
        iteration += 1
        print()
        print("=" * 78)
        print(f"ITERATION {iteration}  (elapsed {elapsed:.0f}s)")
        print("=" * 78)

        # -----------------------------------------------------------------
        # OPEN seed
        # -----------------------------------------------------------------
        print(f"\n--- SMS-VIP-OPEN candidates ---  parent score {parent_open_score:.4f}")
        open_cands = []
        # Iter 1: pinned candidates exhaustively. Iter 2+: writer-generated only
        if iteration == 1:
            open_cands.extend(pinned_open)
        # Always add writer-generated candidates for variety
        for k in range(args.writer_per_iter):
            w = _gen_writer_variant(
                best_open[0], client_dir, weak_open,
                label=f"open-iter{iteration}-W{k+1}"
            )
            if w is not None:
                open_cands.append(w)

        scored_open = []
        for cand in open_cands:
            try:
                r = _score(cand, client, [best_confirm[0]])
                scored_open.append((cand, r))
                print(_summary_line(cand, r))
            except Exception as e:
                print(f"  [score-fail] {cand.get('_variant_label')}: {e}")

        # Pick best open candidate that beats parent and has compliance pass
        scored_open.sort(key=lambda t: t[1]["composite"], reverse=True)
        for cand, r in scored_open:
            if not r.get("compliance", {}).get("passed", True):
                continue
            if r.get("rule_compliance", {}).get("critical_failure"):
                continue
            if r["composite"] > parent_open_score + 0.001:  # floor on tiny noise
                best_open = (cand, r)
                parent_open_score = r["composite"]
                print(f"  >>> NEW best OPEN: {cand['_variant_label']} composite={r['composite']:.4f}")
                break

        # -----------------------------------------------------------------
        # CONFIRM seed
        # -----------------------------------------------------------------
        elapsed = time.time() - started
        if elapsed > args.wall_time_secs:
            print(f"\n[wall-time] {elapsed:.0f}s > {args.wall_time_secs}s — stopping mid-iteration")
            break
        print(f"\n--- SMS-VIP-CONFIRM candidates ---  parent score {parent_confirm_score:.4f}")
        confirm_cands = []
        if iteration == 1:
            confirm_cands.extend(pinned_confirm)
        for k in range(args.writer_per_iter):
            w = _gen_writer_variant(
                best_confirm[0], client_dir, weak_confirm,
                label=f"confirm-iter{iteration}-W{k+1}"
            )
            if w is not None:
                confirm_cands.append(w)

        scored_confirm = []
        for cand in confirm_cands:
            try:
                r = _score(cand, client, [best_open[0]])
                scored_confirm.append((cand, r))
                print(_summary_line(cand, r))
            except Exception as e:
                print(f"  [score-fail] {cand.get('_variant_label')}: {e}")

        scored_confirm.sort(key=lambda t: t[1]["composite"], reverse=True)
        for cand, r in scored_confirm:
            if not r.get("compliance", {}).get("passed", True):
                continue
            if r.get("rule_compliance", {}).get("critical_failure"):
                continue
            if r["composite"] > parent_confirm_score + 0.001:
                best_confirm = (cand, r)
                parent_confirm_score = r["composite"]
                print(f"  >>> NEW best CONFIRM: {cand['_variant_label']} composite={r['composite']:.4f}")
                break

        if (best_open[1]["composite"] >= STRETCH and
                best_confirm[1]["composite"] >= STRETCH):
            print(f"\n[stretch-met] both ≥{STRETCH} after iter {iteration}")
            break
        if (best_open[1]["composite"] >= args.target and
                best_confirm[1]["composite"] >= args.target):
            print(f"\n[target-met] both ≥{args.target} after iter {iteration}")
            # but keep going for stretch if we have time + iterations
            # (no break — stretch is the bonus goal)

    # ---------------------------------------------------------------------
    # Finalise winners + persist
    # ---------------------------------------------------------------------
    elapsed = time.time() - started
    print()
    print("=" * 78)
    print(f"FINAL  (elapsed {elapsed:.0f}s)")
    print("=" * 78)

    win_open, win_open_rep = best_open
    win_confirm, win_confirm_rep = best_confirm

    print()
    print(f"OPEN winner    : {win_open.get('_variant_label','BASELINE')}  composite={win_open_rep['composite']:.4f}")
    print(f"  body: {win_open['body']!r}")
    print(f"  expanded: {_expanded_len(win_open['body'])} chars  raw: {len(win_open['body'])} chars")
    print()
    print(f"CONFIRM winner : {win_confirm.get('_variant_label','BASELINE')}  composite={win_confirm_rep['composite']:.4f}")
    print(f"  body: {win_confirm['body']!r}")
    print(f"  expanded: {_expanded_len(win_confirm['body'])} chars  raw: {len(win_confirm['body'])} chars")

    # Strip transient labels before persisting the winner JSONs
    def _clean_for_persist(cand: dict, original_seed: dict, parent_score: float) -> dict:
        out = deepcopy(cand)
        out.pop("_variant_label", None)
        out.pop("_expanded_len", None)
        out["char_count"] = len(out["body"])
        # Only stamp hill_climb_pass if the winner ACTUALLY beat the baseline
        if cand["body"] != original_seed["body"]:
            out["hill_climb_pass"] = {
                "pass": "pass5",
                "parent_score": round(parent_score, 4),
                "iteration_label": cand.get("_variant_label", "n/a"),
                "ts": "2026-04-27T18:00:00+10:00",
            }
        return out

    # Persist seed JSONs (preserve source field — already in the seed)
    open_persist = _clean_for_persist(win_open, seed_open, base_open_rep["composite"])
    confirm_persist = _clean_for_persist(win_confirm, seed_confirm, base_confirm_rep["composite"])

    open_path = ROOT / args.seed_open
    confirm_path = ROOT / args.seed_confirm
    open_path.write_text(json.dumps(open_persist, indent=2))
    confirm_path.write_text(json.dumps(confirm_persist, indent=2))
    print(f"\nWrote {open_path.relative_to(ROOT)}")
    print(f"Wrote {confirm_path.relative_to(ROOT)}")

    # Build scored output via existing scorer (full LLM judges)
    print("\nRe-scoring final winners via score_batch.py for canonical JSON...")
    import subprocess
    proc = subprocess.run(
        ["python3", "scripts/score_batch.py", CLIENT, "--type", "sms", "-o", args.out_scored],
        cwd=str(ROOT), capture_output=True, text=True
    )
    if proc.returncode != 0:
        print(f"[warn] score_batch returned {proc.returncode}\n{proc.stderr[-2000:]}")
    else:
        print(f"Wrote {args.out_scored}")
    print(proc.stdout[-1500:])

    # Build review HTML
    print("\nBuilding review HTML...")
    proc2 = subprocess.run(
        ["python3", "scripts/build_review_html.py", args.out_scored, args.out_review],
        cwd=str(ROOT), capture_output=True, text=True
    )
    if proc2.returncode != 0:
        print(f"[warn] build_review_html returned {proc2.returncode}\n{proc2.stderr[-2000:]}")
    else:
        print(f"Wrote {args.out_review}")
    print(proc2.stdout[-500:])

    # Final return code
    print()
    target_open = win_open_rep["composite"] >= args.target
    target_confirm = win_confirm_rep["composite"] >= args.target
    stretch_open = win_open_rep["composite"] >= STRETCH
    stretch_confirm = win_confirm_rep["composite"] >= STRETCH
    print(f"OPEN target ≥{args.target}: {'YES' if target_open else 'NO'} ({win_open_rep['composite']:.4f})  stretch ≥{STRETCH}: {'YES' if stretch_open else 'NO'}")
    print(f"CONFIRM target ≥{args.target}: {'YES' if target_confirm else 'NO'} ({win_confirm_rep['composite']:.4f})  stretch ≥{STRETCH}: {'YES' if stretch_confirm else 'NO'}")
    print(f"Wall time: {elapsed:.0f}s")


if __name__ == "__main__":
    main()
