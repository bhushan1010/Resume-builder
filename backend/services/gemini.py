import os
import json
import re
import time
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

from services.key_manager import key_manager

logger = logging.getLogger(__name__)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Proper section display names for LLM prompts — fixes the `section[:-1]` bug
SECTION_DISPLAY_NAME = {
    "summary":        "professional summary",
    "skills":         "technical skills",
    "internship":     "work experience entry",
    "projects":       "project entry",
    "education":      "education entry",
    "certifications": "certification entry",
}


# ---------------------------------------------------------------------------
# Core Gemini call with key rotation + retry
# ---------------------------------------------------------------------------
def call_gemini_with_retry(
    prompt_content,
    max_retries: int = 3,
    system_instruction: str = None
):
    """
    Call Gemini API with automatic key rotation and retry.
    prompt_content can be str or list (for vision calls).
    """
    last_error = None

    # Dynamically scale attempts to ensure every key is tried if needed
    num_keys = len(key_manager.keys)
    actual_attempts = max(max_retries, num_keys)

    for attempt in range(actual_attempts):
        key = key_manager.get_available_key()
        if key is None:
            raise HTTPException(
                status_code=503,
                detail="All API keys are currently rate limited. Please try again in about a minute."
            )

        try:
            client = genai.Client(api_key=key)

            config = (
                types.GenerateContentConfig(system_instruction=system_instruction)
                if system_instruction else None
            )

            if config:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt_content,
                    config=config
                )
            else:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt_content
                )
            return response

        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            error_code = str(e)

            # Detect daily quota exhaustion (free-tier 20/day limit)
            is_daily_exhausted = (
                "per_day" in error_str or
                "per day" in error_str or
                "daily" in error_str or
                "free_tier" in error_str or
                "generateRequestsPerDayPerProjectPerModel".lower() in error_str
            )

            # Detect rate limit (per-minute 429)
            is_rate_limited = (
                "429" in error_code and not is_daily_exhausted
            ) or (
                ("rate" in error_str or "quota" in error_str) and not is_daily_exhausted
            )

            if is_daily_exhausted:
                key_manager.mark_daily_exhausted(key)
                logger.warning(
                    f"📅 Daily quota exhausted for key ...{key[-4:]}. Rotating to next key."
                )
                continue

            elif is_rate_limited:
                key_manager.mark_rate_limited(key)
                wait_seconds = 2 ** attempt   # 1s, 2s, 4s
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{max_retries}). "
                    f"Waiting {wait_seconds}s."
                )
                time.sleep(wait_seconds)
                continue

            else:
                logger.error(f"Gemini call failed (non-retriable): {e}", exc_info=True)
                raise

    logger.error(f"Gemini call failed after {actual_attempts} attempts. Last error: {last_error}")
    raise HTTPException(
        status_code=503,
        detail=(
            "The AI rewriting service has reached its daily request limit. "
            "Please try again tomorrow, or add more Gemini API keys to your .env file."
        )
    )


# ---------------------------------------------------------------------------
# Resume parsing
# ---------------------------------------------------------------------------
def parse_resume(resume_text: str) -> dict:
    """Parse raw resume text into structured JSON using Gemini."""
    system_instruction_text = (
        "You are a resume parser. Parse the given resume text into structured JSON "
        "exactly matching the schema provided. Return ONLY valid JSON, no markdown, "
        "no explanation."
    )

    schema = {
        "header": {
            "name": "", "email": "", "phone": "",
            "linkedin": "", "github": "", "portfolio": "", "leetcode": ""
        },
        "summary": "",
        "education":      [{"institution": "", "degree": "", "duration": ""}],
        "projects":       [{"name": "", "url": "", "duration": "", "bullets": []}],
        "internship":     [{"company": "", "url": "", "role": "", "duration": "", "bullets": []}],
        "skills":         [{"category": "", "items": ""}],
        "certifications": [{"name": "", "url": "", "duration": ""}],
    }

    user_prompt = (
        f"Parse this resume text:\n{resume_text}\n\n"
        f"Return ONLY the JSON matching this schema:\n{json.dumps(schema, indent=2)}"
    )

    try:
        response = call_gemini_with_retry(
            user_prompt,
            system_instruction=system_instruction_text
        )
        cleaned = re.sub(r'```json|```', '', response.text).strip()
        parsed_data = json.loads(cleaned)

        return {
            "header": {
                "name":      parsed_data.get("header", {}).get("name", ""),
                "email":     parsed_data.get("header", {}).get("email", ""),
                "phone":     parsed_data.get("header", {}).get("phone", ""),
                "linkedin":  parsed_data.get("header", {}).get("linkedin", ""),
                "github":    parsed_data.get("header", {}).get("github", ""),
                "portfolio": parsed_data.get("header", {}).get("portfolio", ""),
                "leetcode":  parsed_data.get("header", {}).get("leetcode", ""),
            },
            "summary":        parsed_data.get("summary", ""),
            "education":      parsed_data.get("education", []),
            "projects":       parsed_data.get("projects", []),
            "internship":     parsed_data.get("internship", []),
            "skills":         parsed_data.get("skills", []),
            "certifications": parsed_data.get("certifications", []),
        }
    except Exception as e:
        logger.error(f"Failed to parse resume: {e}", exc_info=True)
        raise


