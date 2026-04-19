import os
import json
import re
import time
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

# Import key manager
from services.key_manager import key_manager

def call_gemini_with_retry(
    prompt_content, 
    max_retries: int = 3,
    system_instruction: str = None
):
    """
    Call Gemini API with automatic key rotation and retry.
    prompt_content can be str or list (for vision calls)
    """
    last_error = None

    for attempt in range(max_retries):
        key = key_manager.get_available_key()

        if key is None:
            raise HTTPException(
                status_code=503,
                detail="All API keys are currently rate limited. Please try again in about a minute."
            )

        try:
            # Configure the model with the current key
            genai.configure(api_key=key)
            if system_instruction:
                model = genai.GenerativeModel(
                    'gemini-2.5-flash',
                    system_instruction=system_instruction
                )
            else:
                model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt_content)
            return response

        except Exception as e:
            last_error = e
            error_str = str(e).lower()

            if "429" in str(e) or "quota" in error_str or "rate" in error_str:
                key_manager.mark_rate_limited(key)
                wait_seconds = (2 ** attempt)  # 1s, 2s, 4s
                time.sleep(wait_seconds)
                continue

            elif "daily" in error_str or "per day" in error_str:
                key_manager.mark_daily_exhausted(key)
                continue

            else:
                # Non-rate-limit error, don't retry
                raise

    raise HTTPException(
        status_code=503,
        detail=f"Failed after {max_retries} attempts. Last error: {str(last_error)}"
    )


def parse_resume(resume_text: str) -> dict:
    """
    Parse raw resume text into structured JSON using Gemini.
    """
    system_instruction_text = """
    You are a resume parser. Parse the given resume text into structured JSON 
    exactly matching the schema provided. Return ONLY valid JSON, no markdown, 
    no explanation.
    """

    schema = {
        "header": {
            "name": "",
            "email": "",
            "phone": "",
            "linkedin": "",
            "github": ""
        },
        "summary": "",
        "education": [
            {
                "institution": "",
                "degree": "",
                "duration": ""
            }
        ],
        "projects": [
            {
                "name": "",
                "url": "",
                "duration": "",
                "bullets": []
            }
        ],
        "internship": [
            {
                "company": "",
                "url": "",
                "role": "",
                "duration": "",
                "bullets": []
            }
        ],
        "skills": [
            {
                "category": "",
                "items": ""
            }
        ],
        "certifications": [
            {
                "name": "",
                "url": "",
                "duration": ""
            }
        ]
    }

    user_prompt = f"""
    Parse this resume text:
    {resume_text}

    Return ONLY the JSON matching this schema:
    {json.dumps(schema, indent=2)}
    """

    try:
        response = call_gemini_with_retry(
            user_prompt,
            system_instruction=system_instruction_text
        )
        # Clean response to extract JSON
        cleaned_response = re.sub(r'```json|```', '', response.text).strip()
        parsed_data = json.loads(cleaned_response)

        # Ensure all required fields exist with proper types
        result = {
            "header": {
                "name": parsed_data.get("header", {}).get("name", ""),
                "email": parsed_data.get("header", {}).get("email", ""),
                "phone": parsed_data.get("header", {}).get("phone", ""),
                "linkedin": parsed_data.get("header", {}).get("linkedin", ""),
                "github": parsed_data.get("header", {}).get("github", "")
            },
            "summary": parsed_data.get("summary", ""),
            "education": parsed_data.get("education", []),
            "projects": parsed_data.get("projects", []),
            "internship": parsed_data.get("internship", []),
            "skills": parsed_data.get("skills", []),
            "certifications": parsed_data.get("certifications", [])
        }

        return result
    except Exception as e:
        # Return empty structure on error
        return {
            "header": {"name": "", "email": "", "phone": "", "linkedin": "", "github": ""},
            "summary": "",
            "education": [],
            "projects": [],
            "internship": [],
            "skills": [],
            "certifications": []
        }

def rewrite_resume(parsed_json: dict, jd: str) -> dict:
    """
    Rewrite resume sections to maximize alignment with job description.
    """
    # Extract locked facts
    locked_facts = extract_locked_facts(parsed_json)
    
    # Sections to rewrite (in order)
    sections_to_rewrite = ["summary", "skills", "internship", "projects"]
    
    # Create a copy to modify
    rewritten_json = parsed_json.copy()
    
    for section_name in sections_to_rewrite:
        try:
            section_content = parsed_json.get(section_name, [])
            
            # For summary, it's a string; for others, it's a list
            if section_name == "summary":
                section_json = json.dumps({"summary": section_content}, indent=2)
                rewritten_section = rewrite_section(
                    section_json, 
                    section_name, 
                    locked_facts, 
                    jd
                )
                # Extract just the summary value
                rewritten_data = json.loads(rewritten_section)
                rewritten_json[section_name] = rewritten_data.get("summary", section_content)
            else:
                # For list sections, rewrite each item
                rewritten_items = []
                for item in section_content:
                    item_json = json.dumps(item, indent=2)
                    rewritten_item = rewrite_section(
                        item_json, 
                        section_name[:-1],  # Singular form (e.g., "internship" -> "internship item")
                        locked_facts, 
                        jd
                    )
                    rewritten_item_data = json.loads(rewritten_item)
                    rewritten_items.append(rewritten_item_data)
                rewritten_json[section_name] = rewritten_items
        except Exception as e:
            # Keep original content if rewrite fails
            continue
    
    # Header, education, and certifications remain unchanged (factual only)
    return rewritten_json

