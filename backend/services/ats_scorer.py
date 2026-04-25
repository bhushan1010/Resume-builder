import re
from typing import Dict, List, Tuple
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob
from nltk.corpus import stopwords
import nltk

# Download required NLTK data (only needed once)
try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords')
    nltk.download('punkt')

# Initialize sentence transformer model for semantic similarity
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def score(resume_text: str, job_description: str) -> Dict:
    """
    Score resume against job description using hybrid approach:
    - Semantic similarity for overall understanding
    - Weighted keyword algorithm for specific term matching
    """
    # Get semantic similarity score (0-1 range)
    semantic_score = calculate_semantic_similarity(resume_text, job_description)
    
    # Get keyword-based score (existing algorithm)
    keyword_result = score_keyword_based(resume_text, job_description)
    
    # Combine scores: 70% semantic, 30% keyword for better balance
    combined_overall = (semantic_score * 0.7) + (keyword_result["overall"] * 0.3)
    
    # Combine section scores similarly
    combined_sections = {}
    for section_name in keyword_result["sections"]:
        keyword_section_score = keyword_result["sections"][section_name]
        # For sections, we don't have direct semantic comparison, so weigh more on keywords
        combined_sections[section_name] = (semantic_score * 0.3) + (keyword_section_score * 0.7)
    
    # Convert numpy types to Python native types for JSON serialization
    return {
        "overall": round(float(combined_overall), 1),
        "sections": {k: round(float(v), 1) for k, v in combined_sections.items()}
    }