# ---------------------------------------------------------------------------
# Resume rewriting — with keyword injection + verification loop
# ---------------------------------------------------------------------------
def rewrite_resume(
    parsed_json: dict,
    jd: str,
    adapted_prompt: str = None,
    jd_keywords: dict = None,
) -> dict:
    """
    Rewrite resume sections to maximise JD alignment.
    - Injects extracted JD keywords into every section prompt
    - Verifies each section scores >= original; falls back if not
    - Uses correct section display names (fixes the `section[:-1]` bug)
    """
    # Lazy import to avoid circular deps
    from services import ats_scorer

    locked_facts = extract_locked_facts(parsed_json)

    # Extract JD keywords if not pre-computed (avoids re-computing per section)
    if jd_keywords is None:
        jd_keywords = ats_scorer.extract_jd_keywords(jd)

    # Build a concise keyword hint string for injection into prompts
    required_hint  = ", ".join(t for t, _ in jd_keywords.get("required",  [])[:20])
    preferred_hint = ", ".join(t for t, _ in jd_keywords.get("preferred", [])[:15])
    keyword_hint = f"REQUIRED KEYWORDS TO USE: {required_hint}"
    if preferred_hint:
        keyword_hint += f"\nPREFERRED KEYWORDS (use if naturally fitting): {preferred_hint}"

    sections_to_rewrite = ["summary", "skills", "internship", "projects"]
    rewritten_json = parsed_json.copy()

    for section_name in sections_to_rewrite:
        try:
            section_content = parsed_json.get(section_name, [])
            display_name = SECTION_DISPLAY_NAME.get(section_name, section_name)

            if section_name == "summary":
                original_text = json.dumps({"summary": section_content}, indent=2)
                rewritten_text = _rewrite_single_item(
                    original_text, display_name, locked_facts, jd,
                    keyword_hint, adapted_prompt
                )
                rewritten_data = json.loads(rewritten_text)
                candidate = rewritten_data.get("summary", section_content)

                # Verification: ensure rewrite didn't degrade summary score
                original_score = ats_scorer.calculate_semantic_similarity(
                    str(section_content), jd
                )
                rewritten_score = ats_scorer.calculate_semantic_similarity(
                    str(candidate), jd
                )
                if rewritten_score >= original_score - 2:   # allow 2pt tolerance
                    rewritten_json[section_name] = candidate
                else:
                    logger.warning(
                        f"Summary rewrite degraded score ({original_score:.1f} → "
                        f"{rewritten_score:.1f}). Keeping original."
                    )
                    rewritten_json[section_name] = section_content

            else:
                rewritten_items = []
                for item in section_content:
                    item_text = json.dumps(item, indent=2)
                    rewritten_text = _rewrite_single_item(
                        item_text, display_name, locked_facts, jd,
                        keyword_hint, adapted_prompt
                    )
                    try:
                        rewritten_item = json.loads(rewritten_text)
                    except json.JSONDecodeError:
                        logger.warning(
                            f"JSON parse failed for rewritten {section_name} item. "
                            "Keeping original."
                        )
                        rewritten_item = item

                    # Verification: check bullet quality didn't drop
                    original_bullets = " ".join(item.get("bullets", []))
                    rewritten_bullets = " ".join(rewritten_item.get("bullets", []))
                    if original_bullets and rewritten_bullets:
                        orig_s = ats_scorer.calculate_semantic_similarity(original_bullets, jd)
                        rew_s  = ats_scorer.calculate_semantic_similarity(rewritten_bullets, jd)
                        if rew_s < orig_s - 5:   # 5pt tolerance for items
                            logger.warning(
                                f"{section_name} item rewrite degraded "
                                f"({orig_s:.1f} → {rew_s:.1f}). Keeping original."
                            )
                            rewritten_item = item

                    rewritten_items.append(rewritten_item)

                rewritten_json[section_name] = rewritten_items

        except Exception as e:
            logger.error(
                f"Failed to rewrite section '{section_name}': {e}", exc_info=True
            )
            # Keep original section — never leave it empty
            rewritten_json[section_name] = parsed_json.get(section_name, [])

    return rewritten_json


