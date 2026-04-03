#!/usr/bin/env python3
"""Build an interactive HTML review page from scored content JSON."""

import json
import sys
from pathlib import Path
from datetime import datetime


def build_html(scored_json_path: str, output_path: str):
    with open(scored_json_path) as f:
        data = json.load(f)

    results = data["results"]
    summary = data["summary"]

    # Load the actual ad content for display
    root = Path(__file__).parent.parent
    ads_by_id = {}
    for r in results:
        file_path = root / r["_file"]
        if file_path.exists():
            with open(file_path) as f:
                ads_by_id[r["ad_id"]] = json.load(f)

    cards_html = []
    for r in results:
        ad_id = r["ad_id"]
        ad = ads_by_id.get(ad_id, {})
        content_type = r.get("content_type", "meta-ad")
        angle = r.get("angle", "")
        verdict = r["verdict"]
        composite = r["composite"]
        headline = r.get("headline", "")
        primary = r.get("primary_text", "")

        # Verdict badge color
        colors = {
            "production_ready": "#22c55e",
            "strong_draft": "#3b82f6",
            "needs_work": "#f59e0b",
            "rewrite": "#ef4444",
        }
        badge_color = colors.get(verdict, "#6b7280")

        # Build failure list
        failures_html = ""
        rule_failures = r.get("rule_compliance", {}).get("failures", [])
        if rule_failures:
            items = "".join(
                f'<li class="fail-item {"critical" if f["severity"]=="critical" else ""}">'
                f'[{f["severity"].upper()}] {f["rule_id"]}: {_esc(f["detail"][:120])}</li>'
                for f in rule_failures
            )
            failures_html = f'<ul class="failures">{items}</ul>'

        fact_details = r.get("fact_accuracy", {}).get("details", [])
        if fact_details:
            items = "".join(
                f'<li class="fact-{d["status"]}">[{d["status"].upper()}] {_esc(d["claim"][:80])}</li>'
                for d in fact_details
            )
            failures_html += f'<ul class="facts">{items}</ul>'

        # Rubric dimensions
        dims_html = ""
        for dim_id, detail in r.get("rubric", {}).get("dimension_details", {}).items():
            bar_width = detail["score"] * 20
            dims_html += (
                f'<div class="dim-row">'
                f'<span class="dim-name">{dim_id}</span>'
                f'<div class="dim-bar"><div class="dim-fill" style="width:{bar_width}%"></div></div>'
                f'<span class="dim-score">{detail["score"]}/5</span>'
                f'</div>'
            )

        # Full content display
        if content_type == "meta-ad":
            content_html = f"""
            <div class="content-preview">
                <div class="field"><label>Headline:</label> {_esc(ad.get("headline", ""))}</div>
                <div class="field"><label>Primary text:</label><pre>{_esc(ad.get("primary_text", ""))}</pre></div>
                <div class="field"><label>Description:</label> {_esc(ad.get("description", ""))}</div>
                <div class="field"><label>CTA:</label> {_esc(ad.get("cta", ""))}</div>
            </div>"""
        elif content_type == "email":
            content_html = f"""
            <div class="content-preview">
                <div class="field"><label>Subject:</label> {_esc(ad.get("subject", ""))}</div>
                <div class="field"><label>Preheader:</label> {_esc(ad.get("preheader", ""))}</div>
                <div class="field"><label>Body:</label><pre>{_esc(ad.get("body", ""))}</pre></div>
                <div class="field"><label>CTA:</label> {_esc(ad.get("cta", ""))}</div>
                <div class="field"><label>Sender:</label> {_esc(ad.get("sender_name", ""))}</div>
            </div>"""
        else:  # landing-page
            sections_text = ""
            for s in ad.get("sections", []):
                if isinstance(s, dict):
                    sections_text += f"\n\n## {s.get('heading', '')}\n{s.get('body', '')}"
            content_html = f"""
            <div class="content-preview">
                <div class="field"><label>Headline:</label> {_esc(ad.get("headline", ""))}</div>
                <div class="field"><label>Subhead:</label> {_esc(ad.get("subhead", ""))}</div>
                <div class="field"><label>Hero copy:</label><pre>{_esc(ad.get("hero_copy", ""))}</pre></div>
                <div class="field"><label>Sections:</label><pre>{_esc(sections_text)}</pre></div>
                <div class="field"><label>CTA:</label> {_esc(ad.get("cta", ""))}</div>
            </div>"""

        card = f"""
        <div class="card" data-verdict="{verdict}" data-type="{content_type}" data-angle="{angle}" data-id="{ad_id}">
            <div class="card-header" onclick="toggleCard(this)">
                <span class="card-id">{ad_id}</span>
                <span class="badge" style="background:{badge_color}">{verdict.replace("_"," ").upper()}</span>
                <span class="composite">{composite:.3f}</span>
                <span class="type-tag">{content_type}</span>
                <span class="angle-tag">{angle}</span>
                <span class="headline-preview">{_esc(headline[:50])}</span>
                <div class="status-buttons">
                    <button class="btn-approve" onclick="setStatus(event,'{ad_id}','approved')">Approve</button>
                    <button class="btn-revise" onclick="setStatus(event,'{ad_id}','revise')">Revise</button>
                    <button class="btn-kill" onclick="setStatus(event,'{ad_id}','kill')">Kill</button>
                </div>
            </div>
            <div class="card-body" style="display:none">
                {content_html}
                <div class="scoring-details">
                    <h4>Rubric scores</h4>
                    {dims_html}
                    {failures_html}
                </div>
                <div class="notes-section">
                    <label>Notes:</label>
                    <textarea class="notes" data-id="{ad_id}" placeholder="Add review notes..."></textarea>
                </div>
            </div>
        </div>"""
        cards_html.append(card)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FarmThru Round 3 Review</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; color: #1a1a1a; padding: 20px; }}
