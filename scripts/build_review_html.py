#!/usr/bin/env python3
"""Build an interactive HTML review page matching the proven loop-review layout."""

import json
import sys
from pathlib import Path
from datetime import datetime


def build_html(scored_json_path: str, output_path: str):
    with open(scored_json_path) as f:
        data = json.load(f)

    results = data["results"]
    summary = data["summary"]

    root = Path(__file__).parent.parent

    cards_html = []
    for r in results:
        # Load ad directly from its file path (most reliable)
        fp = root / r["_file"]
        if fp.exists():
            with open(fp) as f:
                ad = json.load(f)
        else:
            ad = {}

        ad_id = ad.get("ad_id", ad.get("page_id", ad.get("email_id", "unknown")))
        content_type = ad.get("content_type", r.get("content_type", "meta-ad"))
        angle = ad.get("angle", r.get("angle", ""))
        hook_type = ad.get("hook_type", "")
        tactic = ad.get("tactic", "")
        funnel = ad.get("funnel", "")
        verdict = r["verdict"]
        composite = r["composite"]

        # Type badge
        type_labels = {"meta-ad": "AD", "landing-page": "PAGE", "email": "EMAIL"}
        type_colors = {"meta-ad": "#2563eb", "landing-page": "#7c3aed", "email": "#059669"}
        type_label = type_labels.get(content_type, "?")
        type_color = type_colors.get(content_type, "#666")

        # Score circle color
        if composite >= 0.85:
            score_color = "#22c55e"
        elif composite >= 0.70:
            score_color = "#22c55e"
        elif composite >= 0.55:
            score_color = "#f59e0b"
        else:
            score_color = "#ef4444"

        # Verdict label
        verdict_label = verdict.replace("_", " ").upper()

        # Headline preview
        headline = ad.get("headline", ad.get("subject", ""))

        # Score summary line
        rubric_total = r.get("rubric", {}).get("weighted_total", 0)
        rubric_max = r.get("rubric", {}).get("max_possible", 63.75)
        rules_passed = r.get("rule_compliance", {}).get("passed", 0)
        rules_total = r.get("rule_compliance", {}).get("total", 0)
        facts_score = r.get("fact_accuracy", {}).get("score", 1.0) if "fact_accuracy" in r else 1.0
        score_line = f"Composite: {composite:.4f} &nbsp; Rubric: {rubric_total:.1f}/{rubric_max:.1f} &nbsp; Rules: {rules_passed}/{rules_total} &nbsp; Facts: {facts_score:.2f} &nbsp; Hook: {hook_type}"

        # Build content fields based on type
        if content_type == "meta-ad":
            pt = ad.get("primary_text", "")
            hl = ad.get("headline", "")
            desc = ad.get("description", "")
            pt_max = 500
            hl_max = 40
            desc_max = 125
            content_html = f"""
            <div class="two-col">
                <div class="col-left">
                    <div class="field-label">PRIMARY TEXT</div>
                    <textarea class="field-edit" data-id="{ad_id}" data-field="primary_text" rows="8">{_esc(pt)}</textarea>
                    <div class="char-count">{len(pt)}/{pt_max}</div>
                </div>
                <div class="col-right">
                    <div class="field-label">HEADLINE</div>
                    <textarea class="field-edit" data-id="{ad_id}" data-field="headline" rows="2">{_esc(hl)}</textarea>
                    <div class="char-count">{len(hl)}/{hl_max}</div>
                    <div class="field-label" style="margin-top:12px">DESCRIPTION</div>
                    <textarea class="field-edit" data-id="{ad_id}" data-field="description" rows="3">{_esc(desc)}</textarea>
                    <div class="char-count">{len(desc)}/{desc_max}</div>
                </div>
            </div>"""
        elif content_type == "email":
            subj = ad.get("subject", "")
            pre = ad.get("preheader", "")
            body = ad.get("body", "")
            sender = ad.get("sender_name", "")
            content_html = f"""
            <div class="two-col">
                <div class="col-left">
                    <div class="field-label">BODY</div>
                    <textarea class="field-edit" data-id="{ad_id}" data-field="body" rows="12">{_esc(body)}</textarea>
                    <div class="char-count">{len(body)}/2000</div>
                </div>
                <div class="col-right">
                    <div class="field-label">SUBJECT</div>
                    <textarea class="field-edit" data-id="{ad_id}" data-field="subject" rows="2">{_esc(subj)}</textarea>
                    <div class="char-count">{len(subj)}/60</div>
                    <div class="field-label" style="margin-top:12px">PREHEADER</div>
                    <textarea class="field-edit" data-id="{ad_id}" data-field="preheader" rows="2">{_esc(pre)}</textarea>
                    <div class="char-count">{len(pre)}/100</div>
                    <div class="field-label" style="margin-top:12px">SENDER</div>
                    <div class="field-static">{_esc(sender)}</div>
                </div>
            </div>"""
        else:  # landing-page
            hl = ad.get("headline", "")
            sub = ad.get("subhead", "")
            hero = ad.get("hero_copy", "")
            sections = ad.get("sections", [])
            sections_text = ""
            for s in sections:
                if isinstance(s, dict):
                    sections_text += f"\n## {s.get('heading', '')}\n{s.get('body', '')}\n"
            content_html = f"""
            <div class="two-col">
                <div class="col-left">
                    <div class="field-label">HERO COPY</div>
                    <textarea class="field-edit" data-id="{ad_id}" data-field="hero_copy" rows="6">{_esc(hero)}</textarea>
                    <div class="char-count">{len(hero)}/500</div>
                    <div class="field-label" style="margin-top:12px">SECTIONS</div>
                    <textarea class="field-edit" data-id="{ad_id}" data-field="sections" rows="12">{_esc(sections_text.strip())}</textarea>
                </div>
                <div class="col-right">
                    <div class="field-label">HEADLINE</div>
                    <textarea class="field-edit" data-id="{ad_id}" data-field="headline" rows="2">{_esc(hl)}</textarea>
                    <div class="char-count">{len(hl)}/80</div>
                    <div class="field-label" style="margin-top:12px">SUBHEAD</div>
                    <textarea class="field-edit" data-id="{ad_id}" data-field="subhead" rows="3">{_esc(sub)}</textarea>
                    <div class="char-count">{len(sub)}/200</div>
                </div>
            </div>"""

        # Tags row
        cta = ad.get("cta", "")
        creative = ad.get("creative_brief", "")
        tags_html = f"""
        <div class="tags-row">
            <span class="tag">CTA: {_esc(cta)}</span>
            <span class="tag">Tactic: {_esc(tactic)}</span>
            <span class="tag">Funnel: {_esc(funnel)}</span>
        </div>"""
        if creative:
            tags_html += f'<div class="creative-brief"><em>{_esc(creative)}</em></div>'

        card = f"""
        <div class="card" data-verdict="{verdict}" data-type="{content_type}" data-angle="{angle}" data-id="{ad_id}">
            <div class="card-top">
                <span class="card-id">{ad_id}</span>
                <span class="type-badge" style="background:{type_color}">{type_label}</span>
                <span class="angle-label">{angle}</span>
                <span class="hl-preview">{_esc(headline[:60])}</span>
                <div class="card-right">
                    <span class="score-circle" style="background:{score_color}">{composite:.2f}</span>
                    <span class="verdict-label">{verdict_label}</span>
                    <button class="btn btn-approve" onclick="setStatus('{ad_id}','approved',this)">Approve</button>
                    <button class="btn btn-revise" onclick="setStatus('{ad_id}','revise',this)">Revise</button>
                    <button class="btn btn-kill" onclick="setStatus('{ad_id}','kill',this)">Kill</button>
                </div>
            </div>
            <div class="score-summary">{score_line}</div>
            {content_html}
            {tags_html}
            <div class="notes-row">
                <div class="field-label">NOTES</div>
                <textarea class="notes" data-id="{ad_id}" placeholder="Add review notes..."></textarea>
            </div>
        </div>"""
        cards_html.append(card)

    # Status counts
    n_total = summary["total"]
    n_approved = summary["verdicts"].get("production_ready", 0)
    n_edited = summary["verdicts"].get("strong_draft", 0) + summary["verdicts"].get("needs_work", 0)
    n_rewrite = summary["verdicts"].get("rewrite", 0)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FarmThru Round 3 Review</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #1a1a1a; padding: 16px 20px; }}
