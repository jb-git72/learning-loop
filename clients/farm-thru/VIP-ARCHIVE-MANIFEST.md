# FarmThru VIP scheme — archive manifest

**Date archived**: 2026-04-27
**Trigger**: Birchal pushed back on the FMTH $5 VIP deposit scheme on 2026-04-27 (concerns under s738ZE financial-assistance, where investor funds are held, investor risk).
**Companion doc**: `clients/farm-thru/BIRCHAL-PROPOSAL-V2.md` (decoupled $10 product credit + free CSF waitlist).
**Status**: VIP scheme is OFFLINE on every customer-facing surface, but every artefact is RECOVERABLE via the steps below.

If Birchal subsequently approves the original v1 VIP scheme (instead of the v2 proposal), restore via the per-section instructions in this doc. Restoration is intended to be a single PR.

---

## 1. Scope & method summary

| Surface | Method | Reversible? |
|---|---|---|
| 17 LP variants (`sales-skill/web/campaigns/FMTH/index-{b..q}.html`) | VIP card commented out with grep-able marker | Yes — uncomment block |
| Thank-you template (`sales-skill/web/templates/campaign_thankyou.html`) | VIP card commented out with grep-able marker | Yes — uncomment block |
| Email VIP seeds (4 files, `learning-loop/clients/farm-thru/loop/emails/EM-VIP-*.json` + `EM-WELCOME-VIP.json`) | Moved to `_archived/vip-pre-birchal-v2/` | Yes — `git mv` back |
| SMS VIP seeds (2 files, `learning-loop/clients/farm-thru/loop/sms/SMS-VIP-*.json`) | Moved to `_archived/vip-pre-birchal-v2/` | Yes — `git mv` back |
| 12 CSF-VIP wave-5b docs (`learning-loop/clients/farm-thru/CSF-VIP-*.md`) | Moved to `_archived/vip-pre-birchal-v2/` | Yes — `git mv` back |
| `app.py` VIP Stripe checkout route | Top-of-file flag `FMTH_VIP_ENABLED = False` + `if not FMTH_VIP_ENABLED: return _vip_disabled_response()` gate inside `campaign_vip_checkout` | Yes — flip flag to `True` |

### What was NOT touched (intentional)

- `BIRCHAL-PROPOSAL-V2.md` — that's the v2 proposal, not the v1 scheme.
- `clients/farm-thru/regulatory/birchal-vip-restructure-proposals.md` and `birchal-vip-concerns-regulatory-analysis.md` — these document the regulatory analysis backing the v2 proposal (dated 2026-04-27); they are evidence supporting the archival, not v1 content.
- The free CSF waitlist signup form on every LP — that stays functional, that's the v2 path.
- The Stripe webhook handler at `/stripe/webhook` — must keep processing events for any in-flight deposits + refunds. Only the **checkout creation** route is gated; once a session was already created pre-archive and the event arrives, the existing handler fires normally.
- `_handle_vip_deposit()` in `app.py` — must keep processing existing deposits' webhooks (e.g. delayed `checkout.session.completed`).
- The VIP drip-engine fork in `campaign_drip.py` (`if is_vip:` on line ~292) — see "Open question resolved" below.
- The compliance gate (`compliance.enabled: true` in `clients/farm-thru/config.json`) — stays on.
- Production drip templates `drip_vip_*.html` in `sales-skill/web/campaigns/FMTH/emails/` — these serve existing VIP subscribers' drip schedule. They stay in place. No new subscribers can enter the VIP drip flow because `campaign_vip_checkout` is gated; existing subscribers still receive their scheduled emails.
- The thank-you template's VIP-success branch (`{% else %}` block when `is_vip == True`) — left in place because existing VIP customers can still land on the thank-you page after a refresh and we want them to see the confirmed-VIP state, not the deposit prompt. Only the deposit-prompt branch (`{% if not is_vip %}`) is the marketing surface that needs hiding.

### Open question resolved

**Q**: Should the drip-engine VIP segment (a) be removed/short-circuited, or (b) remain in place but receive no NEW recipients?

