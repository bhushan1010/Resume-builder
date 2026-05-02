import re
import json
import logging
import hashlib
from functools import lru_cache
from typing import Dict, List, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob
from nltk.corpus import stopwords
import nltk

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# NLTK data — lazy bootstrap (no longer runs at import time without guard)
# ---------------------------------------------------------------------------
def _ensure_nltk_data():
    """Ensure required NLTK corpora are available (downloaded once)."""
    try:
        stopwords.words('english')
    except LookupError:
        try:
            logger.info("Downloading NLTK 'stopwords' corpus...")
            nltk.download('stopwords', quiet=True)
        except Exception as e:
            logger.error(f"Failed to download NLTK stopwords: {e}", exc_info=True)


_ensure_nltk_data()


# ---------------------------------------------------------------------------
# Sentence-transformer model — lazy singleton
# ---------------------------------------------------------------------------
_model = None


def get_model():
    global _model
    if _model is None:
        logger.info("Loading sentence transformer model 'all-MiniLM-L6-v2'...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


# ---------------------------------------------------------------------------
# High-value semantic categories — encoded ONCE at first use, then cached
# ---------------------------------------------------------------------------
HIGH_VALUE_CATEGORIES = [
    "programming", "software development", "data analysis", "machine learning",
    "cloud computing", "web development", "database management", "devops",
    "algorithm", "framework", "language", "platform", "application"
]

_category_embeddings_cache = None


def _get_category_embeddings():
    global _category_embeddings_cache
    if _category_embeddings_cache is None:
        _category_embeddings_cache = get_model().encode(HIGH_VALUE_CATEGORIES)
    return _category_embeddings_cache


# ---------------------------------------------------------------------------
# Encoding cache — avoids re-encoding the same JD/resume across calls
# ---------------------------------------------------------------------------
@lru_cache(maxsize=128)
def _encode_cached(text_hash: str, text: str):
    return get_model().encode([text])[0]


def _encode_text(text: str):
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    return _encode_cached(text_hash, text)


# ---------------------------------------------------------------------------
# Public scoring entry point
# ---------------------------------------------------------------------------
def score(resume_text: str, job_description: str) -> Dict:
    """
    Score resume against job description using hybrid approach:
    - Semantic similarity for overall understanding (0-100 range)
    - Weighted keyword algorithm for specific term matching (0-100 range)
    Final blend: 70% semantic + 30% keyword overall;
                 30% semantic + 70% keyword per-section.
    """
    # Overall semantic similarity (whole resume vs whole JD)
    semantic_score = calculate_semantic_similarity(resume_text, job_description)

    # Keyword-based scoring (per-section + overall)
    keyword_result = score_keyword_based(resume_text, job_description)

    # Combine overall: 70% semantic, 30% keyword
    combined_overall = (semantic_score * 0.7) + (keyword_result["overall"] * 0.3)

    # Per-section: compute semantic similarity for each section individually
    sections = split_resume_into_sections(resume_text)
    combined_sections = {}
    for section_name, keyword_section_score in keyword_result["sections"].items():
        section_text = sections.get(section_name, "")
        if section_text.strip():
            section_semantic = calculate_semantic_similarity(section_text, job_description)
        else:
            section_semantic = 0.0
        combined_sections[section_name] = (section_semantic * 0.3) + (keyword_section_score * 0.7)

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
        if section_text.strip():
            # FIXED: renamed local var to avoid shadowing the module-level `score` function
            section_score = calculate_section_score(
                section_text,
                high_weight_keywords,
                medium_weight_keywords,
                low_weight_keywords
            )
            section_scores[section_name] = min(100.0, section_score * 100)
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
    if not text1 or not text2 or not text1.strip() or not text2.strip():
        return 0.0

    try:
        # Use cached encodings to avoid recomputing for repeated inputs
        emb1 = _encode_text(text1)
        emb2 = _encode_text(text2)
        similarity = cosine_similarity([emb1], [emb2])[0][0]
        # Clamp to [0, 1] (cosine sim can technically go negative)
        similarity = max(0.0, min(1.0, float(similarity)))
        return similarity * 100
    except Exception as e:
        logger.error(f"Semantic similarity failed: {e}", exc_info=True)
        # Fallback: keyword-only scoring takes over
        return 0.0


# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------
def extract_high_weight_keywords(job_description: str) -> List[Tuple[str, float]]:
    """Extract high weight keywords (3.0) from job description using semantic enhancement."""
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

    must_have_patterns = [
        r"required", r"must have", r"proficient in", r"experience with", r"knowledge of",
        r"familiar with", r"strong background in", r"expertise in"
    ]

    keywords = []
    jd_lower = job_description.lower()

    # Exact tech-term matches
    for term in tech_terms:
        if re.search(r'\b' + re.escape(term) + r'\b', jd_lower):
            keywords.append((term, 3.0))

    # Tech terms appearing near must-have indicators
    for pattern in must_have_patterns:
        for match in re.finditer(pattern, jd_lower):
            start = match.end()
            context = jd_lower[start:start + 50]
            for term in tech_terms:
                if re.search(r'\b' + re.escape(term) + r'\b', context):
                    if (term, 3.0) not in keywords:
                        keywords.append((term, 3.0))

    # SEMANTIC ENHANCEMENT: discover semantically similar high-value terms
    try:
        model = get_model()
        blob = TextBlob(job_description)
        # FIXED: renamed loop var from `np` (which shadowed numpy module) → `phrase`
        noun_phrases = [
            phrase.lower().strip()
            for phrase in blob.noun_phrases
            if len(phrase.split()) <= 3
        ]

        try:
            stop_words = set(stopwords.words('english'))
        except LookupError:
            stop_words = set()

        words = [
            word.lower()
            for word in blob.words
            if len(word) > 3 and word.lower() not in stop_words
        ]

        candidates = list(set(noun_phrases + words))

        if candidates:
            candidate_embeddings = model.encode(candidates)
            # Use cached category embeddings (computed once globally)
            category_embeddings = _get_category_embeddings()

            similarity_matrix = cosine_similarity(candidate_embeddings, category_embeddings)

            existing_terms = {kw[0] for kw in keywords}
            for i, candidate in enumerate(candidates):
                max_similarity = float(np.max(similarity_matrix[i]))
                if max_similarity > 0.6 and candidate not in existing_terms:
                    # Scale similarity 0.6-1.0 → weight 1.8-3.0
                    weight = 1.8 + (max_similarity - 0.6) * (1.2 / 0.4)
                    keywords.append((candidate, min(weight, 3.0)))
                    existing_terms.add(candidate)
    except Exception as e:
        logger.warning(f"Semantic keyword enhancement failed: {e}", exc_info=True)
        # Continue with exact-match keywords only

    return keywords


def extract_medium_weight_keywords(job_description: str) -> List[Tuple[str, float]]:
    """Extract medium weight keywords (2.0) from job description."""
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
        if re.search(r'\b' + re.escape(term) + r'\b', jd_lower):
            keywords.append((term, 2.0))

    return keywords


def extract_low_weight_keywords(job_description: str) -> List[Tuple[str, float]]:
    """Extract low weight keywords (1.0) from job description."""
    low_terms = [
        "experience", "team", "project", "development", "application", "system",
        "solution", "support", "maintenance", "design", "implementation", "analysis",
        "research", "planning", "coordination", "management", "process", "workflow"
    ]

    keywords = []
    jd_lower = job_description.lower()

    for term in low_terms:
        if re.search(r'\b' + re.escape(term) + r'\b', jd_lower):
            keywords.append((term, 1.0))

    return keywords


# ---------------------------------------------------------------------------
# Resume sectioning
# ---------------------------------------------------------------------------
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

    # If input is JSON (rewritten resume), map directly
    try:
        parsed_json = json.loads(resume_text)
        if isinstance(parsed_json, dict):
            sections["summary"] = parsed_json.get("summary", "")

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
    except (json.JSONDecodeError, TypeError):
        # Not a JSON string — fall through to plain-text parsing
        pass

    # Common section headers (case-insensitive)
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
        # FIXED: removed broken `or ... and line.isupper()` branch (operator-precedence bug)
        found_header = False
        for section_name, patterns in header_patterns.items():
            for pattern in patterns:
                if re.search(f'^{pattern}:?$', line_stripped, re.IGNORECASE):
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


# ---------------------------------------------------------------------------
# Per-section scoring
# ---------------------------------------------------------------------------
def calculate_section_score(
    section_text: str,
    high_weight: List[Tuple[str, float]],
    medium_weight: List[Tuple[str, float]],
    low_weight: List[Tuple[str, float]]
) -> float:
    """Calculate score for a section based on keyword matches (0-1 range)."""
    if not section_text.strip():
        return 0.0

    section_lower = section_text.lower()
    total_score = 0.0
    max_possible_score = 0.0

    for keyword, weight in high_weight:
        if re.search(r'\b' + re.escape(keyword) + r'\b', section_lower):
            total_score += weight
        max_possible_score += weight

    for keyword, weight in medium_weight:
        if re.search(r'\b' + re.escape(keyword) + r'\b', section_lower):
            total_score += weight
        max_possible_score += weight

    for keyword, weight in low_weight:
        if re.search(r'\b' + re.escape(keyword) + r'\b', section_lower):
            total_score += weight
        max_possible_score += weight

    if max_possible_score == 0:
        return 0.0

    return total_score / max_possible_score