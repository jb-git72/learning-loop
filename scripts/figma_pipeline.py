#!/usr/bin/env python3
"""Figma API integration: inspect files, export PNGs, set up brand variables,
and prepare plugin input JSON from scored ad copy.

Commands:
    inspect  — list all sections, frames, and TEXT layers in a Figma file
    export   — export specific frames (or all frames in a section) as PNG
    setup    — create brand colour variables in a Figma file
    prepare  — generate plugin-input JSON from scored ads

Requires FIGMA_API_TOKEN in .env (gitignored).
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))

env_path = root / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

FIGMA_TOKEN = os.environ.get("FIGMA_API_TOKEN", "")

# ---------------------------------------------------------------------------
# Figma API helpers
# ---------------------------------------------------------------------------
FIGMA_API = "https://api.figma.com"


def _headers():
    if not FIGMA_TOKEN:
        print("ERROR: FIGMA_API_TOKEN not set. Add it to .env", file=sys.stderr)
        sys.exit(1)
    return {"X-FIGMA-TOKEN": FIGMA_TOKEN}


def _api_get(path: str) -> dict:
    """GET request to the Figma REST API. Returns parsed JSON."""
    url = f"{FIGMA_API}{path}"
    req = urllib.request.Request(url, headers=_headers())
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"Figma API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def _api_post(path: str, payload: dict) -> dict:
    """POST request to the Figma REST API."""
    url = f"{FIGMA_API}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        **_headers(),
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"Figma API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def _download(url: str, dest: Path):
    """Download a URL to a local file."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        dest.write_bytes(resp.read())


# ---------------------------------------------------------------------------
# Tree walkers
# ---------------------------------------------------------------------------

def _walk_tree(node, depth=0, collect=None):
    """Recursively walk the Figma document tree.
    If *collect* is a list, append (node, depth) for every node.
    """
    if collect is not None:
        collect.append((node, depth))
    for child in node.get("children", []):
        _walk_tree(child, depth + 1, collect)


def _find_frames(node):
    """Return all FRAME and COMPONENT nodes (potential ad templates)."""
    frames = []
    if node.get("type") in ("FRAME", "COMPONENT"):
        frames.append(node)
    for child in node.get("children", []):
        frames.extend(_find_frames(child))
    return frames


def _find_text_nodes(node):
    """Return all TEXT nodes under *node*."""
    texts = []
    if node.get("type") == "TEXT":
        texts.append(node)
    for child in node.get("children", []):
        texts.extend(_find_text_nodes(child))
    return texts


def _find_section_frames(tree, section_name: str):
    """Find all top-level frames inside a named SECTION."""
    section_name_lower = section_name.lower()
    for child in tree.get("children", []):
        if child.get("type") == "SECTION" and section_name_lower in child.get("name", "").lower():
            return _find_frames(child)
        # Sections can also be nested inside pages
        for grandchild in child.get("children", []):
            if grandchild.get("type") == "SECTION" and section_name_lower in grandchild.get("name", "").lower():
                return _find_frames(grandchild)
    return []


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_inspect(args):
    """List all sections, frames, and TEXT layers in a Figma file."""
    data = _api_get(f"/v1/files/{args.file}")
    doc = data.get("document", {})
    pages = doc.get("children", [])

    print(f"File: {data.get('name', '?')}")
    print(f"Last modified: {data.get('lastModified', '?')}")
    print(f"Pages: {len(pages)}\n")

    for page in pages:
        print(f"--- Page: {page['name']} [{page['id']}] ---")

        # Walk for sections
        for child in page.get("children", []):
            if child.get("type") == "SECTION":
                print(f"  SECTION: {child['name']} [{child['id']}]")
                frames = _find_frames(child)
                for frame in frames:
                    _print_frame(frame, indent=4)
            elif child.get("type") in ("FRAME", "COMPONENT"):
                _print_frame(child, indent=2)
        print()


def _print_frame(frame, indent=2):
    """Pretty-print a frame and its TEXT layers."""
    pad = " " * indent
    size = frame.get("absoluteBoundingBox", {})
    w = int(size.get("width", 0))
    h = int(size.get("height", 0))
    print(f"{pad}FRAME: {frame['name']} [{frame['id']}] {w}x{h}")

    texts = _find_text_nodes(frame)
    texts.sort(key=lambda t: t.get("style", {}).get("fontSize", 0), reverse=True)
    for t in texts:
        fs = t.get("style", {}).get("fontSize", "?")
        font = t.get("style", {}).get("fontFamily", "?")
        chars = t.get("characters", "")
        preview = chars[:60].replace("\n", " ")
        if len(chars) > 60:
            preview += "..."
        print(f"{pad}  TEXT [{t['id']}] {font} {fs}px: \"{preview}\"")


