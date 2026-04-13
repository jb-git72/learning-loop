"""Convert scored Farm Thru LP JSONs into campaign variant HTML files.

Reads LP-*.json from clients/farm-thru/loop/landing-pages/ and outputs
index-{variant}.html files ready to copy to sales-skill/web/campaigns/FMTH/.

Uses the proven campaign HTML structure (header, hero, form, sections,
trust bar, VIP card, footer, sticky CTA) and injects LP content into
the content sections.

Usage:
    python3 scripts/build_fmth_variants.py
    python3 scripts/build_fmth_variants.py --out /path/to/sales-skill/web/campaigns/FMTH/
"""

import json
import sys
from pathlib import Path

LP_DIR = Path(__file__).parent.parent / "clients/farm-thru/loop/landing-pages"

# Map LP page_id to variant letter for output filename
LP_VARIANT_MAP = {
    "LP-A": "a",   # cause-purpose
    "LP-B": "b",   # transformation-storytelling
    "LP-D": "d",   # cause-purpose (quality angle)
    "LP-E": "e",   # social-belonging / transparency
    "LP-F": "f",   # empathy-founder
    "LP-M": "m",   # transparency-safety
    "LP-N": "n",   # investment-thesis (top scorer)
    "LP-P": "p",   # comparison-switching
}

# Shared images
HERO_IMAGE = "https://farmthru.com.au/cdn/shop/files/69003bffe27c151e286d3416_Rachel_Cow_1.jpg?v=1763463097"
LOGO_URL = "https://farmthru.com.au/cdn/shop/files/Farmthru_he.webp?v=1771293890"


def text_to_paragraphs(text: str) -> str:
    """Convert newline-separated text into HTML paragraphs."""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "\n  ".join(
        f'<p class="campaign-section__text">{p}</p>' for p in paras
    )


def build_sections_html(sections: list[dict]) -> str:
    """Build campaign-section HTML blocks from LP JSON sections.

    The last section titled 'Compliance' gets special treatment — it goes
    in the footer disclaimer, not as a visible section.
    """
    blocks = []
    for section in sections:
        heading = section.get("heading", "")
        body = section.get("body", "")

        # Skip compliance section (handled separately in footer)
        if heading.lower().strip() == "compliance":
            continue

        body_html = text_to_paragraphs(body)
        blocks.append(f"""<section class="campaign-section">
  <h2 class="campaign-section__title">{heading}</h2>
  {body_html}
</section>""")

    return "\n\n".join(blocks)


def get_compliance_text(sections: list[dict]) -> str:
    """Extract compliance section body for footer disclaimer."""
    for section in sections:
        if section.get("heading", "").lower().strip() == "compliance":
            return section.get("body", "")
    # Fallback
    return (
        "This is a pre-registration page for an upcoming equity crowdfunding "
        "campaign. No money is being raised at this stage. Any future offer "
        "will be made via a disclosure document on Birchal. This page is not "
        "financial advice. Consider seeking independent financial advice "
        "before making any investment decision."
    )


