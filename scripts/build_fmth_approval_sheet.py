#!/usr/bin/env python3
"""Build a FarmThru CFE ad-copy approval Google Sheet.

Layout follows the vet-partners "Option B" pattern (single Ad column with
internal hierarchy, tiny grey caps labels, checkbox + Comments column,
landing-page column, auto-fit row heights). Reads the seed live $2-lead ad
plus the top hill-climb variants from clients/farm-thru/loop/live-ad-variants/.

Usage:
    python3 scripts/build_fmth_approval_sheet.py
    python3 scripts/build_fmth_approval_sheet.py --share-with jeremy@launcherlab.com.au,client@example.com
    python3 scripts/build_fmth_approval_sheet.py --landing-url https://farmthru.com.au/ --max-variants 3

Service-account key reused from sister repo (per CLAUDE.md). Impersonates a
real human so the sheet's owner is not the SA; share via notify=False so the
client doesn't get an early "you've been added" email.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Service-account key shared across sister repos per CLAUDE.md.
KEY_FILE = Path("/Users/jb/Documents/GitHub/vet-partners/.gdocs-sync-key.json")
IMPERSONATE_USER = "jeremy@launcherlab.com.au"

REPO = Path(__file__).resolve().parent.parent
SEED_PATH = REPO / "clients" / "farm-thru" / "loop" / "live-ad-test.json"
VARIANTS_DIR = REPO / "clients" / "farm-thru" / "loop" / "live-ad-variants"
DEFAULT_LANDING = "https://farmthru.com.au/"
DEFAULT_SHARE = ["jeremy@launcherlab.com.au"]
DEFAULT_TITLE = f"FarmThru — CFE Pre-Campaign Ad Copy for Approval ({datetime.now().strftime('%Y-%m-%d')})"

# Option B colour palette + format constants (verified via vet-partners review)
YELLOW_HEADER = {"red": 0.992, "green": 0.886, "blue": 0.541}
GREEN_BAND_DARK = {"red": 0.541, "green": 0.769, "blue": 0.557}
ZEBRA = {"red": 0.965, "green": 0.965, "blue": 0.965}
GREY_TEXT = {"red": 0.45, "green": 0.45, "blue": 0.45}

LABEL_FMT = {"bold": True, "fontSize": 8, "foregroundColor": {"red": 0.55, "green": 0.55, "blue": 0.6}}
BODY_FMT = {"bold": False, "italic": False, "fontSize": 11, "foregroundColor": {"red": 0.15, "green": 0.15, "blue": 0.15}}
HEADLINE_FMT = {"bold": True, "italic": False, "fontSize": 13, "foregroundColor": {"red": 0.1, "green": 0.1, "blue": 0.1}}
DESC_FMT = {"bold": False, "italic": True, "fontSize": 10, "foregroundColor": GREY_TEXT}
GAP_FMT = {"fontSize": 6}

LABEL_PT = "PRIMARY TEXT"
LABEL_HL = "HEADLINE"
LABEL_DS = "DESCRIPTION"

HEADERS = ["Source", "Ad", "Approved", "Comments", "Landing page"]
COL_WIDTHS = [120, 720, 110, 340, 220]


def get_client():
    import gspread
    from google.oauth2 import service_account as sa

    if not KEY_FILE.is_file():
        sys.exit(f"Service-account key not found at {KEY_FILE}")

    creds = sa.Credentials.from_service_account_file(
        str(KEY_FILE),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    ).with_subject(IMPERSONATE_USER)
    return gspread.authorize(creds)


def col_letter(idx: int) -> str:
    s = ""
    while idx > 0:
        idx, r = divmod(idx - 1, 26)
        s = chr(65 + r) + s
    return s


def load_ads(max_variants: int) -> list[dict]:
    """Load seed + top N variants. Excludes variants flagged with DISC-001-style
    banned wording (writer occasionally regresses to the old disclaimer wording)."""
    ads: list[dict] = []
    seed = json.loads(SEED_PATH.read_text())
    seed["_source_label"] = "PROVEN ($2 leads in market)"
    ads.append(seed)

    summary_path = VARIANTS_DIR / "summary.json"
    if not summary_path.is_file():
        sys.exit(f"Variants summary not found at {summary_path} — run hill_climb_from_seed.py first.")
    summary = json.loads(summary_path.read_text())

    BANNED = ("seek independent financial advice", "consult a financial advisor", "consider seeking independent")

    candidates = []
    for r in summary.get("results", []):
        ad_path = VARIANTS_DIR / f"{r['ad_id']}.json"
        if not ad_path.is_file():
            continue
        ad = json.loads(ad_path.read_text())
        body = (ad.get("primary_text", "") + " " + ad.get("description", "")).lower()
        if any(p in body for p in BANNED):
            print(f"  excluding {r['ad_id']} — banned DISC-001 wording present")
            continue
        ad["_source_label"] = f"VARIANT (composite {r['composite']:.2f})"
        ad["_variant_meta"] = r
        candidates.append(ad)

    ads.extend(candidates[:max_variants])
    return ads


def build_sheet(sh, ads, landing_url):
    n = len(HEADERS)
    ws = sh.sheet1
    ws.update_title("Copy for Approval")
    ws.resize(rows=200, cols=n)
    sheet_id = ws._properties["sheetId"]

    # Build table
    table = [HEADERS]
    section_rows: list[int] = []
    data_rows: list[int] = []
    ad_meta: list[dict] = []

    table.append([f"Pre-campaign waitlist  ({len(ads)} ad{'s' if len(ads) != 1 else ''})"] + [""] * (n - 1))
    section_rows.append(len(table) - 1)

    for ad in ads:
        headline = ad.get("headline", "")
        body = ad.get("primary_text", "")
        desc = ad.get("description", "")
        parts = [
            (LABEL_PT, "label"),
            ("\n", "gap_small"),
            (body, "body"),
            ("\n\n", "gap"),
            (LABEL_HL, "label"),
            ("\n", "gap_small"),
            (headline, "headline"),
            ("\n\n", "gap"),
            (LABEL_DS, "label"),
            ("\n", "gap_small"),
            (desc, "desc"),
        ]
        ad_text = "".join(p[0] for p in parts)
        source = ad.get("_source_label", "")
        table.append([source, ad_text, False, "", landing_url])
        row_idx = len(table) - 1
        data_rows.append(row_idx)

        # UTF-16 offsets for textFormatRuns
        offsets, cursor = [], 0
        for txt, kind in parts:
            offsets.append({"start": cursor, "kind": kind, "len": len(txt)})
            cursor += len(txt)
        ad_meta.append({"row": row_idx, "offsets": offsets})

    end_a1 = f"{col_letter(n)}{len(table)}"
    ws.update(values=table, range_name=f"A1:{end_a1}", value_input_option="USER_ENTERED")

    requests = []

    # Freeze header
    requests.append({
        "updateSheetProperties": {
            "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
            "fields": "gridProperties.frozenRowCount",
        }
    })
    # Header row
    requests.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": n},
            "cell": {"userEnteredFormat": {
                "backgroundColor": YELLOW_HEADER,
                "textFormat": {"bold": True, "fontSize": 11},
                "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP",
            }},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)",
        }
    })
    # Section bands
    for r in section_rows:
        requests.append({
            "mergeCells": {
                "range": {"sheetId": sheet_id, "startRowIndex": r, "endRowIndex": r + 1, "startColumnIndex": 0, "endColumnIndex": n},
                "mergeType": "MERGE_ALL",
            }
        })
        requests.append({
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": r, "endRowIndex": r + 1, "startColumnIndex": 0, "endColumnIndex": n},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": GREEN_BAND_DARK,
                    "textFormat": {"bold": True, "fontSize": 13, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                    "horizontalAlignment": "LEFT", "verticalAlignment": "MIDDLE",
                    "padding": {"top": 8, "bottom": 8, "left": 12, "right": 12},
                }},
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,padding)",
            }
        })
    # Data rows: zebra background, wrap, padding, checkbox in col C, link in col E
    for i, row_idx in enumerate(data_rows):
        bg = ZEBRA if i % 2 == 1 else {"red": 1, "green": 1, "blue": 1}
        requests.append({
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": row_idx, "endRowIndex": row_idx + 1, "startColumnIndex": 0, "endColumnIndex": n},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": bg,
                    "wrapStrategy": "WRAP",
                    "verticalAlignment": "TOP",
                    "padding": {"top": 14, "bottom": 14, "left": 14, "right": 14},
                }},
                "fields": "userEnteredFormat(backgroundColor,wrapStrategy,verticalAlignment,padding)",
            }
        })
        # Source column: small grey caps for the variant tag
        requests.append({
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": row_idx, "endRowIndex": row_idx + 1, "startColumnIndex": 0, "endColumnIndex": 1},
                "cell": {"userEnteredFormat": {
                    "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.4, "green": 0.4, "blue": 0.45}},
                    "horizontalAlignment": "LEFT", "verticalAlignment": "TOP",
                }},
                "fields": "userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment)",
            }
        })
        # Approved checkbox
        requests.append({
            "setDataValidation": {
                "range": {"sheetId": sheet_id, "startRowIndex": row_idx, "endRowIndex": row_idx + 1, "startColumnIndex": 2, "endColumnIndex": 3},
                "rule": {"condition": {"type": "BOOLEAN"}, "strict": True, "showCustomUi": True},
            }
        })
        requests.append({
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": row_idx, "endRowIndex": row_idx + 1, "startColumnIndex": 2, "endColumnIndex": 3},
                "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"}},
                "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment)",
            }
        })
        # Landing page column — blue underlined link styling
        requests.append({
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": row_idx, "endRowIndex": row_idx + 1, "startColumnIndex": 4, "endColumnIndex": 5},
                "cell": {"userEnteredFormat": {
                    "wrapStrategy": "WRAP",
                    "verticalAlignment": "TOP",
                    "padding": {"top": 14, "bottom": 14, "left": 12, "right": 12},
                    "textFormat": {"fontSize": 10, "foregroundColor": {"red": 0.1, "green": 0.4, "blue": 0.7}, "underline": True},
                }},
                "fields": "userEnteredFormat(wrapStrategy,verticalAlignment,padding,textFormat)",
            }
        })

    # Apply text format runs to the Ad column (col index 1)
    fmt_for_kind = {
        "label": LABEL_FMT,
        "gap_small": GAP_FMT,
        "gap": GAP_FMT,
        "body": BODY_FMT,
        "headline": HEADLINE_FMT,
        "desc": DESC_FMT,
    }

    for meta in ad_meta:
        runs = []
        prev_kind = None
        for o in meta["offsets"]:
            if o["kind"] != prev_kind:
                runs.append({"startIndex": o["start"], "format": fmt_for_kind[o["kind"]]})
                prev_kind = o["kind"]
        requests.append({
            "updateCells": {
                "rows": [{"values": [{"textFormatRuns": runs}]}],
                "fields": "textFormatRuns",
                "range": {"sheetId": sheet_id, "startRowIndex": meta["row"], "endRowIndex": meta["row"] + 1, "startColumnIndex": 1, "endColumnIndex": 2},
            }
        })

    # Column widths
    for i, w in enumerate(COL_WIDTHS):
        requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
                "properties": {"pixelSize": w},
                "fields": "pixelSize",
            }
        })
    # Header row a touch taller
    requests.append({
        "updateDimensionProperties": {
            "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
            "properties": {"pixelSize": 40},
            "fields": "pixelSize",
        }
    })

    sh.batch_update({"requests": requests})

    # Auto-resize all data rows AFTER format requests (separate batch — measuring
    # unformatted text height in the same batch yields rows that snap too short).
    if data_rows:
        rmin = min(data_rows)
        rmax = max(data_rows) + 1
        sh.batch_update({"requests": [{
            "autoResizeDimensions": {
                "dimensions": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": rmin, "endIndex": rmax}
            }
        }]})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--share-with", default=",".join(DEFAULT_SHARE),
                        help="Comma-separated emails to add as editors (notify=False).")
    parser.add_argument("--landing-url", default=DEFAULT_LANDING)
    parser.add_argument("--max-variants", type=int, default=3,
                        help="Max non-seed variants to include (default 3).")
    parser.add_argument("--title", default=DEFAULT_TITLE)
    args = parser.parse_args()

    print(f"Loading seed + variants (max {args.max_variants})...")
    ads = load_ads(args.max_variants)
    print(f"Loaded {len(ads)} ads:")
    for ad in ads:
        print(f"  - {ad.get('_source_label','')} | {ad.get('headline','')[:60]}")

    print(f"\nCreating Sheet: {args.title}")
    gc = get_client()
    sh = gc.create(args.title)
    print(f"  spreadsheet_id: {sh.id}")

    build_sheet(sh, ads, args.landing_url)

    for email in [e.strip() for e in args.share_with.split(",") if e.strip()]:
        sh.share(email, perm_type="user", role="writer", notify=False)
        print(f"  shared with: {email}")

    url = f"https://docs.google.com/spreadsheets/d/{sh.id}/edit"
    print(f"\nDone: {url}")
    return url


if __name__ == "__main__":
    main()