def extract_locked_facts(parsed_json: dict) -> dict:
    """
    Extract locked facts that must not be changed during rewriting.
    """
    locked_facts = {
        "urls": [],
        "dates": [],
        "numbers": [],
        "names": [],
        "contact": []
    }
    
    def extract_from_text(text):
        if not isinstance(text, str):
            return
        
        # Extract URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        locked_facts["urls"].extend(urls)
        
        # Extract dates (various formats)
        date_patterns = [
            r'\\b\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}\\b',
            r'\\b\\d{4}[/-]\\d{1,2}[/-]\\d{1,2}\\b',
            r'\\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \\d{1,2},? \\d{4}\\b',
            r'\\b\\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \\d{4}\\b',
            r'\\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \\d{4}\\b',
            r'\\b\\d{4}\\b'
        ]
        for pattern in date_patterns:
            dates = re.findall(pattern, text, re.IGNORECASE)
            locked_facts["dates"].extend(dates)
        
        # Extract numbers with context (percentages, counts, etc.)
        number_patterns = [
            r'\\b\\d+\\.?\\d*%\\b',
            r'\\b\\d+[+,]?\\d*\\s*(?:users?|people|customers?|clients?|projects?|apps?|websites?)\\b',
            r'\\b\\d+[+,]?\\d*\\s*(?:%|percent)\\b',
            r'\\b\\d+[+,]?\\d*\\s*(?:million|billion|thousand)\\b'
        ]
        for pattern in number_patterns:
            numbers = re.findall(pattern, text, re.IGNORECASE)
            locked_facts["numbers"].extend(numbers)
        
        # Extract potential names (capitalized words sequences)
        # This is simplistic - in production you'd use NER
        name_pattern = r'\\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\\b'
        potential_names = re.findall(name_pattern, text)
        # Filter out common non-names
        common_words = {'The', 'And', 'Or', 'But', 'In', 'On', 'At', 'To', 'For', 'Of', 'With', 'By'}
        names = [name for name in potential_names if name not in common_words and len(name.split()) <= 3]
        locked_facts["names"].extend(names)
    
    # Extract from header
    header = parsed_json.get("header", {})
    for key, value in header.items():
        if value:
            extract_from_text(value)
    
    # Extract from summary
    extract_from_text(parsed_json.get("summary", ""))
    
    # Extract from education
    for edu in parsed_json.get("education", []):
        for key, value in edu.items():
            if value:
                extract_from_text(value)
    
    # Extract from projects
    for project in parsed_json.get("projects", []):
        for key, value in project.items():
            if key != "bullets" and value:
                extract_from_text(value)
        for bullet in project.get("bullets", []):
            extract_from_text(bullet)
    
    # Extract from internship
    for internship in parsed_json.get("internship", []):
        for key, value in internship.items():
            if key != "bullets" and value:
                extract_from_text(value)
        for bullet in internship.get("bullets", []):
            extract_from_text(bullet)
    
    # Extract from skills
    for skill in parsed_json.get("skills", []):
        for key, value in skill.items():
            if value:
                extract_from_text(value)
    
    # Extract from certifications
    for cert in parsed_json.get("certifications", []):
        for key, value in cert.items():
            if value:
                extract_from_text(value)
    
    # Extract contact info separately
    if header.get("email"):
        locked_facts["contact"].append(header["email"])
    if header.get("phone"):
        locked_facts["contact"].append(header["phone"])
    if header.get("linkedin"):
        locked_facts["contact"].append(header["linkedin"])
    if header.get("github"):
        locked_facts["contact"].append(header["github"])
    
    # Remove duplicates while preserving order
    for key in locked_facts:
        seen = set()
        locked_facts[key] = [x for x in locked_facts[key] if not (x in seen or seen.add(x))]
    
    return locked_facts

def rewrite_section(section_json: str, section_name: str, locked_facts: dict, jd: str) -> str:
    """
    Rewrite a single section using Gemini with strict rules.
    """
    # System part: the rules only (static, no variables)
    system_rules = """
    You are an expert ATS resume writer. Rewrite the given resume section to maximize 
    alignment with the job description.

    STRICT RULES:
    1. Never change any fact, number, percentage, date, URL, company name, 
         institution name, or project name
    2. The locked facts provided must appear exactly as given
    3. Inject relevant keywords from the JD naturally
    4. Keep bullet points concise (1-2 lines each)
    5. Use strong action verbs to start each bullet
    6. Return ONLY the rewritten section as valid JSON
    7. Do not add experience or achievements that don't exist
    8. Preserve the original structure (number of bullets, number of entries)
    """

    # User part: the dynamic data (facts + jd + section)
    user_message = f"""
    LOCKED FACTS (never modify these):
    {json.dumps(locked_facts, indent=2)}

    JOB DESCRIPTION:
    {jd}

    SECTION TO REWRITE ({section_name}):
    {section_json}
    """

    try:
        response = call_gemini_with_retry(
            user_message,
            system_instruction=system_rules
        )
        # Clean response to extract JSON
        cleaned_response = re.sub(r'```json|```', '', response.text).strip()
        # Validate that it's valid JSON
        json.loads(cleaned_response)
        return cleaned_response
    except Exception as e:
        # Return original section on error
        return section_json