**Decision**: (b). The drip-engine `is_vip` fork in `campaign_drip.py` line 292 is left UNTOUCHED. Reasoning:
- Existing VIP subscribers (who paid pre-archive) must continue receiving their scheduled drip emails — that's a customer commitment.
- With `campaign_vip_checkout` gated, no new signups can ever flip `vip=True`, so the segment naturally winds down to its pre-archive cohort.
- Touching the drip fork risks regressing live in-flight VIP subscribers' email schedule.

**Implication for the verification agent**: `process_drip_emails` will still send `drip_vip_welcome` / `drip_vip_1/2/3` to existing VIP subscribers. This is intentional, not a regression.

---

## 2. Files moved (archive subdirs)

All moves preserve original filename; the archive path is the original parent + `_archived/vip-pre-birchal-v2/`. Restoration is `git mv` in reverse.

### 2.1 Email VIP seeds (4 files)

| Old path | New path |
|---|---|
| `clients/farm-thru/loop/emails/EM-VIP-01.json` | `clients/farm-thru/loop/emails/_archived/vip-pre-birchal-v2/EM-VIP-01.json` |
| `clients/farm-thru/loop/emails/EM-VIP-02.json` | `clients/farm-thru/loop/emails/_archived/vip-pre-birchal-v2/EM-VIP-02.json` |
| `clients/farm-thru/loop/emails/EM-VIP-03.json` | `clients/farm-thru/loop/emails/_archived/vip-pre-birchal-v2/EM-VIP-03.json` |
| `clients/farm-thru/loop/emails/EM-WELCOME-VIP.json` | `clients/farm-thru/loop/emails/_archived/vip-pre-birchal-v2/EM-WELCOME-VIP.json` |

**Restore**:
```bash
cd /Users/jb/Documents/GitHub/learning-loop
git mv clients/farm-thru/loop/emails/_archived/vip-pre-birchal-v2/EM-VIP-01.json clients/farm-thru/loop/emails/EM-VIP-01.json
git mv clients/farm-thru/loop/emails/_archived/vip-pre-birchal-v2/EM-VIP-02.json clients/farm-thru/loop/emails/EM-VIP-02.json
git mv clients/farm-thru/loop/emails/_archived/vip-pre-birchal-v2/EM-VIP-03.json clients/farm-thru/loop/emails/EM-VIP-03.json
git mv clients/farm-thru/loop/emails/_archived/vip-pre-birchal-v2/EM-WELCOME-VIP.json clients/farm-thru/loop/emails/EM-WELCOME-VIP.json
```

### 2.2 SMS VIP seeds (2 files)

| Old path | New path |
|---|---|
| `clients/farm-thru/loop/sms/SMS-VIP-OPEN.json` | `clients/farm-thru/loop/sms/_archived/vip-pre-birchal-v2/SMS-VIP-OPEN.json` |
| `clients/farm-thru/loop/sms/SMS-VIP-CONFIRM.json` | `clients/farm-thru/loop/sms/_archived/vip-pre-birchal-v2/SMS-VIP-CONFIRM.json` |

**Restore**:
```bash
cd /Users/jb/Documents/GitHub/learning-loop
git mv clients/farm-thru/loop/sms/_archived/vip-pre-birchal-v2/SMS-VIP-OPEN.json clients/farm-thru/loop/sms/SMS-VIP-OPEN.json
git mv clients/farm-thru/loop/sms/_archived/vip-pre-birchal-v2/SMS-VIP-CONFIRM.json clients/farm-thru/loop/sms/SMS-VIP-CONFIRM.json
```

### 2.3 CSF VIP wave-5b docs (12 files)

All `clients/farm-thru/CSF-VIP-*.md` files were moved to `clients/farm-thru/_archived/vip-pre-birchal-v2/`. The flagship `CSF-VIP-COPY-PACKAGE.md` has an inline ARCHIVED header prepended; the rest are listed in `_archived/vip-pre-birchal-v2/README.md` with the same archival context.

