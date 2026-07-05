import os
import json
import re
import requests
import time
import logging
import contextvars
from typing import Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

from services.key_manager import key_manager

logger = logging.getLogger(__name__)

# Request-scoped custom Gemini API key context variable (safe for concurrency)
personal_gemini_key: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("personal_gemini_key", default=None)

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
class LLMResponse:
    def __init__(self, text: str):
        self.text = text


def call_ollama(prompt_content, system_instruction=None):
    """Call local Ollama service using its native API."""
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
    
    headers = {"Content-Type": "application/json"}
    
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
        
    if isinstance(prompt_content, str):
        messages.append({"role": "user", "content": prompt_content})
    elif isinstance(prompt_content, list):
        content_text = ""
        images = []
        for item in prompt_content:
            if isinstance(item, dict) and "inline_data" in item:
                # Add base64 data directly to images list
                images.append(item["inline_data"].get("data", ""))
            elif isinstance(item, dict) and "text" in item:
                content_text += item["text"] + "\n"
            elif isinstance(item, str):
                content_text += item + "\n"
        
        user_message = {"role": "user", "content": content_text.strip()}
        if images:
            user_message["images"] = images
        messages.append(user_message)
        
    payload = {
        "model": ollama_model,
        "messages": messages,
        "options": {"temperature": 0.1},
        "stream": False
    }
    
    response = requests.post(f"{ollama_url}/api/chat", json=payload, headers=headers, timeout=90)
    response.raise_for_status()
    
    result = response.json()
    return LLMResponse(result["message"]["content"])


def call_openrouter(prompt_content, system_instruction=None):
    """Call OpenRouter service using OpenAI-compatible API."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="OPENROUTER_API_KEY is not configured in your .env file."
        )
        
    model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3-8b-instruct:free")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "ATS Resume Builder",
    }
    
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
        
    if isinstance(prompt_content, str):
        messages.append({"role": "user", "content": prompt_content})
    elif isinstance(prompt_content, list):
        content_list = []
        for item in prompt_content:
            if isinstance(item, dict) and "inline_data" in item:
                mime = item["inline_data"].get("mime_type", "image/png")
                b64_data = item["inline_data"].get("data", "")
                content_list.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64_data}"}
                })
            elif isinstance(item, dict) and "text" in item:
                content_list.append({
                    "type": "text",
                    "text": item["text"]
                })
            elif isinstance(item, str):
                content_list.append({
                    "type": "text",
                    "text": item
                })
        messages.append({"role": "user", "content": content_list})
        
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
    }
    
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=90)
    response.raise_for_status()
    
    choice = response.json()["choices"][0]
    return LLMResponse(choice["message"]["content"])


def call_gemini_with_rotation(
    prompt_content,
    max_retries: int = 3,
    system_instruction: str = None
):
    """
    Original Gemini call logic with automatic key rotation and retry.
    Supports a custom request-scoped personal API key which bypasses rotation.
    """
    last_error = None
    custom_key = personal_gemini_key.get()

    if custom_key:
        key = custom_key
        actual_attempts = 1  # Only 1 attempt for custom key
    else:
        # Dynamically scale attempts to ensure every key is tried if needed
        num_keys = len(key_manager.keys)
        actual_attempts = max(max_retries, num_keys)

    for attempt in range(actual_attempts):
        if not custom_key:
            key = key_manager.get_available_key()
            if key is None:
                # Distinguish "temporarily rate-limited" from "permanently dead".
                all_invalid = all(
                    k.get("invalid") for k in key_manager.get_status()
                ) if key_manager.keys else False
                if all_invalid:
                    raise HTTPException(
                        status_code=503,
                        detail="All configured Gemini API keys are invalid or suspended. "
                               "Add a working key (GEMINI_KEY_1) or supply a personal key."
                    )
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

            # Detect a permanently-dead key (suspended, revoked, or malformed).
            # These never recover, so skip the key and try the next one.
            is_invalid_key = (
                "consumer_suspended" in error_str or
                "suspended" in error_str or
                "permission_denied" in error_str or
                "api key not valid" in error_str or
                "api_key_invalid" in error_str or
                "403" in error_code
            )

            if is_invalid_key and not (is_daily_exhausted or is_rate_limited):
                if custom_key:
                    raise HTTPException(
                        status_code=400,
                        detail="Your personal Gemini API key is invalid or suspended. "
                               "Please check the key and try again."
                    )
                key_manager.mark_invalid(key)
                logger.error(
                    f"🚫 Key ...{key[-4:]} is invalid/suspended. Rotating to next key."
                )
                continue

            if is_daily_exhausted:
                if custom_key:
                    raise HTTPException(
                        status_code=429,
                        detail="Your personal Gemini API key has exhausted its daily request limit."
                    )
                key_manager.mark_daily_exhausted(key)
                logger.warning(
                    f"📅 Daily quota exhausted for key ...{key[-4:]}. Rotating to next key."
                )
                continue

            elif is_rate_limited:
                if custom_key:
                    raise HTTPException(
                        status_code=429,
                        detail="Your personal Gemini API key is rate limited. Please try again in a minute."
                    )
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


def call_gemini_with_retry(
    prompt_content,
    max_retries: int = 3,
    system_instruction: str = None,
    provider: str = None
):
    """
    Unified LLM call routing. Supports Gemini, Ollama, and OpenRouter.
    """
    if not provider:
        provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
    else:
        provider = provider.lower().strip()
    
    if provider == "ollama":
        try:
            return call_ollama(prompt_content, system_instruction)
        except Exception as e:
            logger.error(f"Ollama call failed: {e}", exc_info=True)
            raise HTTPException(status_code=502, detail=f"Ollama connection failed: {str(e)}")
            
    elif provider == "openrouter":
        try:
            return call_openrouter(prompt_content, system_instruction)
        except Exception as e:
            logger.error(f"OpenRouter call failed: {e}", exc_info=True)
            raise HTTPException(status_code=502, detail=f"OpenRouter API call failed: {str(e)}")
            
    else:
        # Default: Gemini
        return call_gemini_with_rotation(prompt_content, max_retries, system_instruction)



# ---------------------------------------------------------------------------
# Resume parsing
# ---------------------------------------------------------------------------
def parse_resume(resume_text: str, provider: str = None) -> dict:
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
            system_instruction=system_instruction_text,
            provider=provider
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
    provider: str = None,
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
                    keyword_hint, adapted_prompt, provider
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
                        keyword_hint, adapted_prompt, provider
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
                                f"({orig_s:.1f} \u2192 {rew_s:.1f}). Keeping original."
                            )
                            rewritten_item = item

                    # Keyword coverage check \u2014 retry once if too few keywords matched
                    if jd_keywords and rewritten_item != item:
                        rewritten_text_flat = json.dumps(rewritten_item).lower()
                        required_kws = [t for t, _ in jd_keywords.get("required", [])[:15]]
                        if required_kws:
                            matched_count = sum(
                                1 for kw in required_kws
                                if kw.lower() in rewritten_text_flat
                            )
                            coverage = matched_count / len(required_kws)
                            if coverage < 0.3:  # Less than 30% of required keywords
                                logger.info(
                                    f"{section_name}: keyword coverage {coverage:.0%}, "
                                    f"retrying with stronger prompt"
                                )
                                missing_kws = [
                                    kw for kw in required_kws
                                    if kw.lower() not in rewritten_text_flat
                                ]
                                stronger_hint = (
                                    f"{keyword_hint}\n\n"
                                    f"CRITICAL: The following keywords MUST appear "
                                    f"in this section: {', '.join(missing_kws[:10])}"
                                )
                                retry_text = _rewrite_single_item(
                                    json.dumps(rewritten_item, indent=2),
                                    display_name, locked_facts, jd,
                                    stronger_hint, adapted_prompt, provider
                                )
                                try:
                                    retry_item = json.loads(retry_text)
                                    retry_flat = json.dumps(retry_item).lower()
                                    retry_matched = sum(
                                        1 for kw in required_kws
                                        if kw.lower() in retry_flat
                                    )
                                    if retry_matched > matched_count:
                                        rewritten_item = retry_item
                                        logger.info(
                                            f"{section_name}: retry improved coverage "
                                            f"to {retry_matched}/{len(required_kws)}"
                                        )
                                except (json.JSONDecodeError, Exception) as e:
                                    logger.warning(
                                        f"{section_name}: retry failed ({e}), "
                                        f"keeping first rewrite"
                                    )

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
    adapted_prompt: str = None,
    provider: str = None
) -> str:
    """Rewrite one JSON item (or summary string) with keyword injection."""
    system_rules = f"""You are an elite ATS resume writer. Rewrite the given resume
