#!/usr/bin/env python3
"""Score the seed live ad + top 3 variants into scored-live-variants.json
for the feedback HTML review tool."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from engine.scorer import load_client, score_ad

seed = json.loads((ROOT / "clients/farm-thru/loop/live-ad-test.json").read_text())
seed["ad_id"] = "SEED-LIVE-NEVER-DONE"
ads = [seed]
vd = ROOT / "clients/farm-thru/loop/live-ad-variants"
for i in [1, 2, 3]:
    p = vd / f"LIVE-VARIANT-{i:02d}.json"
    if p.is_file():
        ads.append(json.loads(p.read_text()))

client = load_client(ROOT / "clients/farm-thru", ROOT / "shared")
results = []
for ad in ads:
    r = score_ad(ad, client, existing_ads=ads, use_llm=True)
    r["_file"] = ad.get("ad_id", "unknown")
    r["ad_id"] = ad.get("ad_id", "unknown")
    r["content_type"] = "meta-ad"
    r["angle"] = ad.get("angle", "")
    r["headline"] = ad.get("headline", "")
    r["primary_text"] = ad.get("primary_text", "")
    r["description"] = ad.get("description", "")
    r["cta"] = ad.get("cta", "")
    r["campaign_phase"] = ad.get("campaign_phase", "pre-campaign")
    results.append(r)
    print(f"{ad['ad_id']:30s} {r['composite']:.4f} {r['verdict']}")

out = {
    "summary": {"count": len(results), "avg_composite": sum(r["composite"] for r in results) / len(results)},
    "results": results,
}
out_path = ROOT / "clients/farm-thru/loop/scored-live-variants.json"
out_path.write_text(json.dumps(out, indent=2) + "\n")
print(f"\nwrote {out_path}")
