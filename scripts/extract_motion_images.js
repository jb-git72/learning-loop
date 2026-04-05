/**
 * Browser console script to extract all visual format example images
 * from Motion Creative Benchmarks 2026.
 *
 * HOW TO USE:
 * 1. Open https://motionapp.com/thumbstop-pulse/creative-benchmarks-2026
 * 2. Scroll down to the "Top Visual Styles by Vertical" section (Chart 10)
 * 3. Open browser DevTools (Cmd+Option+I on Mac)
 * 4. Paste this entire script into the Console tab
 * 5. Press Enter — it will cycle through all industries and collect image URLs
 * 6. Copy the JSON output and save it to:
 *    research/motion-benchmarks-2026/image-manifest.json
 *
 * ALTERNATIVE (faster):
 * If the dropdown doesn't auto-cycle, just manually click each industry
 * while this is running. The MutationObserver will capture images as they appear.
 */

(async function extractMotionImages() {
  const results = {};
  const allImages = new Set();

  // Method 1: Capture all images currently visible with runt-media domain
  function captureCurrentImages() {
    const images = document.querySelectorAll('img[src*="runt-media.motionapp.com"]');
    const found = [];
    images.forEach(img => {
      const src = img.src;
      if (src && !allImages.has(src)) {
        allImages.add(src);
        // Parse the URL to extract metadata
        const match = src.match(/cb2026-chart(\d+)\/(.+)\.jpeg/);
        if (match) {
          const filename = match[2];
          const parts = filename.split('-');
          found.push({
            url: src,
            filename: match[2] + '.jpeg',
            chart: 'chart' + match[1],
            alt: img.alt || '',
            width: img.naturalWidth,
            height: img.naturalHeight,
          });
        }
      }
    });
    return found;
  }

  // Method 2: Also check background images
  function captureBackgroundImages() {
    const found = [];
    document.querySelectorAll('*').forEach(el => {
      const bg = getComputedStyle(el).backgroundImage;
      if (bg && bg.includes('runt-media.motionapp.com')) {
        const urlMatch = bg.match(/url\("?([^"]+)"?\)/);
        if (urlMatch && !allImages.has(urlMatch[1])) {
          allImages.add(urlMatch[1]);
          found.push({
            url: urlMatch[1],
            filename: urlMatch[1].split('/').pop(),
            chart: 'background',
          });
        }
      }
    });
    return found;
  }

  // Method 3: Try to find and cycle through the industry selector
  async function cycleIndustries() {
    // Look for dropdown/select elements or buttons that switch industries
    const selectors = [
      'select', '[role="listbox"]', '[data-testid*="select"]',
      'button[data-value]', '[class*="dropdown"]', '[class*="select"]',
      '[class*="vertical"]', '[class*="industry"]',
    ];

    for (const sel of selectors) {
      const elements = document.querySelectorAll(sel);
      for (const el of elements) {
        if (el.tagName === 'SELECT') {
          const options = el.querySelectorAll('option');
          for (const opt of options) {
            el.value = opt.value;
            el.dispatchEvent(new Event('change', { bubbles: true }));
            await new Promise(r => setTimeout(r, 1500));
            const found = captureCurrentImages();
            if (found.length > 0) {
              const industry = opt.textContent.trim() || opt.value;
              results[industry] = (results[industry] || []).concat(found);
              console.log(`Found ${found.length} images for ${industry}`);
            }
          }
        }
      }
    }
  }

  // Capture what's visible now
  console.log('Capturing currently visible images...');
  let initial = captureCurrentImages();
  let bgImages = captureBackgroundImages();
  console.log(`Found ${initial.length} img tags, ${bgImages.length} background images`);

  // Try cycling industries
  console.log('Attempting to cycle through industry selector...');
  await cycleIndustries();

  // Final capture
  let finalCapture = captureCurrentImages();

  // Build output
  const allFound = [...initial, ...bgImages, ...finalCapture];
  const uniqueUrls = [...new Set(allFound.map(i => i.url))];

  const manifest = {
    source: 'https://motionapp.com/thumbstop-pulse/creative-benchmarks-2026',
    extracted_at: new Date().toISOString(),
    total_images: uniqueUrls.length,
    by_industry: results,
    all_images: allFound.filter((item, index, self) =>
      index === self.findIndex(t => t.url === item.url)
    ),
  };

  console.log('\n=== RESULTS ===');
  console.log(`Total unique images: ${uniqueUrls.length}`);
  console.log('\nURLs:');
  uniqueUrls.forEach(u => console.log(u));
  console.log('\nFull manifest (copy this):');
  console.log(JSON.stringify(manifest, null, 2));

  // Also copy to clipboard
  try {
    await navigator.clipboard.writeText(JSON.stringify(manifest, null, 2));
    console.log('\n✓ Manifest copied to clipboard!');
  } catch (e) {
    console.log('\n(Could not copy to clipboard — copy the JSON above manually)');
  }

  return manifest;
})();
