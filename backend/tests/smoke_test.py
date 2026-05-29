import os
import sys
# Add parent directory to sys.path so we can import services, database, etc.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import ats_scorer, gemini
print("IMPORTS OK")

# Quick sanity check on keyword extractor
jd = """
Job Title: Analyst – Analytics & Reporting
Required: Python, SQL, Power BI, data storytelling, Excel
Preferred: Power Query, DAX, HR analytics, people insights
"""
kw = ats_scorer.extract_jd_keywords(jd)
print(f"Required keywords ({len(kw['required'])}): {[t for t,_ in kw['required'][:8]]}")
print(f"Preferred keywords ({len(kw['preferred'])}): {[t for t,_ in kw['preferred'][:8]]}")
print(f"General keywords ({len(kw['general'])}): {[t for t,_ in kw['general'][:8]]}")

resume = """
PROFESSIONAL SUMMARY
B.Tech graduate in AI & Data Science with expertise in Python, SQL, Power BI, and Excel.
Experienced in data storytelling and analytics reporting.

TECHNICAL SKILLS
Analytics: Excel (Advanced), SQL, Power BI, Python (Pandas, NumPy)

PROFESSIONAL EXPERIENCE
RNS Technology Services | Analyst | Jul 2024 - Jun 2025
- Automated reporting workflows using Python and SQL
- Built Power BI dashboards for stakeholders

EDUCATION
B.Tech in AI & Data Science | VIIT, Pune | 2021-2025

CERTIFICATIONS
AWS Certified Solutions Architect
"""
score = ats_scorer.score(resume, jd)
print(f"\nOverall: {score['overall']}")
print(f"Sections: {score['sections']}")
print(f"Missing: {score['missing_keywords'][:5]}")
print(f"Matched: {score['matched_keywords'][:5]}")
