#!/usr/bin/env python3
"""Generate standalone HTML creative briefs with visual format references.

Usage:
    # Single ad
    python3 scripts/build_brief.py farm-thru --ad clients/farm-thru/loop/meta-ads/BR-101.json --output briefs/

    # Scored batch (filter by verdict)
    python3 scripts/build_brief.py farm-thru --scored clients/farm-thru/loop/scored_r3_pass8.json \
        --filter production_ready,strong_draft --output briefs/

    # All ads in loop directory
    python3 scripts/build_brief.py farm-thru --all --output briefs/
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT / "shared" / "brief-template.html"
MANIFEST_PATH = ROOT / "research" / "motion-benchmarks-2026" / "image-manifest.json"
HOOKS_PATH = ROOT / "shared" / "hooks.json"
TACTICS_PATH = ROOT / "shared" / "tactics.json"
IMAGES_REL = "../../research/motion-benchmarks-2026/images"

# ── Defaults ─────────────────────────────────────────────────────────────────

DEFAULT_ACCENT = "#2563eb"
DEFAULT_ACCENT_BG = "#f8faff"

TYPE_LABELS = {"meta-ad": "META AD", "landing-page": "LANDING PAGE", "email": "EMAIL"}
TYPE_COLORS = {"meta-ad": "#2563eb", "landing-page": "#7c3aed", "email": "#059669"}

VERDICT_COLORS = {
    "production_ready": "#22c55e",
    "strong_draft": "#3b82f6",
    "needs_work": "#f59e0b",
    "rewrite": "#ef4444",
}


# ── Helpers ──────────────────────────────────────────────────────────────────


def esc(text: str) -> str:
    """HTML-escape text."""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def score_color(composite: float) -> str:
    if composite >= 0.70:
        return "#22c55e"
    if composite >= 0.55:
        return "#f59e0b"
    return "#ef4444"


def char_badge(text: str, limit: int) -> str:
    n = len(text or "")
    cls = "char-badge over" if n > limit else "char-badge"
    return f'<span class="{cls}">{n}/{limit}</span>'


# ── Image matching ───────────────────────────────────────────────────────────


def load_manifest() -> list[dict]:
    if not MANIFEST_PATH.exists():
        return []
    data = load_json(MANIFEST_PATH)
    return data.get("images", [])


def match_hook_image(images: list[dict], hook_type: str) -> dict | None:
    """Find a THH or hook-mapped image for the given hook_type."""
    if not hook_type:
        return None
    for img in images:
        if img.get("maps_to_id") == hook_type and img.get("maps_to_type") == "hook":
            return img
    return None


def match_tactic_image(images: list[dict], tactic: str) -> dict | None:
    """Find a TVS or tactic-mapped image for the given tactic."""
    if not tactic:
        return None
    for img in images:
        if img.get("maps_to_id") == tactic and img.get("maps_to_type") == "tactic":
            return img
    return None


def match_asset_image(
    images: list[dict], top_visual_formats: list[str]
) -> dict | None:
    """Fuzzy-match a TAT image to the playbook's top_visual_formats."""
    if not top_visual_formats:
        return None
    tat_images = [img for img in images if img.get("category") == "tat"]
    for fmt in top_visual_formats:
        fmt_lower = fmt.lower()
        for img in tat_images:
            name_lower = (img.get("format_name") or "").lower()
            label_lower = (img.get("maps_to_label") or "").lower()
            # Check if the playbook format roughly matches the image name or label
            if (
                fmt_lower in name_lower
                or name_lower in fmt_lower
                or fmt_lower in label_lower
                or label_lower in fmt_lower
            ):
                return img
        # Partial word matching: check if any word from the format appears
        fmt_words = set(fmt_lower.split())
        for img in tat_images:
            name_words = set((img.get("format_name") or "").lower().split())
            if fmt_words & name_words and len(fmt_words & name_words) > 0:
                return img
    # Fallback: return first TAT image if available
    return tat_images[0] if tat_images else None


