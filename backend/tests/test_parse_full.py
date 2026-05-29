import os
import sys
# Add parent directory to sys.path so we can import services, database, etc.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from services import gemini

resume_text = """
BHUSHAN SISODE
Pune, India | bhushansisode12@gmail.com | +91 8830158477
LinkedIn | GitHub | LeetCode | Portfolio

PROFESSIONAL SUMMARY
B.Tech graduate in AI & Data Science (VIIT Pune, 2025) with a strong foundation in data mining, analytics, and reporting. Experienced in transforming complex datasets into actionable insights using advanced Excel, Python, and cloud infrastructure. Proven ability to work cross-functionally with stakeholders to understand requirements, assess complexity, and deliver automated reporting solutions. Seeking to leverage technical expertise in data analysis, trend identification, and visualization to support business leaders as an Analytics & Reporting Analyst.

PROFESSIONAL EXPERIENCE
Project Governance Consultant | RNS Technology Services | Jul 2024 - Jun 2025 | Pune, India
- Analyzed and governed identity data for 50,000+ users across 10+ applications, ensuring compliance with IAM protocols.
- Automated reporting workflows using Python and Excel, reducing manual effort by 30% and accelerating access reviews.

RELEVANT PROJECTS
Predictive Maintenance Engine | Python, Scikit-learn, IoT Sensors | Jan 2024 - Apr 2024
- Built a machine learning model to predict equipment failure with 85% accuracy.

TECHNICAL SKILLS
Analytics & Reporting: Excel (Advanced), SQL, Power BI, Python (Pandas, NumPy)
Cloud & Architecture: AWS (EC2, S3, RDS), System Design Basics
Programming Languages: Python, C++, JavaScript (Basic)

EDUCATION
B.Tech in Artificial Intelligence & Data Science | VIIT, Pune | 2021 - 2025

CERTIFICATIONS
AWS Certified Solutions Architect – Amazon Web Services (Oct - Nov 2024)
Google Project Management Certificate – Google (Jun - Dec 2024)
"""

async def test():
    res = await asyncio.to_thread(gemini.parse_resume, resume_text)
    print(json.dumps(res, indent=2))

asyncio.run(test())
