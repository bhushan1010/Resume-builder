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
LinkedIn | GitHub | LeetCode | Portfolio

PROFESSIONAL SUMMARY
B.Tech graduate in AI & Data Science (VIIT Pune, 2025) with a strong foundation in data mining, analytics, and reporting. Experienced in transforming complex datasets into actionable insights using advanced Excel, Python, and cloud infrastructure. Proven ability to work cross-functionally with stakeholders to understand requirements, assess complexity, and deliver automated reporting solutions. Seeking to leverage technical expertise in data analysis, trend identification, and visualization to support business leaders as an Analytics & Reporting Analyst.

TECHNICAL SKILLS
Analytics & Reporting: Advanced Excel (Macros, Power Query, Dashboard Building), Data Mining, Tableau, PowerBI, Trend Analysis, HR Data Governance
Programming & Systems: Python, SQL, AWS (EC2, S3), FastAPI, Cloud Monitoring, SuccessFactors (Familiarity)
Collaboration & Tools: MS Office Suite, Confluence, Zoho Projects, Incident Ticketing Systems
Core Competencies: Stakeholder Collaboration, Strategic Consulting, Cross-functional Problem Solving, Clear Technical Communication

PROFESSIONAL EXPERIENCE
Project Governance Consultant | RNS Technology Services | Jul 2024 - Jun 2025 | Pune, India
- Analyzed and governed identity data for 3,000+ digital profiles, creating accurate reports and tracking metrics to support organizational security goals.
- Applied critical thinking to data mining requests; developed automated monitoring workflows that identified operational bottlenecks and reduced incident response times by 70%.
- Maintained detailed resolution logs and governance documentation, regularly interpreting data to provide insightful reports and risk summaries to non-technical stakeholders and leadership.
- Acted as a liaison between cross-functional IT teams, utilizing data-driven decision-making to drive audit closures and translate technical needs into strategic recommendations.

RELEVANT PROJECTS
Automated Analytics & Knowledge Assistant | Python, AWS, Data Pipelines | Nov 2025 - Feb 2026
- Understood data flow and interfacing systems to build automated solutions for monitoring and analytics needs, deployed on AWS (EC2/Lambda/EKS).
- Gathered and analyzed system performance data to identify trends, translating metrics into actionable troubleshooting runbooks and operational SOPs for leadership.

Network Data & Fundamentals | TCP/IP, DNS, Routing | Jul - Dec 2023
- Analyzed network traffic and connectivity trends to troubleshoot failures, developing strong diagnostic and analytical capabilities.

EDUCATION
B.Tech in Artificial Intelligence & Data Science | VIIT, Pune | 2021 - 2025

CERTIFICATIONS
AWS Certified Solutions Architect – Amazon Web Services (Oct - Nov 2024)
Google Project Management Certificate – Google (Jun - Dec 2024)

LEADERSHIP
Treasurer, AI Student Association | VIIT Pune | 2023 - 2024
- Managed financial data, reporting, and operations for a 100+ member organization, demonstrating strong attention to detail, organizational discipline, and collaborative reporting.
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