def build_ref_card(label: str, image: dict, caption: str) -> str:
    filename = image.get("filename", "")
    format_name = image.get("format_name", "")
    return f"""
      <div class="ref-card">
        <img src="{IMAGES_REL}/{esc(filename)}" alt="{esc(format_name)}">
        <div class="ref-card-body">
          <div class="ref-card-label">{esc(label)}</div>
          <div class="ref-card-title">{esc(format_name)}</div>
          <div class="ref-card-caption">{esc(caption)}</div>
        </div>
      </div>"""


# ── Copy fields ──────────────────────────────────────────────────────────────


def build_field(label: str, value: str, limit: int) -> str:
    return f"""
      <div class="field-block">
        <div class="field-label">{esc(label)} {char_badge(value, limit)}</div>
        <div class="field-value">{esc(value)}</div>
      </div>"""


def build_copy_fields(ad: dict, content_type: str, constraints: dict) -> str:
    html = ""
    if content_type == "meta-ad":
        html += build_field(
            "Primary Text",
            ad.get("primary_text", ""),
            constraints.get("primary_text_max_chars", 500),
        )
        html += build_field(
            "Headline",
            ad.get("headline", ""),
            constraints.get("headline_max_chars", 40),
        )
        html += build_field(
            "Description",
            ad.get("description", ""),
            constraints.get("description_max_chars", 125),
        )
        cta = ad.get("cta", "")
        html += build_field("CTA", cta, 30)

    elif content_type == "email":
        html += build_field(
            "Subject",
            ad.get("subject", ""),
            constraints.get("subject_max_chars", 60),
        )
        html += build_field(
            "Preheader",
            ad.get("preheader", ""),
            constraints.get("preheader_max_chars", 100),
        )
        html += build_field(
            "Body",
            ad.get("body", ""),
            constraints.get("body_max_chars", 2000),
        )
        html += build_field("CTA", ad.get("cta", ""), 30)
        html += build_field("Sender", ad.get("sender_name", ""), 60)

    elif content_type == "landing-page":
        html += build_field(
            "Headline",
            ad.get("headline", ""),
            constraints.get("headline_max_chars", 80),
        )
        html += build_field(
            "Subhead",
            ad.get("subhead", ""),
            constraints.get("subhead_max_chars", 120),
        )
        html += build_field(
            "Hero Copy",
            ad.get("hero_copy", ""),
            constraints.get("hero_copy_max_chars", 500),
        )

        # Sections
        sections = ad.get("sections", [])
        if sections:
            html += '<div class="section-title">Sections</div>'
            for s in sections:
                if isinstance(s, dict):
                    heading = s.get("heading", "")
                    body = s.get("body", "")
                    html += f"""
      <div class="lp-section">
        <div class="lp-section-heading">{esc(heading)}</div>
        <div class="lp-section-body">{esc(body)}</div>
      </div>"""

        html += build_field("CTA", ad.get("cta", ""), 40)

    return html


# ── Format guidance ──────────────────────────────────────────────────────────


def load_hook_guidance(hook_type: str, content_type: str) -> tuple[str, str]:
    """Return (template, adaptation) for the given hook and content type."""
    if not HOOKS_PATH.exists():
        return ("", "")
    data = load_json(HOOKS_PATH)
    for hook in data.get("hooks", []):
        if hook.get("id") == hook_type:
            template = hook.get("template", "")
            adaptation = (
                hook.get("content_type_adaptations", {}).get(content_type, "")
            )
            return (template, adaptation)
    return ("", "")


def load_tactic_guidance(tactic_id: str) -> tuple[str, str]:
    """Return (structure, guidance) for the given tactic."""
    if not TACTICS_PATH.exists():
        return ("", "")
    data = load_json(TACTICS_PATH)
    for t in data.get("tactics", []):
        if t.get("id") == tactic_id:
            return (t.get("structure", ""), t.get("guidance", ""))
    return ("", "")


