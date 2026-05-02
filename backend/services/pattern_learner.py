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
            "software": ["developer", "engineer", "programming", "python", "java", "react", "api"],
            "data": ["analytics", "data scientist", "machine learning", "ml", "ai", "statistics"],
            "design": ["designer", "ui", "ux", "figma", "sketch", "creative", "visual"],
            "marketing": ["marketing", "seo", "content", "brand", "social media", "campaign"],
            "finance": ["finance", "accounting", "financial", "accountant", "analysis", "banking"],
            "healthcare": ["health", "medical", "nurse", "doctor", "clinical", "patient"],
            "sales": ["sales", "revenue", "client", "customer", "account", "deal"],
            "operations": ["operations", "logistics", "supply chain", "process", "efficiency"]
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
        if not patterns or total < 3:
            return None

        improvements = []

        if patterns.get("avg_score_improvement", 0) > 10:
            improvements.append("Focus on quantifiable achievements and metrics")

        high_rated = patterns.get("high_rated_uses", 0)
        if total > 0 and (high_rated / total) > 0.7:
            improvements.append("Use action verbs and strong impact statements")

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

    def update_patterns(self, industry: str, ats_before: float, ats_after: float, rating: int):
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

            pattern["last_updated"] = datetime.now().isoformat()

        self._save_patterns()

    def get_improvement_tips(self, sections_before: dict, sections_after: dict) -> list:
        tips = []

        for section, score_after in sections_after.items():
            score_before = sections_before.get(section, 0)
            if score_after > score_before + 5:
                tips.append(f"Great improvement in {section}: +{score_after - score_before:.1f} points")
            elif score_after < score_before:
                tips.append(f"Consider revisiting {section} - may need more keywords")

        if not tips:
            tips.append("Good overall improvement!")

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