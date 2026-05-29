import re
import json
import math
import logging
import hashlib
from functools import lru_cache
from collections import Counter
from typing import Dict, List, Tuple, Set

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
import nltk

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# NLTK data — lazy bootstrap
# ---------------------------------------------------------------------------
def _ensure_nltk_data():
    """Ensure required NLTK corpora are available (downloaded once)."""
    for corpus in ('stopwords', 'punkt'):
        try:
            if corpus == 'stopwords':
                stopwords.words('english')
        except LookupError:
            try:
                logger.info(f"Downloading NLTK '{corpus}' corpus...")
                nltk.download(corpus, quiet=True)
            except Exception as e:
                logger.error(f"Failed to download NLTK {corpus}: {e}")


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
# Encoding cache
# ---------------------------------------------------------------------------
@lru_cache(maxsize=256)
def _encode_cached(text_hash: str, text: str):
    return get_model().encode([text])[0]


def _encode_text(text: str):
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    return _encode_cached(text_hash, text)


# ---------------------------------------------------------------------------
# Section weights — calibrated to match user specifications exactly
# ---------------------------------------------------------------------------
SECTION_WEIGHTS = {
    "summary":        0.20,
    "skills":         0.25,
    "internship":     0.25,
    "projects":       0.15,
    "education":      0.10,
    "certifications": 0.05,
}


def _score_section_detailed(
    section_text: str,
    section_name: str,
    all_kw: List[Tuple[str, float]],
    jd: str
) -> float:
    """
    Score a single section from 0 to 100 based on the 4 ATS criteria:
    - Keyword density (40%): ATS-relevant terms matched
    - Action verbs & quantified achievements (30%): action verbs and metrics/percentages
    - Formatting clarity (20%): bullets, dates, spacing structure
    - Relevance to JD (10%): semantic similarity
    """
    if not section_text.strip():
        return 0.0

    # 1. Keyword density (40%)
    sec_keyword_score, _ = _score_section_keywords(section_text, all_kw, section_name)
    keyword_score = sec_keyword_score * 100.0

    # 2. Action verbs and quantified achievements (30%)
    action_verbs = {
        'led', 'managed', 'developed', 'built', 'created', 'designed', 'implemented',
        'optimized', 'improved', 'increased', 'decreased', 'reduced', 'saved', 'achieved',
        'automated', 'established', 'coordinated', 'engineered', 'launched', 'delivered',
        'formulated', 'spearheaded', 'generated', 'cultivated', 'streamlined', 'maximized',
        'minimized', 'facilitated', 'executed', 'conducted', 'resolved', 'analyzed',
        'programmed', 'coded', 'deployed', 'migrated', 'administered', 'collaborated'
    }
    words = re.findall(r'[a-zA-Z]+', section_text.lower())
    verb_matches = sum(1 for w in words if w in action_verbs)
    
    # Quantified achievements: count occurrences of percentages, numbers, metrics (e.g. 30%, $10k, 3x)
    metrics_matches = len(re.findall(r'\b\d+(?:[\d,.]*\d)?%?|\b\d+x\b|\$\d+', section_text))
    
    action_score = min(100.0, (verb_matches * 35.0) + (metrics_matches * 30.0))
    if section_name in ("skills", "education", "certifications"):
        # For non-narrative sections, score based on content richness
        items_count = len(section_text.split(',')) if section_name == "skills" else len(section_text.split('\n'))
        action_score = min(100.0, items_count * 20.0)

    # 3. Formatting clarity (20%)
    has_bullets = any(char in section_text for char in ('•', '·', '▪', '▸', '→', '*', '- '))
    has_dates = bool(re.search(r'\b(19|20)\d{2}\b|present|current', section_text, re.IGNORECASE))
    lines = [line for line in section_text.split('\n') if line.strip()]
    good_structure = len(lines) >= 2 or len(section_text) < 150
    
    clarity_score = 0.0
    if has_bullets or section_name in ("summary", "skills"):
        clarity_score += 40.0
    else:
        if len(lines) >= 2:
            clarity_score += 30.0
        
    if has_dates or section_name in ("summary", "skills"):
        clarity_score += 40.0
        
    if good_structure:
        clarity_score += 20.0

    # 4. Relevance to job description (10%)
    semantic_score = calculate_semantic_similarity(section_text, jd)

    # Blend them together matching user weights
    final_score = (
        (keyword_score * 0.40) +
        (action_score * 0.30) +
        (clarity_score * 0.20) +
        (semantic_score * 0.10)
    )
    return min(100.0, max(0.0, final_score))