def _rewrite_single_item(
    item_json: str,
    display_name: str,
    locked_facts: dict,
    jd: str,
    keyword_hint: str,
    adapted_prompt: str = None
) -> str:
    """Rewrite one JSON item (or summary string) with keyword injection."""
    system_rules = """You are an elite ATS resume writer. Rewrite the given resume
section to maximise alignment with the job description.

STRICT RULES:
1. NEVER change any fact: numbers, percentages, dates, URLs, company names,
   institution names, project names, or person names.
2. The locked facts provided must appear EXACTLY as given.
3. Inject the REQUIRED KEYWORDS naturally — they MUST appear in the output.
4. Keep bullets concise (1-2 lines). Start each with a strong action verb.
5. Return ONLY the rewritten section as valid JSON — no markdown, no explanation.
6. Do NOT invent experience or achievements that don't exist in the original.
7. Preserve structure exactly: same number of bullets, same number of entries."""

    user_message = (
        f"LOCKED FACTS (never modify):\n{json.dumps(locked_facts, indent=2)}\n\n"
        f"{keyword_hint}\n\n"
        f"JOB DESCRIPTION:\n{jd}\n\n"
        f"SECTION TO REWRITE ({display_name}):\n{item_json}"
    )

    if adapted_prompt:
        user_message += f"\n\nLEARNED IMPROVEMENTS (apply if relevant): {adapted_prompt}"

    try:
        response = call_gemini_with_retry(user_message, system_instruction=system_rules)
        cleaned = re.sub(r'```json|```', '', response.text).strip()
        json.loads(cleaned)   # validate JSON before returning
        return cleaned
    except Exception as e:
        logger.error(f"Rewrite failed for '{display_name}': {e}", exc_info=True)
        return item_json   # return original on any error


# ---------------------------------------------------------------------------
# Locked fact extraction
# ---------------------------------------------------------------------------
def extract_locked_facts(parsed_json: dict) -> dict:
    """Extract facts that must not be changed during rewriting."""
    locked = {"urls": [], "dates": [], "numbers": [], "names": [], "contact": []}

    def _extract(text):
        if not isinstance(text, str):
            return
        locked["urls"].extend(re.findall(r'https?://\S+', text))

        for pat in [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',
            r'\b\d{4}\b',
        ]:
            locked["dates"].extend(re.findall(pat, text, re.IGNORECASE))

        for pat in [
            r'\b\d+\.?\d*%\b',
            r'\b\d+[+,]?\d*\s*(?:users?|people|customers?|clients?|projects?)\b',
            r'\b\d+[+,]?\d*\s*(?:million|billion|thousand)\b',
        ]:
            locked["numbers"].extend(re.findall(pat, text, re.IGNORECASE))

        common = {'The', 'And', 'Or', 'But', 'In', 'On', 'At', 'To', 'For', 'Of'}
        names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        locked["names"].extend(
            n for n in names if n not in common and len(n.split()) <= 3
        )

    header = parsed_json.get("header", {})
    for v in header.values():
        if v:
            _extract(v)

    _extract(parsed_json.get("summary", ""))

    for section in ("education", "projects", "internship", "skills", "certifications"):
        for item in parsed_json.get(section, []):
            if isinstance(item, dict):
                for k, v in item.items():
                    if k == "bullets":
                        for b in v:
                            _extract(b)
                    elif v:
                        _extract(v)

    if header.get("email"):
        locked["contact"].append(header["email"])
    if header.get("phone"):
        locked["contact"].append(header["phone"])
    if header.get("linkedin"):
        locked["contact"].append(header["linkedin"])
    if header.get("github"):
        locked["contact"].append(header["github"])

    # Deduplicate
    for k in locked:
        seen = set()
        locked[k] = [x for x in locked[k] if not (x in seen or seen.add(x))]

    return locked