section to maximise alignment with the job description.

You are rewriting a {display_name}.

STRICT RULES:
1. NEVER change any fact: numbers, percentages, dates, URLs, company names,
   institution names, project names, or person names.
2. The locked facts provided must appear EXACTLY as given.
3. Inject the REQUIRED KEYWORDS naturally \u2014 they MUST appear in the output.
4. Keep bullets concise (1-2 lines). Start each with a strong action verb.
5. Return ONLY the rewritten section as valid JSON \u2014 no markdown, no explanation.
6. Do NOT invent experience or achievements that don't exist in the original.
7. Preserve structure exactly: same number of bullets, same number of entries.

SECTION-SPECIFIC GUIDANCE:
- If this is a professional summary: Lead with the target job title and years of experience. Include top 3-5 required skills. Keep it 3-4 sentences max.
- If this is technical skills: Ensure ALL required technologies from the JD appear. Group by category. Use exact technology names matching the JD.
- If this is a work experience entry: Use STAR format (Situation-Task-Action-Result). Quantify impact with metrics. Start each bullet with a past-tense action verb.
- If this is a project entry: Highlight technologies that overlap with JD requirements. Emphasize measurable outcomes and scale."""

    user_message = (
        f"LOCKED FACTS (never modify):\n{json.dumps(locked_facts, indent=2)}\n\n"
        f"{keyword_hint}\n\n"
        f"JOB DESCRIPTION:\n{jd}\n\n"
        f"SECTION TO REWRITE ({display_name}):\n{item_json}"
    )

    if adapted_prompt:
        user_message += f"\n\nLEARNED IMPROVEMENTS (apply if relevant): {adapted_prompt}"

    try:
        response = call_gemini_with_retry(user_message, system_instruction=system_rules, provider=provider)
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