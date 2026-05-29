import os
import sys
# Add parent directory to sys.path so we can import services, database, etc.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from services import ats_scorer

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

skeleton = {
    "header": {"name": "", "email": "", "phone": "", "linkedin": "", "github": "", "portfolio": "", "leetcode": ""},
    "summary": "",
    "education": [],
    "projects": [],
    "internship": [],
    "skills": [],
    "certifications": []
}

score = ats_scorer.score(json.dumps(skeleton), jd)
print(json.dumps(score, indent=2))
