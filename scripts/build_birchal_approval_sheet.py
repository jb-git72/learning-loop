#!/usr/bin/env python3
"""Build the Birchal CSF ad-copy approval Google Sheet.

This is the iteration sheet for Birchal Meta ad copy. JB ticks Approved /
leaves comments per row; copy is regenerated and a new tab is added on each
review pass. Same sheet across iterations -- never spawn orphans.

Default (no --sheet-id): creates a NEW spreadsheet and pushes BOTH tabs
("Bodies V1" + "Headlines V1") in one shot. Captures the new sheet ID into
clients/birchal/sheet-id.txt for subsequent runs.

With --sheet-id: adds ONE new tab to the existing sheet. Use --mode to pick
bodies (default) or headlines, and --tab-name to set the title.

Run:
    # First run -- creates sheet with both tabs
    python3 scripts/build_birchal_approval_sheet.py

    # Subsequent iteration -- add a new bodies tab to the same sheet
    python3 scripts/build_birchal_approval_sheet.py \\
        --sheet-id <ID> --tab-name "Bodies V2" --mode bodies

    # Subsequent iteration -- add a new headlines tab
    python3 scripts/build_birchal_approval_sheet.py \\
        --sheet-id <ID> --tab-name "Headlines V2" --mode headlines

Bodies tab: same Option-B layout as FMTH (yellow header, green section band,
single Ad column with PRIMARY TEXT / HEADLINE / DESCRIPTION labels, checkbox +
Comments + Landing-page columns, auto-fit row heights, angle-banded by segment).

Headlines tab: flat table (ID | Headline | Angle | Segment | Words | Approved
| Comments). Same yellow header, banded by angle category.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from build_fmth_approval_sheet import (
    build_sheet,
    get_client,
    HEADERS,
    YELLOW_HEADER,
    GREEN_BAND_DARK,
    ZEBRA,
    col_letter,
)

VARIANTS_DIR = REPO / "clients" / "birchal" / "loop" / "birchal-ad-variants"
HEADLINES_PATH = REPO / "clients" / "birchal" / "loop" / "birchal-headlines.json"
SHEET_ID_CACHE = REPO / "clients" / "birchal" / "sheet-id.txt"
DEFAULT_LANDING = "https://join.birchal.com/"
DEFAULT_SHARE = ["jeremy@launcherlab.com.au"]
DEFAULT_TITLE = f"Birchal CSF Ad Copy (iteration sheet, opened {datetime.now().strftime('%Y-%m-%d')})"

HEADLINES_HEADERS = ["ID", "Headline", "Angle", "Segment", "Words", "Approved", "Comments"]
HEADLINES_COL_WIDTHS = [110, 360, 220, 110, 80, 110, 320]


SEGMENT_BANDS = [
    ("A_first_time_csf", "Segment A -- First-time CSF investors"),
    ("B_existing_birchal_investors", "Segment B -- Existing Birchal investors"),
]


def load_ads() -> list[dict]:
    """Load every ad JSON in the variants dir, in summary.json order."""
    summary_path = VARIANTS_DIR / "summary.json"
    if summary_path.is_file():
        order = [r["ad_id"] for r in json.loads(summary_path.read_text()).get("results", [])]
    else:
        order = sorted(p.stem for p in VARIANTS_DIR.glob("*.json") if p.stem != "summary")

    ads = []
    for ad_id in order:
        p = VARIANTS_DIR / f"{ad_id}.json"
        if not p.is_file():
            print(f"  warn: missing {p.name}, skipping")
            continue
        ad = json.loads(p.read_text())
        ad["_source_label"] = ad.get("_source_label") or ad_id
        ads.append(ad)
    return ads


def build_bodies_with_segment_bands(sh, ads, landing_url, ws=None, tab_title=None):
    """Like build_sheet() but inserts a section band before each segment.

    The base build_sheet() inserts a single 'Pre-campaign waitlist' band; for
    Birchal we want one band per segment so JB can tick by segment cluster.
    Easiest path: regroup ads by segment and feed them in band-aware batches.
    """
    n = len(HEADERS)
    if ws is None:
        ws = sh.sheet1
        ws.update_title(tab_title or "Bodies V1")
    ws.resize(rows=400, cols=n)
    sheet_id = ws._properties["sheetId"]

    # Reuse imported format constants
    from build_fmth_approval_sheet import (
        LABEL_FMT, BODY_FMT, HEADLINE_FMT, DESC_FMT, GAP_FMT,
        LABEL_PT, LABEL_HL, LABEL_DS, COL_WIDTHS,
    )

    table = [HEADERS]
    section_rows: list[int] = []
    data_rows: list[int] = []
    ad_meta: list[dict] = []

    for seg_id, seg_label in SEGMENT_BANDS:
        seg_ads = [a for a in ads if a.get("segment") == seg_id]
        if not seg_ads:
            continue
        table.append([f"{seg_label}  ({len(seg_ads)} ad{'s' if len(seg_ads) != 1 else ''})"] + [""] * (n - 1))
        section_rows.append(len(table) - 1)
        for ad in seg_ads:
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

            offsets, cursor = [], 0
            for txt, kind in parts:
                offsets.append({"start": cursor, "kind": kind, "len": len(txt)})
                cursor += len(txt)
            ad_meta.append({"row": row_idx, "offsets": offsets})

    end_a1 = f"{col_letter(n)}{len(table)}"
    ws.update(values=table, range_name=f"A1:{end_a1}", value_input_option="USER_ENTERED")

    requests = []
    requests.append({
        "updateSheetProperties": {
            "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
            "fields": "gridProperties.frozenRowCount",
        }
    })
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

    fmt_for_kind = {
        "label": LABEL_FMT,
        "gap_small": GAP_FMT,
        "gap": GAP_FMT,
        "body": BODY_FMT,
        "headline": HEADLINE_FMT,
        "desc": DESC_FMT,
    }
    for meta in ad_meta:
        runs = [{"startIndex": o["start"], "format": fmt_for_kind[o["kind"]]} for o in meta["offsets"]]
        requests.append({
            "updateCells": {
                "range": {"sheetId": sheet_id, "startRowIndex": meta["row"], "endRowIndex": meta["row"] + 1, "startColumnIndex": 1, "endColumnIndex": 2},
                "rows": [{"values": [{"textFormatRuns": runs}]}],
                "fields": "textFormatRuns",
            }
        })

    for i, w in enumerate(COL_WIDTHS):
        requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
                "properties": {"pixelSize": w},
                "fields": "pixelSize",
            }
        })

    sh.batch_update({"requests": requests})

    # Auto-resize rows AFTER formatting (separate call -- ordering matters)
    if data_rows:
        sh.batch_update({"requests": [{
            "autoResizeDimensions": {
                "dimensions": {"sheetId": sheet_id, "dimension": "ROWS",
                               "startIndex": min(data_rows), "endIndex": max(data_rows) + 1},
            }
        }]})


ANGLE_BANDS = [
    ("curiosity / mechanism", "Curiosity / mechanism (FMTH-validated curiosity hook)"),
    ("curiosity / specificity", "Curiosity / specificity"),
    ("curiosity / question", "Curiosity / question"),
    ("curiosity / social proof", "Curiosity / social proof"),
    ("curiosity / loss frame", "Curiosity / loss frame"),
    ("belonging / identity", "Belonging / identity"),
    ("belonging / co-ownership", "Belonging / co-ownership"),
    ("belonging / recursion", "Belonging / recursion"),
    ("belonging / cadence-of-three", "Belonging / cadence of three"),
    ("empathy / access", "Empathy / access"),
    ("investor-validation / peer", "Investor-validation / peer"),
    ("investor-validation / authority", "Investor-validation / authority"),
]


def build_headlines_sheet(sh, headlines, ws=None, tab_title=None):
    """Flat-table layout for headlines: ID | Headline | Angle | Segment |
    Words | Approved | Comments. Banded by angle category."""
    n = len(HEADLINES_HEADERS)
    if ws is None:
        ws = sh.sheet1
        ws.update_title(tab_title or "Headlines V1")
    ws.resize(rows=200, cols=n)
    sheet_id = ws._properties["sheetId"]

    # Group headlines by angle category (curiosity / belonging / empathy / investor-validation)
    def angle_category(angle: str) -> str:
        a = angle.split("/")[0].strip().lower()
        return a

    categories = ["curiosity", "belonging", "empathy", "investor-validation"]
    cat_label = {
        "curiosity": "Curiosity-led (FMTH-validated +0.18 composite over founder-voice)",
        "belonging": "Belonging / community-led",
        "empathy": "Empathy / access-led",
        "investor-validation": "Investor-validation / peer-led",
    }

    table = [HEADLINES_HEADERS]
    section_rows: list[int] = []
    data_rows: list[int] = []
    for cat in categories:
        cat_hls = [h for h in headlines if angle_category(h["angle"]) == cat]
        if not cat_hls:
            continue
        table.append([cat_label[cat]] + [""] * (n - 1))
        section_rows.append(len(table) - 1)
        for h in cat_hls:
            table.append([
                h["id"],
                h["text"],
                h["angle"],
                h["segment"],
                h["words"],
                False,
                "",
            ])
            data_rows.append(len(table) - 1)

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
    # Section bands (angle-grouped)
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
                    "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                    "horizontalAlignment": "LEFT", "verticalAlignment": "MIDDLE",
                    "padding": {"top": 6, "bottom": 6, "left": 12, "right": 12},
                }},
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,padding)",
            }
        })
    # Data rows
    for i, row_idx in enumerate(data_rows):
        bg = ZEBRA if i % 2 == 1 else {"red": 1, "green": 1, "blue": 1}
        requests.append({
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": row_idx, "endRowIndex": row_idx + 1, "startColumnIndex": 0, "endColumnIndex": n},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": bg,
                    "wrapStrategy": "WRAP",
                    "verticalAlignment": "MIDDLE",
                    "padding": {"top": 8, "bottom": 8, "left": 12, "right": 12},
                }},
                "fields": "userEnteredFormat(backgroundColor,wrapStrategy,verticalAlignment,padding)",
            }
        })
        # Headline column (B): bold 13pt
        requests.append({
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": row_idx, "endRowIndex": row_idx + 1, "startColumnIndex": 1, "endColumnIndex": 2},
                "cell": {"userEnteredFormat": {
                    "textFormat": {"bold": True, "fontSize": 13, "foregroundColor": {"red": 0.1, "green": 0.1, "blue": 0.1}},
                    "verticalAlignment": "MIDDLE",
                }},
                "fields": "userEnteredFormat(textFormat,verticalAlignment)",
            }
        })
        # ID, Angle, Segment, Words columns: small grey
        for col_start, col_end in [(0, 1), (2, 3), (3, 4), (4, 5)]:
            requests.append({
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": row_idx, "endRowIndex": row_idx + 1, "startColumnIndex": col_start, "endColumnIndex": col_end},
                    "cell": {"userEnteredFormat": {
                        "textFormat": {"fontSize": 10, "foregroundColor": {"red": 0.4, "green": 0.4, "blue": 0.45}},
                        "verticalAlignment": "MIDDLE",
                    }},
                    "fields": "userEnteredFormat(textFormat,verticalAlignment)",
                }
            })
        # Approved checkbox (col F = index 5)
        requests.append({
            "setDataValidation": {
                "range": {"sheetId": sheet_id, "startRowIndex": row_idx, "endRowIndex": row_idx + 1, "startColumnIndex": 5, "endColumnIndex": 6},
                "rule": {"condition": {"type": "BOOLEAN"}, "strict": True, "showCustomUi": True},
            }
        })
        requests.append({
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": row_idx, "endRowIndex": row_idx + 1, "startColumnIndex": 5, "endColumnIndex": 6},
                "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"}},
                "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment)",
            }
        })

    # Column widths
    for i, w in enumerate(HEADLINES_COL_WIDTHS):
        requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
                "properties": {"pixelSize": w},
                "fields": "pixelSize",
            }
        })

    sh.batch_update({"requests": requests})

    # Auto-resize rows after formatting
    if data_rows:
        sh.batch_update({"requests": [{
            "autoResizeDimensions": {
                "dimensions": {"sheetId": sheet_id, "dimension": "ROWS",
                               "startIndex": min(data_rows), "endIndex": max(data_rows) + 1},
            }
        }]})


def main() -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument("--share-with", default=",".join(DEFAULT_SHARE))
    parser.add_argument("--landing-url", default=DEFAULT_LANDING)
    parser.add_argument("--title", default=DEFAULT_TITLE)
    parser.add_argument("--sheet-id", default=None,
                        help="Existing Birchal sheet ID. Adds a new tab instead of creating a new sheet.")
    parser.add_argument("--tab-name", default=None,
                        help="Tab title when using --sheet-id.")
    parser.add_argument("--mode", choices=["bodies", "headlines", "both"], default=None,
                        help="Push bodies, headlines, or both. Default: 'both' for new sheet, 'bodies' for --sheet-id.")
    args = parser.parse_args()

    mode = args.mode
    if mode is None:
        mode = "both" if not args.sheet_id else "bodies"

    if args.sheet_id and not args.tab_name and mode != "both":
        sys.exit("--tab-name is required when --sheet-id is set.")

    if mode in ("bodies", "both"):
        ads = load_ads()
        if not ads:
            sys.exit(f"No ads in {VARIANTS_DIR}")
        print(f"Loaded {len(ads)} ad bodies:")
        for ad in ads:
            print(f"  - {ad.get('_source_label','')} | {ad.get('headline','')[:60]}")

    if mode in ("headlines", "both"):
        if not HEADLINES_PATH.is_file():
            sys.exit(f"No headlines file at {HEADLINES_PATH}")
        headlines = json.loads(HEADLINES_PATH.read_text())["headlines"]
        print(f"Loaded {len(headlines)} headlines.")

    gc = get_client()

    if args.sheet_id:
        sh = gc.open_by_key(args.sheet_id)
        print(f"\nUsing existing sheet: {sh.title}")
    else:
        print(f"\nCreating new sheet: {args.title}")
        sh = gc.create(args.title)
        print(f"  spreadsheet_id: {sh.id}")
        SHEET_ID_CACHE.parent.mkdir(parents=True, exist_ok=True)
        SHEET_ID_CACHE.write_text(sh.id + "\n")
        print(f"  cached id -> {SHEET_ID_CACHE}")

    if mode == "both":
        # Write Bodies into sheet1 (rename), then add Headlines as a new ws
        build_bodies_with_segment_bands(sh, ads, args.landing_url, tab_title="Bodies V1")
        ws_h = sh.add_worksheet(title="Headlines V1", rows=200, cols=len(HEADLINES_HEADERS))
        build_headlines_sheet(sh, headlines, ws=ws_h, tab_title="Headlines V1")
    elif mode == "bodies":
        if args.sheet_id:
            existing = [w.title for w in sh.worksheets()]
            if args.tab_name in existing:
                sys.exit(f"Tab {args.tab_name!r} already exists.")
            ws = sh.add_worksheet(title=args.tab_name, rows=400, cols=len(HEADERS))
            build_bodies_with_segment_bands(sh, ads, args.landing_url, ws=ws, tab_title=args.tab_name)
        else:
            build_bodies_with_segment_bands(sh, ads, args.landing_url, tab_title="Bodies V1")
    elif mode == "headlines":
        if args.sheet_id:
            existing = [w.title for w in sh.worksheets()]
            if args.tab_name in existing:
                sys.exit(f"Tab {args.tab_name!r} already exists.")
            ws = sh.add_worksheet(title=args.tab_name, rows=200, cols=len(HEADLINES_HEADERS))
            build_headlines_sheet(sh, headlines, ws=ws, tab_title=args.tab_name)
        else:
            build_headlines_sheet(sh, headlines, tab_title="Headlines V1")

    for email in [e.strip() for e in args.share_with.split(",") if e.strip()]:
        try:
            sh.share(email, perm_type="user", role="writer", notify=False)
        except Exception:
            pass

    url = f"https://docs.google.com/spreadsheets/d/{sh.id}/edit"
    print(f"\nDone: {url}")
    return url


if __name__ == "__main__":
    main()