| Old name (in `clients/farm-thru/`) | Archived to |
|---|---|
| `CSF-VIP-BIRCHAL-SUBMISSION.md` | `_archived/vip-pre-birchal-v2/CSF-VIP-BIRCHAL-SUBMISSION.md` |
| `CSF-VIP-BRAINSTORM.md` | `_archived/vip-pre-birchal-v2/CSF-VIP-BRAINSTORM.md` |
| `CSF-VIP-COPY-PACKAGE.md` | `_archived/vip-pre-birchal-v2/CSF-VIP-COPY-PACKAGE.md` (inline header added) |
| `CSF-VIP-GO-LIVE-PLAN.md` | `_archived/vip-pre-birchal-v2/CSF-VIP-GO-LIVE-PLAN.md` |
| `CSF-VIP-LIVE-VERIFICATION.md` | `_archived/vip-pre-birchal-v2/CSF-VIP-LIVE-VERIFICATION.md` |
| `CSF-VIP-MARKETING-COPY.md` | `_archived/vip-pre-birchal-v2/CSF-VIP-MARKETING-COPY.md` |
| `CSF-VIP-PREMERGE-CHECK.md` | `_archived/vip-pre-birchal-v2/CSF-VIP-PREMERGE-CHECK.md` |
| `CSF-VIP-RESEARCH-RG261.md` | `_archived/vip-pre-birchal-v2/CSF-VIP-RESEARCH-RG261.md` |
| `CSF-VIP-RESEARCH-RG262.md` | `_archived/vip-pre-birchal-v2/CSF-VIP-RESEARCH-RG262.md` |
| `CSF-VIP-RESEARCH.md` | `_archived/vip-pre-birchal-v2/CSF-VIP-RESEARCH.md` |
| `CSF-VIP-SCARCITY-DISCUSSION.md` | `_archived/vip-pre-birchal-v2/CSF-VIP-SCARCITY-DISCUSSION.md` |
| `CSF-VIP-TOUCHPOINTS-AUDIT.md` | `_archived/vip-pre-birchal-v2/CSF-VIP-TOUCHPOINTS-AUDIT.md` |

**Restore (all 12)**:
```bash
cd /Users/jb/Documents/GitHub/learning-loop
for f in clients/farm-thru/_archived/vip-pre-birchal-v2/CSF-VIP-*.md; do
  git mv "$f" "clients/farm-thru/$(basename "$f")"
done
# Then manually strip the inline ARCHIVED header from CSF-VIP-COPY-PACKAGE.md
# (the `# ARCHIVED 2026-04-27 ...` h1 + blockquote, ~3 lines at the top)
```

---

## 3. Template sections commented out (LP variants + thank-you)

All wrapped blocks use ONE HTML comment around the markup, with grep-able BEGIN/END marker text inside the comment. This guarantees the markup is invisible in the rendered DOM AND searchable for restoration:

```html
<!--
VIP_ARCHIVED_2026-04-27_PENDING_BIRCHAL_V2_APPROVAL_BEGIN
Restore by uncommenting block; see clients/farm-thru/VIP-ARCHIVE-MANIFEST.md
...the original VIP card markup, untouched...
VIP_ARCHIVED_2026-04-27_PENDING_BIRCHAL_V2_APPROVAL_END
-->
```

(Earlier draft of this manifest used two separate `<!-- ... -->` comments around the markup, which would have left the markup in the rendered DOM. The shipped sales-skill PR #226 uses the one-big-comment style above. The archival script `sales-skill:scripts/archive_fmth_vip_card.py` auto-detects + fixes the broken style if it ever appears.)

### 3.1 LP variants (16 files — index-o.html had no VIP block, no change needed)

| File | VIP block lines (pre-archive) |
|---|---|
| `sales-skill/web/campaigns/FMTH/index-b.html` | 139–153 (`<section class="vip">` ... `</section>`) |
| `sales-skill/web/campaigns/FMTH/index-c.html` | 152–166 |
| `sales-skill/web/campaigns/FMTH/index-d.html` | 119–133 |
| `sales-skill/web/campaigns/FMTH/index-e.html` | 127–141 |
| `sales-skill/web/campaigns/FMTH/index-f.html` | 130–144 |
| `sales-skill/web/campaigns/FMTH/index-g.html` | 165–179 |
| `sales-skill/web/campaigns/FMTH/index-h.html` | 140–154 |
| `sales-skill/web/campaigns/FMTH/index-i.html` | 154–168 |
| `sales-skill/web/campaigns/FMTH/index-j.html` | 93–107 |
| `sales-skill/web/campaigns/FMTH/index-k.html` | 139–153 |
| `sales-skill/web/campaigns/FMTH/index-l.html` | 155–169 |
| `sales-skill/web/campaigns/FMTH/index-m.html` | 127–141 |
| `sales-skill/web/campaigns/FMTH/index-n.html` | 131–145 |
| `sales-skill/web/campaigns/FMTH/index-o.html` | n/a (no VIP block — already excluded by design) |
| `sales-skill/web/campaigns/FMTH/index-p.html` | 131–145 |
| `sales-skill/web/campaigns/FMTH/index-q.html` | 70–82 (inline `<div class="vip__card">` inside `<section class="thank-you">`, NOT a top-level `<section class="vip">`) |

### 3.2 Thank-you template

| File | VIP block lines (pre-archive) |
|---|---|
| `sales-skill/web/templates/campaign_thankyou.html` | 59–73 (the `{% if not is_vip %}` deposit-prompt branch) |

The `{% else %}` VIP-confirmed branch (lines 75–80) is LEFT IN PLACE so existing VIP customers still see their confirmed state.

### 3.3 Restoration (all template sections)

For the one-big-comment style shipped in sales-skill PR #226, restoration strips:
- the leading `<!--\n` line
- the `VIP_ARCHIVED_2026-04-27_PENDING_BIRCHAL_V2_APPROVAL_BEGIN\n` line
- the `Restore by uncommenting...\n` line
- the trailing `VIP_ARCHIVED_2026-04-27_PENDING_BIRCHAL_V2_APPROVAL_END\n` line
- the trailing `-->\n` line

leaving the original markup intact.

```bash
cd /Users/jb/Documents/GitHub/sales-skill