def build_format_guidance(hook_type: str, tactic: str, content_type: str) -> str:
    html = ""
    template, adaptation = load_hook_guidance(hook_type, content_type)
    if template:
        text = template
        if adaptation:
            text += f"\n\n{content_type.upper()} adaptation: {adaptation}"
        html += f"""
      <div class="guidance-block">
        <div class="guidance-label">Hook: {esc(hook_type.replace('_', ' ').title())}</div>
        <div class="guidance-text">{esc(text)}</div>
      </div>"""

    structure, guidance = load_tactic_guidance(tactic)
    if structure:
        text = f"Structure: {structure}"
        if guidance:
            text += f"\n\n{guidance}"
        html += f"""
      <div class="guidance-block">
        <div class="guidance-label">Tactic: {esc(tactic.replace('-', ' ').replace('_', ' ').title())}</div>
        <div class="guidance-text">{esc(text)}</div>
      </div>"""

    return html


# ── Brand context ────────────────────────────────────────────────────────────


def build_brand_context(config: dict, playbook: dict | None) -> str:
    sc = config.get("scoring_context", {})
    parts = []
    if sc.get("brand_positioning"):
        parts.append(sc["brand_positioning"])
    if sc.get("product"):
        parts.append(f"Product: {sc['product']}")
    if sc.get("audience"):
        parts.append(f"Audience: {sc['audience'][:200]}...")

    creative_ctx = ""
    if playbook:
        creative_ctx = playbook.get("creative_context", "")
    if creative_ctx:
        parts.append(f"Industry insight: {creative_ctx}")

    return "\n\n".join(parts)


# ── Production notes ─────────────────────────────────────────────────────────


def build_production_notes(
    ad: dict, content_type: str, constraints: dict, score_result: dict | None
) -> str:
    parts = []

    # Platform constraints
    constraint_lines = []
    for key, val in constraints.items():
        if key != "platform":
            label = key.replace("_", " ").replace("max chars", "limit")
            constraint_lines.append(f"  {label}: {val}")
    if constraint_lines:
        parts.append("Platform constraints:\n" + "\n".join(constraint_lines))

    # Creative brief from the ad
    creative = ad.get("creative_brief", "")
    if creative:
        parts.append(f"Creative direction:\n  {creative}")

    # Score details if available
    if score_result:
        rubric = score_result.get("rubric", {})
        wt = rubric.get("weighted_total", 0)
        mx = rubric.get("max_possible", 0)
        rc = score_result.get("rule_compliance", {})
        fa = score_result.get("fact_accuracy", {})
        parts.append(
            f"Scoring breakdown:\n"
            f"  Rubric: {wt:.1f}/{mx:.1f}\n"
            f"  Rules: {rc.get('passed', 0)}/{rc.get('total', 0)} passed\n"
            f"  Facts: {fa.get('score', 1.0):.2f} ({fa.get('verified', 0)} verified, "
            f"{fa.get('unverified', 0)} unverified)"
        )

    return "\n\n".join(parts)


# ── Brief generator ──────────────────────────────────────────────────────────


