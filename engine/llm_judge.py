"""
LLM Judge — Separate-context scoring for subjective rubric dimensions.

KEY DESIGN: This makes a SEPARATE API call for each dimension.
The LLM doing the scoring has ZERO shared context with the writer.
It only sees: the rubric definition + the ad text. Nothing else.

This is the anti-cheating mechanism. The writer can't game what it can't see.

Uses claude CLI (haiku model, temperature 0) for cost-efficient scoring.
Falls back to API call if anthropic SDK is available.
Falls back to heuristic if nothing works (clearly marked in output).
"""

import json
import os
import re
import subprocess
import threading


def _format_content_block(ad):
    """Format ad content fields based on content_type. Used by all scoring prompts."""
    ct = ad.get("content_type", "meta-ad")
    if ct == "email":
        return "SUBJECT: %s\nPREHEADER: %s\nBODY: %s" % (
            ad.get("subject", ""), ad.get("preheader", ""), ad.get("body", "")[:500])
    elif ct == "sms":
        return "SMS BODY (purpose=%s, audience=%s):\n%s" % (
            ad.get("purpose", "?"), ad.get("audience", "?"), ad.get("body", ""))
    elif ct == "landing-page":
        parts = ["HEADLINE: %s" % ad.get("headline", ""),
                 "SUBHEAD: %s" % ad.get("subhead", ""),
                 "HERO COPY: %s" % ad.get("hero_copy", "")]
        for section in ad.get("sections", []):
            if isinstance(section, dict):
                heading = section.get("heading", "")
                body = section.get("body", "")[:300]
                if heading:
                    parts.append("SECTION: %s\n%s" % (heading, body))
        return "\n\n".join(parts)
    else:
        return "HEADLINE: %s\nPRIMARY TEXT: %s\nDESCRIPTION: %s" % (
            ad.get("headline", ""), ad.get("primary_text", ""), ad.get("description", ""))


def judge_dimension(dim_id, ad, dimension_schema, client_config):
    """Score one dimension via a separate LLM call.

    Uses the batch cache if available (all 3 dimensions scored in 1 call).
    Falls back to single-dimension call if cache miss.
    """
    # Check batch cache first
    ad_id = ad.get("ad_id", "")
    cache_key = "%s:%s" % (ad_id, id(ad))
    with _cache_lock:
        if cache_key in _batch_cache:
            cached = _batch_cache[cache_key]
            if dim_id in cached:
                s, e = cached[dim_id]
                return s, "LLM(batch): %s" % e

    # Not cached — do a batch call for all 3 LLM dimensions at once
    all_dims = _get_llm_dimensions()
    if dim_id in [d["id"] for d in all_dims]:
        results = _batch_score(ad, all_dims, client_config)
        if results:
            with _cache_lock:
                _batch_cache[cache_key] = results
            if dim_id in results:
                s, e = results[dim_id]
                return s, "LLM(batch): %s" % e

    # Single dimension fallback
    prompt = _build_scoring_prompt(dim_id, ad, dimension_schema, client_config)
    score, explanation, method = _try_cli(prompt)
    if score is not None:
        return score, "LLM(%s): %s" % (method, explanation)
    score, explanation, method = _try_api(prompt)
    if score is not None:
        return score, "LLM(%s): %s" % (method, explanation)

    return _heuristic_fallback(dim_id, ad)


# Batch cache: avoids 3 separate LLM calls per ad
_batch_cache = {}
_rubric_schema_cache = None
_cache_lock = threading.Lock()


def _get_llm_dimensions():
    """Get the LLM-scored dimension schemas from the rubric."""
    global _rubric_schema_cache
    with _cache_lock:
        if _rubric_schema_cache is not None:
            return [d for d in _rubric_schema_cache.get("dimensions", []) if d.get("scoring_method") == "llm"]
        import glob
        from pathlib import Path
        for p in [Path("learning-loop/shared/rubric-schema.json"), Path("shared/rubric-schema.json")]:
            if p.exists():
                with open(p) as f:
                    _rubric_schema_cache = json.load(f)
                break
        if _rubric_schema_cache is None:
            return []
        return [d for d in _rubric_schema_cache.get("dimensions", []) if d.get("scoring_method") == "llm"]


