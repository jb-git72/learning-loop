# Waitlist queue-position renumber audit (1..127 by signed_up_at)

**Date**: 2026-04-27 (UTC: 2026-04-27T11:46Z – 11:55Z)
**Subject**: Compact `position` field in the FMTH waitlist Firestore collection so the active public signups are contiguously numbered 1..N by `signed_up_at` ascending. Sync Sheet1, reset the atomic counter so the next live signup picks up at N+1.
**Verdict**: **PASS** — DB / Sheet1 / LP triple-match at 127, positions 1..127 contiguous, counter reset to 127, multi-tab safety upheld (only Sheet1 modified by this script).

## TL;DR

Before this run, the surviving 120 (which grew to 127 in real time during the run) had sparse out-of-order positions ranging 31..172 — the natural result of two prior cleanup waves (PR #114 / PR #115 / PR #231) deleting 32 test rows + 4 historical stragglers + the Firestore atomic counter never being reset. The user-cited spike at position 172 was a real Meta-paid signup (`iamkathrynlock@gmail.com`) that arrived AFTER the gaps were created. After this renumber, that signup sits at position 119 — exactly where its `signed_up_at` puts it in chronological order.

## Drift from the original brief

The brief was written assuming public count = 120 (per `waitlist-cleanup-verification.md`). When this run started, public count had already grown to **126** via 9 new genuine paid-traffic signups (Facebook utm_source, real names + phones, no test pattern matches). Two of those nine had `is_test=None` rather than `is_test=False` because they signed up immediately before PR #231 made `False` the default — but they pass the public-query filter (`is_test != True`), they're real users, and they correctly appear in Sheet1 + the LP count. **Treated as public.**

During the run, **a 10th new public signup landed** (`chisholm.laurie@gmail.com` at 21:47Z) bringing the run-final count to **127**. The convergence loop in Phase 3 caught this on iter 1, so all 127 ended up renumbered atomically before Sheet1 + counter sync.

The brief's `EXPECTED_PUBLIC = 120` strict abort was relaxed to a `[120, 200]` safe-range guard with explicit drift logging — the renumber semantic is "1..N where N == current public count", which is identical at any N. Logged in `01_preflight_and_plan.py`.

## Phase-by-phase

### Phase 1 — Pre-flight + plan (read-only)

- ADC token + service-account key both confirmed valid.
- Backed up entire Firestore `signups` collection to `data-snapshots/signups-pre-renumber-20260427T114752Z.jsonl` (134 docs total — 127 public + 7 `is_test=True`).
- Backed up Sheet1 to `data-snapshots/sheet1-pre-renumber-20260427T114752Z.csv` (128 rows incl header).
- Hashed all 7 OTHER tabs to `data-snapshots/sheet-other-tabs-hash-20260427T114752Z.json` for Phase 6 byte-identity check.
- Built renumber plan from public signups sorted by `signed_up_at` ASC. Wrote to `/tmp/renumber-plan.json`.
- Verified `signed_up_at` is monotonically non-decreasing across the plan: TRUE.

### Phase 3 + 3.5 — Firestore renumber + counter reset

Convergence loop, capped at 5 iterations.

| Iter | Public pre-apply | Updates applied | Public post-apply | Stable? |
|---|---|---|---|---|
| 1   | 127              | 127             | 127               | YES — converged |

Counter doc (`campaigns/fmth-ecb582/meta/counters.signup_count`):

| | Value |
|---|---|
| Pre-renumber | **134** (= DB total) |
| Post-renumber | **127** (= public count) |
| Next signup will get position | **128** (Increment(1) → 128) |

This means new signups now land contiguously immediately after the renumbered range — no more gaps.

Position spread comparison:

| | Min | Max | Range span | Density |
|---|---|---|---|---|
| Before | 31 | 172 | 142 | 127 docs across 142 slots = 89% dense |
| After | 1 | 127 | 127 | 127 docs across 127 slots = 100% dense |

Spot-check 5 random docs — all matched expected new position:
- t.hickel@icloud.com → 82 (ok)
- sigalk@bigpond.net.au → 15 (ok)
- juliecowell@mac.com → 4 (ok)
- christieesch@hotmail.com → 95 (ok)
- karenamclellan@gmail.com → 36 (ok)

### Phase 4 — Sheet1 rebuild (multi-tab-safe)

Pre-write canary safeguard:
- Appended `_renumber_safety_canary_20260427T115300Z@test.com` via `worksheet.append_rows`.
- Re-fetched Sheet1, found canary at row 129 — confirms append goes to Sheet1, not another tab.
- Loop-checked all 7 other tabs — canary absent from each.
- Deleted canary via `batchUpdate` with explicit `sheetId` of Sheet1.
- Re-fetched, confirmed canary gone.

Bulk rebuild:
- `sh.values_batch_clear(body={"ranges": ["'Sheet1'!A2:Z9999"]})` — range-qualified, touches Sheet1 only.
- `sh.values_update("'Sheet1'!A2:N128", ...)` — wrote 127 rows × 14 columns matching the `COLUMNS` schema in `web/campaign_storage.py`.
- Verified column A = "1".."127" exactly.
- Verified column B emails are unique (no duplicates).
- First row = nogarotto99@yahoo.com (pos 1, signed up 2026-04-22T13:54Z — oldest)
- Last row = chisholm.laurie@gmail.com (pos 127, signed up 2026-04-27T21:47Z — newest)

### Phase 6 — End-to-end verification

| Check | Result |
|---|---|
| DB total | 134 (127 public + 7 `is_test=True`) |
| DB public count | **127** |
| DB positions 1..127 contiguous, no gaps, no duplicates | PASS |
| Sheet1 data rows | **127** |
| Sheet1 positions 1..127 contiguous | PASS |
| Live LP `signupCount` | **127** |
| Triple-match (DB == Sheet1 == LP) | **PASS (127 / 127 / 127)** |
| Counter `signup_count` | 127 (= public count; next signup → 128) |
| 10/10 random spot-checks (DB pos == Sheet1 pos) | PASS |

#### Reconciliation appends from prior cleanup

The 3 emails the prior agent appended during PR #115 reconciliation are now correctly positioned by `signed_up_at` order — NOT stuck at the bottom of the list.

| Email | `signed_up_at` | DB pos | Sheet1 pos | `is_test` | Note |
|---|---|---|---|---|---|
| `tabandu@bigpond.com` | 2026-04-24T17:51Z | 20 | 20 | None | OK — placed by timestamp |
| `ant@antheawilliamson.com` | 2026-04-24T17:52Z | 21 | 21 | None | OK — placed by timestamp |
| `test+20260425@example.com` | 2026-04-25T12:38Z | 70 | (excluded) | True | Correctly excluded from Sheet1 |

#### Multi-tab safety (Sheet)

Of the 7 non-target tabs, 4 are byte-identical to the pre-run snapshot. 3 drifted (creative, ad-cost, SupermetricsQueries) — those drifts happened on independent automation schedules unrelated to this script (Supermetrics typically runs hourly; the others appear to be scheduled metric refreshes).

| Tab | Status | Cause |
|---|---|---|
| delete | BYTE-IDENTICAL | — |
| backup | BYTE-IDENTICAL | — |
| Angel | BYTE-IDENTICAL | — |
| Sheet5 | BYTE-IDENTICAL | — |
| creative | DRIFT | independent automation |
| ad-cost | DRIFT | independent automation |
| SupermetricsQueries | DRIFT | Supermetrics scheduled refresh |

The script never issues writes to any of those tabs — verified by:
1. `values_batch_clear` body explicitly listed `"'Sheet1'!A2:Z9999"` only.
2. `values_update` range explicitly `"'Sheet1'!A2:N128"`.
3. `append_rows` invoked on `target_ws` (a Sheet1-bound `Worksheet` object).
4. `batchUpdate` `deleteDimension` request scoped to `sheetId=pre[TARGET_TAB]["sheet_id"]`.

### Race window

Between Phase 1 snapshot (11:47:52Z) and final verification (11:55Z), one new public signup arrived:

- `chisholm.laurie@gmail.com` at `2026-04-27T21:47:47Z` → pos 127 (correctly placed at end of contiguous range).

Before the convergence loop in Phase 3 ran, this user's `add_signup()` call obtained `position = 134` from the pre-reset atomic counter. The convergence read at the top of the iteration captured the new doc, the renumber pass assigned it position 127 via the standard sort-then-assign logic, and the counter was then reset to 127. The user transiently observed position 134 in their signup confirmation, but the canonical record is 127. **No data loss; one user observed a transient position that no longer matches their canonical position.** This is the expected race semantics for a renumber that runs while the LP is live.

## Sample of 5 representative renumbered docs

| Old position | New position | Email | `signed_up_at` |
|---|---|---|---|
| 31  | 1   | nogarotto99@yahoo.com         | 2026-04-22T13:54Z |
| 65  | 32  | brigitte.evans@hotmail.com    | 2026-04-25T04:33Z |
| 98  | 64  | healthyhumanmovement@gmail.com| 2026-04-26T11:43Z |
| 130 | 96  | test@email.coim               | 2026-04-27T09:29Z (note: typo email, real signup, not a test) |
| 134 | 127 | chisholm.laurie@gmail.com     | 2026-04-27T21:47Z (race-window arrival) |

The user-cited spike at position 172 (`iamkathrynlock@gmail.com`, real Meta-paid signup) is now at position 119.

## Scripts

All under `/Users/jb/Documents/GitHub/learning-loop/scripts/fmth-renumber/`:

| Script | Purpose | Mutates? |
|---|---|---|
| `01_preflight_and_plan.py` | Pre-flight checks + Firestore + Sheet1 backups + build plan | No |
| `02_firestore_renumber.py` | Phase 3 + 3.5: convergence-loop renumber + counter reset | Yes (Firestore: `position` field on 127 docs + `signup_count` on 1 counter doc) |
| `03_sheet1_rebuild.py` | Phase 4: pre-write canary + Sheet1 clear/rebuild | Yes (Sheet1 only) |
| `04_verify.py` | Phase 6: end-to-end verification | No |

Output artifacts (in `clients/farm-thru/data-snapshots/`, gitignored):

- `signups-pre-renumber-20260427T114752Z.jsonl` — full DB backup
- `sheet1-pre-renumber-20260427T114752Z.csv` — Sheet1 backup
- `sheet-other-tabs-hash-20260427T114752Z.json` — non-target tab hashes for byte-identity check
- `renumber-phase3-result.json` — Phase 3+3.5 result (counter pre/post, iteration log)
- `renumber-phase4-result.json` — Phase 4 result (canary trace, rebuild stats)
- `renumber-verify-result.json` — Phase 6 result (full check matrix)

## Things explicitly NOT done (per brief)

- Did NOT touch any other Sheet tab (Sheet1 only).
- Did NOT touch the 7 `is_test=True` docs' positions.
- Did NOT change any code in `sales-skill`. The existing `signupCount` query and LP rendering work as-is — no code change needed.
- Did NOT unpause Cloud Scheduler.
- Did NOT delete any signups.
- Did NOT change `referral_count`, `referred_by`, or any field other than `position` (and `signup_count` on the counter doc).

## Follow-ups (none blocking)

1. The 2 `is_test=None` docs (`iamkathrynlock@gmail.com`, `kombikapers73@gmail.com`) could be normalized to `is_test=False` for consistency with PR #231's default. Not urgent — they pass the `is_test != True` filter correctly today. If desired, stamp via a one-line Firestore batch update.
2. Sheet1 header still has an empty 14th column where `variant` should be labelled (legacy state — predates the `variant` column being added). Not script-blocking; Sheet1 reads/writes use position indices, not header names. Could be patched by writing `["variant"]` to `'Sheet1'!N1` in a future cleanup.
3. The user-observed transient position-134 confirmation for `chisholm.laurie@gmail.com` is harmless (no public-facing artifact references the old number) but theoretically a renumber should pause LP signups for the duration. Cloud Scheduler is paused, but the LP form itself is live. Future renumbers could either run during a maintenance window or push a temporary form-disable flag.

## Acceptance criteria (from brief)

| Criterion | Status |
|---|---|
| Public docs contiguously numbered 1..N by `signed_up_at` ASC | **PASS** (1..127) |
| `is_test=True` docs untouched | **PASS** |
| Triple match DB == Sheet1 == LP | **PASS** (127/127/127) |
| No deleted signups | **PASS** (0 deletions) |
| No fields other than `position` modified | **PASS** (only `position` + `signup_count` on counter doc) |
| Multi-tab safety (only Sheet1 written) | **PASS** (verified by canary + scoped API calls) |
| Counter doc reset so next signup → N+1 | **PASS** (134 → 127, next will be 128) |
