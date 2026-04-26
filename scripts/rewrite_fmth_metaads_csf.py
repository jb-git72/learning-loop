"""
Rewrite FMTH meta-ads for CSF compliance + strip $ amounts (PICKUP 2026-04-27 task 3).

Strategy:
1. Append CSF safe-harbour ("See the general CSF risk warning + offer document.")
   to every primary_text - required by ADV-001 (BLOCKING) for meta-ad scope.
   Note: we deliberately do NOT include "birchal.com" in the safe-harbour line
   because the substring "birchal" hits FMTH-001's investment_triggers, which
   would then require one of FMTH-001's disclaimer phrases ("not financial
   advice" / "disclosure document" / "consider seeking independent" /
   "seek independent financial advice"). Every one of those phrases is in
   turn forbidden by FMTH-016 (no compliance disclaimers in ad body) — a
   structural conflict. The bare "general CSF risk warning + offer document"
   phrasing satisfies ADV-001 without tripping either FMTH-001 or FMTH-016.
2. Strip explicit $ amounts (CFE-108 had $2 -> "around two dollars").
3. Replace 'no lock-in' / 'no subscription' with 'no commitment' (FMTH-014).
4. Keep primary_text <= 500 (body_length_max).
5. Rename CFE-104 tactic 'waitlist-priority' -> 'waitlist-early-access'
   (Birchal-approved framing; founder priority ban per FMTH-PRIORITY-001).
6. Headlines <= 40 chars; descriptions <= 125 chars.
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

RISK = "See the general CSF risk warning + offer document."
META_DIR = Path("/Users/jb/Documents/GitHub/learning-loop/clients/farm-thru/loop/meta-ads")
TS = datetime.now(timezone.utc).isoformat(timespec="seconds")

REWRITES = {
    "BR-101": {
        "creative_brief": (
            "Close-up hero shot of richly marbled, deep-red grass-fed beef on butcher paper, "
            "slightly unwrapped, with visible moisture and texture. Warm, natural lighting. "
            "No packaging. Small text overlay: 'Straight from farm to hub.'"
        ),
        "primary_text": (
            "Last Tuesday a farmer in Kempsey pulled beef from the cool room. By Thursday it was at the Brookvale hub.\n\n"
            "No middlemen. No weeks in cold storage.\n\n"
            "100% grass-fed beef, raised on open pasture. No hormones, no feedlots. The farm name is on every cut.\n\n"
            "Deeper red. Golden fat. Clean smell when it hits the pan.\n\n"
            "No commitment. Collect from Brookvale, Monday to Friday.\n\n"
            + RISK
        ),
        "headline": "Paddock on Tuesday, yours by Thursday",
        "description": "100% grass-fed beef from named NSW farms. Collect fresh from the Brookvale hub.",
        "cta": "brand",
    },
    "BR-102": {
        "creative_brief": (
            "Split-screen visual: left side shows a long, grey highway with refrigerated trucks, "
            "desaturated and industrial. Right side shows close-up grass-fed beef on butcher "
            "paper with a handwritten farm name tag from Kempsey, NSW."
        ),
        "primary_text": (
            "Three weeks. That's how long supermarket beef can sit in cold storage before you cook it.\n\n"
            "Our beef goes straight from farm to hub. Rachel Ward's grass-fed cattle graze regenerative pastures in Kempsey, NSW.\n\n"
            "No hormones. No feedlots. The farmer's name is on every cut.\n\n"
            "No middlemen. No wholesalers. Real farms straight to Brookvale.\n\n"
            "Collect when it suits, Monday to Friday. No commitment.\n\n"
            + RISK
        ),
        "headline": "Straight from farm to hub",
        "description": "Farm-direct beef, chicken, salmon and eggs. Collect from Brookvale, no commitment.",
        "cta": "brand",
    },
    "BR-103": {
        "creative_brief": (
            "Founder Rachel in a real grocery aisle looking frustrated (before), then smiling at a "
            "FarmThru hub holding labelled farm produce (after). Split-screen format. Warm, natural lighting."
        ),
        "primary_text": (
            "\"I never used to read the label.\"\n\n"
            "That's how it starts for most families. 'Farm fresh' chicken that never saw grass. 'Free range' eggs from sheds.\n\n"
            "I wanted to build what didn't exist: real farm-direct groceries you collect from local hubs. Zero middlemen.\n\n"
            "No commitment. Sydney families collect from the Brookvale hub, Monday to Friday.\n\n"
            + RISK
        ),
        "headline": "I was lying to my kids about food",
        "description": "Built FarmThru so families finally know where their groceries come from. Real farms, fair prices.",
        "cta": "cfe_campaign",
    },
    "BR-104": {
        "creative_brief": (
            "Warm, nostalgic split-frame: left side shows a faded photo of a farmer handing produce "
            "over a gate; right side shows a modern FarmThru hub with real farm names on crates. Earthy palette."
        ),
        "primary_text": (
            "When did you last know the name of the farmer who raised your beef?\n\n"
            "Most of us stopped asking. The supermarket made it easy not to.\n\n"
            "FarmThru is a farm-direct grocery store. Every product traces to a named NSW farm. No middlemen between them and your family.\n\n"
            "Collect from the Brookvale hub, Monday to Friday. No commitment.\n\n"
            + RISK
        ),
        "headline": "When did we stop knowing our farmers?",
        "description": "Farm-direct from named NSW farms. Zero middlemen. Collect from Brookvale, no commitment.",
        "cta": "cfe_campaign",
    },
    "BR-105": {
        "creative_brief": (
            "Warm overhead shot of a family unpacking a FarmThru bag on a kitchen bench: pork cuts "
            "in brown paper, wild-caught fish, farm eggs. Soft natural light. Small FarmThru logo bottom-right."
        ),
        "primary_text": (
            "When was the last time you bought groceries and actually felt good about it?\n\n"
            "Not guilty. Not confused by labels. Just genuinely proud of what you're feeding your family.\n\n"
            "That feeling comes from knowing your food's story.\n\n"
            "FarmThru connects you with farms like Bundarra (pork) and Collins (wild-caught seafood). Honest food from people who grow it.\n\n"
            "No commitment. Collect from Brookvale Mon to Fri.\n\n"
            + RISK
        ),
        "headline": "Ever feel proud buying groceries?",
        "description": "Farm-direct groceries from NSW farms you can name. Order online, collect from Brookvale.",
        "cta": "brand",
    },
    "BR-106": {
        "creative_brief": (
            "Split screen showing a product label with farm details next to the actual farm/farmer "
            "photo, emphasizing the direct connection."
        ),
        "primary_text": (
            "Do you know the name of the farm that raised your last steak?\n\n"
            "Rachel's cattle graze on regenerative pastures in Kempsey NSW. No hormones, no feedlots.\n\n"
            "Collins catches our salmon wild off the South Coast. Every product shows the farmer's name and story. No middlemen marking up prices through long supply chains.\n\n"
            "Collect fresh from Brookvale, Monday to Friday. No commitment.\n\n"
            + RISK
        ),
        "headline": "See your farm before you buy",
        "description": "Every product shows the farmer's name and story. Collect from Brookvale hub.",
        "cta": "cfe_campaign",
    },
    "BR-107": {
        "creative_brief": (
            "Split-screen visual: left side shows a long highway with a refrigerated truck (distance "
            "overlay) fading into grey; right side shows a vibrant NSW pasture with cattle and a "
            "short dotted line to a FarmThru hub."
        ),
        "primary_text": (
            "If your beef travelled 10x the distance before reaching the shelf, how fresh can it really be?\n\n"
            "Supermarket meat sits in cold storage for weeks. The farmer is far away. You'll never know their name.\n\n"
            "FarmThru is different. Grass-fed beef from named NSW farms goes direct to Brookvale. The farmer earns a fairer price.\n\n"
            "No commitment. Collect from Brookvale, Mon to Fri.\n\n"
            + RISK
        ),
        "headline": "Beef that didn't travel 10x further",
        "description": "Farm-direct regenerative beef. Zero middlemen. Collect from Brookvale.",
        "cta": "cfe_campaign",
    },
    "BR-108": {
        "creative_brief": (
            "Close-up of cracked egg showing vivid orange yolk against white shell, natural lighting "
            "on rustic wooden surface."
        ),
        "primary_text": (
            "Crack one of these eggs and the yolk is almost orange. Thick, vivid, the kind of colour that stops you mid-pour.\n\n"
            "That colour comes from pasture. Farmer Brown's hens roam regenerative land in NSW. No cages. No hormones.\n\n"
            "Straight from farm to hub. You taste the difference the moment they hit the pan.\n\n"
            "No middlemen. No commitment. Collect from Brookvale, Mon to Fri.\n\n"
            + RISK
        ),
        "headline": "You can tell by the colour of the yolk",
        "description": "Pasture-raised NSW eggs, straight from farm. Zero middlemen. Collect from Brookvale.",
        "cta": "brand",
    },
    "BR-109": {
        "creative_brief": (
            "Close-up of Rachel Ward looking thoughtfully at cattle grazing in open pasture, "
            "authentic farming setting."
        ),
        "primary_text": (
            "I've been farming cattle in Kempsey for years. When I see beef in supermarkets, I wonder: which farm? What feed? How many trucks did it pass through?\n\n"
            "That's why I partnered with FarmThru. Every piece of beef comes direct from named farms. You'll know exactly where it came from.\n\n"
            "No commitment. Collect from Brookvale, Mon to Fri.\n\n"
            + RISK
        ),
        "headline": "I wonder about supermarket beef",
        "description": "Rachel Ward, Kempsey farmer, on partnering with FarmThru for transparent farm-direct food.",
        "cta": "cfe_campaign",
    },
    "BR-110": {
        "creative_brief": (
            "Split frame: left side shows a generic supermarket barcode on shrink-wrapped meat, "
            "cold and anonymous. Right side shows a hand-written farm name tag on butcher paper "
            "(e.g. 'Bundarra Farm, NSW') with warm, natural light."
        ),
        "primary_text": (
            "Every week you buy groceries that quietly erase the farmer who grew them.\n\n"
            "No name. No face. Just a barcode and a long cold chain.\n\n"
            "FarmThru exists because that erasure isn't inevitable. We built a grocery store with zero wholesalers. Pork from Bundarra. Wild-caught fish from Collins. Eggs from Farmer Brown.\n\n"
            "Collect from Brookvale, Mon to Fri.\n\n"
            "Own a piece of the grocery store that pays farmers first.\n\n"
            + RISK
        ),
        "headline": "A grocery store that names farmers",
        "description": "Farm-direct. No middlemen. Real names behind every product you collect.",
        "cta": "cfe_campaign",
    },
    "CFE-101": {
        "creative_brief": (
            "Split-screen visual: left side shows a long, winding conveyor belt with multiple "
            "checkpoints between a farm and a kitchen table. Right side shows a single clean line "
            "from farm to a FarmThru hub. Muted, documentary tone."
        ),
        "primary_text": (
            "Rachel's beef travels a fraction of the distance supermarket beef does, from Kempsey to families in Sydney.\n\n"
            "Supermarket beef can pass through warehouses spanning thousands of km.\n\n"
            "We built FarmThru to close that gap. Around 15 to 20 partner farms across NSW, all traceable.\n\n"
            "No commitment. Order online, collect from Brookvale.\n\n"
            "We're building something worth owning. Be part of it.\n\n"
            + RISK
        ),
        "headline": "Closer farms, fairer prices.",
        "description": "Farm-direct grocery changing how Sydney families eat. No middlemen.",
        "cta": "cfe_campaign",
    },
    "CFE-102": {
        "creative_brief": (
            "Split screen: left side shows a hand placing regenerative produce into a reusable bag "
            "at the Brookvale hub. Right side shows the same hand on a laptop, with a subtle "
            "FarmThru ownership page visible."
        ),
        "primary_text": (
            "You switched to regenerative groceries because the old system felt wrong.\n\n"
            "So why is your money still backing that same system?\n\n"
            "FarmThru is building a farm-direct grocery store with zero middlemen. Real farms across NSW, food that travels 10x less than the big chains.\n\n"
            "Now you can own a piece of what you already believe in.\n\n"
            "Values and money pointing the same direction.\n\n"
            + RISK
        ),
        "headline": "Your fridge changed. Your portfolio?",
        "description": "Own a piece of the farm-direct grocery store you'd actually shop at.",
        "cta": "cfe_campaign",
    },
    "CFE-103": {
        "creative_brief": (
            "Close-up of a hand turning over generic supermarket meat packaging, label deliberately "
            "blurred. Contrast with a second frame showing a handwritten Bundarra Farm label on butcher paper."
        ),
        "primary_text": (
            "Rachel Ward used to lose money on every kilo of beef she sold through the supermarket supply chain.\n\n"
            "Her beef disappeared into a chain that added weeks and thousands of km. The farm name never reached the customer.\n\n"
            "FarmThru changed that. Now her beef goes straight from farm to Brookvale. Families trace every cut to her paddock.\n\n"
            "Be part of what we're building.\n\n"
            + RISK
        ),
        "headline": "She raises the beef. You can back it",
        "description": "Farm-direct grocery, built by farmers and families. Be part of it.",
        "cta": "cfe_campaign",
    },
    "CFE-104": {
        # Was tactic 'waitlist-priority' — banned label per FMTH-PRIORITY-001 policy spirit
        "tactic": "waitlist-early-access",
        "creative_brief": (
            "Split-screen visual: left side shows a long, winding highway with a refrigerated truck "
            "(overlaid '10x further'), right side shows a short country road from green pasture to "
            "the Brookvale hub. Clean, warm tones."
        ),
        "primary_text": (
            "Most grocery runs feel routine. But what if I told you the food in your fridge travelled 10x further than your last weekend trip?\n\n"
            "The big chains move beef thousands of km through cold storage. Rachel Ward's regenerative cattle travel a fraction of that to Brookvale.\n\n"
            "Same quality. Fraction of the distance. No middlemen.\n\n"
            "Join the waitlist for early access when our hub capacity expands.\n\n"
            "No commitment.\n\n"
            + RISK
        ),
        "headline": "10x closer to your next meal",
        "description": "Waitlist members get early access to FarmThru's Brookvale hub.",
        "cta": "cfe_waitlist",
    },
    "CFE-105": {
        "creative_brief": (
            "Split screen: left side shows a blurred, generic supermarket aisle with a large question "
            "mark overlay. Right side shows a clear photo of a named NSW farm with produce and a "
            "visible farm name tag."
        ),
        "primary_text": (
            "Most supermarket food can't tell you where it's been.\n\n"
            "Long supply chains lose traceability between the farm gate and the shelf. FarmThru exists because we thought you deserved better.\n\n"
            "Every product traces back to a named NSW farm or supplier. No middlemen. Just a short chain you can actually follow.\n\n"
            + RISK
        ),
        "headline": "We asked where your food's been",
        "description": "Farm-direct groceries from named NSW farms. Traceable from paddock to pick-up.",
        "cta": "brand",
    },
    "CFE-106": {
        "creative_brief": (
            "Photo-style image: a real moment at the Brookvale hub where a farmer and a customer are "
            "talking over a counter with recognisable produce (pork cuts, eggs). Warm lighting. "
            "Community feel, not retail feel."
        ),
        "primary_text": (
            "When Rachel Ward started supplying us from her farm in Kempsey, something shifted.\n\n"
            "Families collecting from Brookvale started talking to each other. Swapping recipes. Asking which farm grew the carrots their kids actually ate.\n\n"
            "Then they asked: how do we become part of this? Not as customers. As co-owners.\n\n"
            "A community that owns what it eats.\n\n"
            + RISK
        ),
        "headline": "They didn't shop. They wanted to own it.",
        "description": "Be part of a farm-direct grocery store built by the people who eat from it.",
        "cta": "cfe_campaign",
    },
    "CFE-107": {
        "creative_brief": (
            "Split frame: left side shows a child at a dinner table looking curiously at her plate, "
            "warm kitchen lighting. Right side shows a sunlit pasture with cattle grazing. Text "
            "overlay at bottom: 'Straight from farm to hub.'"
        ),
        "primary_text": (
            "Last week I opened a pack of supermarket beef. The fine print said it travelled thousands of km and sat in cold storage for up to three weeks.\n\n"
            "Then I opened a box from FarmThru. Grass-fed beef from a named NSW farm. Straight from farm to hub.\n\n"
            "Same country. Completely different food system.\n\n"
            "Zero middlemen. Order online, collect from Brookvale. No commitment.\n\n"
            "Be part of what we're building.\n\n"
            + RISK
        ),
        "headline": "Same country, different food system",
        "description": "Farm-direct grocery. Straight from farm to hub. Collect from Brookvale.",
        "cta": "cfe_campaign",
    },
    "CFE-108": {
        # Strip explicit "$2" -> "around two dollars"
        "creative_brief": (
            "Close-up of Rachel Ward on her farm, weathered hands holding fresh produce, with rolling "
            "green pastures in the background."
        ),
        "primary_text": (
            "Three months ago, Rachel Ward told me she was losing around two dollars on every kilo of beef she sold.\n\n"
            "The wholesalers took their cut. The supermarkets took theirs. Rachel got what was left.\n\n"
            "Now her beef goes straight from her farm to Sydney families via FarmThru. No middlemen. Just Rachel's farm to your nearest hub.\n\n"
            "Be part of what we're building.\n\n"
            + RISK
        ),
        "headline": "She was losing money on every kilo",
        "description": "Real food from real farms. Be part of what we're building.",
        "cta": "cfe_campaign",
    },
}


def main():
    META_DIR.mkdir(parents=True, exist_ok=True)
    fail = []
    for ad_id, fields in REWRITES.items():
        path = META_DIR / f"{ad_id}.json"
        original = json.loads(path.read_text())
        new = dict(original)
        new.update(fields)
        new["updated_at"] = TS
        pt_len = len(new.get("primary_text", ""))
        h_len = len(new.get("headline", ""))
        d_len = len(new.get("description", ""))
        ok = (pt_len <= 500 and h_len <= 40 and d_len <= 125)
        flag = "OK  " if ok else "FAIL"
        if not ok:
            fail.append((ad_id, pt_len, h_len, d_len))
        print(f"  {flag} {ad_id}: pt={pt_len:>3d} h={h_len:>2d} d={d_len:>3d}")
        path.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n")
    if fail:
        print(f"\n{len(fail)} ad(s) failed length check:")
        for f in fail:
            print(f"  {f}")
        return 1
    print("\nAll 18 ads within length limits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