def cmd_export(args):
    """Export frames as PNG at 2x scale."""
    file_key = args.file
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine which frame IDs to export
    frame_ids = []
    frame_names = {}  # id -> name

    if args.frames:
        # User provided explicit frame IDs
        frame_ids = [fid.strip() for fid in args.frames.split(",")]
        # Fetch file to get frame names
        data = _api_get(f"/v1/files/{file_key}")
        doc = data.get("document", {})
        all_nodes = []
        _walk_tree(doc, collect=all_nodes)
        for node, _ in all_nodes:
            if node.get("id") in frame_ids:
                frame_names[node["id"]] = node.get("name", node["id"])
    elif args.section:
        # Find all frames in a section
        data = _api_get(f"/v1/files/{file_key}")
        doc = data.get("document", {})
        for page in doc.get("children", []):
            frames = _find_section_frames(page, args.section)
            for f in frames:
                frame_ids.append(f["id"])
                frame_names[f["id"]] = f.get("name", f["id"])
        if not frame_ids:
            print(f"No frames found in section matching '{args.section}'", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERROR: provide --frames or --section", file=sys.stderr)
        sys.exit(1)

    if not frame_ids:
        print("No frames to export.", file=sys.stderr)
        sys.exit(1)

    print(f"Exporting {len(frame_ids)} frame(s) at 2x...")

    # Figma images API — comma-separated IDs
    ids_param = ",".join(frame_ids)
    images_data = _api_get(f"/v1/images/{file_key}?ids={ids_param}&format=png&scale=2")

    images = images_data.get("images", {})
    for fid, url in images.items():
        if not url:
            print(f"  SKIP {fid} — no image URL returned (may be empty frame)")
            continue
        name = frame_names.get(fid, fid).replace("/", "-").replace(" ", "_")
        dest = output_dir / f"{name}.png"
        _download(url, dest)
        print(f"  Saved {dest}")

    print("Done.")


def cmd_setup(args):
    """Create brand colour variables in a Figma file."""
    file_key = args.file

    # Default neutral palette
    colours = {
        "primary":    {"r": 0.2, "g": 0.2, "b": 0.2, "a": 1},
        "secondary":  {"r": 0.4, "g": 0.4, "b": 0.4, "a": 1},
        "accent":     {"r": 0.0, "g": 0.48, "b": 1.0, "a": 1},
        "background": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1},
        "text":       {"r": 0.1, "g": 0.1, "b": 0.1, "a": 1},
    }

    # Override from client config if provided
    if args.client:
        config_path = root / "clients" / args.client / "config.json"
        if config_path.exists():
            config = json.loads(config_path.read_text())
            brand_style = config.get("brand_style", {})
            for key in colours:
                if key in brand_style:
                    colours[key] = _hex_to_rgba(brand_style[key])

    # Build the variables payload
    # Figma Variables API: POST /v1/files/:key/variables
    variable_collection = {
        "name": "Brand",
        "variableCollections": [
            {
                "action": "CREATE",
                "name": "Brand",
                "id": "brand-collection",  # temp ID for creation
            }
        ],
        "variables": [],
        "variableModes": [],
    }

    for name, rgba in colours.items():
        variable_collection["variables"].append({
            "action": "CREATE",
            "name": name,
            "variableCollectionId": "brand-collection",
            "resolvedType": "COLOR",
            "valuesByMode": {
                "default": rgba
            },
        })

    print(f"Setting up Brand variables in file {file_key}...")
    result = _api_post(f"/v1/files/{file_key}/variables", variable_collection)
    print(f"Result: {json.dumps(result, indent=2)[:500]}")
    print("Done.")


def _hex_to_rgba(hex_str: str) -> dict:
    """Convert '#RRGGBB' to Figma RGBA dict (0-1 floats)."""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 6:
        r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
        return {"r": r / 255, "g": g / 255, "b": b / 255, "a": 1.0}
    return {"r": 0.5, "g": 0.5, "b": 0.5, "a": 1.0}


