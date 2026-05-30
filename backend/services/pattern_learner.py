import json
import os
import re
import logging
import threading
import tempfile
from collections import defaultdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Configurable file path (defaults to file next to this module)
PATTERNS_FILE = os.getenv(
    "PATTERNS_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "patterns_data.json")
)

# Default schema for a pattern entry — used to merge with loaded data
DEFAULT_PATTERN = {
    "avg_score_improvement": 0,
    "total_uses": 0,
    "high_rated_uses": 0,
    "keywords_preferred": [],
    "effective_sections": {},
    "last_updated": None
}


class PatternLearner:
    def __init__(self):
        self.patterns = defaultdict(lambda: dict(DEFAULT_PATTERN))
        self._lock = threading.Lock()
        self._load_patterns()

    def detect_industry(self, job_description: str) -> Optional[str]:
        industry_keywords = {
            "software": ["developer", "engineer", "programming", "python", "java", "react", "api",
                         "backend", "frontend", "fullstack", "microservices", "devops"],
            "data": ["analytics", "data scientist", "machine learning", "ml", "ai", "statistics",
                     "big data", "data engineer", "etl", "warehouse", "pipeline"],
            "design": ["designer", "ui", "ux", "figma", "sketch", "creative", "visual",
                       "graphic", "interaction", "wireframe", "prototype"],
            "marketing": ["marketing", "seo", "content", "brand", "social media", "campaign",
                          "digital marketing", "growth", "acquisition", "retention"],
            "finance": ["finance", "accounting", "financial", "accountant", "analysis", "banking",
                        "investment", "portfolio", "risk", "compliance", "audit"],
            "healthcare": ["health", "medical", "nurse", "doctor", "clinical", "patient",
                           "pharmaceutical", "biotech", "therapy", "diagnosis"],
            "sales": ["sales", "revenue", "client", "customer", "account", "deal",
                      "pipeline", "quota", "territory", "commission"],
            "operations": ["operations", "logistics", "supply chain", "process", "efficiency",
                           "procurement", "warehouse", "inventory", "distribution"],
            "consulting": ["consultant", "consulting", "advisory", "strategy", "stakeholder",
                           "engagement", "transformation", "change management"],
            "product": ["product manager", "product owner", "roadmap", "backlog", "agile",
                        "scrum", "sprint", "user stories", "product development"],
            "security": ["security", "cybersecurity", "infosec", "penetration", "vulnerability",
                         "encryption", "firewall", "soc", "threat"],
            "education": ["teacher", "instructor", "professor", "curriculum", "teaching",
                          "learning", "education", "academic", "training", "tutoring"],
            "legal": ["lawyer", "attorney", "legal", "paralegal", "litigation", "contract",
                      "regulatory", "intellectual property"],
            "hr": ["human resources", "hr", "recruitment", "talent", "onboarding",
                   "employee relations", "compensation", "benefits", "workforce"],
        }

        jd_lower = job_description.lower()
        scores = {}

        for industry, keywords in industry_keywords.items():
            score = 0
            for kw in keywords:
                # Use word boundary to avoid substring false-positives
                # (e.g. "ai" matching "available", "main", etc.)
                if re.search(r'\b' + re.escape(kw) + r'\b', jd_lower):
                    score += 1
            if score > 0:
                scores[industry] = score

        if scores:
            return max(scores, key=scores.get)
        return "general"

    def get_patterns_for_industry(self, industry: str) -> dict:
        return self.patterns.get(industry, {})

    def get_adapted_prompt(self, industry: str, patterns: dict) -> Optional[str]:
        total = patterns.get("total_uses", 0) if patterns else 0
        if not patterns or total < 1:
            return None

        improvements = []

        if patterns.get("avg_score_improvement", 0) > 10:
            improvements.append("Focus on quantifiable achievements and metrics")
        elif patterns.get("avg_score_improvement", 0) > 5:
            improvements.append("Include specific numbers and percentages in achievements")

        high_rated = patterns.get("high_rated_uses", 0)
        if total > 0 and (high_rated / total) > 0.7:
            improvements.append("Use action verbs and strong impact statements")
        elif total > 0 and (high_rated / total) > 0.4:
            improvements.append("Start bullets with diverse action verbs")

        # Industry-specific hints
        industry_hints = {
            "software": "Emphasize technical stack alignment, system design, and scalability",
            "data": "Highlight data pipeline experience, statistical methods, and ML model performance metrics",
            "consulting": "Focus on client impact, stakeholder management, and strategic recommendations",
            "product": "Emphasize user impact metrics, roadmap execution, and cross-functional collaboration",
            "security": "Highlight compliance frameworks, vulnerability reduction metrics, and incident response",
            "finance": "Focus on financial impact, risk reduction, and regulatory compliance",
        }
        if industry in industry_hints:
            improvements.append(industry_hints[industry])

        effective = patterns.get("effective_sections", {})
        if effective.get("skills"):
            improvements.append(f"Emphasize {effective['skills']} skills prominently")

        if improvements:
            return " | ".join(improvements)
        return None

    def calculate_pattern_score(self, ats_before: float, ats_after: float, rating: int) -> float:
        improvement = ats_after - ats_before
        rating_factor = (rating - 3) * 2
        return improvement + rating_factor

    def update_patterns(self, industry: str, ats_before: float, ats_after: float, rating: int,
                        sections_before: dict = None, sections_after: dict = None):
        with self._lock:
            pattern = self.patterns[industry]

            total = pattern["total_uses"]
            current_avg = pattern["avg_score_improvement"]

            new_improvement = ats_after - ats_before
            new_avg = ((current_avg * total) + new_improvement) / (total + 1)
            pattern["avg_score_improvement"] = new_avg
            pattern["total_uses"] = total + 1

            if rating >= 4:
                pattern["high_rated_uses"] = pattern.get("high_rated_uses", 0) + 1

            # Phase 8: Track per-section effectiveness for adaptive prompting
            if sections_before and sections_after and rating >= 4:
                effective = pattern.get("effective_sections", {})
                for section, after_score in sections_after.items():
                    before_score = sections_before.get(section, 0)
                    delta = after_score - before_score
                    if delta > 5:
                        sec_data = effective.get(section, {"avg_delta": 0, "count": 0})
                        old_avg = sec_data.get("avg_delta", 0)
                        old_count = sec_data.get("count", 0)
                        sec_data["avg_delta"] = ((old_avg * old_count) + delta) / (old_count + 1)
                        sec_data["count"] = old_count + 1
                        effective[section] = sec_data
                pattern["effective_sections"] = effective

            pattern["last_updated"] = datetime.now().isoformat()

        self._save_patterns()

    def get_improvement_tips(self, sections_before: dict, sections_after: dict) -> list:
        """Generate rich, actionable improvement tips by comparing section scores."""
        tips = []

        # Section-specific advice templates
        section_advice = {
            "summary": {
                "low":  "Rewrite your summary to lead with the target job title and top 3-5 required skills",
                "stale": "Try including specific years of experience and 2-3 key achievements in your summary",
                "good":  "Summary effectively highlights your value proposition",
            },
            "skills": {
                "low":  "Align your skills section with the exact technologies listed in the job description",
                "stale": "Group skills by category (Languages, Frameworks, Cloud, Tools) to improve readability",
                "good":  "Skills section is well-aligned with the job requirements",
            },
            "internship": {
                "low":  "Add quantified metrics (%, $, numbers) to each internship bullet point",
                "stale": "Start each bullet with a strong action verb and include measurable outcomes",
                "good":  "Internship section demonstrates strong quantified impact",
            },
            "projects": {
                "low":  "Highlight the tech stack and measurable outcomes in each project description",
                "stale": "Emphasize technologies that match the job description in your project bullets",
                "good":  "Projects section effectively showcases relevant technical experience",
            },
            "education": {
                "low":  "Include relevant coursework, GPA (if strong), and academic achievements",
                "stale": "Add relevant certifications or training alongside your degree",
                "good":  "Education section is well-structured",
            },
            "certifications": {
                "low":  "Add industry-relevant certifications to strengthen your profile",
                "stale": "Consider adding certification dates and issuing organizations",
                "good":  "Certifications add strong credibility to your profile",
            },
        }

        total_before = 0
        total_after = 0
        section_count = 0

        for section, score_after in sections_after.items():
            score_before = sections_before.get(section, 0)
            delta = score_after - score_before
            total_before += score_before
            total_after += score_after
            section_count += 1

            advice = section_advice.get(section, {})
            section_label = section.replace("_", " ").title()

            if delta > 10:
                tips.append(f"Great improvement in {section_label}: +{delta:.1f} points! {advice.get('good', '')}")
            elif delta > 5:
                tips.append(f"Good progress in {section_label}: +{delta:.1f} points")
            elif delta < -2:
                tips.append(f"Consider revisiting {section_label} (dropped {abs(delta):.1f} pts) — {advice.get('stale', 'may need more keywords')}")
            elif score_after < 40:
                tips.append(f"{section_label} needs attention ({score_after:.0f}%) — {advice.get('low', 'add more relevant content')}")
            elif score_after < 60:
                tips.append(f"{section_label} could be stronger ({score_after:.0f}%) — {advice.get('stale', 'try adding more specifics')}")

        # Overall summary
        if section_count > 0:
            avg_before = total_before / section_count
            avg_after = total_after / section_count
            overall_delta = avg_after - avg_before
            if overall_delta > 10:
                tips.insert(0, f"Excellent overall improvement: +{overall_delta:.1f} points on average across all sections!")
            elif overall_delta > 0:
                tips.insert(0, f"Overall improvement: +{overall_delta:.1f} points on average")

        if not tips:
            tips.append("Good overall match — consider fine-tuning individual sections for additional points")

        return tips

    def get_industry_stats(self, industry: str) -> Optional[dict]:
        pattern = self.patterns.get(industry)
        if not pattern:
            return None

        total = pattern.get("total_uses", 0)
        return {
            "industry": industry,
            "total_uses": total,
            "avg_improvement": pattern.get("avg_score_improvement", 0),
            "success_rate": pattern.get("high_rated_uses", 0) / max(total, 1),
            "effective_sections": pattern.get("effective_sections", {}),
            "last_updated": pattern.get("last_updated")
        }

    def _load_patterns(self):
        if not os.path.exists(PATTERNS_FILE):
            return
        try:
            with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for industry, pattern in data.items():
                    # Merge with defaults so old saved files survive schema evolution
                    merged = {**DEFAULT_PATTERN, **pattern}
                    self.patterns[industry] = merged
            logger.info(f"Loaded {len(data)} industry patterns from {PATTERNS_FILE}")
        except Exception as e:
            logger.error(f"Failed to load patterns from {PATTERNS_FILE}: {e}", exc_info=True)

    def _save_patterns(self):
        """
        Atomic + thread-safe write:
          1. Acquire lock (no concurrent writers)
          2. Write to a temp file in the same directory
          3. os.replace() -> atomic rename (works on POSIX & Windows)
        """
        try:
            with self._lock:
                patterns_dict = dict(self.patterns)
                dir_name = os.path.dirname(os.path.abspath(PATTERNS_FILE)) or "."
                os.makedirs(dir_name, exist_ok=True)

                # Write to temp file, then atomically rename
                fd, tmp_path = tempfile.mkstemp(
                    prefix=".patterns_", suffix=".tmp", dir=dir_name
                )
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                        json.dump(patterns_dict, tmp, indent=2)
                    os.replace(tmp_path, PATTERNS_FILE)
                except Exception:
                    # Cleanup temp file on failure
                    if os.path.exists(tmp_path):
                        try:
                            os.remove(tmp_path)
                        except OSError:
                            pass
                    raise
        except Exception as e:
            logger.error(f"Failed to save patterns to {PATTERNS_FILE}: {e}", exc_info=True)


pattern_learner = PatternLearner()