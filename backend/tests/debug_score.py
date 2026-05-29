"""
Debug: Score a JSON resume string to see what sections produce.
"""
import os
import sys
# Add parent directory to sys.path so we can import services, database, etc.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from services import ats_scorer

jd = """
Job Title: Analyst – Analytics & Reporting
Required: Python, SQL, Power BI, data storytelling, Excel, reporting
Preferred: Power Query, DAX, HR analytics, people insights
"""

# Simulate what json.dumps(rewritten_resume) looks like
rewritten_json = {
    "header": {"name": "Bhushan Sisode", "email": "bhushansisode12@gmail.com", "phone": "+91 8830158477",
               "linkedin": "https://linkedin.com/in/bhushansisode", "github": "", "portfolio": "", "leetcode": ""},
    "summary": "B.Tech graduate in AI & Data Science with expertise in Python, SQL, Power BI, and Excel. Experienced in data storytelling and analytics reporting.",
    "education": [{"institution": "VIIT Pune", "degree": "B.Tech AI & Data Science", "duration": "2021-2025"}],
    "internship": [{"company": "RNS Technology Services", "url": "", "role": "Project Governance Consultant",
                    "duration": "Jul 2024 - Jun 2025",
                    "bullets": ["Automated reporting workflows using Python and SQL, reducing manual effort by 30%",
                                "Built Power BI dashboards for stakeholders"]}],
    "projects": [],
    "skills": [{"category": "Analytics", "items": "Excel, SQL, Power BI, Python (Pandas, NumPy)"}],
    "certifications": [{"name": "AWS Certified Solutions Architect", "url": "", "duration": "2024"}]
}

rewritten_text = json.dumps(rewritten_json)

# Step 1: Show what split_resume_into_sections extracts
sections = ats_scorer.split_resume_into_sections(rewritten_text)
print("=== EXTRACTED SECTIONS ===")
for k, v in sections.items():
    print(f"  [{k}]: '{v[:80]}...'" if len(v) > 80 else f"  [{k}]: '{v}'")

# Step 2: Show extracted JD keywords
kw = ats_scorer.extract_jd_keywords(jd)
print(f"\n=== JD KEYWORDS ({len(kw['all'])} total) ===")
for term, w in kw['all'][:20]:
    print(f"  ({w:.1f}) {term}")

# Step 3: Score it
score = ats_scorer.score(rewritten_text, jd)
print(f"\n=== FINAL SCORE ===")
print(f"Overall: {score['overall']}")
for k, v in score['sections'].items():
    print(f"  {k}: {v}")
print(f"Missing: {score['missing_keywords'][:5]}")
print(f"Matched: {score['matched_keywords'][:5]}")
