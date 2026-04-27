"""Audit is_test field state. The Phase 1 result showed 119 docs with is_test=None,
but the renumber audit doc said only 2. Investigate."""
from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

PROJECT = "launcher-lab-proposals"
SLUG = "fmth-ecb582"

from google.cloud import firestore  # type: ignore

db = firestore.Client(project=PROJECT)
coll = db.collection("campaigns").document(SLUG).collection("signups")
docs = list(coll.stream())
parsed = [{"_doc_id": d.id, **(d.to_dict() or {})} for d in docs]

# Bucket by is_test value AND by has_field
buckets = {"True": [], "False": [], "None_explicit": [], "absent": []}
for r in parsed:
    if "is_test" not in r:
        buckets["absent"].append(r)
    elif r["is_test"] is True:
        buckets["True"].append(r)
    elif r["is_test"] is False:
        buckets["False"].append(r)
    elif r["is_test"] is None:
        buckets["None_explicit"].append(r)

print(f"Total docs: {len(parsed)}")
for k, v in buckets.items():
    print(f"  is_test = {k:15s}  count = {len(v)}")

# Show emails for non-True buckets to understand which got is_test=False vs absent
print(f"\nis_test=True docs ({len(buckets['True'])}):")
for r in buckets["True"][:20]:
    print(f"  {r.get('email','?'):40s}  pos={r.get('position'):>3}  signed={(r.get('signed_up_at') or '')[:25]}")

print(f"\nis_test=False docs ({len(buckets['False'])}):")
for r in buckets["False"][:20]:
    print(f"  {r.get('email','?'):40s}  pos={r.get('position'):>3}  signed={(r.get('signed_up_at') or '')[:25]}")

print(f"\nis_test=None_explicit docs ({len(buckets['None_explicit'])}):")
for r in buckets["None_explicit"][:5]:
    print(f"  {r.get('email','?'):40s}  pos={r.get('position'):>3}  signed={(r.get('signed_up_at') or '')[:25]}")

print(f"\nis_test absent (no field at all) docs ({len(buckets['absent'])}):")
for r in buckets["absent"][:5]:
    print(f"  {r.get('email','?'):40s}  pos={r.get('position'):>3}  signed={(r.get('signed_up_at') or '')[:25]}")

# Verify the public-query semantics: get_signups uses `is_test != True`
# Check: how many would the LP public-count query return?
public_by_neq_true = [r for r in parsed if r.get("is_test") is not True]
print(f"\nPublic count via 'is_test is not True' (Python semantics): {len(public_by_neq_true)}")
