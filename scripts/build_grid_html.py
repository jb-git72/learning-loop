#!/usr/bin/env python3
"""Build MAP-Elites grid coverage HTML from scored JSON + optional ROAS CSV.

Usage:
    python3 scripts/build_grid_html.py scored.json output.html
    python3 scripts/build_grid_html.py scored.json output.html --csv meta-export.csv --client tyroola
"""

import argparse
import csv
import json
import sys
from pathlib import Path

root = Path(__file__).parent.parent

COLUMN_ALIASES = {
    "ad_name": ["Ad name", "Ad Name", "ad_name", "Ad"],
    "spend": ["Amount spent (AUD)", "Amount spent (USD)", "Amount spent",
              "Spend", "spend", "Cost"],
    "revenue": ["Website purchases conversion value", "Conversion value",
                "revenue", "Revenue"],
    "purchases": ["Website purchases", "Purchases", "purchases", "Results"],
    "roas": ["Website purchase ROAS (return on advertising spend)",
             "Purchase ROAS", "ROAS"],
}


def _resolve_columns(header):
    clean = [h.strip() for h in header]
    mapping = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in clean:
                mapping[canonical] = clean.index(alias)
                break
    return mapping


def _parse_number(raw):
    if not raw or not raw.strip():
        return 0.0
    cleaned = raw.strip().replace("$", "").replace(",", "").replace("%", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def load_roas_from_csv(csv_path):
    """Load per-ad ROAS from CSV. Returns {ad_name: {roas, spend, revenue}}."""
    ads = {}
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        col_map = _resolve_columns(header)
        if "ad_name" not in col_map:
            return ads
        for row in reader:
            if not row or len(row) < 2:
                continue
            name = row[col_map["ad_name"]].strip()
            if not name or name in ads:
                continue
            roas = _parse_number(row[col_map["roas"]]) if "roas" in col_map else 0
            spend = _parse_number(row[col_map["spend"]]) if "spend" in col_map else 0
            revenue = _parse_number(row[col_map["revenue"]]) if "revenue" in col_map else 0
            purchases = _parse_number(row[col_map["purchases"]]) if "purchases" in col_map else 0
            if roas == 0 and spend > 0:
                roas = revenue / spend
            ads[name] = {"roas": roas, "spend": spend, "revenue": revenue, "purchases": purchases}
    return ads


def build_grid_data(scored_path, roas_data=None):
    """Build grid data from scored JSON."""
    with open(scored_path) as f:
        data = json.load(f)
    results = data if isinstance(data, list) else data.get("results", [])

    angles = set()
    hooks = set()
    cells = {}
    # Track aggregates per cell (sum across all ads)
    cell_agg = {}

    for ad in results:
        angle = ad.get("angle", "?")
        hook = ad.get("hook_type", "?")
        composite = ad.get("composite", 0)
        ad_id = ad.get("ad_id", "?")
        original_name = ad.get("original_ad_name", "")

        if angle == "?" or hook == "?":
            continue

        angles.add(angle)
        hooks.add(hook)
        key = f"{angle}|{hook}"

        # Aggregate revenue/spend/purchases across all ads in cell
        if key not in cell_agg:
            cell_agg[key] = {"total_revenue": 0, "total_spend": 0,
                             "total_purchases": 0, "ad_count": 0}
        if roas_data and original_name in roas_data:
            r = roas_data[original_name]
            cell_agg[key]["total_revenue"] += r.get("revenue", 0)
            cell_agg[key]["total_spend"] += r.get("spend", 0)
            cell_agg[key]["total_purchases"] += r.get("purchases", 0)
        cell_agg[key]["ad_count"] += 1

        # Keep best score per cell
        if key not in cells or composite > cells[key]["score"]:
            cell = {"score": round(composite, 4), "ad_id": ad_id}

            # Add ROAS if available
            if roas_data and original_name in roas_data:
                r = roas_data[original_name]
                cell["roas"] = round(r["roas"], 2)
                cell["spend"] = round(r["spend"], 2)

            cells[key] = cell

    # Merge aggregates into cells
    for key, agg in cell_agg.items():
        if key in cells:
            cells[key]["total_revenue"] = round(agg["total_revenue"], 2)
            cells[key]["total_spend"] = round(agg["total_spend"], 2)
            cells[key]["total_purchases"] = int(agg["total_purchases"])
            cells[key]["ad_count"] = agg["ad_count"]

    return {
        "angles": sorted(angles),
        "hooks": sorted(hooks),
        "cells": cells,
    }


def build_html(grid_data, client_name="Client"):
    """Build the grid coverage HTML."""
    data_json = json.dumps(grid_data)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>MAP-Elites Grid Coverage — {client_name}</title>
<style>
  body {{ background: #0d1117; color: #c9d1d9; font-family: 'SF Mono', monospace; padding: 32px; }}
  h1 {{ color: #e6edf3; font-size: 22px; margin-bottom: 4px; }}
  .subtitle {{ color: #8b949e; font-size: 13px; margin-bottom: 24px; }}
  .stats {{ display: flex; gap: 24px; margin-bottom: 24px; flex-wrap: wrap; }}
  .stat {{ background: #161b22; border: 1px solid #21262d; border-radius: 8px; padding: 16px 20px; }}
  .stat .value {{ font-size: 28px; font-weight: 700; color: #e6edf3; }}
  .stat .label {{ font-size: 12px; color: #8b949e; margin-top: 4px; }}
  table {{ border-collapse: collapse; margin-top: 16px; }}
  th {{ padding: 8px 6px; font-size: 11px; color: #8b949e; text-align: center; transform: rotate(-45deg); white-space: nowrap; height: 80px; }}
  th.row-header {{ transform: none; text-align: right; padding-right: 12px; font-size: 12px; color: #c9d1d9; }}
  td {{ width: 52px; height: 40px; text-align: center; font-size: 11px; font-weight: 600; border: 1px solid #21262d; cursor: default; }}
  td.empty {{ background: #161b22; color: #484f58; }}
  td.low {{ background: #3d1e1e; color: #f85149; }}
  td.mid {{ background: #2d2a0e; color: #d29922; }}
  td.good {{ background: #0e2d1e; color: #3fb950; }}
  td.great {{ background: #1a4d2e; color: #56d364; }}
  .legend {{ display: flex; gap: 16px; margin-top: 20px; font-size: 12px; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; }}
  .legend-swatch {{ width: 16px; height: 16px; border-radius: 3px; }}
  .tooltip {{ position: absolute; background: #1c2128; border: 1px solid #30363d; border-radius: 6px; padding: 8px 12px; font-size: 12px; pointer-events: none; display: none; z-index: 10; white-space: pre-line; }}
  .toggle {{ margin: 16px 0; }}
  .toggle button {{ background: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 12px; margin-right: 8px; }}
  .toggle button.active {{ background: #1f6feb; border-color: #388bfd; }}
</style>
</head>
<body>
<h1>MAP-Elites Grid Coverage</h1>
<div class="subtitle">{client_name} — angle x hook heatmap (quality scores from classified Meta ads)</div>
<div class="stats" id="stats"></div>
<div class="toggle" id="toggles">
  <button class="active" onclick="setMode('score')">Quality Score</button>
  <button onclick="setMode('roas')">ROAS</button>
  <button onclick="setMode('revenue')">Revenue</button>
</div>
<table id="grid"></table>
<div class="legend" id="legend"></div>
<div class="tooltip" id="tooltip"></div>

<script>
const DATA = {data_json};
const angles = DATA.angles;
const hooks = DATA.hooks;
const cells = DATA.cells;
let mode = 'score';

const total = angles.length * hooks.length;
const filled = Object.keys(cells).length;
const scores = Object.values(cells).map(c => c.score);
const avg = scores.length ? scores.reduce((a,b) => a+b, 0) / scores.length : 0;
const hasRoas = Object.values(cells).some(c => c.roas !== undefined);
const roasValues = Object.values(cells).filter(c => c.roas).map(c => c.roas);
const avgRoas = roasValues.length ? roasValues.reduce((a,b) => a+b, 0) / roasValues.length : 0;
const hasRevenue = Object.values(cells).some(c => c.total_revenue > 0);
const totalRevenue = Object.values(cells).reduce((s, c) => s + (c.total_revenue || 0), 0);
const totalSpend = Object.values(cells).reduce((s, c) => s + (c.total_spend || 0), 0);

document.getElementById('stats').innerHTML = `
  <div class="stat"><div class="value">${{filled}}/${{total}}</div><div class="label">Cells filled (${{Math.round(filled/total*100)}}%)</div></div>
  <div class="stat"><div class="value">${{avg.toFixed(3)}}</div><div class="label">Avg quality score</div></div>
  ${{hasRoas ? `<div class="stat"><div class="value">${{avgRoas.toFixed(1)}}x</div><div class="label">Avg ROAS</div></div>` : ''}}
  ${{hasRevenue ? `<div class="stat"><div class="value">$${{totalRevenue.toLocaleString(undefined, {{maximumFractionDigits:0}})}}</div><div class="label">Total revenue</div></div>` : ''}}
  ${{hasRevenue ? `<div class="stat"><div class="value">$${{totalSpend.toLocaleString(undefined, {{maximumFractionDigits:0}})}}</div><div class="label">Total spend</div></div>` : ''}}
  <div class="stat"><div class="value">${{total - filled}}</div><div class="label">Empty cells</div></div>
`;

if (!hasRoas && !hasRevenue) document.getElementById('toggles').style.display = 'none';

function setMode(m) {{
  mode = m;
  document.querySelectorAll('.toggle button').forEach(b => b.classList.remove('active'));
  document.querySelector(`.toggle button[onclick="setMode('${{m}}')"]`).classList.add('active');
  renderGrid();
  renderLegend();
}}

function renderLegend() {{
  const leg = document.getElementById('legend');
  if (mode === 'score') {{
    leg.innerHTML = `
      <div class="legend-item"><div class="legend-swatch" style="background:#161b22"></div> Empty</div>
      <div class="legend-item"><div class="legend-swatch" style="background:#3d1e1e"></div> &lt;0.50</div>
      <div class="legend-item"><div class="legend-swatch" style="background:#2d2a0e"></div> 0.50-0.69</div>
      <div class="legend-item"><div class="legend-swatch" style="background:#0e2d1e"></div> 0.70-0.84</div>
      <div class="legend-item"><div class="legend-swatch" style="background:#1a4d2e"></div> 0.85+</div>`;
  }} else if (mode === 'roas') {{
    leg.innerHTML = `
      <div class="legend-item"><div class="legend-swatch" style="background:#161b22"></div> No data</div>
      <div class="legend-item"><div class="legend-swatch" style="background:#3d1e1e"></div> &lt;5x</div>
      <div class="legend-item"><div class="legend-swatch" style="background:#2d2a0e"></div> 5-20x</div>
      <div class="legend-item"><div class="legend-swatch" style="background:#0e2d1e"></div> 20-50x</div>
      <div class="legend-item"><div class="legend-swatch" style="background:#1a4d2e"></div> 50x+</div>`;
  }} else {{
    leg.innerHTML = `
      <div class="legend-item"><div class="legend-swatch" style="background:#161b22"></div> No data</div>
      <div class="legend-item"><div class="legend-swatch" style="background:#3d1e1e"></div> &lt;$500</div>
      <div class="legend-item"><div class="legend-swatch" style="background:#2d2a0e"></div> $500-$2k</div>
      <div class="legend-item"><div class="legend-swatch" style="background:#0e2d1e"></div> $2k-$10k</div>
      <div class="legend-item"><div class="legend-swatch" style="background:#1a4d2e"></div> $10k+</div>`;
  }}
}}

function renderGrid() {{
  const table = document.getElementById('grid');
  let headerRow = '<tr><th class="row-header"></th>';
  hooks.forEach(h => {{ headerRow += `<th>${{h}}</th>`; }});
  headerRow += '</tr>';
  table.innerHTML = headerRow;

  angles.forEach(angle => {{
    let row = `<tr><th class="row-header">${{angle}}</th>`;
    hooks.forEach(hook => {{
      const key = `${{angle}}|${{hook}}`;
      const cell = cells[key];
      if (cell) {{
        let val, cls;
        if (mode === 'revenue' && cell.total_revenue > 0) {{
          const rev = cell.total_revenue;
          val = rev >= 1000 ? '$' + (rev/1000).toFixed(1) + 'k' : '$' + rev.toFixed(0);
          cls = rev >= 10000 ? 'great' : rev >= 2000 ? 'good' : rev >= 500 ? 'mid' : 'low';
        }} else if (mode === 'revenue') {{
          val = '-';
          cls = 'empty';
        }} else if (mode === 'roas' && cell.roas !== undefined) {{
          val = cell.roas.toFixed(1);
          cls = cell.roas >= 50 ? 'great' : cell.roas >= 20 ? 'good' : cell.roas >= 5 ? 'mid' : 'low';
        }} else if (mode === 'roas') {{
          val = '-';
          cls = 'empty';
        }} else {{
          val = cell.score.toFixed(2);
          cls = cell.score >= 0.85 ? 'great' : cell.score >= 0.70 ? 'good' : cell.score >= 0.50 ? 'mid' : 'low';
        }}
        const rev = cell.total_revenue || 0;
        const spend = cell.total_spend || 0;
        const info = `${{angle}} + ${{hook}}\\nQuality: ${{cell.score.toFixed(3)}}${{cell.roas !== undefined ? '\\nROAS: ' + cell.roas.toFixed(1) + 'x' : ''}}${{rev > 0 ? '\\nRevenue: $' + rev.toLocaleString(undefined, {{maximumFractionDigits:0}}) : ''}}${{spend > 0 ? '\\nSpend: $' + spend.toLocaleString(undefined, {{maximumFractionDigits:0}}) : ''}}${{cell.ad_count ? '\\nAds: ' + cell.ad_count : ''}}`;
        row += `<td class="${{cls}}" data-info="${{info}}">${{val}}</td>`;
      }} else {{
        row += '<td class="empty">-</td>';
      }}
    }});
    row += '</tr>';
    table.innerHTML += row;
  }});
}}

renderGrid();
renderLegend();

// Tooltip
const table = document.getElementById('grid');
const tooltip = document.getElementById('tooltip');
table.addEventListener('mouseover', e => {{
  if (e.target.dataset.info) {{ tooltip.textContent = e.target.dataset.info; tooltip.style.display = 'block'; }}
}});
table.addEventListener('mousemove', e => {{
  tooltip.style.left = (e.pageX + 12) + 'px'; tooltip.style.top = (e.pageY + 12) + 'px';
}});
table.addEventListener('mouseout', () => {{ tooltip.style.display = 'none'; }});
</script>
</body>
</html>"""


def parse_args():
    parser = argparse.ArgumentParser(description="Build MAP-Elites grid HTML")
    parser.add_argument("scored", help="Path to scored JSON")
    parser.add_argument("output", help="Output HTML path")
    parser.add_argument("--csv", default=None, help="Meta CSV for ROAS overlay")
    parser.add_argument("--client", default="Client", help="Client name for title")
    return parser.parse_args()


def main():
    args = parse_args()
    scored_path = Path(args.scored)

    roas_data = None
    if args.csv:
        roas_data = load_roas_from_csv(Path(args.csv))
        print(f"Loaded ROAS for {len(roas_data)} ads from CSV", file=sys.stderr)

    grid_data = build_grid_data(scored_path, roas_data)
    print(f"Grid: {len(grid_data['angles'])} angles x {len(grid_data['hooks'])} hooks = "
          f"{len(grid_data['angles']) * len(grid_data['hooks'])} cells, "
          f"{len(grid_data['cells'])} filled", file=sys.stderr)

    html = build_html(grid_data, args.client)
    Path(args.output).write_text(html)
    print(f"Written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
