"""
ai_engine.py  –  Multi-backend AI engine for resume tailoring
Supports Google Gemini (via google.genai), OpenAI, and Anthropic Claude.
Includes retry logic, model fallback, streaming, and structured output.
"""

import os
import json
import time
from pydantic import BaseModel, Field
from typing import List

# ── Schema definitions ───────────────────────────────────────────────────────

class Project(BaseModel):
    name: str
    technologies: List[str]
    bullets: List[str]

class Experience(BaseModel):
    company: str
    role: str
    location: str
    startDate: str
    endDate: str
    bullets: List[str]

class Skills(BaseModel):
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)

class TailoredProfile(BaseModel):
    skills: Skills
    experience: List[Experience]
    projects: List[Project]

# ── Configuration ────────────────────────────────────────────────────────────

GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
OPENAI_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
ANTHROPIC_MODELS = ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022"]

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

SUPPORTED_BACKENDS = ("gemini", "openai", "anthropic")

# ── Helpers ──────────────────────────────────────────────────────────────────

def _validate_base_profile(profile: dict) -> dict:
    """Validate that the base profile has the required structure."""
    if 'basics' not in profile or not isinstance(profile['basics'], dict):
        raise ValueError("Base profile must contain 'basics' as a dictionary.")
    basics = profile['basics']
    if 'name' not in basics or not basics['name']:
        raise ValueError("Base profile 'basics' must include a 'name'.")
    return profile


def _build_prompt(base_profile_dict: dict, job_description: str, company_name: str) -> str:
    """Build the prompt for the AI model."""
    return f"""You are an expert technical resume strategist. You will be given:
1. [CANDIDATE PROFILE] — the candidate's master resume (skills, experience, projects, education)
2. [JD] — a job description
3. [COMPANY BG] — brief company background

Your task: Rewrite the candidate's resume to maximize ATS score and recruiter relevance for THIS specific role and company. Follow these rules precisely:

─── STRUCTURE ───────────────────────────────────
- Keep the same section order: Experience → Projects → Skills → Education → Certifications
- Do NOT invent any new experience, companies, dates, or credentials
- Every sentence must be grounded in the candidate's actual background

─── EXPERIENCE SECTION ──────────────────────────
- Rewrite bullet points to front-load impact verbs that match JD keywords
- Map each bullet to a JD requirement where possible
- Inject relevant technical terms from the JD naturally (do not keyword-stuff)
- Highlight governance, scalability, or domain-specific wins that match the company's domain

─── PROJECTS SECTION ────────────────────────────
- Reorder projects: most relevant to the JD comes first
- For each project, add a one-line "Impact" or "Relevance" note tied to the JD
- Expand or compress tech stack mentions based on JD emphasis
- If the company uses a specific cloud (AWS/GCP/Azure), emphasize that project's infra side
- Generate 2-3 NEW project ideas that perfectly fit this JD and company context

─── SKILLS SECTION ──────────────────────────────
- Reorder skill categories so the most JD-relevant category appears first
- If the JD mentions a specific tool/framework, surface it prominently
- Remove or de-emphasize skills the JD has no mention of
- Keep skill names verbatim as they appear in the JD (for ATS matching)

─── TONE & KEYWORDS ─────────────────────────────
- Analyze the JD and extract: core_role_keywords, tech_stack, soft_skills, domain_language
- Use at least 70% of core_role_keywords naturally in the resume
- Match the company's culture tone: startup → action-driven, enterprise → governance-heavy, product → outcome-focused

TARGET COMPANY: {company_name}

JOB DESCRIPTION:
{job_description}

CANDIDATE BASE PROFILE:
{json.dumps(base_profile_dict, indent=2)}

Return the result as valid JSON matching this exact structure:
{{
  "skills": {{ "languages": ["..."], "frameworks": ["..."], "tools": ["..."] }},
  "experience": [{{ "company": "...", "role": "...", "location": "...", "startDate": "...", "endDate": "...", "bullets": ["..."] }}],
  "projects": [{{ "name": "...", "technologies": ["..."], "bullets": ["..."] }}]
}}
"""


# ── Backend: Google Gemini (google.genai) ────────────────────────────────────

def _generate_gemini(prompt: str, schema: type, model_name: str, api_key: str):
    """Generate structured output using Google Gen AI SDK."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # Convert Pydantic schema to JSON schema dict
    json_schema = schema.model_json_schema()

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=json_schema,
        ),
    )

    return response.text


def _generate_gemini_stream(prompt: str, schema: type, model_name: str, api_key: str):
    """Stream structured output using Google Gen AI SDK. Yields text chunks."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    json_schema = schema.model_json_schema()

    for chunk in client.models.generate_content_stream(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=json_schema,
        ),
    ):
        if chunk.text:
            yield chunk.text


# ── Backend: OpenAI ─────────────────────────────────────────────────────────

def _generate_openai(prompt: str, schema: type, model_name: str, api_key: str):
    """Generate structured output using OpenAI API."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    json_schema = schema.model_json_schema()

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_schema", "json_schema": {"name": "tailored_profile", "schema": json_schema}},
    )

    return response.choices[0].message.content


def _generate_openai_stream(prompt: str, schema: type, model_name: str, api_key: str):
    """Stream output using OpenAI API. Yields text chunks."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    json_schema = schema.model_json_schema()

    stream = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_schema", "json_schema": {"name": "tailored_profile", "schema": json_schema}},
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


# ── Backend: Anthropic Claude ───────────────────────────────────────────────

