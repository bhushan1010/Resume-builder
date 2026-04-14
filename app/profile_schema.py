"""
profile_schema.py  –  JSON Schema for profile validation
"""

PROFILE_SCHEMA = {
    "type": "object",
    "required": ["basics"],
    "properties": {
        "basics": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "email": {"type": "string", "format": "email"},
                "phone": {"type": "string"},
                "linkedin": {"type": "string"},
                "github": {"type": "string"},
                "leetcode": {"type": "string"},
            },
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "institution": {"type": "string"},
                    "location": {"type": "string"},
                    "degree": {"type": "string"},
                    "startDate": {"type": "string"},
                    "endDate": {"type": "string"},
                },
            },
        },
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["company", "role", "bullets"],
                "properties": {
                    "company": {"type": "string"},
                    "role": {"type": "string"},
                    "location": {"type": "string"},
                    "startDate": {"type": "string"},
                    "endDate": {"type": "string"},
                    "bullets": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                    },
                },
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "technologies", "bullets"],
                "properties": {
                    "name": {"type": "string"},
                    "technologies": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "bullets": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                    },
                },
            },
        },
        "skills": {
            "type": "object",
            "properties": {
                "languages": {"type": "array", "items": {"type": "string"}},
                "frameworks": {"type": "array", "items": {"type": "string"}},
                "tools": {"type": "array", "items": {"type": "string"}},
            },
        },
        "certifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "issuer": {"type": "string"},
                    "date": {"type": "string"},
                },
            },
        },
    },
}


def validate_profile(profile: dict) -> list[str]:
    """Validate a profile dict against the schema.

    Returns a list of error messages (empty if valid).
    """
    errors = []

    if not isinstance(profile, dict):
        return ["Profile must be a dictionary."]

    if 'basics' not in profile:
        errors.append("Missing required section: 'basics'")
        return errors

    basics = profile['basics']
    if not isinstance(basics, dict):
        errors.append("'basics' must be a dictionary.")
        return errors

    if 'name' not in basics or not basics['name']:
        errors.append("'basics.name' is required and cannot be empty.")

    if 'email' in basics and basics['email']:
        if '@' not in basics['email']:
            errors.append("'basics.email' does not appear to be a valid email.")

    for section in ['education', 'experience', 'projects', 'certifications']:
        if section in profile and not isinstance(profile[section], list):
            errors.append(f"'{section}' must be a list.")

    if 'experience' in profile and isinstance(profile['experience'], list):
        for i, exp in enumerate(profile['experience']):
            if not isinstance(exp, dict):
                errors.append(f"'experience[{i}]' must be a dictionary.")
                continue
            for field in ['company', 'role', 'bullets']:
                if field not in exp:
                    errors.append(f"'experience[{i}]' is missing '{field}'.")
            if 'bullets' in exp and not isinstance(exp['bullets'], list):
                errors.append(f"'experience[{i}].bullets' must be a list.")

    if 'projects' in profile and isinstance(profile['projects'], list):
        for i, proj in enumerate(profile['projects']):
            if not isinstance(proj, dict):
                errors.append(f"'projects[{i}]' must be a dictionary.")
                continue
            for field in ['name', 'technologies', 'bullets']:
                if field not in proj:
                    errors.append(f"'projects[{i}]' is missing '{field}'.")

    if 'skills' in profile and isinstance(profile['skills'], dict):
        for cat in ['languages', 'frameworks', 'tools']:
            if cat in profile['skills'] and not isinstance(profile['skills'][cat], list):
                errors.append(f"'skills.{cat}' must be a list.")

    return errors