def generate_brief(
    ad: dict,
    config: dict,
    output_dir: Path,
    score_result: dict | None = None,
    playbook: dict | None = None,
):
    """Generate a single HTML brief for one ad."""
    # Resolve IDs
    ad_id = ad.get("ad_id", ad.get("page_id", ad.get("email_id", "unknown")))
    content_type = ad.get("content_type", "meta-ad")
    hook_type = ad.get("hook_type", "")
    tactic = ad.get("tactic", "")
    angle = ad.get("angle", "")
    funnel = ad.get("funnel", "")

    # Verdict + composite from score result
    verdict = "unscored"
    composite = 0.0
    if score_result:
        verdict = score_result.get("verdict", "unscored")
        composite = score_result.get("composite", 0.0)

    # Config values
    client_name = config.get("client_name", config.get("client_id", "Unknown"))
    brand_style = config.get("brand_style", {})
    accent = brand_style.get("accent_color", DEFAULT_ACCENT)
    accent_bg = brand_style.get("accent_bg", DEFAULT_ACCENT_BG)
    constraints = config.get("platform_constraints", {}).get(content_type, {})

    # Load template
    template = TEMPLATE_PATH.read_text()

    # Build image references
    images = load_manifest()
    ref_cards_html = ""

    hook_img = match_hook_image(images, hook_type)
    if hook_img:
        notes = hook_img.get("notes", "")
        caption = f"Matched to hook type '{hook_type}'. {notes}"
        ref_cards_html += build_ref_card("Hook Reference", hook_img, caption)

    tactic_img = match_tactic_image(images, tactic)
    if tactic_img:
        notes = tactic_img.get("notes", "")
        caption = f"Matched to tactic '{tactic}'. {notes}"
        ref_cards_html += build_ref_card("Tactic Reference", tactic_img, caption)

    top_visual_formats = playbook.get("top_visual_formats", []) if playbook else []
    asset_img = match_asset_image(images, top_visual_formats)
    if asset_img:
        notes = asset_img.get("notes", "")
        matched_label = asset_img.get("format_name", "")
        caption = f"Suggested asset type: {matched_label}. {notes}"
        ref_cards_html += build_ref_card("Asset Type Reference", asset_img, caption)

    if not ref_cards_html:
        ref_cards_html = '<div class="guidance-text" style="color:#aaa">No matching visual references found.</div>'

    # Build all sections
    copy_html = build_copy_fields(ad, content_type, constraints)
    guidance_html = build_format_guidance(hook_type, tactic, content_type)
    brand_ctx = build_brand_context(config, playbook)
    prod_notes = build_production_notes(ad, content_type, constraints, score_result)

    # Substitutions
    replacements = {
        "{{AD_ID}}": esc(ad_id),
        "{{CLIENT_NAME}}": esc(client_name),
        "{{TYPE_LABEL}}": TYPE_LABELS.get(content_type, content_type.upper()),
        "{{TYPE_COLOR}}": TYPE_COLORS.get(content_type, "#666"),
        "{{VERDICT_LABEL}}": verdict.replace("_", " ").upper(),
        "{{VERDICT_COLOR}}": VERDICT_COLORS.get(verdict, "#888"),
        "{{COMPOSITE}}": f"{composite:.2f}" if score_result else "N/A",
        "{{SCORE_COLOR}}": score_color(composite) if score_result else "#888",
        "{{DATE}}": datetime.now().strftime("%Y-%m-%d"),
        "{{ANGLE}}": esc(angle),
        "{{HOOK_TYPE}}": esc(hook_type),
        "{{TACTIC}}": esc(tactic),
        "{{FUNNEL}}": esc(funnel),
        "{{ACCENT_COLOR}}": accent,
        "{{ACCENT_BG}}": accent_bg,
        "{{COPY_FIELDS}}": copy_html,
        "{{REFERENCE_CARDS}}": ref_cards_html,
        "{{FORMAT_GUIDANCE}}": guidance_html if guidance_html else '<div class="guidance-text" style="color:#aaa">No format guidance available.</div>',
        "{{BRAND_CONTEXT}}": esc(brand_ctx),
        "{{PRODUCTION_NOTES}}": esc(prod_notes),
    }

    html = template
    for key, val in replacements.items():
        html = html.replace(key, val)

    # Write output
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"brief-{ad_id}.html"
    out_path.write_text(html)
    return out_path


# ── Ad discovery ─────────────────────────────────────────────────────────────


def find_all_ads(client_slug: str) -> list[Path]:
    """Find all ad JSON files in a client's loop directory."""
    loop_dir = ROOT / "clients" / client_slug / "loop"
    if not loop_dir.exists():
        return []
    paths = []
    for subdir in ["meta-ads", "landing-pages", "emails"]:
        d = loop_dir / subdir
        if d.exists():
            paths.extend(sorted(d.glob("*.json")))
    return paths