# ---------------------------------------------------------------------------
# Public scoring entry point
# ---------------------------------------------------------------------------
def score(resume_text: str, job_description: str) -> Dict:
    """
    Hybrid ATS scoring:
    - Dynamic keyword extraction from the actual JD (required + preferred tiers)
    - TF-IDF-style n-gram matching for multi-word terms
    - Section-scoped keyword matching (skills vs internship vs summary)
    - Calculated based on user-requested sub-weights (40% keyword, 30% action verbs, 20% format, 10% semantic)
    - Section weights: summary 20%, skills 25%, experience 25%, projects 15%, education 10%, certs 5%
    Returns overall + per-section scores (0–100) and missing_keywords list.
    """
    # Extract structured keywords from JD
    jd_keywords = extract_jd_keywords(job_description)

    # Keyword scoring to get matched/missing keywords list
    keyword_result = score_keyword_based(resume_text, job_description, jd_keywords)

    # Per-section detailed scoring
    sections = split_resume_into_sections(resume_text)
    combined_sections = {}
    
    all_kw = jd_keywords["all"]
    for section_name in SECTION_WEIGHTS:
        section_text = sections.get(section_name, "")
        sec_score = _score_section_detailed(section_text, section_name, all_kw, job_description)
        combined_sections[section_name] = round(float(sec_score), 1)

    # Overall: weighted average of combined section scores
    overall = 0.0
    total_weight = 0.0
    for section_name, weight in SECTION_WEIGHTS.items():
        if section_name in combined_sections:
            overall += combined_sections[section_name] * weight
            total_weight += weight
    if total_weight > 0:
        overall = overall / total_weight

    return {
        "overall": round(float(overall), 1),
        "sections": combined_sections,
        "missing_keywords": keyword_result.get("missing_keywords", []),
        "matched_keywords": keyword_result.get("matched_keywords", []),
    }


# ---------------------------------------------------------------------------
# Dynamic JD keyword extraction
# ---------------------------------------------------------------------------
# Signal patterns that mark REQUIRED skills (high weight: 3.0)
_REQUIRED_SIGNALS = re.compile(
    r'\b(required|must have|must-have|mandatory|essential|critical|'
    r'proficient in|strong experience|expertise in|proven experience)\b',
    re.IGNORECASE
)

# Signal patterns that mark PREFERRED skills (medium weight: 2.0)
_PREFERRED_SIGNALS = re.compile(
    r'\b(preferred|nice to have|plus|advantage|bonus|ideally|'
    r'familiar with|knowledge of|experience with|exposure to)\b',
    re.IGNORECASE
)

# Generic stop-words to skip when extracting n-grams
_JD_STOP_WORDS = {
    'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
    'with', 'by', 'from', 'as', 'an', 'a', 'is', 'are', 'was', 'were',
    'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
    'will', 'would', 'could', 'should', 'may', 'might', 'shall', 'can',
    'not', 'no', 'nor', 'so', 'yet', 'both', 'either', 'neither',
    'this', 'that', 'these', 'those', 'we', 'our', 'you', 'your',
    'they', 'their', 'us', 'its', 'who', 'which', 'what', 'how',
    'also', 'well', 'including', 'such', 'other', 'across', 'within',
    'team', 'role', 'position', 'job', 'work', 'company', 'organization',
    # JD structural boilerplate — not meaningful keywords
    'title', 'type', 'level', 'location', 'shift', 'timings', 'summary',
    'required', 'preferred', 'must', 'have', 'nice', 'bonus', 'plus',
    'full', 'time', 'part', 'contract', 'remote', 'hybrid', 'onsite',
    'responsibilities', 'qualifications', 'requirements', 'about',
    'looking', 'seeking', 'join', 'candidate', 'ideal', 'strong',
    'ability', 'skills', 'experience', 'years', 'year', 'day', 'days',
}