.header {{ max-width: 1200px; margin: 0 auto 20px; }}
.header h1 {{ font-size: 24px; margin-bottom: 8px; }}
.summary {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 16px; }}
.summary-card {{ background: white; border-radius: 8px; padding: 12px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.summary-card .label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
.summary-card .value {{ font-size: 24px; font-weight: 700; }}
.filters {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }}
.filters select, .filters button {{ padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px; background: white; cursor: pointer; }}
.filters button.active {{ background: #2563eb; color: white; border-color: #2563eb; }}
.cards {{ max-width: 1200px; margin: 0 auto; }}
.card {{ background: white; border-radius: 8px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; }}
.card.status-approved {{ border-left: 4px solid #22c55e; }}
.card.status-revise {{ border-left: 4px solid #f59e0b; }}
.card.status-kill {{ border-left: 4px solid #ef4444; }}
.card-header {{ display: flex; align-items: center; gap: 8px; padding: 12px 16px; cursor: pointer; flex-wrap: wrap; }}
.card-header:hover {{ background: #f1f5f9; }}
.card-id {{ font-weight: 700; font-size: 14px; min-width: 70px; }}
.badge {{ color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
.composite {{ font-family: monospace; font-size: 14px; min-width: 50px; }}
.type-tag {{ background: #e2e8f0; padding: 2px 6px; border-radius: 3px; font-size: 11px; }}
.angle-tag {{ background: #fef3c7; padding: 2px 6px; border-radius: 3px; font-size: 11px; }}
.headline-preview {{ color: #666; font-size: 13px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.status-buttons {{ display: flex; gap: 4px; margin-left: auto; }}
.status-buttons button {{ padding: 4px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; cursor: pointer; background: white; }}
.btn-approve:hover, .btn-approve.active {{ background: #22c55e; color: white; border-color: #22c55e; }}
.btn-revise:hover, .btn-revise.active {{ background: #f59e0b; color: white; border-color: #f59e0b; }}
.btn-kill:hover, .btn-kill.active {{ background: #ef4444; color: white; border-color: #ef4444; }}
.card-body {{ padding: 16px; border-top: 1px solid #eee; }}
.content-preview {{ margin-bottom: 16px; }}
.field {{ margin-bottom: 8px; }}
.field label {{ font-weight: 600; font-size: 12px; color: #666; text-transform: uppercase; display: block; }}
.field pre {{ white-space: pre-wrap; font-family: inherit; font-size: 14px; line-height: 1.5; margin-top: 4px; background: #f8f9fa; padding: 8px; border-radius: 4px; }}
.scoring-details {{ margin-top: 12px; }}
.scoring-details h4 {{ font-size: 13px; margin-bottom: 8px; color: #666; }}
.dim-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }}
.dim-name {{ font-size: 12px; min-width: 160px; color: #444; }}
.dim-bar {{ flex: 1; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }}
.dim-fill {{ height: 100%; background: #3b82f6; border-radius: 4px; transition: width 0.3s; }}
.dim-score {{ font-size: 12px; min-width: 30px; text-align: right; font-family: monospace; }}
.failures {{ list-style: none; margin-top: 8px; }}
.fail-item {{ padding: 4px 8px; margin-bottom: 2px; background: #fef2f2; border-radius: 3px; font-size: 12px; color: #991b1b; }}
.fail-item.critical {{ background: #fee2e2; font-weight: 600; }}
.facts {{ list-style: none; margin-top: 4px; }}
.fact-verified {{ color: #166534; font-size: 12px; padding: 2px 8px; }}
.fact-unverified {{ color: #92400e; font-size: 12px; padding: 2px 8px; background: #fffbeb; }}
.fact-contradicted {{ color: #991b1b; font-size: 12px; padding: 2px 8px; background: #fef2f2; font-weight: 600; }}
.notes-section {{ margin-top: 12px; }}
.notes-section label {{ font-size: 12px; color: #666; font-weight: 600; }}
.notes {{ width: 100%; height: 60px; margin-top: 4px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-family: inherit; font-size: 13px; resize: vertical; }}
.actions {{ max-width: 1200px; margin: 20px auto; display: flex; gap: 8px; }}
.actions button {{ padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; }}
.btn-save {{ background: #2563eb; color: white; }}
.btn-export {{ background: #059669; color: white; }}
.btn-expand {{ background: #6b7280; color: white; }}
.counter {{ max-width: 1200px; margin: 0 auto 16px; font-size: 13px; color: #666; }}
</style>
</head>
<body>
<div class="header">
    <h1>FarmThru Round 3 Review</h1>
    <p style="color:#666;font-size:13px">Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} | {summary['total']} items</p>
    <div class="summary">
        <div class="summary-card"><div class="label">Total</div><div class="value">{summary['total']}</div></div>
        <div class="summary-card"><div class="label">Avg Score</div><div class="value">{summary['avg_composite']:.3f}</div></div>
        <div class="summary-card"><div class="label">Critical Fails</div><div class="value" style="color:{'#ef4444' if summary['critical_failures'] > 0 else '#22c55e'}">{summary['critical_failures']}</div></div>
        <div class="summary-card"><div class="label">Production Ready</div><div class="value" style="color:#22c55e">{summary['verdicts'].get('production_ready', 0)}</div></div>
        <div class="summary-card"><div class="label">Strong Draft</div><div class="value" style="color:#3b82f6">{summary['verdicts'].get('strong_draft', 0)}</div></div>
        <div class="summary-card"><div class="label">Needs Work</div><div class="value" style="color:#f59e0b">{summary['verdicts'].get('needs_work', 0)}</div></div>
        <div class="summary-card"><div class="label">Rewrite</div><div class="value" style="color:#ef4444">{summary['verdicts'].get('rewrite', 0)}</div></div>
    </div>
    <div class="filters">
        <select id="filterType" onchange="filterCards()">
            <option value="all">All types</option>
            <option value="meta-ad">Meta ads</option>
            <option value="landing-page">Landing pages</option>
            <option value="email">Emails</option>
        </select>
        <select id="filterVerdict" onchange="filterCards()">
            <option value="all">All verdicts</option>
            <option value="production_ready">Production ready</option>
            <option value="strong_draft">Strong draft</option>
            <option value="needs_work">Needs work</option>
            <option value="rewrite">Rewrite</option>
        </select>
        <select id="filterStatus" onchange="filterCards()">
            <option value="all">All statuses</option>
            <option value="approved">Approved</option>
            <option value="revise">Revise</option>
            <option value="kill">Kill</option>
            <option value="unreviewed">Unreviewed</option>
        </select>
        <button class="btn-expand" onclick="expandAll()">Expand all</button>
        <button class="btn-expand" onclick="collapseAll()">Collapse all</button>
    </div>
</div>
<div class="counter" id="counter"></div>
<div class="cards" id="cards">
    {"".join(cards_html)}
</div>
<div class="actions">
    <button class="btn-save" onclick="saveJSON()">Save review JSON</button>
    <button class="btn-export" onclick="exportCSV()">Export CSV</button>
</div>
<script>
const statuses = {{}};
const notes = {{}};

function toggleCard(header) {{
    const body = header.nextElementSibling;
    body.style.display = body.style.display === 'none' ? 'block' : 'none';
}}

function setStatus(e, id, status) {{
    e.stopPropagation();
    statuses[id] = status;
    const card = document.querySelector(`[data-id="${{id}}"]`);
    card.className = card.className.replace(/status-\\w+/g, '') + ` status-${{status}}`;
    // Update button states
    card.querySelectorAll('.status-buttons button').forEach(b => b.classList.remove('active'));
    e.target.classList.add('active');
    updateCounter();
}}

function filterCards() {{
    const type = document.getElementById('filterType').value;
    const verdict = document.getElementById('filterVerdict').value;
    const status = document.getElementById('filterStatus').value;
    document.querySelectorAll('.card').forEach(c => {{
        const matchType = type === 'all' || c.dataset.type === type;
        const matchVerdict = verdict === 'all' || c.dataset.verdict === verdict;
        const id = c.dataset.id;
        const matchStatus = status === 'all' ||
            (status === 'unreviewed' && !statuses[id]) ||
            statuses[id] === status;
        c.style.display = matchType && matchVerdict && matchStatus ? '' : 'none';
    }});
    updateCounter();
}}

function expandAll() {{ document.querySelectorAll('.card-body').forEach(b => b.style.display = 'block'); }}
function collapseAll() {{ document.querySelectorAll('.card-body').forEach(b => b.style.display = 'none'); }}

function updateCounter() {{
    const visible = document.querySelectorAll('.card:not([style*="display: none"])').length;
    const total = document.querySelectorAll('.card').length;
    const reviewed = Object.keys(statuses).length;
    document.getElementById('counter').textContent = `Showing ${{visible}}/${{total}} | Reviewed: ${{reviewed}}/${{total}} | Approved: ${{Object.values(statuses).filter(s=>s==='approved').length}} | Revise: ${{Object.values(statuses).filter(s=>s==='revise').length}} | Kill: ${{Object.values(statuses).filter(s=>s==='kill').length}}`;
}}

function saveJSON() {{
    // Collect notes from textareas
    document.querySelectorAll('.notes').forEach(n => {{
        if (n.value.trim()) notes[n.dataset.id] = n.value.trim();
    }});
    const data = {{ statuses, notes, exported: new Date().toISOString() }};
    const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'review-r3-decisions.json';
    a.click();
}}

function exportCSV() {{
    document.querySelectorAll('.notes').forEach(n => {{
        if (n.value.trim()) notes[n.dataset.id] = n.value.trim();
    }});
    let csv = 'id,type,angle,verdict,composite,status,notes\\n';
    document.querySelectorAll('.card').forEach(c => {{
        const id = c.dataset.id;
        csv += `${{id}},${{c.dataset.type}},${{c.dataset.angle}},${{c.dataset.verdict}},` +
               `${{c.querySelector('.composite').textContent}},${{statuses[id]||'unreviewed'}},` +
               `"${{(notes[id]||'').replace(/"/g,'""')}}"\\n`;
    }});
    const blob = new Blob([csv], {{type: 'text/csv'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'review-r3.csv';
    a.click();
}}

updateCounter();
</script>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    print(f"Review HTML written to {output_path}", file=sys.stderr)


def _esc(text):
    """HTML-escape text."""
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python build_review_html.py <scored.json> <output.html>", file=sys.stderr)
        sys.exit(1)
    build_html(sys.argv[1], sys.argv[2])