def load_scored_batch(scored_path: Path, filter_verdicts: list[str] | None = None):
    """Load scored batch and return list of (ad_path, score_result) tuples."""
    data = load_json(scored_path)
    results = data.get("results", [])
    items = []
    for r in results:
        if filter_verdicts and r.get("verdict") not in filter_verdicts:
            continue
        file_rel = r.get("_file", "")
        if file_rel:
            ad_path = ROOT / file_rel
        else:
            # Try to resolve from ad_id
            ad_id = r.get("ad_id", r.get("page_id", r.get("email_id", "")))
            ad_path = None
            if ad_id:
                # Search in all content-type subdirectories
                for subdir in ["meta-ads", "landing-pages", "emails"]:
                    candidate = (
                        ROOT
                        / "clients"
                        / scored_path.parent.parent.name
                        / "loop"
                        / subdir
                        / f"{ad_id}.json"
                    )
                    if candidate.exists():
                        ad_path = candidate
                        break
            if not ad_path:
                continue
        items.append((ad_path, r))
    return items


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML creative briefs with visual format references."
    )
    parser.add_argument("client", help="Client slug (e.g. farm-thru)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ad", help="Path to a single ad JSON file")
    group.add_argument("--scored", help="Path to a scored batch JSON file")
    group.add_argument(
        "--all", action="store_true", help="Process all ads in loop directory"
    )
    parser.add_argument(
        "--filter",
        help="Comma-separated verdict filter (e.g. production_ready,strong_draft)",
    )
    parser.add_argument(
        "--output", default="briefs/", help="Output directory (default: briefs/)"
    )
    args = parser.parse_args()

    # Load client config
    config_path = ROOT / "clients" / args.client / "config.json"
    if not config_path.exists():
        print(f"Error: config not found at {config_path}", file=sys.stderr)
        sys.exit(1)
    config = load_json(config_path)

    # Load industry playbook
    industry = config.get("industry", "general")
    playbook_path = ROOT / "shared" / "playbooks" / f"{industry}.json"
    playbook = load_json(playbook_path) if playbook_path.exists() else None

    output_dir = Path(args.output)

    # Determine which ads to process
    ad_score_pairs = []  # list of (ad_dict, score_result_or_None)

    if args.ad:
        ad_path = Path(args.ad)
        if not ad_path.is_absolute():
            ad_path = ROOT / ad_path
        if not ad_path.exists():
            print(f"Error: ad file not found: {ad_path}", file=sys.stderr)
            sys.exit(1)
        ad = load_json(ad_path)
        ad_score_pairs.append((ad, None))

    elif args.scored:
        scored_path = Path(args.scored)
        if not scored_path.is_absolute():
            scored_path = ROOT / scored_path
        if not scored_path.exists():
            print(f"Error: scored file not found: {scored_path}", file=sys.stderr)
            sys.exit(1)
        filter_verdicts = None
        if args.filter:
            filter_verdicts = [v.strip() for v in args.filter.split(",")]
        items = load_scored_batch(scored_path, filter_verdicts)
        for ad_path, score_result in items:
            if ad_path.exists():
                ad = load_json(ad_path)
                ad_score_pairs.append((ad, score_result))
            else:
                print(f"  Warning: ad file not found: {ad_path}", file=sys.stderr)

    elif args.all:
        ad_paths = find_all_ads(args.client)
        if not ad_paths:
            print(f"No ad files found for client '{args.client}'", file=sys.stderr)
            sys.exit(1)
        for ad_path in ad_paths:
            ad = load_json(ad_path)
            ad_score_pairs.append((ad, None))

    if not ad_score_pairs:
        print("No ads to process.", file=sys.stderr)
        sys.exit(1)

    # Generate briefs
    generated = []
    for ad, score_result in ad_score_pairs:
        out_path = generate_brief(ad, config, output_dir, score_result, playbook)
        generated.append(out_path)
        ad_id = ad.get("ad_id", ad.get("page_id", ad.get("email_id", "unknown")))
        print(f"  {ad_id} -> {out_path}")

    print(f"\n{len(generated)} brief(s) generated in {output_dir}/", file=sys.stderr)


if __name__ == "__main__":
    main()
