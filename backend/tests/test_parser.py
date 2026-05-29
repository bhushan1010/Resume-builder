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
LinkedIn: https://linkedin.com/in/bhushansisode | GitHub: https://github.com/bhushansisode | LeetCode: https://leetcode.com/bhushan | Portfolio: https://bhushan.dev

PROFESSIONAL SUMMARY
B.Tech graduate in AI & Data Science
"""

parsed = gemini.parse_resume(resume_text)
print(json.dumps(parsed, indent=2))