def cmd_prepare(args):
    """Generate plugin-input JSON from scored ads."""
    scored_path = Path(args.scored)
    if not scored_path.exists():
        print(f"ERROR: scored file not found: {scored_path}", file=sys.stderr)
        sys.exit(1)

    scored = json.loads(scored_path.read_text())
    if isinstance(scored, dict):
        ads = scored.get("ads", scored.get("results", [scored]))
    elif isinstance(scored, list):
        ads = scored
    else:
        print("ERROR: unexpected scored file format", file=sys.stderr)
        sys.exit(1)

    # Filter by verdict
    verdict_filter = args.filter.lower() if args.filter else None
    if verdict_filter:
        ads = [a for a in ads if _matches_verdict(a, verdict_filter)]

    # Load client config for brand colours
    brand_colours = {}
    if args.client:
        config_path = root / "clients" / args.client / "config.json"
        if config_path.exists():
            config = json.loads(config_path.read_text())
            brand_colours = config.get("brand_style", {})

    # Hook type -> template frame pattern mapping
    hook_map = {
        "question":    "B",   # question-style templates
        "statistic":   "A",   # bold stat templates
        "story":       "C",   # narrative templates
        "provocation": "B",
        "contrast":    "A",
        "social_proof": "A",
    }

    plugin_input = []
    for ad in ads:
        ad_id = ad.get("ad_id", ad.get("page_id", ad.get("email_id", "unknown")))
        hook = ad.get("hook_type", "").lower()
        template_pattern = hook_map.get(hook, "A")

        entry = {
            "ad_id": ad_id,
            "hook_type": ad.get("hook_type", ""),
            "tactic": ad.get("tactic", ""),
            "angle": ad.get("angle", ""),
            "headline": ad.get("headline", ""),
            "primary_text": ad.get("primary_text", ""),
            "description": ad.get("description", ""),
            "cta": ad.get("cta", ad.get("cta_text", "")),
            "suggested_template_pattern": template_pattern,
            "brand_colours": brand_colours,
        }

        # Landing page fields
        if ad.get("hero_copy"):
            entry["hero_copy"] = ad["hero_copy"]
        if ad.get("subhead"):
            entry["subhead"] = ad["subhead"]
        if ad.get("sections"):
            entry["sections"] = ad["sections"]

        plugin_input.append(entry)

    output_path = Path(args.output) if args.output else Path("figma-input.json")
    output_path.write_text(json.dumps(plugin_input, indent=2))
    print(f"Wrote {len(plugin_input)} ad(s) to {output_path}")


def _matches_verdict(ad: dict, target: str) -> bool:
    """Check if ad verdict matches or exceeds the target."""
    verdict = ad.get("verdict", ad.get("score", {}).get("verdict", "")).lower().replace(" ", "_")
    hierarchy = ["production_ready", "strong_draft", "needs_work", "rewrite"]
    if target not in hierarchy or verdict not in hierarchy:
        return verdict == target
    return hierarchy.index(verdict) <= hierarchy.index(target)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Figma pipeline for learning-loop")
    sub = parser.add_subparsers(dest="command")

    # inspect
    p_inspect = sub.add_parser("inspect", help="List frames and text layers")
    p_inspect.add_argument("--file", required=True, help="Figma file key")

    # export
    p_export = sub.add_parser("export", help="Export frames as PNG")
    p_export.add_argument("--file", required=True, help="Figma file key")
    p_export.add_argument("--frames", help="Comma-separated frame IDs (e.g. '1:66,1:113')")
    p_export.add_argument("--section", help="Export all frames in a named section")
    p_export.add_argument("--output", required=True, help="Output directory for PNGs")

    # setup
    p_setup = sub.add_parser("setup", help="Create brand colour variables")
    p_setup.add_argument("--file", required=True, help="Figma file key")
    p_setup.add_argument("--client", help="Client slug for brand colours")

    # prepare
    p_prepare = sub.add_parser("prepare", help="Generate plugin input JSON from scored ads")
    p_prepare.add_argument("--client", help="Client slug")
    p_prepare.add_argument("--scored", required=True, help="Path to scored JSON file")
    p_prepare.add_argument("--filter", help="Filter by verdict (e.g. strong_draft, production_ready)")
    p_prepare.add_argument("--output", default="figma-input.json", help="Output path")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "inspect": cmd_inspect,
        "export": cmd_export,
        "setup": cmd_setup,
        "prepare": cmd_prepare,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