# Find every wrapped block:
grep -rl 'VIP_ARCHIVED_2026-04-27_PENDING_BIRCHAL_V2_APPROVAL_BEGIN' web/

# Strip the wrapping comment + marker text, restore the markup:
python3 - <<'PY'
import re
from pathlib import Path
ROOT = Path("/Users/jb/Documents/GitHub/sales-skill/web")
WRAPPER = re.compile(
    r'<!--\s*\nVIP_ARCHIVED_2026-04-27_PENDING_BIRCHAL_V2_APPROVAL_BEGIN\n'
    r'Restore by uncommenting block; see clients/farm-thru/VIP-ARCHIVE-MANIFEST\.md\n'
    r'(.*?)\n'
    r'VIP_ARCHIVED_2026-04-27_PENDING_BIRCHAL_V2_APPROVAL_END\n-->',
    re.DOTALL,
)
for p in list(ROOT.rglob("index-?.html")) + [ROOT / "templates" / "campaign_thankyou.html"]:
    if not p.is_file():
        continue
    s = p.read_text()
    new = WRAPPER.sub(lambda m: m.group(1), s)
    if new != s:
        p.write_text(new)
        print(f"restored {p.relative_to(ROOT.parent)}")
PY
```

---

## 4. Code paths gated (app.py)

### 4.1 New module-level constant

Added near the top of `sales-skill/web/app.py`, just after the Stripe configuration block (around line 45):

```python
# FMTH VIP scheme archived 2026-04-27 pending Birchal v2 approval.
# See clients/farm-thru/VIP-ARCHIVE-MANIFEST.md (in learning-loop) for restoration.
FMTH_VIP_ENABLED = False
```

### 4.2 New helper for the disabled response

Added near the VIP checkout route (just above `campaign_vip_checkout`):

```python
def _vip_disabled_response():
    """Returned by the VIP checkout route while FMTH_VIP_ENABLED is False.
    HTTP 503 so monitoring sees this as 'service unavailable', and a structured
    JSON body so the LP-side fetch handler shows a polite message to the user.
    """
    return jsonify({
        "error": "vip_currently_disabled",
        "message": (
            "VIP access is temporarily unavailable while we update the offer. "
            "Please join the free waitlist and we will email you when access reopens."
        ),
    }), 503
```

### 4.3 Gate inside `campaign_vip_checkout`

The route function `campaign_vip_checkout(slug)` returns the disabled response as the first thing it does (before any other validation):

```python
@app.route("/campaigns/<slug>/vip-checkout", methods=["POST"])
def campaign_vip_checkout(slug: str):
    """..."""
    if not FMTH_VIP_ENABLED:
        return _vip_disabled_response()
    # ... existing logic ...
