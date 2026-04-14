"""
ats_analytics.py  –  ATS score estimation & keyword match analysis
Analyzes a tailored profile against a job description to estimate
ATS compatibility and provide actionable improvement suggestions.
"""

import re
from collections import Counter


def _extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from text (lowercased, filtered)."""
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'shall', 'can', 'need', 'dare',
        'ought', 'used', 'it', 'its', 'this', 'that', 'these', 'those', 'i',
        'you', 'he', 'she', 'we', 'they', 'what', 'which', 'who', 'whom',
        'whose', 'where', 'when', 'why', 'how', 'all', 'each', 'every',
        'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'about',
        'above', 'below', 'between', 'into', 'through', 'during', 'before',
        'after', 'while', 'as', 'if', 'then', 'also', 'well', 'etc', 'per',
        'able', 'across', 'against', 'along', 'among', 'around', 'back',
        'because', 'become', 'becomes', 'became', 'begin', 'began', 'begun',
        'beside', 'besides', 'beyond', 'both', 'down', 'during', 'except',
        'further', 'here', 'however', 'including', 'less', 'like', 'much',
        'never', 'nor', 'now', 'off', 'once', 'over', 'rather', 'since',
        'still', 'throughout', 'under', 'until', 'upon', 'whether', 'yet',
        'your', 'our', 'their', 'my', 'his', 'her', 'its', 'our', 'their',
        'am', 'any', 'another', 'anything', 'everything', 'something',
        'nothing', 'someone', 'anyone', 'everyone', 'noone', 'everybody',
        'somebody', 'anybody', 'nobody', 'within', 'without', 'along',
        'already', 'always', 'never', 'often', 'sometimes', 'usually',
        'really', 'quite', 'rather', 'pretty', 'fairly', 'simply', 'highly',
        'deeply', 'strongly', 'greatly', 'closely', 'directly', 'exactly',
        'ensure', 'ensuring', 'ensure', 'ensured', 'demonstrating',
        'demonstrate', 'demonstrated', 'providing', 'provide', 'provided',
        'developing', 'develop', 'developed', 'designing', 'design',
        'designed', 'implementing', 'implement', 'implemented', 'managing',
        'manage', 'managed', 'leading', 'lead', 'led', 'building', 'build',
        'built', 'creating', 'create', 'created', 'working', 'work',
        'worked', 'collaborating', 'collaborate', 'collaborated',
        'coordinating', 'coordinate', 'coordinated', 'supporting',
        'support', 'supported', 'maintaining', 'maintain', 'maintained',
        'improving', 'improve', 'improved', 'reducing', 'reduce', 'reduced',
        'increasing', 'increase', 'increased', 'optimizing', 'optimize',
        'optimized', 'delivering', 'deliver', 'delivered', 'driving',
        'drive', 'driven', 'executing', 'execute', 'executed', 'handling',
        'handle', 'handled', 'serving', 'serve', 'served', 'processing',
        'process', 'processed', 'achieving', 'achieve', 'achieved',
        'enabling', 'enable', 'enabled', 'integrating', 'integrate',
        'integrated', 'deploying', 'deploy', 'deployed', 'monitoring',
        'monitor', 'monitored', 'testing', 'test', 'tested', 'reviewing',
        'review', 'reviewed', 'analyzing', 'analyze', 'analyzed',
        'researching', 'research', 'researched', 'training', 'train',
        'trained', 'mentoring', 'mentor', 'mentored', 'presenting',
        'present', 'presented', 'reporting', 'report', 'reported',
        'tracking', 'track', 'tracked', 'responsible', 'responsibilities',
        'responsibility', 'experience', 'expertise', 'proficiency',
        'proficient', 'familiar', 'knowledge', 'understanding', 'skills',
        'skill', 'ability', 'abilities', 'capable', 'capability',
        'capabilities', 'qualified', 'qualification', 'qualifications',
        'requirements', 'requirement', 'required', 'preferred', 'plus',
        'including', 'includes', 'include', 'etc', 'ie', 'eg', 'via',
        'using', 'use', 'used', 'utilizing', 'utilize', 'utilized',
        'leveraging', 'leverage', 'leveraged', 'applying', 'apply',
        'applied', 'implementing', 'implementation',
    }
    words = re.findall(r'[a-zA-Z][a-zA-Z0-9+#.]*', text.lower())
    return {w for w in words if len(w) > 2 and w not in stop_words}


def _extract_tech_keywords(text: str) -> set[str]:
    """Extract technology-related keywords (case-sensitive patterns)."""
    tech_patterns = [
        r'\b[A-Z][a-zA-Z0-9+#]*\b',
        r'\b(?:AWS|GCP|Azure|CI/CD|API|REST|GraphQL|SQL|NoSQL|ML|AI|LLM|RAG|NLP|IoT|DevOps|Agile|Scrum|KPI|SLA|OKR|IAM|SaaS|PaaS|IaaS|UI|UX|UX/UI|TDD|BDD|DDD|OOP|SOLID|DRY|KISS|YAGNI)\b',
    ]
    results = set()
    for pattern in tech_patterns:
        results.update(re.findall(pattern, text))
    return results


def analyze_ats_score(profile_data: dict, job_description: str, company_name: str = '') -> dict:
    """Analyze how well a profile matches a job description.

    Returns a dict with:
        - overall_score: 0-100
        - keyword_match: dict with matched, missing, and percentage
        - section_scores: scores per section (experience, skills, projects, education)
        - suggestions: list of actionable improvement tips
        - strengths: list of strong points found
    """
    jd_keywords = _extract_keywords(job_description)
    jd_tech = _extract_tech_keywords(job_description)

    # Combine all profile text
    profile_text_parts = []
    b = profile_data.get('basics', {})
    if b.get('name'): profile_text_parts.append(b['name'])

    for edu in profile_data.get('education', []):
        for field in ['institution', 'degree', 'location']:
            if edu.get(field): profile_text_parts.append(edu[field])

    for exp in profile_data.get('experience', []):
        for field in ['company', 'role', 'location']:
            if exp.get(field): profile_text_parts.append(exp[field])
        for bullet in exp.get('bullets', []):
            profile_text_parts.append(bullet)

    for proj in profile_data.get('projects', []):
        profile_text_parts.append(proj.get('name', ''))
        for tech in proj.get('technologies', []):
            profile_text_parts.append(tech)
        for bullet in proj.get('bullets', []):
            profile_text_parts.append(bullet)

    skills = profile_data.get('skills', {})
    if hasattr(skills, '__dict__'):
        skills = vars(skills)
    for cat in ['languages', 'frameworks', 'tools']:
        for item in skills.get(cat, []):
            profile_text_parts.append(item)

    for cert in profile_data.get('certifications', []):
        for field in ['name', 'issuer']:
            if cert.get(field): profile_text_parts.append(cert[field])

    profile_text = ' '.join(profile_text_parts)
    profile_keywords = _extract_keywords(profile_text)
    profile_tech = _extract_tech_keywords(profile_text)

    # Keyword matching
    all_jd_keywords = jd_keywords | jd_tech
    matched_keywords = all_jd_keywords & (profile_keywords | profile_tech)
    missing_keywords = all_jd_keywords - (profile_keywords | profile_tech)

    keyword_pct = (len(matched_keywords) / len(all_jd_keywords) * 100) if all_jd_keywords else 100

    # Section scores
    exp_text = ' '.join([
        ' '.join(exp.get('bullets', []))
        for exp in profile_data.get('experience', [])
    ])
    exp_keywords = _extract_keywords(exp_text)
    exp_match = (len(exp_keywords & jd_keywords) / len(jd_keywords) * 100) if jd_keywords else 100

    skill_items = []
    for cat in ['languages', 'frameworks', 'tools']:
        skill_items.extend(skills.get(cat, []))
    skill_text = ' '.join(skill_items)
    skill_keywords = _extract_keywords(skill_text) | _extract_tech_keywords(skill_text)
    skill_match = (len(skill_keywords & all_jd_keywords) / len(all_jd_keywords) * 100) if all_jd_keywords else 100

    proj_text = ' '.join([
        proj.get('name', '') + ' ' + ' '.join(proj.get('technologies', [])) + ' ' + ' '.join(proj.get('bullets', []))
        for proj in profile_data.get('projects', [])
    ])
    proj_keywords = _extract_keywords(proj_text) | _extract_tech_keywords(proj_text)
    proj_match = (len(proj_keywords & all_jd_keywords) / len(all_jd_keywords) * 100) if all_jd_keywords else 100

    # Overall score (weighted)
    overall_score = round(
        keyword_pct * 0.35 +
        min(exp_match, 100) * 0.30 +
        min(skill_match, 100) * 0.20 +
        min(proj_match, 100) * 0.15
    )

    # Generate suggestions
    suggestions = []
    strengths = []

    if keyword_pct < 40:
        suggestions.append("Low keyword match. Consider incorporating more terms from the job description into your experience bullets.")
    elif keyword_pct < 60:
        suggestions.append("Moderate keyword match. Add a few more JD-specific terms to strengthen ATS compatibility.")
    else:
        strengths.append(f"Strong keyword match ({keyword_pct:.0f}%) with the job description.")

    if exp_match < 40:
        suggestions.append("Experience section lacks JD-relevant keywords. Rewrite bullets to highlight matching skills and achievements.")
    elif exp_match >= 60:
        strengths.append("Experience section is well-aligned with the job requirements.")

    if skill_match < 30:
        suggestions.append("Skills section is missing key technologies from the JD. Add relevant tools and frameworks.")
    elif skill_match >= 50:
        strengths.append("Skills section covers most technologies requested in the JD.")

    if proj_match < 30:
        suggestions.append("Projects don't strongly align with the JD. Consider adding projects that use the requested technologies.")
    elif proj_match >= 50:
        strengths.append("Projects demonstrate relevant technical skills for this role.")

    if missing_keywords:
        top_missing = sorted(missing_keywords, key=lambda w: len(w), reverse=True)[:10]
        suggestions.append(f"Consider adding these missing keywords: {', '.join(top_missing)}")

    if not profile_data.get('experience'):
        suggestions.append("No experience section found. Add work experience to improve ATS score.")

    if not profile_data.get('projects'):
        suggestions.append("No projects section found. Adding relevant projects can boost your score.")

    if len(skill_items) < 5:
        suggestions.append("List more technical skills to improve keyword coverage.")

    if not strengths:
        strengths.append("Profile has a good foundation. Focus on adding missing keywords to improve the score.")

    return {
        'overall_score': min(overall_score, 100),
        'keyword_match': {
            'matched': sorted(matched_keywords),
            'missing': sorted(missing_keywords),
            'percentage': round(keyword_pct, 1),
            'total_jd_keywords': len(all_jd_keywords),
            'matched_count': len(matched_keywords),
        },
        'section_scores': {
            'experience': round(min(exp_match, 100)),
            'skills': round(min(skill_match, 100)),
            'projects': round(min(proj_match, 100)),
        },
        'suggestions': suggestions,
        'strengths': strengths,
    }
