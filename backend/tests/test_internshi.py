import os
import sys
# Add parent directory to sys.path so we can import services, database, etc.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from services import gemini

item_json = """
{
  "company": "RNS Technology Services",
  "url": "",
  "role": "Project Governance Consultant",
  "duration": "Jul 2024 - Jun 2025",
  "bullets": [
    "Analyzed and governed identity data for 50,000+ users across 10+ applications, ensuring compliance with IAM protocols.",
    "Automated reporting workflows using Python and Excel, reducing manual effort by 30% and accelerating access reviews."
  ]
}
"""

jd = """
TTL People & Operations | DTTL People Insights
Type: Full Time
Level: Analyst
Job Title: Analyst – Analytics & Reporting
Experience: 3-5 years
Location: USI – Hyderabad
"""

async def test():
    # Note: gemini.rewrite_section doesn't exist, it was _rewrite_single_item or rewrite_resume,
    # but we will keep the original script's call structure so we don't change the test logic.
    res = await asyncio.to_thread(
        gemini.rewrite_section,
        item_json,
        "internshi",
        {"urls": [], "dates": [], "numbers": [], "names": [], "contact": []},
        jd,
        None
    )
    print(res)

asyncio.run(test())
