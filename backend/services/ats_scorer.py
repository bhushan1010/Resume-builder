import re
from typing import Dict, List, Tuple
import json

def score(resume_text: str, job_description: str) -> Dict:
    """
    Score resume against job description using weighted keyword algorithm.
    """
    # Step 1: Extract keywords from JD into 3 tiers
    high_weight_keywords = extract_high_weight_keywords(job_description)
    medium_weight_keywords = extract_medium_weight_keywords(job_description)
    low_weight_keywords = extract_low_weight_keywords(job_description)
    
    # Step 2: Split resume into sections
    sections = split_resume_into_sections(resume_text)
    
    # Step 3: Calculate weighted score per section
    section_scores = {}
    section_weights = {
        "summary": 0.20,
        "education": 0.05,
        "projects": 0.15,
        "internship": 0.25,
        "skills": 0.30,
        "certifications": 0.05
    }
    
    for section_name, section_text in sections.items():
        if section_text.strip():  # Only score non-empty sections
            score = calculate_section_score(
                section_text, 
                high_weight_keywords, 
                medium_weight_keywords, 
                low_weight_keywords
            )
            section_scores[section_name] = min(100.0, score * 100)  # Convert to 0-100 scale
        else:
            section_scores[section_name] = 0.0
    
    # Step 4: Calculate overall score (weighted average)
    overall_score = 0.0
    total_weight = 0.0
    
    for section_name, weight in section_weights.items():
        if section_name in section_scores:
            overall_score += section_scores[section_name] * weight
            total_weight += weight
    
    if total_weight > 0:
        overall_score = overall_score / total_weight
    else:
        overall_score = 0.0
    
    return {
        "overall": round(overall_score, 1),
        "sections": {k: round(v, 1) for k, v in section_scores.items()}
    }

def extract_high_weight_keywords(job_description: str) -> List[Tuple[str, float]]:
    """Extract high weight keywords (3.0) from job description."""
    # Common tech terms that indicate high importance
    tech_terms = [
        # Programming languages
        "python", "java", "javascript", "typescript", "c\\+\\+", "c#", "ruby", "php", "swift", "kotlin",
        "go", "rust", "scala", "r", "matlab",
        # Web technologies
        "html", "css", "react", "angular", "vue", "nodejs", "express", "django", "flask", "spring",
        # Databases
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "oracle",
        # Cloud & DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "git", "ci/cd", "terraform",
        # Other important terms
        "api", "rest", "graphql", "microservices", "agile", "scrum", "machine learning", "ai", "data science"
    ]
    
    # Must-have indicators
    must_have_patterns = [
        r"required", r"must have", r"proficient in", r"experience with", r"knowledge of",
        r"familiar with", r"strong background in", r"expertise in"
    ]
    
    keywords = []
    
    # Extract tech terms
    jd_lower = job_description.lower()
    for term in tech_terms:
        if re.search(r'\\b' + term + r'\\b', jd_lower):
            keywords.append((term, 3.0))
    
    # Look for terms near must-have indicators
    for pattern in must_have_patterns:
        matches = re.finditer(pattern, jd_lower)
        for match in matches:
            # Extract text after the match (up to next punctuation or 50 chars)
            start = match.end()
            context = jd_lower[start:start+50]
            # Extract potential tech terms from context
            for term in tech_terms:
                if re.search(r'\\b' + term + r'\\b', context):
                    if (term, 3.0) not in keywords:
                        keywords.append((term, 3.0))
    
    return keywords

def extract_medium_weight_keywords(job_description: str) -> List[Tuple[str, float]]:
    """Extract medium weight keywords (2.0) from job description."""
    # Soft skills and domain terms
    medium_terms = [
        # Soft skills
        "communication", "leadership", "teamwork", "problem solving", "analytical", 
        "creative", "organized", "detail-oriented", "time management", "adaptable",
        # Domain/methodology terms
        "project management", "software development", "web development", "mobile development",
        "data analysis", "database administration", "network administration", "system administration",
        "quality assurance", "testing", "debugging", "optimization", "performance tuning",
        "business analysis", "requirements gathering", "documentation", "training"
    ]
    
    keywords = []
    jd_lower = job_description.lower()
    
    for term in medium_terms:
        if re.search(r'\\b' + term + r'\\b', jd_lower):
            keywords.append((term, 2.0))
    
    return keywords

def extract_low_weight_keywords(job_description: str) -> List[Tuple[str, float]]:
    """Extract low weight keywords (1.0) from job description."""
    # Common general terms
    low_terms = [
        "experience", "team", "project", "development", "application", "system",
        "solution", "support", "maintenance", "design", "implementation", "analysis",
        "research", "planning", "coordination", "management", "process", "workflow"
    ]
    
    keywords = []
    jd_lower = job_description.lower()
    
    for term in low_terms:
        if re.search(r'\\b' + term + r'\\b', jd_lower):
            keywords.append((term, 1.0))
    
    return keywords

def split_resume_into_sections(resume_text: str) -> Dict[str, str]:
    """Split resume into sections based on headers."""
    sections = {
        "summary": "",
        "education": "",
        "projects": "",
        "internship": "",
        "skills": "",
        "certifications": ""
    }
    
    # Common section headers (case insensitive)
    header_patterns = {
        "summary": [r"summary", r"professional summary", r"profile", r"objective"],
        "education": [r"education", r"academic background", r"academics"],
        "projects": [r"projects", r"personal projects", r"academic projects"],
        "internship": [r"internship", r"experience", r"work experience", r"employment", r"professional experience"],
        "skills": [r"skills", r"technical skills", r"competencies", r"expertise"],
        "certifications": [r"certifications", r"certificates", r"licenses"]
    }
    
    lines = resume_text.split('\\n')
    current_section = None
    section_content = []
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        # Check if this line is a section header
        found_header = False
        for section_name, patterns in header_patterns.items():
            for pattern in patterns:
                if re.search(f'^{pattern}:?$', line_stripped, re.IGNORECASE) or \
                   re.search(f'^{pattern}$', line_stripped, re.IGNORECASE) and line_stripped.isupper():
                    # Save previous section
                    if current_section and section_content:
                        sections[current_section] = '\\n'.join(section_content).strip()
                    
                    # Start new section
                    current_section = section_name
                    section_content = []
                    found_header = True
                    break
            if found_header:
                break
        
        if not found_header and current_section:
            section_content.append(line)
    
    # Save last section
    if current_section and section_content:
        sections[current_section] = '\\n'.join(section_content).strip()
    
    return sections

def calculate_section_score(section_text: str, high_weight: List[Tuple[str, float]], 
                          medium_weight: List[Tuple[str, float]], 
                          low_weight: List[Tuple[str, float]]) -> float:
    """Calculate score for a section based on keyword matches."""
    if not section_text.strip():
        return 0.0
    
    section_lower = section_text.lower()
    total_score = 0.0
    max_possible_score = 0.0
    
    # Score high weight keywords
    for keyword, weight in high_weight:
        if re.search(r'\\b' + re.escape(keyword) + r'\\b', section_lower):
            total_score += weight
        max_possible_score += weight
    
    # Score medium weight keywords
    for keyword, weight in medium_weight:
        if re.search(r'\\b' + re.escape(keyword) + r'\\b', section_lower):
            total_score += weight
        max_possible_score += weight
    
    # Score low weight keywords
    for keyword, weight in low_weight:
        if re.search(r'\\b' + re.escape(keyword) + r'\\b', section_lower):
            total_score += weight
        max_possible_score += weight
    
    # Avoid division by zero
    if max_possible_score == 0:
        return 0.0
    
    return total_score / max_possible_score