.header {{ max-width: 1400px; margin: 0 auto 12px; }}
.header-info {{ font-size: 13px; color: #666; margin-bottom: 10px; }}
.status-bar {{ display: flex; gap: 12px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }}
.status-pill {{ padding: 4px 12px; border-radius: 4px; font-size: 13px; font-weight: 500; background: #f0f0f0; }}
.status-pill.green {{ border: 1.5px solid #22c55e; color: #166534; }}
.status-pill.blue {{ border: 1.5px solid #3b82f6; color: #1d4ed8; }}
.status-pill.red {{ border: 1.5px solid #ef4444; color: #991b1b; }}
.toolbar {{ display: flex; gap: 0; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }}
.toolbar .sep {{ width: 16px; }}
.tbtn {{ padding: 6px 14px; border: 1px solid #ddd; background: white; cursor: pointer; font-size: 13px; font-weight: 500; color: #555; }}
.tbtn:first-child {{ border-radius: 6px 0 0 6px; }}
.tbtn:last-child {{ border-radius: 0 6px 6px 0; }}
.tbtn:not(:first-child) {{ border-left: none; }}
.tbtn.active {{ background: #1a1a1a; color: white; border-color: #1a1a1a; }}
.toolbar-right {{ margin-left: auto; display: flex; gap: 6px; }}
.toolbar-right .tbtn {{ border-radius: 6px; border: 1px solid #ddd; }}
.toolbar-right .tbtn:not(:first-child) {{ border-left: 1px solid #ddd; }}
.cards {{ max-width: 1400px; margin: 0 auto; }}
.card {{ background: white; border-radius: 8px; margin-bottom: 12px; padding: 16px 20px; border-left: 4px solid transparent; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
.card.status-approved {{ border-left-color: #22c55e; }}
.card.status-revise {{ border-left-color: #3b82f6; }}
.card.status-kill {{ border-left-color: #ef4444; }}
.card-top {{ display: flex; align-items: center; gap: 10px; margin-bottom: 6px; flex-wrap: wrap; }}
.card-id {{ font-weight: 700; font-size: 16px; }}
.type-badge {{ color: white; padding: 2px 10px; border-radius: 3px; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; }}
.angle-label {{ color: #666; font-size: 13px; }}
.hl-preview {{ color: #444; font-size: 13px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.card-right {{ display: flex; align-items: center; gap: 8px; margin-left: auto; flex-shrink: 0; }}
.score-circle {{ color: white; font-weight: 700; font-size: 13px; padding: 4px 10px; border-radius: 20px; min-width: 50px; text-align: center; }}
.verdict-label {{ font-size: 12px; font-weight: 600; color: #666; text-transform: uppercase; min-width: 80px; text-align: center; }}
.btn {{ padding: 5px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; cursor: pointer; background: white; font-weight: 500; }}
.btn-approve.active {{ background: #22c55e; color: white; border-color: #22c55e; }}
.btn-revise.active {{ background: #3b82f6; color: white; border-color: #3b82f6; }}
.btn-kill.active {{ background: #ef4444; color: white; border-color: #ef4444; }}
.btn:hover {{ opacity: 0.85; }}
.score-summary {{ font-size: 12px; color: #888; margin-bottom: 12px; }}
.two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 12px; }}
.field-label {{ font-size: 11px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
.field-edit {{ width: 100%; padding: 10px; border: 1px solid #e0e0e0; border-radius: 6px; font-family: inherit; font-size: 14px; line-height: 1.6; resize: vertical; color: #1a1a1a; }}
.field-edit:focus {{ outline: none; border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.15); }}
.field-static {{ font-size: 14px; color: #444; padding: 4px 0; }}
.char-count {{ font-size: 11px; color: #aaa; text-align: right; margin-top: 2px; }}
.tags-row {{ display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }}
.tag {{ background: #f0f0f0; padding: 3px 10px; border-radius: 4px; font-size: 12px; color: #555; }}
.creative-brief {{ font-size: 13px; color: #777; margin-bottom: 10px; }}
.notes-row {{ margin-top: 8px; }}
.notes {{ width: 100%; height: 50px; padding: 8px; border: 1px solid #e0e0e0; border-radius: 6px; font-family: inherit; font-size: 13px; resize: vertical; }}
.counter {{ max-width: 1400px; margin: 0 auto 12px; font-size: 13px; color: #888; }}
</style>
</head>
<body>
<div class="header">
    <div class="header-info">{n_total} items | Brand guidelines v1.1 | Hub-and-collect | No named competitors | {summary['critical_failures']} critical failures</div>
    <div class="status-bar" id="statusBar">
        <span class="status-pill">{n_total} items</span>
        <span class="status-pill" id="pillPending">Pending: {n_total}</span>
        <span class="status-pill green" id="pillApproved">Approved: 0</span>
        <span class="status-pill blue" id="pillEdited">Edited: 0</span>
        <span class="status-pill red" id="pillKilled">Killed: 0</span>
    </div>
    <div class="toolbar">
        <button class="tbtn active" onclick="setFilter('type','all',this)">All</button>
        <button class="tbtn" onclick="setFilter('type','meta-ad',this)">Ads</button>
        <button class="tbtn" onclick="setFilter('type','landing-page',this)">Pages</button>
        <button class="tbtn" onclick="setFilter('type','email',this)">Emails</button>
        <div class="sep"></div>
        <button class="tbtn" onclick="setFilter('status','unreviewed',this)">Pending</button>
        <button class="tbtn" onclick="setFilter('status','approved',this)">Approved</button>
        <button class="tbtn" onclick="setFilter('status','revise',this)">Edited</button>
        <button class="tbtn" onclick="setFilter('status','kill',this)">Killed</button>
        <div class="toolbar-right">
            <button class="tbtn" onclick="saveJSON()">Save JSON</button>
            <button class="tbtn" onclick="exportCSV()">CSV</button>
        </div>
    </div>
</div>
<div class="counter" id="counter"></div>
<div class="cards" id="cards">
    {"".join(cards_html)}
</div>
<script>
const statuses = {{}};
const notes = {{}};
const filters = {{ type: 'all', status: 'all' }};

function setStatus(id, status, btn) {{
    statuses[id] = status;
    const card = document.querySelector(`[data-id="${{id}}"]`);
    card.className = card.className.replace(/status-\\w+/g, '') + ` status-${{status}}`;
    card.querySelectorAll('.card-right .btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    updatePills();
    updateCounter();
}}

function setFilter(group, value, btn) {{
    filters[group] = value;
    // Update active state in toolbar
    if (group === 'type') {{
        document.querySelectorAll('.toolbar .tbtn').forEach((b, i) => {{
            if (i < 4) b.classList.remove('active');
        }});
    }}
    btn.classList.add('active');
    filterCards();
}}

function filterCards() {{
    document.querySelectorAll('.card').forEach(c => {{
        const matchType = filters.type === 'all' || c.dataset.type === filters.type;
        const id = c.dataset.id;
        const matchStatus = filters.status === 'all' ||
            (filters.status === 'unreviewed' && !statuses[id]) ||
            statuses[id] === filters.status;
        c.style.display = matchType && matchStatus ? '' : 'none';
    }});
    updateCounter();
}}

function updatePills() {{
    const counts = {{ approved: 0, revise: 0, kill: 0 }};
    Object.values(statuses).forEach(s => {{ if (counts[s] !== undefined) counts[s]++; }});
    const total = {n_total};
    const reviewed = Object.keys(statuses).length;
    document.getElementById('pillPending').textContent = `Pending: ${{total - reviewed}}`;
    document.getElementById('pillApproved').textContent = `Approved: ${{counts.approved}}`;
    document.getElementById('pillEdited').textContent = `Edited: ${{counts.revise}}`;
    document.getElementById('pillKilled').textContent = `Killed: ${{counts.kill}}`;
}}

function updateCounter() {{
    const visible = document.querySelectorAll('.card:not([style*="display: none"])').length;
    document.getElementById('counter').textContent = `Showing ${{visible}}/{n_total}`;
}}

function saveJSON() {{
    document.querySelectorAll('.notes').forEach(n => {{
        if (n.value.trim()) notes[n.dataset.id] = n.value.trim();
    }});
    // Also collect edited field values
    const edits = {{}};
    document.querySelectorAll('.field-edit').forEach(el => {{
        const id = el.dataset.id;
        const field = el.dataset.field;
        if (!edits[id]) edits[id] = {{}};
        edits[id][field] = el.value;
    }});
    const data = {{ statuses, notes, edits, exported: new Date().toISOString() }};
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
               `${{c.querySelector('.score-circle').textContent}},${{statuses[id]||'pending'}},` +
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
