#!/usr/bin/env python3
"""Download Motion Benchmarks 2026 creative example images."""

import os
import time
import urllib.request
import urllib.error

BASE_URL = "https://runt-media.motionapp.com/strapi/"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "research", "motion-benchmarks-2026", "images")

IMAGES = [
    # TVS (Top Visual Styles)
    "tvs_raw_002_sign_afcb56ebdf.png",
    "tvs_raw_003_feature_benefit_pointout_a5c16e39f6.png",
    "tvs_raw_004_ugc_overlay_780f649f60.png",
    "tvs_raw_006_us_vs_them_7a29286c9f.png",
    "tvs_006_how_to_c2d32d3334.png",
    "tvs_raw_008_letter_c7d3e93add.png",
    "tvs_raw_009_unconventional_text_placement_9e6f2f9ec8.png",
    # THH (Top Hooks & Headlines)
    "thh_001_offer_only_f2c56357d6.png",
    "thh_002_storytelling_80034ad25b.png",
    "thh_003_question_a5db71c1de.png",
    "thh_005_listicle_cfeb53e356.png",
    "thh_007_explainer_a822a823cf.png",
    "thh_008_curiosity_5c4fd0d5d4.png",
    "thh_009_confession_06739c5b8c.png",
    "thh_010_bold_claim_9f81b833f4.png",
    # TAT (Top Asset Types)
    "tat_raw_001_ugc_36c50a1436.png",
    "tat_raw_002_high_production_1c387e8dce.png",
    "tat_raw_003_product_image_with_text_f89a73d14d.png",
    "tat_raw_004_lifestyle_image_with_text_3f440751ff.png",
    "tat_raw_005_lifestyle_product_image_with_text_905ca11174.png",
    "tat_raw_006_text_only_e23b7f3997.png",
    "tat_raw_007_gif_487fe3c0f2.png",
    "tat_raw_008_ugc_mashup_9774cb27d2.png",
    "tat_raw_009_animation_55f952a7f9.png",
    "tat_raw_010_hybrid_f25a3d0ccd.png",
]

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    success = 0
    failed = []

    for i, filename in enumerate(IMAGES):
        url = BASE_URL + filename
        dest = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            print(f"  [{i+1}/{len(IMAGES)}] SKIP (exists): {filename}")
            success += 1
            continue

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "learning-loop/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            with open(dest, "wb") as f:
                f.write(data)
            size_kb = len(data) / 1024
            print(f"  [{i+1}/{len(IMAGES)}] OK ({size_kb:.0f} KB): {filename}")
            success += 1
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            print(f"  [{i+1}/{len(IMAGES)}] FAIL: {filename} — {e}")
            failed.append(filename)

        # Be polite to the CDN
        if i < len(IMAGES) - 1:
            time.sleep(0.3)

    print(f"\nDone: {success}/{len(IMAGES)} downloaded, {len(failed)} failed.")
    if failed:
        print("Failed files:")
        for f in failed:
            print(f"  - {f}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