def extract_jd_keywords(jd: str) -> Dict:
    """
    Dynamically extract keywords from the job description into three tiers:
    - required  (weight 3.0): explicitly flagged as must-have, or in the job title
    - preferred (weight 2.0): flagged as nice-to-have / preferred
    - general   (weight 1.5): any other meaningful n-gram in the JD

    Returns:
        {
          "required":  [(term, weight), ...],
          "preferred": [(term, weight), ...],
          "general":   [(term, weight), ...],
          "all":       [(term, weight), ...],   # deduplicated union
          "title_terms": [str, ...],            # words from job title
        }
    """
    title_terms = _extract_title_terms(jd)

    # Split JD into sentences for context-window checking
    sentences = re.split(r'[.;\n]+', jd)

    required_terms:  Dict[str, float] = {}
    preferred_terms: Dict[str, float] = {}
    general_terms:   Dict[str, float] = {}

    for sentence in sentences:
        is_required  = bool(_REQUIRED_SIGNALS.search(sentence))
        is_preferred = bool(_PREFERRED_SIGNALS.search(sentence))

        ngrams = _extract_ngrams(sentence)
        for term in ngrams:
            if term in _JD_STOP_WORDS:
                continue

            # Title boost: terms matching job title get required tier
            if any(t in term or term in t for t in title_terms):
                w = 3.0
                required_terms[term] = max(required_terms.get(term, 0.0), w)
                continue

            if is_required:
                required_terms[term] = max(required_terms.get(term, 0.0), 3.0)
            elif is_preferred:
                preferred_terms[term] = max(preferred_terms.get(term, 0.0), 2.0)
            else:
                general_terms[term] = max(general_terms.get(term, 0.0), 1.5)

    # Build deduplicated combined list (required > preferred > general)
    all_terms: Dict[str, float] = {}
    for term, w in general_terms.items():
        all_terms[term] = w
    for term, w in preferred_terms.items():
        all_terms[term] = w  # overwrite with higher weight
    for term, w in required_terms.items():
        all_terms[term] = w  # overwrite with highest weight

    return {
        "required":    list(required_terms.items()),
        "preferred":   list(preferred_terms.items()),
        "general":     list(general_terms.items()),
        "all":         list(all_terms.items()),
        "title_terms": title_terms,
    }


def _extract_title_terms(jd: str) -> List[str]:
    """
    Try to extract the job title from common JD patterns.
    E.g. "Job Title: Analyst – Analytics & Reporting" → ["analyst", "analytics", "reporting"]
    """
    patterns = [
        r'(?:job title|position|role)[:\s]+([^\n]+)',
        r'^([^\n]{5,60})(?:\n|$)',  # first non-empty line is often the title
    ]
    title_text = ""
    for pat in patterns:
        m = re.search(pat, jd, re.IGNORECASE | re.MULTILINE)
        if m:
            title_text = m.group(1).strip()
            break

    if not title_text:
        return []

    # Tokenise and filter
    words = re.findall(r'[a-zA-Z]+', title_text.lower())
    return [w for w in words if len(w) > 2 and w not in _JD_STOP_WORDS]


