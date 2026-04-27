# FMTH waitlist cleanup audit — 2026-04-27

**Agent:** Claude Opus 4.7 (1M context)
**UTC stamp:** 20260427T095223Z
**Delete-list source:** `/Users/jb/Downloads/CFE Signups - FarmThru - delete.csv` (141 raw rows, 140 unique lowercase emails after dedupe)
**Sales-skill PR:** `feat/fmth-test-email-prevention-filter` — TBD link
**Cloud Scheduler state at start:** `fmth-drip-hourly` was PAUSED (verified pre-flight). Left PAUSED at end (separate Stripe-rebrand decision).

---

## Pre-delete state

| Surface | Count | Notes |
|---|---|---|
| Firestore signups (`launcher-lab-proposals`/campaigns/fmth-ecb582/signups) | 153 | streamed via `google.cloud.firestore` |
| Sheet1 (waitlist tab) | 260 data rows + 1 header | drift from DB count due to historical sync gaps |
| LP `signupCount` (computed live) | 153 → 122 mid-run (concurrent traffic) | from `len(campaign_store.get_signups(slug))` rendered into HTML at request time |
| `meta/counters.signup_count` doc | 153 | Firestore atomic counter — used only for assigning new `position`. Never decrements automatically; manually corrected post-delete. |

## Match validation (read-only, exact lowercase + trim match)

- CSV unique emails: **140**
- Matched in DB: **32** (will be deleted)
- CSV-only / not in DB: **108** (already gone, or sheet-only artefacts)

The 108 CSV-only emails were almost entirely `e2e-<hex>@test.com` records — old E2E-test signups present in Sheet1 (append-only history) but already cleared from Firestore in a prior cleanup. No legitimate-looking domains in the CSV.

Safety threshold check: `matched (32) <= raw CSV rows (141)` — pass.

## Sheet structure inventory

The FarmThru Google Sheet (`1ooyw7zCCP039ml_4cZfPbhrxtFKuQsFa5VSfsyq6NhA`) contains **8 tabs**:

| Tab | sheetId | Pre-rows | Header row | Touched? |
|---|---|---|---|---|
| `Sheet1` | 0 | 261 | `position, email, name, phone, ref_code, …` | YES — target |
| `delete` | 622363742 | 141 | (no header — manual delete-list paste) | NO |
| `backup` | 55188237 | 120 | `position, email, name, phone, ref_code, …` | NO (historical snapshot left intact) |
| `Angel` | 956153329 | 1 | (empty) | NO |
| `creative` | 317024530 | 15 | `ad creative, Leads, Cost, …` | NO |
| `ad-cost` | 1696074559 | 15 | `Ad ID, …` | NO |
| `Sheet5` | 1739655139 | 14 | (numeric ad-id header) | NO |
| `SupermetricsQueries` | 58191658 | 21 | `Supermetrics Queries, …` | NO |

**Approach used:** row-level `deleteDimension` via `batchUpdate` against `sheetId=0` (Sheet1) only, in descending-row order so prior deletes don't shift later indexes. Single `batchUpdate` call with all 141 requests.

**Non-target tab integrity:** every non-target tab's full `get_all_values()` was SHA-256 hashed pre + post. All hashes byte-identical post-delete. Confirmed in `sheet-delete-result-20260427T094109Z.json` (`non_target_tabs_unchanged` lists all 7).

## Execution

### Phase 4a — Firestore delete