def _generate_anthropic(prompt: str, schema: type, model_name: str, api_key: str):
    """Generate structured output using Anthropic Claude API."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    json_schema = schema.model_json_schema()

    response = client.messages.create(
        model=model_name,
        max_tokens=4096,
        system="You are an expert ATS-resume writer. Return ONLY valid JSON matching the provided schema.",
        messages=[{"role": "user", "content": prompt}],
        tools=[{
            "name": "tailored_profile",
            "description": "A tailored resume profile matching the schema",
            "input_schema": json_schema,
        }],
        tool_choice={"type": "tool", "name": "tailored_profile"},
    )

    # Extract JSON from tool use
    for block in response.content:
        if block.type == "tool_use" and block.name == "tailored_profile":
            return json.dumps(block.input)

    raise ValueError("Anthropic did not return structured tool output.")


def _generate_anthropic_stream(prompt: str, schema: type, model_name: str, api_key: str):
    """Stream output using Anthropic Claude API. Yields text chunks."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    json_schema = schema.model_json_schema()

    with client.messages.stream(
        model=model_name,
        max_tokens=4096,
        system="You are an expert ATS-resume writer. Return ONLY valid JSON.",
        messages=[{"role": "user", "content": prompt}],
        tools=[{
            "name": "tailored_profile",
            "description": "A tailored resume profile",
            "input_schema": json_schema,
        }],
        tool_choice={"type": "tool", "name": "tailored_profile"},
    ) as stream:
        for text in stream.text_stream:
            yield text


# ── Public API ───────────────────────────────────────────────────────────────

def generate_tailored_profile(
    base_profile_dict: dict,
    job_description: str,
    company_name: str,
    backend: str = "gemini",
) -> dict:
    """Generate a tailored resume profile using AI with retry and fallback logic.

    Args:
        base_profile_dict: The candidate's base profile data
        job_description: The target job description text
        company_name: The target company name
        backend: AI backend to use — 'gemini', 'openai', or 'anthropic'

    Returns:
        dict with the tailored profile merged into the base profile
    """
    _validate_base_profile(base_profile_dict)

    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"Unsupported backend '{backend}'. Must be one of {SUPPORTED_BACKENDS}")

    prompt = _build_prompt(base_profile_dict, job_description, company_name)

    # Select models and API keys based on backend
    if backend == "gemini":
        models = GEMINI_MODELS
        api_key = os.environ.get("GEMINI_API_KEY", "")
        generator = _generate_gemini
    elif backend == "openai":
        models = OPENAI_MODELS
        api_key = os.environ.get("OPENAI_API_KEY", "")
        generator = _generate_openai
    elif backend == "anthropic":
        models = ANTHROPIC_MODELS
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        generator = _generate_anthropic
    else:
        raise ValueError(f"Unknown backend: {backend}")

    if not api_key:
        raise ValueError(f"No API key found for backend '{backend}'. Set the appropriate environment variable.")

    last_error = None
    for model_name in models:
        for attempt in range(MAX_RETRIES):
            try:
                response_text = generator(prompt, TailoredProfile, model_name, api_key)
                result = json.loads(response_text)
                validated = TailoredProfile(**result)

                final_profile = base_profile_dict.copy()
                final_profile['skills'] = validated.skills.model_dump()
                final_profile['experience'] = [exp.model_dump() for exp in validated.experience]
                final_profile['projects'] = [proj.model_dump() for proj in validated.projects]

                return final_profile

            except json.JSONDecodeError as e:
                last_error = ValueError(f"AI returned invalid JSON: {e}")
                print(f"[ai_engine] JSON parse error with {model_name} (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

            except Exception as e:
                last_error = e
                print(f"[ai_engine] Error with {model_name} (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))

    raise RuntimeError(f"All AI model attempts failed with backend '{backend}'. Last error: {last_error}")


def generate_tailored_profile_stream(
    base_profile_dict: dict,
    job_description: str,
    company_name: str,
    backend: str = "gemini",
):
    """Stream a tailored resume profile. Yields text chunks as they arrive.

    Args:
        base_profile_dict: The candidate's base profile data
        job_description: The target job description text
        company_name: The target company name
        backend: AI backend — 'gemini', 'openai', or 'anthropic'

    Yields:
        str: Text chunks of the JSON response
    """
    _validate_base_profile(base_profile_dict)

    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"Unsupported backend '{backend}'. Must be one of {SUPPORTED_BACKENDS}")

    prompt = _build_prompt(base_profile_dict, job_description, company_name)

    if backend == "gemini":
        models = GEMINI_MODELS
        api_key = os.environ.get("GEMINI_API_KEY", "")
        streamer = _generate_gemini_stream
    elif backend == "openai":
        models = OPENAI_MODELS
        api_key = os.environ.get("OPENAI_API_KEY", "")
        streamer = _generate_openai_stream
    elif backend == "anthropic":
        models = ANTHROPIC_MODELS
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        streamer = _generate_anthropic_stream
    else:
        raise ValueError(f"Unknown backend: {backend}")

    if not api_key:
        raise ValueError(f"No API key found for backend '{backend}'.")

    for model_name in models:
        try:
            full_text = []
            for chunk in streamer(prompt, TailoredProfile, model_name, api_key):
                full_text.append(chunk)
                yield chunk

            # Validate final result
            result = json.loads("".join(full_text))
            TailoredProfile(**result)
            return  # Success

        except Exception as e:
            print(f"[ai_engine] Stream error with {model_name}: {e}")
            continue

    raise RuntimeError(f"All streaming attempts failed with backend '{backend}'.")