def _extract_ngrams(text: str, max_n: int = 2) -> List[str]:
    """
    Extract 1–2 word n-grams from text, cleaned and lower-cased.
    Capped at bigrams to prevent meaningless tri-gram keyword explosions.
    """
    # Normalise: strip bullets, punctuation (keep hyphens inside words)
    text = re.sub(r'[•·▪▸→*]', ' ', text)
    text = re.sub(r'[^\w\s\-/]', ' ', text)
    words = [w.lower().strip('-') for w in text.split() if len(w) > 1 and not w.isdigit()]
    words = [w for w in words if w not in _JD_STOP_WORDS]

    ngrams = []
    for n in range(1, max_n + 1):
        for i in range(len(words) - n + 1):
            gram = ' '.join(words[i:i + n])
            if gram.strip():
                ngrams.append(gram)
    return ngrams


# ---------------------------------------------------------------------------
# Keyword-based scoring (uses dynamic JD keywords)
# ---------------------------------------------------------------------------
def score_keyword_based(resume_text: str, job_description: str, jd_keywords: Dict = None) -> Dict:
    """
    Score resume against JD using dynamic keyword matching.
    - Matches exact phrases (n-grams) not just single words
    - Tracks which required keywords are missing (for UI display)
    - Section scores use only keywords relevant to each section's domain
    """
    if jd_keywords is None:
        jd_keywords = extract_jd_keywords(job_description)

    all_kw = jd_keywords["all"]  # [(term, weight), ...]

    sections = split_resume_into_sections(resume_text)

    # Fall back to whole-text if section parsing failed
    if all(not v.strip() for v in sections.values()):
        sections["summary"]    = resume_text
        sections["internship"] = resume_text
        sections["skills"]     = resume_text

    # Score each section
    section_scores = {}
    matched_set: Set[str] = set()
    missing_required: List[str] = []

    for section_name in SECTION_WEIGHTS:
        section_text = sections.get(section_name, "")
        if not section_text.strip():
            section_scores[section_name] = 0.0
            continue

        sec_score, sec_matched = _score_section_keywords(
            section_text, all_kw, section_name
        )
        section_scores[section_name] = min(100.0, sec_score * 100)
        matched_set.update(sec_matched)

    # Identify missing required keywords (for UI "Suggested Keywords" panel)
    full_resume_lower = resume_text.lower()
    for term, _ in jd_keywords["required"]:
        if not _term_in_text(term, full_resume_lower):
            missing_required.append(term)

    # Overall keyword score: weighted average of sections
    overall = 0.0
    total_w = 0.0
    for sec, w in SECTION_WEIGHTS.items():
        overall += section_scores.get(sec, 0.0) * w
        total_w += w
    if total_w > 0:
        overall /= total_w

    return {
        "overall":          round(float(overall), 1),
        "sections":         {k: round(float(v), 1) for k, v in section_scores.items()},
        "missing_keywords": missing_required[:20],   # cap at 20 for UI
        "matched_keywords": sorted(matched_set)[:30],
    }


def _term_in_text(term: str, text_lower: str) -> bool:
    """Check if a term (possibly multi-word) appears as a whole phrase in text.
    Both term and text_lower are expected to be lowercase already.
    """
    escaped = re.escape(term.lower())
    # Use word boundary that works with multi-word phrases
    pattern = r'(?<![a-z])' + escaped + r'(?![a-z])'
    return bool(re.search(pattern, text_lower))


# Section-domain hints: which keyword tiers are most relevant per section
_SECTION_DOMAIN_WEIGHT = {
    # (required_multiplier, preferred_multiplier, general_multiplier)
    "summary":        (1.0, 1.0, 0.8),
    "skills":         (1.2, 1.1, 0.6),   # boost exact tech matches
    "internship":     (1.2, 1.0, 0.8),   # boost required terms
    "projects":       (1.0, 1.0, 0.9),
    "education":      (0.8, 0.8, 1.0),
    "certifications": (1.1, 1.0, 0.7),
}


