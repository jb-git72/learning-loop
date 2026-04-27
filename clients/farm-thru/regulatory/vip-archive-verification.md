# FMTH VIP-archive verification

**Date**: 2026-04-27
**Agent**: VIP-archive verifier (worktree)
**Scope**: Verify the 4 PRs that shipped the VIP archive (learning-loop #110, #111, #112; sales-skill #226), validate every claim in `clients/farm-thru/VIP-ARCHIVE-MANIFEST.md`, re-run production smoke tests, fix the documented gaps where safe.

## Verdict

**PASS-WITH-REVISIONS** — the structural archive is sound. One critical leak (the `index.html` variant=a default) and 8 in-prose VIP mentions on other LP variants were addressed by sales-skill PR #227. Everything else verified clean.

---

## Phase 1 — Manifest validation

### 1.1 Files moved to archive

| Manifest claim | Verified |
|---|---|
| 4 EM-VIP*.json moved to `loop/emails/_archived/vip-pre-birchal-v2/` | OK — all 4 files exist in archive, none at original path |
| 2 SMS-VIP*.json moved to `loop/sms/_archived/vip-pre-birchal-v2/` | OK — both files exist in archive, none at original path |
| 12 CSF-VIP-*.md moved to `clients/farm-thru/_archived/vip-pre-birchal-v2/` | OK — all 12 in archive, none at original path |

All `git mv` history preserved (filenames identical, parent dir changed only).

### 1.2 Comment-marker sections (LP variants + thank-you template)

Manifest §3.1 claims 16 LPs (b through q minus o) plus the thank-you template = 17 total. Actual: **15 LP variants + 1 thank-you template = 16 marker pairs** (manifest table says 16 LPs, but the underlying PR description and the `archive_fmth_vip_card.py` script both correctly state 15 LP variants).

| File | BEGIN+END markers present | Single-comment wrap | Markup leaks outside comment |
|---|---|---|---|
| `web/campaigns/FMTH/index-b.html` | OK | OK | none |
| `web/campaigns/FMTH/index-c.html` | OK | OK | none |
| `web/campaigns/FMTH/index-d.html` | OK | OK | none |
| `web/campaigns/FMTH/index-e.html` | OK | OK | none |
| `web/campaigns/FMTH/index-f.html` | OK | OK | none |
| `web/campaigns/FMTH/index-g.html` | OK | OK | none |
| `web/campaigns/FMTH/index-h.html` | OK | OK | none |
| `web/campaigns/FMTH/index-i.html` | OK | OK | none |
| `web/campaigns/FMTH/index-j.html` | OK | OK | none |
| `web/campaigns/FMTH/index-k.html` | OK | OK | none |
| `web/campaigns/FMTH/index-l.html` | OK | OK | none |
| `web/campaigns/FMTH/index-m.html` | OK | OK | none |
| `web/campaigns/FMTH/index-n.html` | OK | OK | none |
| `web/campaigns/FMTH/index-o.html` | n/a (correctly excluded — no VIP block) | n/a | n/a |
| `web/campaigns/FMTH/index-p.html` | OK | OK | none |
| `web/campaigns/FMTH/index-q.html` | OK | OK | none |
| `web/templates/campaign_thankyou.html` | OK | OK | INTENTIONAL — `{% else %}` confirmed-VIP branch (lines 79-86) is `vip__card`-classed but per manifest §1+§3.2 left in place for existing in-flight VIP customers refreshing the page |

### 1.3 app.py flag and gate

| Manifest claim | Verified |
|---|---|
| `FMTH_VIP_ENABLED = False` at line 55 | NEAR-MATCH — actually at line 56 (manifest off-by-one). Flag value = False, semantic identical |
| `_vip_disabled_response()` helper exists | OK — defined at line 683 |
| Helper returns HTTP 503 + `{"error": "vip_currently_disabled", "message": "..."}` | OK — exact match |
| `campaign_vip_checkout` gates on flag first | OK — line 716 `if not FMTH_VIP_ENABLED: return _vip_disabled_response()` is the first line of the route body after docstring |
| `stripe_webhook` (line 1424) UNCHANGED | OK — `_handle_vip_deposit` dispatch on line 1442 still present and not in PR #226 diff |
| `_handle_vip_deposit` (line 788) UNCHANGED | OK — not in PR #226 diff |
| Refund flow (Stripe Dashboard, no `charge.refunded` handler in app.py) | OK — manifest §4.4 accurately documents that webhook only handles `checkout.session.completed`; refunds flow via Dashboard |

### 1.4 Restoration commands (dry-run)

| Manifest section | Restoration command verified |
|---|---|
| §2.1 `git mv` for 4 email seeds | OK — source paths exist, target paths free |
| §2.2 `git mv` for 2 SMS seeds | OK — source paths exist, target paths free |
| §2.3 `git mv` loop for 12 CSF docs | OK — all 12 in archive, target paths free |
| §3.3 Python regex restoration script | OK — re-ran the manifest regex against 16 wrapped files in-process; would correctly restore 16/16 (200 chars stripped per file) |
| §4.5 sed flip `FMTH_VIP_ENABLED` | OK — exactly 1 match for `FMTH_VIP_ENABLED = False` in app.py; sed would round-trip |

---

## Phase 2 — Production smoke tests

All hits against `https://join.farmthru.com.au` from the verification agent at 2026-04-27.

### 2.1 LP variant HTTP status (a-q)

All 17 variants returned **HTTP 200**. No 500s, no template errors.

### 2.2 Markers + visible VIP markup per variant (HTMLParser scan)

| Variant | Marker count (BEGIN+END) | Live `vip`-classed tags | Status |
|---|---|---|---|
| a (default `index.html`) | **0** | **12** | **CRITICAL — leak; fixed in sales-skill PR #227** |
| b | 2 | 0 | OK |
| c | 2 | 0 | OK |
| d | 2 | 0 | OK |
| e | 2 | 0 | OK |
| f | 2 | 0 | OK |
| g | 2 | 0 | OK |
| h | 2 | 0 | OK |
| i | 2 | 0 | OK |
| j | 2 | 0 | OK |
| k | 2 | 0 | OK |
| l | 2 | 0 | OK |
| m | 2 | 0 | OK |
| n | 2 | 0 | OK |
| o | 0 | 0 | OK (correctly excluded) |
| p | 2 | 0 | OK |
| q | 2 | 0 | OK |

### 2.3 Thank-you template

```
GET https://join.farmthru.com.au/campaigns/fmth-ecb582/thank-you
HTTP 200, marker_count=2, visible_vip_tags=0
```

OK — pre-archive deposit-prompt branch is wrapped; visit without `?vip=success` shows zero VIP markup.

### 2.4 VIP checkout endpoint

```
POST https://join.farmthru.com.au/campaigns/fmth-ecb582/vip-checkout
  -F email=test@example.com
HTTP 503
{"error":"vip_currently_disabled","message":"VIP access is temporarily unavailable while we update the offer. Please join the free waitlist and we will email you when access reopens."}
```

OK — exact match to manifest §4.2.

### 2.5 Free waitlist signup (live test against prod)

```
POST https://join.farmthru.com.au/campaigns/fmth-ecb582/signup
  -F email=vip-archive-verify-test+1761650400@example.com
  -F variant=b
HTTP 200
{"event_id":"74d6c08c-2c70-49f1-b140-10dcc0b11ff2","ok":true,"position":152,"ref_code":"a5f4e343","total":152}
```

OK — signup queue alive, position assigned, no regression.

### 2.6 Stripe webhook

```
POST https://join.farmthru.com.au/stripe/webhook
  -H 'Stripe-Signature: t=1,v1=invalid'
HTTP 400 (Bad Request)
```

OK — route alive, signature verification working, dispatching to handler.

### 2.7 Refund flow (non-regression)

No separate refund endpoint exists; refunds are issued via the Stripe Dashboard. Webhook handler currently only dispatches `checkout.session.completed`. PR #226 did NOT modify `stripe_webhook` or `_handle_vip_deposit`; both remain live for in-flight VIP customers. Existing customer refund flow is unchanged.

---

## Phase 3 — Documented gaps

### Gap 1 — In-prose VIP mentions on LPs

**Status**: ADDRESSED in sales-skill PR #227 (squash-merged to main).

#### New gap discovered: `index.html` (variant=a default) was missed entirely

The original archive PR #226 did not touch `web/campaigns/FMTH/index.html`. This file is the default served to variant=a (per `_load_campaign(slug, variant="a")` in `app.py` line 374-385: if variant is "a" or missing, fall back to `index.html`). Cookie-less and parameter-less visitors get random variant assignment from `VALID_VARIANTS = {a..q}` so roughly 1/17 visitors landed on the leaking page.

The leak was 12 live `vip`-classed tags (the full `<section class="vip">` card) plus 2 prose mentions:
- L107: "A small refundable deposit secures your spot on the VIP list."
- L115-116: "What does the VIP deposit do?" / "It's a small, fully refundable deposit..."

PR #227 wraps the VIP card in the same one-big-comment marker block and rewrites both prose mentions. Post-fix HTMLParser scan confirms 0 visible `vip`-classed tags and the manifest restoration regex round-trips cleanly.

#### Other LP in-prose mentions fixed

| File | Before (excerpt) | After (excerpt) |
|---|---|---|
| `index-b.html` L112 | "Place a small refundable deposit to join our VIP waitlist..." | "Join the FarmThru investor waitlist. We'll email you the moment our CSF offer opens at Birchal..." |
| `index-d.html` L97 | "Join the waitlist with a small refundable deposit..." | "Join the waitlist to be first in line when the campaign opens at Birchal. Free to join. Over 2,500 people have already signed up." |
| `index-e.html` L101 | "Want early access to invest? Place a $5 refundable deposit to secure VIP status..." | "Join the FarmThru investor waitlist for first notification when our CSF offer opens at Birchal..." |
| `index-f.html` L103 | "...Place a $5 refundable deposit to secure VIP status — VIP investors get..." | "Join the waitlist to hear when our CSF offer opens at Birchal, plus early investor updates from the founders. Free to join. No commitment." |
| `index-m.html` L80 | "327 people have already joined the VIP waitlist. Spots close before we launch." | "327 people have already joined the FarmThru investor waitlist." |
| `index-m.html` L100-103 | "Place a $5 refundable deposit to secure VIP status..." (3 paras) | "Join the FarmThru investor waitlist for first notification..." (3 paras, no deposit/VIP framing) |
| `index-n.html` L98, L101 | "Place a $5 refundable deposit..." + "The VIP waitlist exists so we can open strong. Your small refundable deposit signals intent..." | "Join the FarmThru investor waitlist..." + "The waitlist exists so we can open strong. It tells us who's planning to be there on day one." |
| `index-p.html` L105, L110 | "Place a $5 refundable deposit to secure VIP status..." + "The VIP deposit is fully refundable if you change your mind." | "Join the waitlist to hear when our CSF offer opens..." + "Joining the waitlist is free. You can leave any time." |

All rewrites use established Rachel voice patterns from already-fixed LPs (no new claims, no new stats, no investor-specific promises about access timing).

### Gap 2 — JS handler `vipDepositBtn` in `campaign_thankyou.html`

**Deferred to post-variant-build cleanup**. The variant-build agent (`fmth-thankyou-fb-variant-ship`) is currently editing this template; per coordination instructions in the brief, this verification agent did not touch the file. Recommend a future PR removes the JS event listener (the button it binds to is inside the now-commented-out `{% if not is_vip %}` branch, so the listener finds no element — harmless but dead code) once the variant-build agent has merged. The `?vip=success` URL parameter handling at the end of the JS is intentional and should stay (Stripe redirects from in-flight pre-archive deposits still need it).

### Gap 3 — `drip_vip_welcome` send inside `_handle_vip_deposit`

**Confirmed intentional, no action**. The drip-engine `is_vip` fork in `campaign_drip.py` and the `drip_vip_welcome` template send for in-flight Stripe deposits whose webhook arrives post-archival are both correctly preserved. Existing VIP subscribers continue receiving their scheduled drip schedule. Per manifest §1, §4.4, and §6 gap 5 — accurate and stable.

---

## New gaps discovered

### NEW GAP A — `index.html` (variant=a default) was completely missed by the original archive

See Gap 1 section above. **Fixed in sales-skill PR #227.** Recommend the original agent's `archive_fmth_vip_card.py` script be updated to ALSO scan `index.html` (the variant=a default) — it currently only scans `index-?.html` per the regex `rglob("index-?.html")` which excludes the bare `index.html`. This is a script bug; if the script ever re-runs (e.g. on another client) it would have the same blind spot.

### NEW GAP B — Manifest §3.1 table count off by one

Manifest table says "16 LP variants" but the underlying PR description (#226) and `archive_fmth_vip_card.py` script both correctly say 15. The 16 marker-pair files in the repo are 15 LP variants (b through q minus o) plus 1 thank-you template. Cosmetic only — recommend aligning the manifest text on a future revision.

### NEW GAP C — Manifest §4.1 line number off by one

Manifest says `FMTH_VIP_ENABLED = False` is at line 55 of `app.py`; actual is line 56 (the leading multi-line comment block ends at line 55, the constant starts at 56). Cosmetic only.

---

## Lawyer-relevant items

None. The structural archive holds: no new VIP checkouts can be created (HTTP 503), no new VIP customers can join the drip flow, every LP variant including the previously-missed variant=a now hides the VIP card. Existing VIP customers' webhook + drip + refund flows are intentionally preserved per manifest §1 + §4.4. All in-prose VIP mentions on rendered LP HTML are now removed.

The Birchal s738ZE financial-assistance / fund-custody / investor-risk concerns were the trigger; the v1 customer-facing VIP marketing surface is now fully off the published LPs.

---

## Files referenced

### sales-skill
- `web/app.py` — `FMTH_VIP_ENABLED` flag, `_vip_disabled_response` helper, `campaign_vip_checkout` gate, `stripe_webhook`, `_handle_vip_deposit`
- `web/campaigns/FMTH/index.html` (NEW: VIP card wrapped + 2 prose rewrites in PR #227)
- `web/campaigns/FMTH/index-{b..q}.html` — 16 LP variants total, 15 with marker pairs (o intentionally excluded). 7 of these (b, d, e, f, m, n, p) had in-prose mentions fixed by PR #227
- `web/templates/campaign_thankyou.html` — deposit-prompt branch wrapped; confirmed-VIP `{% else %}` branch intentionally preserved
- `scripts/archive_fmth_vip_card.py` — archival script; gap-flag (NEW GAP A) recommends adding `index.html` to its scan list

### learning-loop
- `clients/farm-thru/VIP-ARCHIVE-MANIFEST.md` — primary manifest
- `clients/farm-thru/_archived/vip-pre-birchal-v2/` — 12 CSF-VIP docs
- `clients/farm-thru/loop/emails/_archived/vip-pre-birchal-v2/` — 4 EM-VIP seeds
- `clients/farm-thru/loop/sms/_archived/vip-pre-birchal-v2/` — 2 SMS-VIP seeds
- `clients/farm-thru/regulatory/vip-archive-verification.md` — this document

## PRs merged during verification

- **sales-skill PR #227** (squash-merged into main) — `fix(fmth): remove in-prose VIP mentions on landing pages (post-archive cleanup)`. 8 files, 20+/15-.

## Recommended follow-ups (not blocking)

1. Update `scripts/archive_fmth_vip_card.py` to scan `index.html` in addition to `index-?.html`
2. Cosmetic: align manifest §3.1 LP count (16 -> 15) and §4.1 line number (55 -> 56)
3. Once `fmth-thankyou-fb-variant-ship` merges, sweep `campaign_thankyou.html` for the dead `vipDepositBtn` event listener
