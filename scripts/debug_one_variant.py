#!/usr/bin/env python3
"""Generate ONE FMTH meta-ad variant and print why it scored 0.000."""
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
from writer import generate_variant

client_dir = ROOT / "clients" / "farm-thru"
shared_dir = ROOT / "shared"
client = load_client(client_dir, shared_dir)

# Load the seed ad — pick BR-101
seed = json.loads((client_dir / "loop" / "meta-ads" / "BR-101.json").read_text())
print("=== SEED ===")
print(json.dumps(seed, indent=2)[:600])
print()

# Generate one variant
variant = generate_variant(
    angle=seed.get("angle", "quality-craft"),
    tactic=seed.get("tactic", "sensory-detail"),
    hook_type=seed.get("hook_type", "question"),
    funnel=seed.get("funnel", "TOF"),
    client_dir=client_dir,
    current_best=seed,
    content_type="meta-ad",
    mode="improve",
)
print("=== VARIANT ===")
print(json.dumps(variant, indent=2)[:1200])
print()

# Score it
report = score_ad(variant, client, existing_ads=[seed], use_llm=False)
print("=== SCORE ===")
print(f"composite: {report['composite']}")
print(f"verdict: {report['verdict']}")
print()
print("rule_compliance failures:")
for f in report["rule_compliance"].get("failures", []):
    print(f"  - {f.get('rule_id')} [{f.get('severity')}]: {f.get('detail', '')[:150]}")
print()
print(f"critical_failure: {report['rule_compliance'].get('critical_failure')}")
print()
if "compliance" in report:
    print("compliance:")
    print(json.dumps(report["compliance"], indent=2)[:2500])
print()
print("overrides:", report.get("overrides"))