def _score_section_keywords(
    section_text: str,
    all_kw: List[Tuple[str, float]],
    section_name: str
) -> Tuple[float, Set[str]]:
    """
    Score a single section against keyword list.
    Returns (raw_score 0-1, matched_terms set).
    """
    if not section_text.strip() or not all_kw:
        return 0.0, set()

    text_lower = section_text.lower()
    total_score   = 0.0
    max_possible  = 0.0
    matched_terms: Set[str] = set()

    for term, weight in all_kw:
        if _term_in_text(term, text_lower):
            total_score += weight
            matched_terms.add(term)
        max_possible += weight

    if max_possible == 0:
        return 0.0, set()

    return total_score / max_possible, matched_terms


# ---------------------------------------------------------------------------
# Semantic similarity
# ---------------------------------------------------------------------------
def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """Returns score 0–100."""
    if not text1 or not text2 or not text1.strip() or not text2.strip():
        return 0.0
    try:
        emb1 = _encode_text(text1)
        emb2 = _encode_text(text2)
        sim = cosine_similarity([emb1], [emb2])[0][0]
        sim = max(0.0, min(1.0, float(sim)))
        return sim * 100
    except Exception as e:
        logger.error(f"Semantic similarity failed: {e}", exc_info=True)
        return 0.0


# ---------------------------------------------------------------------------
# Resume sectioning — unchanged logic, just cleaned up
# ---------------------------------------------------------------------------
def split_resume_into_sections(resume_text: str) -> Dict[str, str]:
    """Split resume into named sections. Handles both plain text and JSON."""
    sections = {k: "" for k in SECTION_WEIGHTS}

    # JSON input (rewritten resume from Gemini)
    try:
        parsed_json = json.loads(resume_text)
        if isinstance(parsed_json, dict):
            sections["summary"] = str(parsed_json.get("summary", ""))

            for edu in parsed_json.get("education", []):
                sections["education"] += (
                    f"{edu.get('institution', '')} {edu.get('degree', '')} "
                    f"{edu.get('duration', '')}\n"
                )

            for proj in parsed_json.get("projects", []):
                bullets = " ".join(proj.get("bullets", []))
                sections["projects"] += (
                    f"{proj.get('name', '')} {proj.get('duration', '')} {bullets}\n"
                )

            for exp in parsed_json.get("internship", []):
                bullets = " ".join(exp.get("bullets", []))
                sections["internship"] += (
                    f"{exp.get('company', '')} {exp.get('role', '')} "
                    f"{exp.get('duration', '')} {bullets}\n"
                )

            for skill in parsed_json.get("skills", []):
                sections["skills"] += (
                    f"{skill.get('category', '')} {skill.get('items', '')}\n"
                )

            for cert in parsed_json.get("certifications", []):
                sections["certifications"] += (
                    f"{cert.get('name', '')} {cert.get('duration', '')}\n"
                )

            return sections
    except (json.JSONDecodeError, TypeError):
        pass  # Not JSON — parse as plain text

    # Plain text: match section headers
    header_patterns = {
        "summary":        [r"summary", r"professional summary", r"profile",
                           r"objective", r"about me"],
        "education":      [r"education", r"academic background", r"academics",
                           r"qualification"],
        "projects":       [r"projects?", r"personal projects?", r"academic projects?",
                           r"key projects?"],
        "internship":     [r"internship", r"experience", r"work experience",
                           r"employment", r"professional experience",
                           r"relevant experience"],
        "skills":         [r"skills?", r"technical skills?", r"competenc(?:y|ies)",
                           r"expertise", r"technologies"],
        "certifications": [r"certifications?", r"certificates?", r"licenses?",
                           r"credentials?"],
    }

    lines = resume_text.split('\n')
    current_section = None
    section_content: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        found = False
        for sec_name, patterns in header_patterns.items():
            for pat in patterns:
                if re.search(rf'^{pat}:?\s*$', stripped, re.IGNORECASE):
                    if current_section and section_content:
                        sections[current_section] = '\n'.join(section_content).strip()
                    current_section = sec_name
                    section_content = []
                    found = True
                    break
            if found:
                break

        if not found and current_section:
            section_content.append(line)

    if current_section and section_content:
        sections[current_section] = '\n'.join(section_content).strip()

    return sections