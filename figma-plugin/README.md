# Learning Loop Ad Injector — Figma Plugin

Injects ad copy from the learning-loop scoring pipeline into Figma template frames.

## How it works

1. The Python pipeline (`scripts/figma_pipeline.py prepare`) exports scored ads as `figma-input.json`
2. This plugin reads that JSON and injects text into cloned template frames
3. Text is assigned by font-size hierarchy: largest text node gets the headline, second largest gets body copy, etc.

## Installation

1. Open Figma Desktop
2. Go to **Plugins > Development > Import plugin from manifest...**
3. Select `figma-plugin/manifest.json` from this repo

The plugin appears under **Plugins > Development > Learning Loop Ad Injector**.

## Usage

1. **Select a template frame** in your Figma file (e.g. `BestPrices-A-001`)
2. **Run the plugin** from the Plugins menu
3. **Paste the JSON** from `figma-input.json` into the textarea
4. Click **Inject Ads**

The plugin will:
- Clone the selected frame once per ad
- Replace TEXT nodes by font-size hierarchy (largest = headline, next = body, etc.)
- Rename each cloned frame to the ad's `ad_id`
- Optionally update SOLID fill colours if `brand_colours.primary` is provided
- Zoom to the last injected frame

## JSON format

The plugin expects an array of ad objects:

```json
[
  {
    "ad_id": "FT-META-001",
    "headline": "Your headline here",
    "primary_text": "Body copy goes here",
    "description": "Fine print or disclaimer",
    "cta": "Shop Now",
    "brand_colours": {
      "primary": "#2D5F2D"
    }
  }
]
```

Fields used for text injection (in priority order):
- `headline` / `hero_copy` — assigned to largest text node
- `primary_text` / `subhead` — assigned to second largest
- `description` — assigned to third largest
- `cta` — assigned to smallest remaining

## End-to-end workflow

```bash
# 1. Score ads through the learning loop
python3 scripts/score_batch.py farm-thru

# 2. Generate plugin input (only strong_draft and above)
python3 scripts/figma_pipeline.py prepare \
  --client farm-thru \
  --scored clients/farm-thru/loop/scored.json \
  --filter strong_draft \
  --output figma-input.json

# 3. Inspect available templates
python3 scripts/figma_pipeline.py inspect --file kSheTaRFmA7bOKL7ywqA44

# 4. Open Figma, select template, run plugin, paste JSON

# 5. Export finished designs as PNG
python3 scripts/figma_pipeline.py export \
  --file kSheTaRFmA7bOKL7ywqA44 \
  --section "Best prices" \
  --output briefs/
```

## File structure

```
figma-plugin/
  manifest.json   — Figma plugin manifest
  code.js         — Plugin logic (runs in Figma sandbox)
  ui.html         — Plugin UI (textarea + inject button)
  README.md       — This file
```
