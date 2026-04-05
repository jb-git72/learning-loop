// Learning Loop Ad Injector — Figma Plugin
// Multi-template: each ad specifies a "template" name, plugin finds and clones it.
figma.showUI(__html__, { width: 420, height: 600 });

function log(message) {
  figma.ui.postMessage({ type: "status", message: "LOG: " + message, error: false });
}

function logError(message) {
  figma.ui.postMessage({ type: "status", message: "ERR: " + message, error: true });
}

function findTextNodes(node) {
  var texts = [];
  if (node.type === "TEXT") {
    texts.push(node);
  }
  if ("children" in node) {
    var children = node.children;
    for (var i = 0; i < children.length; i++) {
      var childTexts = findTextNodes(children[i]);
      for (var j = 0; j < childTexts.length; j++) {
        texts.push(childTexts[j]);
      }
    }
  }
  return texts;
}

function getFontSize(textNode) {
  try {
    var fs = textNode.fontSize;
    if (typeof fs === "number") return fs;
  } catch (e) {}
  return 12;
}

async function setTextSafe(node, newText) {
  var fontName = null;
  try { fontName = node.fontName; } catch (e) {}

  if (fontName && fontName !== figma.mixed) {
    try {
      await figma.loadFontAsync(fontName);
      node.characters = newText;
      return true;
    } catch (e) {}
  } else if (fontName === figma.mixed) {
    try {
      var len = node.characters.length;
      var loaded = {};
      for (var i = 0; i < len; i++) {
        var fn = node.getRangeFontName(i, i + 1);
        if (fn && fn !== figma.mixed) {
          var key = fn.family + "|" + fn.style;
          if (!loaded[key]) {
            await figma.loadFontAsync(fn);
            loaded[key] = true;
          }
        }
      }
      node.characters = newText;
      return true;
    } catch (e) {}
  }

  var fallbacks = [
    { family: "Inter", style: "Regular" },
    { family: "Roboto", style: "Regular" },
    { family: "Arial", style: "Regular" }
  ];
  for (var f = 0; f < fallbacks.length; f++) {
    try {
      await figma.loadFontAsync(fallbacks[f]);
      node.fontName = fallbacks[f];
      node.characters = newText;
      return true;
    } catch (e) {}
  }
  logError("Could not set text: no font worked");
  return false;
}

// Build a map of all top-level frames on the current page by name
function buildTemplateMap() {
  var map = {};
  var children = figma.currentPage.children;
  for (var i = 0; i < children.length; i++) {
    var node = children[i];
    if (node.type === "FRAME" || node.type === "COMPONENT") {
      map[node.name] = node;
    }
    // Also index frames inside sections
    if (node.type === "SECTION" && "children" in node) {
      var sectionChildren = node.children;
      for (var j = 0; j < sectionChildren.length; j++) {
        var child = sectionChildren[j];
        if (child.type === "FRAME" || child.type === "COMPONENT") {
          map[child.name] = child;
        }
      }
    }
  }
  return map;
}

// Find the best matching template for an ad
function findTemplate(ad, templateMap, fallbackFrame) {
  // 1. Exact match on ad.template field
  if (ad.template && templateMap[ad.template]) {
    return templateMap[ad.template];
  }

  // 2. Partial match (template name contains the value)
  if (ad.template) {
    var target = ad.template.toLowerCase();
    var keys = Object.keys(templateMap);
    for (var i = 0; i < keys.length; i++) {
      if (keys[i].toLowerCase().indexOf(target) >= 0) {
        return templateMap[keys[i]];
      }
    }
  }

  // 3. Fall back to selected frame
  return fallbackFrame;
}

figma.ui.onmessage = async function(msg) {
  if (msg.type === "cancel") {
    figma.closePlugin();
    return;
  }
  if (msg.type !== "inject") return;

  var ads = msg.ads;
  log("Received " + ads.length + " ad(s)");

  // Build template map from all frames on page
  var templateMap = buildTemplateMap();
  var templateNames = Object.keys(templateMap);
  log("Templates available (" + templateNames.length + "):");
  for (var t = 0; t < Math.min(templateNames.length, 20); t++) {
    log("  - " + templateNames[t]);
  }

  // Get selected frame as fallback
  var fallbackFrame = null;
  var selection = figma.currentPage.selection;
  if (selection.length > 0) {
    fallbackFrame = selection[0];
    log("Fallback template (selected): " + fallbackFrame.name);
  }

  if (!fallbackFrame && templateNames.length === 0) {
    logError("No frames found on page and nothing selected.");
    return;
  }

  var count = 0;
  var xOffset = 0;

  for (var i = 0; i < ads.length; i++) {
    var ad = ads[i];
    var adId = ad.ad_id || ("ad-" + i);

    // Find the right template
    var template = findTemplate(ad, templateMap, fallbackFrame);
    if (!template) {
      logError(adId + ": no template found for '" + (ad.template || "none") + "'");
      continue;
    }

    log(adId + " -> template: " + template.name);

    try {
      // Clone
      var clone = template.clone();
      // Place clones in a row below all existing content
      if (i === 0) {
        // Find the lowest point on the page
        var maxY = 0;
        for (var c = 0; c < figma.currentPage.children.length; c++) {
          var child = figma.currentPage.children[c];
          var bottom = child.y + child.height;
          if (bottom > maxY) maxY = bottom;
        }
        xOffset = 0;
        clone.y = maxY + 100;
        clone.x = 0;
      } else {
        clone.y = figma.currentPage.children[figma.currentPage.children.length - 2].y;
        clone.x = xOffset;
      }
      xOffset += clone.width + 40;
      clone.name = adId;

      // Find and sort text nodes
      var textNodes = findTextNodes(clone);
      textNodes.sort(function(a, b) { return getFontSize(b) - getFontSize(a); });

      // Build text values
      var textValues = [];
      if (ad.headline) textValues.push(ad.headline);
      if (ad.hero_copy) textValues.push(ad.hero_copy);
      if (ad.primary_text) textValues.push(ad.primary_text);
      if (ad.subhead) textValues.push(ad.subhead);
      if (ad.description) textValues.push(ad.description);
      if (ad.cta) textValues.push(ad.cta);

      var limit = Math.min(textNodes.length, textValues.length);
      for (var j = 0; j < limit; j++) {
        await setTextSafe(textNodes[j], textValues[j]);
      }

      count++;
      log("OK: " + adId + " (" + count + "/" + ads.length + ")");

    } catch (err) {
      logError("FAIL " + adId + ": " + err.message);
    }
  }

  // Zoom to show all new frames
  if (count > 0) {
    var newFrames = [];
    var allChildren = figma.currentPage.children;
    for (var n = allChildren.length - count; n < allChildren.length; n++) {
      if (n >= 0) newFrames.push(allChildren[n]);
    }
    if (newFrames.length > 0) {
      figma.viewport.scrollAndZoomIntoView(newFrames);
    }
  }

  log("=== Done. " + count + "/" + ads.length + " ad(s) injected. ===");
};