def score_keyword_based(resume_text: str, job_description: str) -> Dict:
    """
    Original keyword-based scoring algorithm (preserved for hybrid approach).
    """
    # Step 1: Extract keywords from JD into 3 tiers
    high_weight_keywords = extract_high_weight_keywords(job_description)
    medium_weight_keywords = extract_medium_weight_keywords(job_description)
    low_weight_keywords = extract_low_weight_keywords(job_description)
    
    # Step 2: Split resume into sections
    sections = split_resume_into_sections(resume_text)
    
    # If no sections were detected, score the whole text as one block
    if all(not v.strip() for v in sections.values()):
        sections["summary"] = resume_text
        sections["internship"] = resume_text
        sections["skills"] = resume_text
    
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
        "overall": round(float(overall_score), 1),
        "sections": {k: round(float(v), 1) for k, v in section_scores.items()}
    }

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity between two texts using sentence transformers.
    Returns score in 0-100 range.
    """
    try:
        model = get_model()
        # Encode both texts
        embeddings = model.encode([text1, text2])
        # Calculate cosine similarity
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        # Convert from 0-1 range to 0-100 range
        return similarity * 100
    except Exception as e:
        # Fallback to keyword-only scoring if semantic fails
        return 0.0

def extract_high_weight_keywords(job_description: str) -> List[Tuple[str, float]]:
    """Extract high weight keywords (3.0) from job description using semantic enhancement."""
    # Common tech terms that indicate high importance
    tech_terms = [
        # Programming languages
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "php", "swift", "kotlin",
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
    
    # Extract tech terms (exact match)
    jd_lower = job_description.lower()
    for term in tech_terms:
        if re.search(r'\b' + term + r'\b', jd_lower):
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
                if re.search(r'\b' + term + r'\b', context):
                    if (term, 3.0) not in keywords:
                        keywords.append((term, 3.0))
    
    # SEMANTIC ENHANCEMENT: Find semantically similar terms
    # Only run if we have the model available
    try:
        model = get_model()
        # Extract nouns and noun phrases from JD as candidates
        blob = TextBlob(job_description)
        noun_phrases = [np.lower().strip() for np in blob.noun_phrases if len(np.split()) <= 3]
        
        # Also get individual important words
        words = [word.lower() for word in blob.words 
                if len(word) > 3 and word.lower() not in stopwords.words('english')]
        
        # Combine candidates
        candidates = list(set(noun_phrases + words))
        
        # Define high-value semantic categories
        high_value_categories = [
            "programming", "software development", "data analysis", "machine learning",
            "cloud computing", "web development", "database management", "devops",
            "algorithm", "framework", "language", "platform", "application"
        ]
        
        # For each candidate, check semantic similarity to high-value categories
        if candidates and high_value_categories:
            # Encode candidates and categories
            candidate_embeddings = model.encode(candidates)
            category_embeddings = model.encode(high_value_categories)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(candidate_embeddings, category_embeddings)
            
            # For each candidate, find max similarity to any high-value category
            for i, candidate in enumerate(candidates):
                max_similarity = np.max(similarity_matrix[i])
                # If similarity is high enough (>0.6), add as keyword
                if max_similarity > 0.6 and candidate not in [kw[0] for kw in keywords]:
                    # Weight based on similarity score (0.6-1.0 maps to 1.8-3.0)
                    weight = 1.8 + (max_similarity - 0.6) * (1.2 / 0.4)  # Scale to 1.8-3.0
                    keywords.append((candidate, min(weight, 3.0)))  # Cap at 3.0
    except Exception:
        # If semantic enhancement fails, continue with original keywords
        pass
    
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
        if re.search(r'\b' + term + r'\b', jd_lower):
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
        if re.search(r'\b' + term + r'\b', jd_lower):
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
    
    # Check if the input is actually a JSON string (rewritten resume)
    try:
        parsed_json = json.loads(resume_text)
        if isinstance(parsed_json, dict):
            # Map JSON to sections directly
            sections["summary"] = parsed_json.get("summary", "")
            
            # Extract lists of objects into text blocks
            for edu in parsed_json.get("education", []):
                sections["education"] += f"{edu.get('institution', '')} {edu.get('degree', '')}\n"
            
            for proj in parsed_json.get("projects", []):
                bullets = " ".join(proj.get("bullets", []))
                sections["projects"] += f"{proj.get('name', '')} {bullets}\n"
            
            for exp in parsed_json.get("internship", []):
                bullets = " ".join(exp.get("bullets", []))
                sections["internship"] += f"{exp.get('company', '')} {exp.get('role', '')} {bullets}\n"
            
            for skill in parsed_json.get("skills", []):
                sections["skills"] += f"{skill.get('category', '')} {skill.get('items', '')}\n"
                
            for cert in parsed_json.get("certifications", []):
                sections["certifications"] += f"{cert.get('name', '')}\n"
                
            return sections
    except json.JSONDecodeError:
        # Not a JSON string, proceed with standard text splitting
        pass
    
    # Common section headers (case insensitive)
    header_patterns = {
        "summary": [r"summary", r"professional summary", r"profile", r"objective"],
        "education": [r"education", r"academic background", r"academics"],
        "projects": [r"projects", r"personal projects", r"academic projects"],
        "internship": [r"internship", r"experience", r"work experience", r"employment", r"professional experience"],
        "skills": [r"skills", r"technical skills", r"competencies", r"expertise"],
        "certifications": [r"certifications", r"certificates", r"licenses"]
    }
    
    lines = resume_text.split('\n')
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
                        sections[current_section] = '\n'.join(section_content).strip()
                    
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
        sections[current_section] = '\n'.join(section_content).strip()
    
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
        if re.search(r'\b' + re.escape(keyword) + r'\b', section_lower):
            total_score += weight
        max_possible_score += weight
    
    # Score medium weight keywords
    for keyword, weight in medium_weight:
        if re.search(r'\b' + re.escape(keyword) + r'\b', section_lower):
            total_score += weight
        max_possible_score += weight
    
    # Score low weight keywords
    for keyword, weight in low_weight:
        if re.search(r'\b' + re.escape(keyword) + r'\b', section_lower):
            total_score += weight
        max_possible_score += weight
    
    # Avoid division by zero
    if max_possible_score == 0:
        return 0.0
    
    return total_score / max_possible_score