// Learning Loop Ad Injector — Figma Plugin
// Injects ad copy from JSON into template frames.
//
// Workflow:
// 1. Select a template frame in Figma
// 2. Paste ad JSON into the plugin UI
// 3. Plugin clones the frame, replaces TEXT nodes by font size hierarchy:
//    - Largest  -> headline
//    - Second   -> subhead / primary_text
//    - Third+   -> fine print / description
// 4. Optionally updates SOLID fill colours to brand colours

figma.showUI(__html__, { width: 420, height: 560 });

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Recursively find all TEXT nodes under a given node.
 */
function findTextNodes(node) {
  const texts = [];
  if (node.type === "TEXT") {
    texts.push(node);
  }
  if ("children" in node) {
    for (const child of node.children) {
      texts.push(...findTextNodes(child));
    }
  }
  return texts;
}

/**
 * Get the primary font size of a text node.
 * Uses the fontSize property (most TEXT nodes have a single size).
 */
function getFontSize(textNode) {
  const fs = textNode.fontSize;
  if (typeof fs === "number") return fs;
  // Mixed sizes — use the first range
  const len = textNode.characters.length;
  if (len > 0) {
    const first = textNode.getRangeFontSize(0, 1);
    if (typeof first === "number") return first;
  }
  return 0;
}

/**
 * Load fonts used by a text node before modifying its characters.
 */
async function loadFontsForNode(textNode) {
  const len = textNode.characters.length;
  if (len === 0) {
    // Empty node — load the node's default font
    const fontName = textNode.fontName;
    if (fontName && fontName !== figma.mixed) {
      await figma.loadFontAsync(fontName);
    }
    return;
  }
  // Collect all unique fonts in the node
  const fonts = new Set();
  for (let i = 0; i < len; i++) {
    const fn = textNode.getRangeFontName(i, i + 1);
    if (fn && fn !== figma.mixed) {
      fonts.add(JSON.stringify(fn));
    }
  }
  for (const f of fonts) {
    await figma.loadFontAsync(JSON.parse(f));
  }
}

/**
 * Parse hex colour string to Figma RGB (0-1 floats).
 */
function hexToRgb(hex) {
  hex = hex.replace("#", "");
  if (hex.length !== 6) return null;
  return {
    r: parseInt(hex.slice(0, 2), 16) / 255,
    g: parseInt(hex.slice(2, 4), 16) / 255,
    b: parseInt(hex.slice(4, 6), 16) / 255,
  };
}

/**
 * Find nodes with SOLID fills and update their colour.
 */
function updateFillColours(node, brandColours) {
  if (!brandColours || !brandColours.primary) return;
  const rgb = hexToRgb(brandColours.primary);
  if (!rgb) return;

  if ("fills" in node && Array.isArray(node.fills)) {
    const newFills = node.fills.map((fill) => {
      if (fill.type === "SOLID") {
        return { ...fill, color: rgb };
      }
      return fill;
    });
    node.fills = newFills;
  }
  if ("children" in node) {
    for (const child of node.children) {
      updateFillColours(child, brandColours);
    }
  }
}

// ---------------------------------------------------------------------------
// Main injection logic
// ---------------------------------------------------------------------------

async function injectAd(adData, sourceFrame) {
  // 1. Clone the frame
  const clone = sourceFrame.clone();
  clone.x = sourceFrame.x + sourceFrame.width + 40;

  // 2. Rename to ad_id
  clone.name = adData.ad_id || "injected-ad";

  // 3. Find TEXT nodes and sort by font size descending
  const textNodes = findTextNodes(clone);
  textNodes.sort((a, b) => getFontSize(b) - getFontSize(a));

  // 4. Build text assignment list
  //    Priority: headline > primary_text/subhead > description > cta
  const textValues = [];
  if (adData.headline) textValues.push(adData.headline);
  if (adData.hero_copy) textValues.push(adData.hero_copy);
  if (adData.primary_text) textValues.push(adData.primary_text);
  if (adData.subhead) textValues.push(adData.subhead);
  if (adData.description) textValues.push(adData.description);
  if (adData.cta) textValues.push(adData.cta);

  // 5. Assign text values to nodes by size hierarchy
  for (let i = 0; i < Math.min(textNodes.length, textValues.length); i++) {
    await loadFontsForNode(textNodes[i]);
    textNodes[i].characters = textValues[i];
  }

  // 6. Optionally update fill colours
  if (adData.brand_colours) {
    updateFillColours(clone, adData.brand_colours);
  }

  // 7. Zoom to the new frame
  figma.viewport.scrollAndZoomIntoView([clone]);

  return clone.name;
}

// ---------------------------------------------------------------------------
// Message handler
// ---------------------------------------------------------------------------

figma.ui.onmessage = async (msg) => {
  if (msg.type === "inject") {
    const ads = msg.ads; // array of ad objects

    // Get selected frame
    const selection = figma.currentPage.selection;
    if (selection.length === 0) {
      figma.ui.postMessage({
        type: "status",
        message: "Error: select a template frame first.",
        error: true,
      });
      return;
    }

    const sourceFrame = selection[0];
    if (sourceFrame.type !== "FRAME" && sourceFrame.type !== "COMPONENT") {
      figma.ui.postMessage({
        type: "status",
        message: "Error: selected node must be a FRAME or COMPONENT.",
        error: true,
      });
      return;
    }

    let count = 0;
    for (const ad of ads) {
      try {
        const name = await injectAd(ad, sourceFrame);
        count++;
        figma.ui.postMessage({
          type: "status",
          message: `Injected: ${name} (${count}/${ads.length})`,
          error: false,
        });
      } catch (err) {
        figma.ui.postMessage({
          type: "status",
          message: `Error injecting ${ad.ad_id || "?"}: ${err.message}`,
          error: true,
        });
      }
    }

    figma.ui.postMessage({
      type: "status",
      message: `Done. ${count} ad(s) injected.`,
      error: false,
    });
  }

  if (msg.type === "cancel") {
    figma.closePlugin();
  }
};