- Streamed all 153 docs, filtered to those whose `email` field (lowercased + stripped) is in the matched delete-set → 32 targets
- Single `batch.commit()` with 32 deletes
- Post-delete: 121 docs
- `meta/counters.signup_count` manually overwritten to 121 (atomic counter does not decrement on delete; without this fix, the next signup's `position` would jump from 122 to 154)

Result file: `db-delete-result-20260427T094109Z.json`

### Phase 4b — Sheet1 row-level deletes

- 141 row indices identified (1-indexed) where `Sheet1!B<row>` (lowercased + stripped) ∈ delete-set
- Sent in one `batchUpdate` with 141 `deleteDimension` requests (descending row order)
- Post-delete: Sheet1 = 120 rows (1 header + 119 data)
- Other 7 tabs verified byte-identical pre/post (SHA-256 hash match)

Result file: `sheet-delete-result-20260427T094109Z.json`

### Phase 4c — Sync gap reconciliation (added during execution)

After delete, DB had 122 data rows but Sheet1 had 119 — drift of 3 caused by historical Firestore→Sheet sync failures (Sheet was unavailable when these signups landed):

```
ant@antheawilliamson.com
tabandu@bigpond.com
test+20260425@example.com
```

These 3 records were appended to Sheet1 from current DB state (`scripts/fmth-cleanup/04_sync_missing_to_sheet.py`). Note `test+20260425@example.com` is clearly a test signup but NOT in the user-provided CSV → **left in DB** per the "don't delete anything not in the CSV" rule. Once the prevention filter ships, future signups matching this pattern will be auto-tagged `is_test=True`.

## Post-delete counts (Phase 5 verification)

| Surface | Post-cleanup | Match? |
|---|---|---|
| Firestore signups count | 122 | yes |
| Firestore `meta/counters.signup_count` | 122 (auto-incremented from 121 by 1 concurrent signup) | yes |
| Sheet1 data rows | 122 | yes |
| LP `signupCount` (rendered into JS CONFIG, server-side) | 122 | yes |

All three surfaces match. (Note: the count rose from 121 → 122 mid-run because a real signup landed during execution; the system handled this correctly — atomic counter incremented, drip dry-run included the new record.)

## Phase 6 — Drip-recipient dry-run

`scripts/fmth-cleanup/05_drip_dryrun.py` mirrors the recipient query in `campaign_drip.process_drip_emails`:
  - Reads current Firestore signups
  - For each, computes which drip templates would fire NOW (within the 3-day-stale window, not already-sent)
  - Cross-references the would-send set against the just-deleted set

**Result: 17 would-send pairs, 0 overlap with deleted set.** Pass.

## Phase 7 — Prevention filter shipped (sales-skill PR)

Branch: `feat/fmth-test-email-prevention-filter`

Soft-tag rather than hard-block (per user pref): test-pattern signups still get written to Firestore and the welcome email still attempts, but the record is flagged `is_test=True` so it is excluded from the public counter, the drip recipient query, and the Sheet sync.

### Patterns (in `web/campaign_store.py::_TEST_EMAIL_PATTERNS`)

| Pattern | Catches |
|---|---|
| `@(test\|example\|sheettest\|email\|ref)\.com$` (case-insensitive) | `john@test.com`, `bob@sheettest.com`, `someone@example.com`, `test@email.com`, `someone@ref.com` |
| `^(e2e\|firestore-test\|verify\|count-check\|flow-demo\|test-diagnosis\|aest-test\|jb-demo\|sheets-test\|live-sheets-test\|webhook\|slack\|noslack\|slackvar\|vipslack\|markvip\|vipemail\|welcome)[-_]?` | `e2e-abc@anywhere.com`, `verify-1234@launcherlab.com.au`, `webhook-x@gmail.com` |
| `@launcherlab\.com\.au$` | All internal-team addresses (blanket flag) |
| `\+(test\|qa\|verify\|claude\|staging\|e2e)@` | `user+test@gmail.com`, `me+e2e@hotmail.com` |

### Call-site updates

| File | Change |
|---|---|
| `web/campaign_store.py` | Added `is_test_email()` + `_TEST_EMAIL_PATTERNS`. `add_signup()` sets `signup["is_test"]`. `get_signups()` gains `exclude_test: bool = False` param. |
| `web/app.py:412` (campaign LP) | `get_signups(slug, exclude_test=True)` — drives `signupCount` in JS CONFIG |
| `web/app.py:452` (thank-you page) | `get_signups(slug, exclude_test=True)` — social-proof counter |
| `web/app.py:489` (signup dup-check) | `get_signups(slug, exclude_test=True)` — for the "you're #X of N" return |
| `web/app.py:535-545` (Sheet sync thread) | Skip `save_signup_to_sheet` thread spawn if `signup["is_test"]` |
| `web/campaign_drip.py:229` (drip) | `get_signups(slug, exclude_test=True)` — recipient query |
| `web/campaign_drip.py:391` (triggered emails) | `get_signups(slug, exclude_test=True)` |
| `web/tests/test_test_email_filter.py` | New test file: 3 tests covering patterns + tagging + filter (45+ assertion cases). All pass. |

Admin pages (`/leaderboard`, `/variants`, `/dashboard`, `/status`) intentionally still see `exclude_test=False` so the team can audit test-tagged records.

### What's NOT done in this PR (deferred)

1. **Backfill `is_test=True` on existing 122 records.** The remaining DB has e.g. `jeremy+test1@launcherlab.com.au`, `jeremy+fmth-test@launcherlab.com.au`, `test+20260425@example.com` etc. — these will continue to receive drip emails until backfilled or manually cleaned. Recommended follow-up: a one-shot script that runs `is_test_email()` against every existing signup and updates the doc. Out of scope for the immediate cleanup.
2. **Live deploy + canary.** The PR ships the code; the canary (POST a test email to prod, confirm `is_test=True` lands, confirm Sheet/LP/drip excluded) must be re-run AFTER Cloud Run picks up the new container.

### Test results

- `pytest web/tests/test_test_email_filter.py -v` → 3/3 pass
- 20 pre-existing test failures in `test_campaigns.py` / `test_campaign_integrations.py` are unrelated to this change (they hit live Firestore now that ADC is set up — verified by running them after stashing my diffs)

## Backup file paths

All artefacts live in `clients/farm-thru/data-snapshots/` (gitignored — added `clients/*/data-snapshots/` to `.gitignore`):

- `signups-pre-cleanup-20260427T094104Z.jsonl` — full Firestore export (153 docs)
- `sheet-pre-cleanup-20260427T094106Z-manifest.json` — tab inventory + headers + row counts
- `sheet-pre-cleanup-20260427T094106Z-tab-Sheet1.csv` — Sheet1 pre-state (260 data rows)
- `sheet-pre-cleanup-20260427T094106Z-tab-{Angel,backup,ad-cost,creative,delete,Sheet5,SupermetricsQueries}.csv` — other tabs
- `cleanup-plan-20260427T094109Z.json` — match validation, target tab list, per-tab match counts
- `db-delete-result-20260427T094109Z.json` — 32 deleted, counter 153→121
- `sheet-delete-result-20260427T094109Z.json` — 141 row-deletes from Sheet1, all other tabs unchanged
- `drip-dryrun-20260427T094109Z.json` — 17 would-send pairs, 0 overlap

## Notes / unexpected findings

1. The CSV had **141 rows** but only **140 unique lowercase emails** (one duplicate). De-duped at load.
2. The DB only matched **32** of the 140 CSV emails — the other 108 were stale Sheet rows. The Sheet was append-only with no reverse-sync from a prior cleanup, so it accumulated history that never existed in DB.
3. Firestore's atomic `signup_count` counter does NOT decrement on document delete. Manually corrected post-delete (153→121) so the next signup's `position` reflects reality.
4. `test+20260425@example.com` is in DB but NOT in the user-provided delete CSV → left in DB. The shipped prevention filter would auto-tag it `is_test=True` if it were re-added, but the existing record needs manual `is_test=True` backfill (deferred follow-up).
5. The `backup` tab contains a 120-row historical snapshot of signups. Left UNTOUCHED to preserve history.
6. Admin `/leaderboard`, `/variants`, `/dashboard`, `/status` pages will continue to count test signups in their numbers (they pass `exclude_test=False` by default). This is intentional — the team should be able to see test signups for debugging. Public-facing surfaces only get the filtered count.

## Don'ts respected

- Cloud Scheduler `fmth-drip-hourly` left PAUSED (separate Stripe-rebrand decision).
- Nothing deleted outside the user-provided CSV (the typo `test@email.coim` and several `jeremy+...@launcherlab.com.au` entries were left in DB).
- Backups taken before any mutation.
- Exact-match only (no substring).
- `FMTH_VIP_ENABLED` and VIP-archive code untouched.
- No Resend API-level unsubscribe attempted (test addresses; no real Resend recipient records).
- `clients/farm-thru/data-snapshots/` added to root `.gitignore` — backups and CSVs containing PII are not committed.
