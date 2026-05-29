import os
import sys
# Add parent directory to sys.path so we can import services, database, etc.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from services import ats_scorer

resume_text = """
BHUSHAN SISODE
Pune, India | bhushansisode12@gmail.com | +91 8830158477
LinkedIn: https://linkedin.com/in/bhushansisode | GitHub: https://github.com/bhushansisode | LeetCode: https://leetcode.com/bhushan | Portfolio: https://bhushan.dev

PROFESSIONAL SUMMARY
B.Tech graduate in AI & Data Science (VIIT Pune, 2025) with a strong foundation in data mining, analytics, and reporting. Experienced in transforming complex datasets into actionable insights using advanced Excel, Python, and cloud infrastructure. Proven ability to work cross-functionally with stakeholders to understand requirements, assess complexity, and deliver automated reporting solutions. Seeking to leverage technical expertise in data analysis, trend identification, and visualization to support business leaders as an Analytics & Reporting Analyst.
"""

jd = """
TTL People & Operations | DTTL People Insights
Type: Full Time
Level: Analyst
Job Title: Analyst – Analytics & Reporting
Experience: 3-5 years
Location: USI – Hyderabad
Shift Timings: 2:00 PM – 11:00 PM

Summary:
DTTL People Insights team supporting Deloitte Global is looking for a technical, curious, ambitious and innovative individual to join its growing team. 
This team’s mission is centered around providing actionable insights to its clients so that they can make informed decisions regarding its people. And we do that by transforming data to “tell the story” – both visually and verbally.
"""

score = ats_scorer.score(resume_text, jd)
print(json.dumps(score, indent=2))