```

### 4.4 What was NOT gated (defense by design)

- `/stripe/webhook` (line ~1374): MUST keep processing all events. If a pre-archive checkout completes after archival, or a refund event fires, the webhook handler dispatches it correctly.
- `_handle_vip_deposit(session_data)` (line ~738): MUST keep processing because a delayed `checkout.session.completed` for a pre-archive session could still arrive.
- `process_drip_emails` and the `is_vip` fork in `campaign_drip.py` line 292: MUST keep working so existing VIP customers continue receiving their drip schedule.
- Refund flow: there's no Stripe-side refund endpoint in `app.py`; refunds are issued via the Stripe Dashboard. The webhook handler does not currently process `charge.refunded`, so nothing changes there.

### 4.5 Restoration (app.py)

1. Open `sales-skill/web/app.py`.
2. Find `FMTH_VIP_ENABLED = False` (single occurrence). Change to `True`.
3. Optionally remove `_vip_disabled_response()` and the gating `if` block, but leaving them in place is harmless — once `FMTH_VIP_ENABLED = True` they're skipped.

```bash
cd /Users/jb/Documents/GitHub/sales-skill
# Verify exactly one match:
grep -n 'FMTH_VIP_ENABLED' web/app.py
# Should show 2 hits: the constant + the gate. Then flip:
sed -i '' 's/FMTH_VIP_ENABLED = False/FMTH_VIP_ENABLED = True/' web/app.py
# Verify:
grep 'FMTH_VIP_ENABLED = ' web/app.py
```

---

## 5. Spot-check commands for the verification agent

Run these against the deployed sales-skill revision (or `localhost:5000` for local).

```bash
# 1. LP variants — VIP card should be wrapped in an HTML comment (not in the rendered DOM).
# Two checks: (a) the marker is present (proof the archive happened);
# (b) Python HTMLParser confirms zero visible vip-classed tags after parsing.
for v in b c d e f g h i j k l m n o p q; do
  url="https://join.farmthru.com.au/campaigns/fmth/?v=$v"
  body=$(curl -s "$url")
  has_marker=$(echo "$body" | grep -c 'VIP_ARCHIVED_2026-04-27' | head -1)
  visible=$(echo "$body" | python3 -c "
import sys
from html.parser import HTMLParser
class V(HTMLParser):
    def __init__(self):
        super().__init__()
        self.n = 0
    def handle_starttag(self, tag, attrs):
        if any('vip' in (v or '') for k, v in attrs if k == 'class'):
            self.n += 1
p = V()
p.feed(sys.stdin.read())
print(p.n)
")
  echo "variant=$v has_marker=$has_marker visible_vip_tags=$visible  # marker should be 1 (or 0 for index-o), visible should be 0"
done

# 2. Thank-you template — VIP deposit prompt should NOT appear (visit fresh, no ?vip=success).
# The {% else %} VIP-confirmed branch IS still rendered if ?vip=success is set; that's intentional.
body=$(curl -s 'https://join.farmthru.com.au/campaigns/fmth/thank-you')
has_marker=$(echo "$body" | grep -c 'VIP_ARCHIVED_2026-04-27' | head -1)
visible=$(echo "$body" | python3 -c "
import sys
from html.parser import HTMLParser
class V(HTMLParser):
    def __init__(self):
        super().__init__()
        self.n = 0
    def handle_starttag(self, tag, attrs):
        if any('vip' in (v or '') for k, v in attrs if k == 'class'):
            self.n += 1
p = V()
p.feed(sys.stdin.read())
print(p.n)
")
echo "thank-you (no vip): has_marker=$has_marker visible_vip_tags=$visible  # marker=1, visible=0"

# 3. VIP checkout endpoint — should return HTTP 503 + structured JSON
curl -s -X POST 'https://join.farmthru.com.au/campaigns/fmth/vip-checkout' \
     -F 'email=test@example.com' \
     -w '\nHTTP=%{http_code}\n'
# Expected: HTTP=503 + {"error": "vip_currently_disabled", "message": "..."}

# 4. Free waitlist signup — should still work (this is the v2 path)
curl -s -X POST 'https://join.farmthru.com.au/campaigns/fmth/signup' \
     -F 'email=verify-vip-archive@example.com' \
     -F 'variant=b' \
     -w '\nHTTP=%{http_code}\n'
# Expected: HTTP=200 (or whatever the existing success status is)

# 5. Stripe webhook — should still ACK events (test with the Stripe CLI, NOT in prod)
# stripe trigger checkout.session.completed --add checkout_session:metadata.type=vip_deposit
# (only against test mode / staging — not against the prod webhook)

# 6. Archived files exist & are recoverable
test -f clients/farm-thru/loop/emails/_archived/vip-pre-birchal-v2/EM-VIP-01.json && echo "EM-VIP-01 archived OK"
test -f clients/farm-thru/loop/sms/_archived/vip-pre-birchal-v2/SMS-VIP-OPEN.json && echo "SMS-VIP-OPEN archived OK"
test -f clients/farm-thru/_archived/vip-pre-birchal-v2/CSF-VIP-COPY-PACKAGE.md && echo "COPY-PACKAGE archived OK"
test ! -f clients/farm-thru/CSF-VIP-COPY-PACKAGE.md && echo "COPY-PACKAGE no longer at original path"

# 7. Markers are grep-able for restoration
grep -rl 'VIP_ARCHIVED_2026-04-27_PENDING_BIRCHAL_V2_APPROVAL_BEGIN' /Users/jb/Documents/GitHub/sales-skill/web/ | wc -l
# Expected: 17 (16 LP variants + 1 thank-you template)

# 8. app.py flag is set correctly
grep -n 'FMTH_VIP_ENABLED' /Users/jb/Documents/GitHub/sales-skill/web/app.py
# Expected: 2 hits — the constant (False) + the gate

# 9. Webhook handler still routes vip_deposit events to _handle_vip_deposit
grep -n '_handle_vip_deposit' /Users/jb/Documents/GitHub/sales-skill/web/app.py
# Expected: 2 hits — the def + the call inside stripe_webhook (the call MUST still exist)
```

---

## 6. Known scope-bounded gaps (flagged for the verification agent)

These were identified during the archival but left out of scope per the brief ("only the VIP card section comes out", "Don't touch the LP variants' main hero / signup form / footer"):

1. **In-prose VIP mentions on LP variants** — most LPs (e.g. index-b.html line 112) still have a prose paragraph reading "Place a small refundable deposit to join our VIP waitlist. You'll get a launch-day SMS the moment our round opens at Birchal, plus a heads-up before launch. No obligation to invest." This is in a `<p class="campaign-section__text">` inside the main copy section, NOT in the `<section class="vip">` card. The brief was scoped to the card only. **Recommendation for the next pass**: rewrite these prose lines to talk about the free waitlist only (no deposit, no VIP language), or remove them entirely. Search command:
   ```bash
   grep -rn 'small refundable deposit\|VIP waitlist' /Users/jb/Documents/GitHub/sales-skill/web/campaigns/FMTH/
   ```

2. **Drip email production templates** — `sales-skill/web/campaigns/FMTH/emails/drip_vip_*.html` are LEFT IN PLACE because existing VIP subscribers still receive them. Once Birchal blesses v2 and we're confident no in-flight VIP subscribers remain (e.g., after issuing all refunds), these templates can be archived too. Until then they're still production assets for the existing cohort.

3. **The `vipCheckoutEndpoint` JS in `campaign_thankyou.html`** — the JS handler at the bottom of the template (around line 117) is left as-is. It was wired to the now-503'd endpoint. The button it controls (`#vipDepositBtn`) is inside the now-commented-out card, so the JS will simply find no element to bind to. Harmless. The `?vip=success` URL handling at the end of the JS is also harmless — that branch only fires if a Stripe redirect lands the user on the page, which will only happen for in-flight pre-archive deposits.

4. **Stripe Dashboard / business name** — out of scope (separate Stripe-rebrand task in PICKUP-2026-04-28). Mentioning here only because the VIP product description in Stripe Checkout Session was "VIP Access - FarmThru". No new sessions are being created so no new Stripe records will reference VIP. Existing records remain untouched.

5. **`drip_vip_welcome` send inside `_handle_vip_deposit`** — line 794 of app.py calls `_load_email_template(slug, "drip_vip_welcome.html")`. This path stays live for in-flight pre-archive deposits whose webhook arrives post-archival. The welcome email content is unchanged — it tells the customer their $5 is locked in and they'll get early access. If we want to send a different message to these stragglers ("VIP scheme is on hold; here's a refund"), that's a separate decision and should be handled in Stripe Dashboard refunds + manual email outreach.