def build_variant_html(lp: dict) -> str:
    """Build a complete campaign variant HTML file from LP JSON."""
    headline = lp.get("headline", "")
    subhead = lp.get("subhead", "")
    hero_copy = lp.get("hero_copy", "")
    sections = lp.get("sections", [])
    compliance = get_compliance_text(sections)

    hero_paragraphs = text_to_paragraphs(hero_copy)
    sections_html = build_sections_html(sections)

    return f"""<header class="campaign-header">
  <div class="campaign-header__logos">
    <img src="{LOGO_URL}" alt="FarmThru" class="campaign-header__logo">
  </div>
  <a href="#signupForm" class="campaign-header__cta">Join Waitlist</a>
</header>

<section class="hero">
  <span class="hero__badge">Pre-Launch</span>
  <h1 class="hero__title">{headline}</h1>
  <p class="hero__subtitle">{subhead}</p>

  <img src="{HERO_IMAGE}" alt="FarmThru partner farm" class="hero__image">

  <div class="countdown" id="countdown">
    <div class="countdown__block">
      <span class="countdown__number" data-days>00</span>
      <span class="countdown__label">Days</span>
    </div>
    <div class="countdown__block">
      <span class="countdown__number" data-hours>00</span>
      <span class="countdown__label">Hours</span>
    </div>
    <div class="countdown__block">
      <span class="countdown__number" data-mins>00</span>
      <span class="countdown__label">Mins</span>
    </div>
    <div class="countdown__block">
      <span class="countdown__number" data-secs>00</span>
      <span class="countdown__label">Secs</span>
    </div>
  </div>

  <div class="social-proof">
    <div class="social-proof__avatars">
      <span class="social-proof__avatar">JB</span>
      <span class="social-proof__avatar">KL</span>
      <span class="social-proof__avatar">AM</span>
    </div>
    <span>Join <span class="social-proof__count" id="signupCounter" data-count="0">0</span> people on the waitlist</span>
  </div>
</section>

<section class="signup" id="formContainer">
  <form class="signup__form" id="signupForm">
    <div class="signup__field">
      <input type="text" name="name" class="signup__input" placeholder="First name" autocomplete="given-name">
    </div>
    <div class="signup__field">
      <input type="email" name="email" class="signup__input" placeholder="Email address" required autocomplete="email">
    </div>
    <div class="signup__field">
      <input type="tel" name="phone" class="signup__input" placeholder="Mobile (optional, for SMS updates)" autocomplete="tel">
    </div>
    <input type="hidden" name="utm_source" id="utmSource">
    <input type="hidden" name="utm_medium" id="utmMedium">
    <input type="hidden" name="utm_campaign" id="utmCampaign">
    <input type="hidden" name="utm_content" id="utmContent">
    <button type="submit" class="signup__button">Join the Waitlist</button>
    <p class="signup__disclaimer">Free to join. No obligation. We'll notify you when the campaign goes live.</p>
  </form>
</section>

<section class="thank-you" id="thankYou">
  <div class="thank-you__icon">&#127881;</div>
  <h2 class="thank-you__title">You're on the list.</h2>
  <p class="thank-you__position">Your queue position: <strong id="queuePosition">#0</strong></p>
  <p class="campaign-section__text" style="max-width: 400px; margin: 0 auto 20px;">Share with friends to move up the queue. The higher your position, the earlier you get access when the campaign opens.</p>
  <div class="share">
    <button class="share__btn" data-share="whatsapp">WhatsApp</button>
    <button class="share__btn" data-share="twitter">Twitter</button>
    <button class="share__btn" data-share="facebook">Facebook</button>
    <button class="share__btn" data-share="linkedin">LinkedIn</button>
    <button class="share__btn" data-share="email">Email</button>
    <button class="share__btn" data-share="copy">Copy Link</button>
  </div>
</section>

<section class="campaign-section">
  {hero_paragraphs}
</section>

{sections_html}

<div class="trust">
  <div class="trust__stats">
    <div class="trust__stat">
      <span class="trust__stat-value">50+</span>
      <span class="trust__stat-label">Partner Farms</span>
    </div>
    <div class="trust__stat">
      <span class="trust__stat-value">Sydney+</span>
      <span class="trust__stat-label">Delivery Area</span>
    </div>
    <div class="trust__stat">
      <span class="trust__stat-value">100%</span>
      <span class="trust__stat-label">Regenerative</span>
    </div>
  </div>
</div>

<section class="vip">
  <div class="vip__card">
    <span class="vip__badge">VIP ACCESS</span>
    <h2 class="vip__title">Get first access to invest.</h2>
    <p class="vip__text">Place a refundable $5 deposit to secure VIP status. VIP investors get priority access, exclusive founder updates, and early notice before the campaign opens to the public.</p>
    <ul class="vip__perks">
      <li class="vip__perk">First access when the campaign opens</li>
      <li class="vip__perk">Priority investor updates from the founders</li>
      <li class="vip__perk">Exclusive Q&amp;A session with the FarmThru team</li>
      <li class="vip__perk">Fully refundable at any time</li>
    </ul>
    <div class="vip__price">Refundable deposit: <strong>$5</strong></div>
    <button class="vip__button" id="vipDepositBtn">Secure VIP Access</button>
    <p class="vip__refund">100% refundable. No obligation to invest.</p>
  </div>
</section>

<section class="campaign-section" style="text-align: center;">
  <h2 class="campaign-section__title">Don't miss out.</h2>
  <p class="campaign-section__text" style="max-width: 440px; margin: 0 auto 24px;">Join the waitlist now. It takes 10 seconds and you'll be first to know when FarmThru opens investment to the public.</p>
  <a href="#signupForm" class="signup__button" style="display: inline-block; max-width: 320px; text-decoration: none;">Join the Waitlist</a>
</section>

<footer class="campaign-footer">
  <div class="campaign-footer__logos">
    <img src="{LOGO_URL}" alt="FarmThru" class="campaign-footer__logo" style="filter: brightness(0) invert(1);">
  </div>
  <p class="campaign-footer__disclaimer">{compliance}</p>
</footer>

<div class="sticky-cta hidden" id="stickyCta">
  <a href="#signupForm" class="sticky-cta__btn">Join the Waitlist</a>
</div>

<script>
(function() {{
  var params = new URLSearchParams(window.location.search);
  var utmMap = {{ utm_source: 'utmSource', utm_medium: 'utmMedium', utm_campaign: 'utmCampaign', utm_content: 'utmContent' }};
  Object.keys(utmMap).forEach(function(key) {{
    var el = document.getElementById(utmMap[key]);
    if (el && params.get(key)) el.value = params.get(key);
  }});

  var formSection = document.getElementById('formContainer');
  var stickyCta = document.getElementById('stickyCta');
  if (formSection && stickyCta) {{
    var observer = new IntersectionObserver(function(entries) {{
      entries.forEach(function(entry) {{
        stickyCta.classList.toggle('hidden', entry.isIntersecting);
      }});
    }}, {{ threshold: 0 }});
    observer.observe(formSection);
  }}
}})();
</script>
"""


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Convert LP JSONs to campaign HTML variants")
    parser.add_argument("--out", type=str, default=None,
                        help="Output directory (default: clients/farm-thru/campaigns/variants/)")
    args = parser.parse_args()

    out_dir = Path(args.out) if args.out else (
        Path(__file__).parent.parent / "clients/farm-thru/campaigns/variants"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    lp_files = sorted(LP_DIR.glob("LP-*.json"))
    if not lp_files:
        print(f"ERROR: No LP-*.json files found in {LP_DIR}")
        sys.exit(1)

    print(f"Found {len(lp_files)} LP files in {LP_DIR}")
    print(f"Output directory: {out_dir}\n")

    for lp_file in lp_files:
        lp = json.loads(lp_file.read_text(encoding="utf-8"))
        page_id = lp.get("page_id", lp_file.stem)
        variant = LP_VARIANT_MAP.get(page_id)

        if not variant:
            print(f"  SKIP {page_id} — no variant mapping defined")
            continue

        html = build_variant_html(lp)

        # index.html for variant "a", index-{x}.html for others
        filename = "index.html" if variant == "a" else f"index-{variant}.html"
        out_path = out_dir / filename
        out_path.write_text(html, encoding="utf-8")

        section_count = len([s for s in lp.get("sections", [])
                             if s.get("heading", "").lower().strip() != "compliance"])
        print(f"  OK  {page_id} -> {filename}  ({section_count} sections, {len(html):,} chars)")

    print(f"\nDone. Copy variants to sales-skill with:")
    print(f"  cp {out_dir}/*.html ~/Documents/GitHub/sales-skill/web/campaigns/FMTH/")


if __name__ == "__main__":
    main()