def _batch_score(ad, dimensions, client_config):
    """Score all LLM dimensions in ONE call. 3x faster than individual calls."""
    dim_sections = []
    for dim in dimensions:
        guide = "\n".join("    %s = %s" % (k, v) for k, v in sorted(dim.get("scoring_guide", {}).items()))
        dim_sections.append("""DIMENSION %d: %s
  Definition: %s
  Scoring scale:
%s""" % (len(dim_sections) + 1, dim.get("name", dim["id"]), dim.get("description", ""), guide))

    # Build brand context from scoring_context in config
    scoring_ctx = client_config.get("scoring_context", {})
    brand_block = ""
    if scoring_ctx:
        brand_block = "\nBRAND CONTEXT:\n"
        if scoring_ctx.get("product"):
            brand_block += "Product: %s\n" % scoring_ctx["product"]
        if scoring_ctx.get("audience"):
            brand_block += "Audience: %s\n" % scoring_ctx["audience"]
        if scoring_ctx.get("key_motivations"):
            brand_block += "Key motivations: %s\n" % "; ".join(scoring_ctx["key_motivations"])
        if scoring_ctx.get("brand_values"):
            brand_block += "Brand values: %s\n" % scoring_ctx["brand_values"]
        if scoring_ctx.get("success_looks_like"):
            brand_block += "Success: %s\n" % scoring_ctx["success_looks_like"]

    content_block = _format_content_block(ad)

    prompt = """Score this ad on %d dimensions. Be strict. Use the FULL 1-5 range.
%s
%s

AD:
Angle: %s | Tactic: %s | Hook: %s

%s

Respond with ONLY valid JSON (no other text):
{%s}""" % (
        len(dimensions),
        "\n\n".join(dim_sections),
        brand_block,
        ad.get("angle", "?"), ad.get("tactic", "?"), ad.get("hook_type", "?"),
        content_block,
        ", ".join('"%s": {"score": <1-5>, "explanation": "<one sentence>"}' % d["id"] for d in dimensions),
    )

    # Try API first (fastest — direct HTTP, no process spawn)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            return _parse_batch_response(response.content[0].text.strip(), [d["id"] for d in dimensions])
        except Exception:
            pass

    # Fallback: CLI
    try:
        result = subprocess.run(
            ["claude", "--model", "haiku", "--print", "-p", prompt],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return _parse_batch_response(result.stdout.strip(), [d["id"] for d in dimensions])
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    return None


def score_ads_parallel(ads, client_config, shared_dir, max_workers=5):
    """Score multiple ads in parallel. Returns list of (ad, scores_dict).

    This is the fast path for batch scoring. Spawns up to max_workers
    parallel CLI processes for the LLM-judged dimensions.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    all_dims = _get_llm_dimensions()
    if not all_dims:
        return {}

    def score_one(ad):
        results = _batch_score(ad, all_dims, client_config)
        return ad.get("ad_id", "?"), results

    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(score_one, ad): ad for ad in ads}
        for future in as_completed(futures):
            ad_id, scores = future.result()
            if scores:
                results[ad_id] = scores
    return results


def _parse_batch_response(text, dim_ids):
    """Parse a batch response with multiple dimension scores."""
    try:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            results = {}
            for dim_id in dim_ids:
                if dim_id in data:
                    entry = data[dim_id]
                    score = int(entry.get("score", 0))
                    if 1 <= score <= 5:
                        results[dim_id] = (score, entry.get("explanation", ""))
            if results:
                return results
    except (json.JSONDecodeError, ValueError, KeyError, AttributeError):
        pass
    return None


def _build_scoring_prompt(dim_id, ad, dimension_schema, client_config):
    """Build a self-contained scoring prompt with brand context but no writer context."""

    scoring_guide = dimension_schema.get("scoring_guide", {})
    dim_name = dimension_schema.get("name", dim_id)
    description = dimension_schema.get("description", "")

    guide_lines = "\n".join("  %s = %s" % (k, v) for k, v in sorted(scoring_guide.items()))

    # Brand context from scoring_context
    scoring_ctx = client_config.get("scoring_context", {})
    brand_block = ""
    if scoring_ctx:
        parts = []
        if scoring_ctx.get("product"):
            parts.append("Product: %s" % scoring_ctx["product"])
        if scoring_ctx.get("audience"):
            parts.append("Audience: %s" % scoring_ctx["audience"])
        if scoring_ctx.get("key_motivations"):
            parts.append("Key motivations: %s" % "; ".join(scoring_ctx["key_motivations"]))
        if parts:
            brand_block = "\nBRAND CONTEXT:\n" + "\n".join(parts) + "\n"

    content_block = _format_content_block(ad)

    return """Score this ad on ONE dimension. Be strict and discriminating.

DIMENSION: %s
DEFINITION: %s

SCORING SCALE:
%s
%s
IMPORTANT: Use the FULL range. Most ads should score 2-4. A 5 is exceptional. A 1 is genuinely bad. Do not default to 3.

AD TO SCORE:
Angle: %s
Tactic: %s
Hook type: %s

%s

Respond with ONLY valid JSON, no other text:
{"score": <integer 1-5>, "explanation": "<one sentence justifying the score>"}""" % (
        dim_name,
        description,
        guide_lines,
        brand_block,
        ad.get("angle", "unknown"),
        ad.get("tactic", "unknown"),
        ad.get("hook_type", "unknown"),
        content_block,
    )


def _try_cli(prompt):
    """Score via claude CLI — separate process, zero shared context."""
    try:
        result = subprocess.run(
            ["claude", "--model", "haiku", "--print", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            score, explanation = _parse_response(result.stdout.strip())
            if score is not None:
                return score, explanation, "haiku-cli"
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass
    return None, None, None


def _try_api(prompt):
    """Score via Anthropic API — if SDK and key are available."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None, None, None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        score, explanation = _parse_response(text)
        if score is not None:
            return score, explanation, "haiku-api"
    except Exception:
        pass
    return None, None, None


def _parse_response(text):
    """Parse LLM response. Returns (score, explanation) or (None, None)."""
    # Try JSON parse — use DOTALL so explanations containing {} don't truncate
    try:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            score = int(data.get("score", 0))
            if 1 <= score <= 5:
                return score, data.get("explanation", "")
    except (json.JSONDecodeError, ValueError, KeyError):
        pass

    # Try bare number
    num_match = re.search(r'\b([1-5])\b', text)
    if num_match:
        return int(num_match.group(1)), text[:100]

    return None, None


def score_pairwise(new_ad: dict, current_ad: dict, client_config: dict,
                   weak_dimensions: list = None) -> tuple:
    """Compare new candidate against current best. Returns (1-5, explanation).
    1 = new is much worse, 3 = equal, 5 = new is much better."""
    scoring_ctx = client_config.get("scoring_context", {})
    brand_name = client_config.get("client_name", scoring_ctx.get("product", "this brand"))

    current_block = _format_content_block(current_ad)
    new_block = _format_content_block(new_ad)

    # Build focus text for weak dimensions
    focus_text = ""
    if weak_dimensions:
        dims_str = ", ".join("%s (%d/%d)" % (d[0], d[1], d[2]) for d in weak_dimensions)
        focus_text = "\nFocus especially on these weak areas: %s\n" % dims_str

    prompt = """Compare these two ads for %s. Which is stronger overall?

CURRENT (the one being replaced):
%s

NEW CANDIDATE:
%s
%s
Score the NEW candidate relative to CURRENT:
1 = Much worse (significant regression)
2 = Worse (noticeable step back)
3 = About equal
4 = Better (meaningful improvement)
5 = Much better (clear winner)

Respond with ONLY valid JSON: {"score": <1-5>, "reason": "<one sentence>"}""" % (
        brand_name, current_block, new_block, focus_text,
    )

    # Try API first
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            result = _parse_pairwise_response(text)
            if result:
                return result
        except Exception:
            pass

    # Fallback: CLI
    try:
        result = subprocess.run(
            ["claude", "--model", "haiku", "--print", "-p", prompt],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            parsed = _parse_pairwise_response(result.stdout.strip())
            if parsed:
                return parsed
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    # Graceful fallback
    return (3, "pairwise unavailable")


def _parse_pairwise_response(text):
    """Parse pairwise JSON response. Returns (score, reason) or None."""
    try:
        # Use DOTALL so reasons containing {} don't truncate the match
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            score = int(data.get("score", 0))
            if 1 <= score <= 5:
                return (score, data.get("reason", ""))
    except (json.JSONDecodeError, ValueError, KeyError):
        pass
    # Try bare number
    num_match = re.search(r'\b([1-5])\b', text)
    if num_match:
        return (int(num_match.group(1)), text[:100])
    return None


def _heuristic_fallback(dim_id, ad):
    """Last resort. Clearly marked as heuristic in output."""
    ct = ad.get("content_type", "meta-ad")
    if ct == "email":
        text = " ".join(ad.get(f, "") for f in ["subject", "preheader", "body"])
    elif ct == "sms":
        text = ad.get("body", "")
    elif ct == "landing-page":
        text = " ".join(ad.get(f, "") for f in ["headline", "subhead", "hero_copy"])
    else:
        text = " ".join(ad.get(f, "") for f in ["primary_text", "headline", "description"])

    if dim_id == "angle_clarity":
        word_count = len(text.split())
        if 50 <= word_count <= 120:
            return 3, "HEURISTIC(degraded): reasonable length, no LLM available"
        return 2, "HEURISTIC(degraded): length suggests unclear focus, no LLM available"

    if dim_id == "motivation_match":
        emotional = len(re.findall(
            r'\b(love|worry|guilt|relief|peace|fear|anxiety|dread|stress|joy)\b',
            text, re.IGNORECASE
        ))
        score = min(2 + emotional, 4)  # cap at 4, never 5 without LLM
        return score, "HEURISTIC(degraded): %d emotional words, no LLM available" % emotional

    if dim_id == "tactic_execution":
        if ct == "email":
            has_parts = sum([bool(ad.get("subject")), len(ad.get("body", "")) > 50, bool(ad.get("cta"))])
        elif ct == "landing-page":
            has_parts = sum([bool(ad.get("headline")), len(ad.get("hero_copy", "")) > 50, bool(ad.get("cta"))])
        else:
            has_parts = sum([bool(ad.get("headline")), len(ad.get("primary_text", "")) > 50, bool(ad.get("cta"))])
        return min(1 + has_parts, 3), "HEURISTIC(degraded): %d/3 structural parts, no LLM available" % has_parts

    if dim_id == "tone_brand_fit":
        # SMS-specific dimension. Rough heuristic: short and on-brand if body
        # contains the brand and avoids hype words.
        body = ad.get("body", "")
        has_brand = bool(re.search(r"farm.?thru", body, re.IGNORECASE))
        hype = bool(re.search(r"\b(huge|amazing|unmissable|don't miss|act now)\b", body, re.IGNORECASE))
        if has_brand and not hype:
            return 3, "HEURISTIC(degraded): brand present, no hype, no LLM available"
        if has_brand:
            return 2, "HEURISTIC(degraded): brand present but hype detected, no LLM available"
        return 2, "HEURISTIC(degraded): brand not detected, no LLM available"

    return 2, "HEURISTIC(degraded): default, no LLM available"
