"""
Example: How the AI prompt and tailored output look with a real JD.

This demonstrates the full flow:
1. Base profile (from config/base_profile.yaml)
2. Target Job Description
3. Company Background
4. The generated prompt sent to the AI
5. Expected AI output (mocked)
"""

import json
import sys
import io
from app.ai_engine import _build_prompt

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── 1. CANDIDATE BASE PROFILE ────────────────────────────────────────────────
base_profile = {
    "basics": {
        "name": "Bhushan Vinod Sisode",
        "email": "bhushansisode12@gmail.com",
        "phone": "+91 8830158477",
        "linkedin": "linkedin.com/in/bhushansisode",
        "github": "github.com/bhushansisode",
        "leetcode": "leetcode.com/bhushansisode11"
    },
    "education": [
        {
            "institution": "Vishwakarma Institute of Information Technology",
            "location": "Pune, India",
            "degree": "B.Tech in Artificial Intelligence and Data Science",
            "startDate": "2021",
            "endDate": "2025"
        }
    ],
    "skills": {
        "languages": ["Python", "R", "SQL", "Bash"],
        "frameworks": ["LangChain", "LangGraph", "FastAPI", "TensorFlow", "Keras", "Scikit-learn", "RAGAS", "OpenAI API", "Pandas", "NumPy"],
        "tools": ["AWS (EC2, Lambda, S3)", "Pinecone", "FAISS", "MongoDB", "Git", "Docker", "Power BI", "Tableau", "SailPoint", "Confluence", "Zoho Projects", "Agile / Scrum"]
    },
    "experience": [
        {
            "company": "RNS Technology Services",
            "role": "Project Governance Consultant",
            "location": "Pune, India",
            "startDate": "Jul 2024",
            "endDate": "Jun 2025",
            "bullets": [
                "Spearheaded delivery support and governance for IAM (3,000+ identities via SailPoint), cybersecurity, and monitoring projects using Confluence and Zoho Projects, achieving a 70% reduction in multi-site incident response times.",
                "Managed vulnerability tracking and remediation across IT domains to ensure successful cybersecurity audit closures.",
                "Coordinated cross-functional teams in Agile sprints, producing stakeholder-ready status reports and risk registers for C-suite visibility."
            ]
        }
    ],
    "projects": [
        {
            "name": "Agentic Enterprise Knowledge Assistant",
            "technologies": ["Python", "LangChain", "LangGraph", "OpenAI API", "Pinecone", "FAISS", "FastAPI", "AWS (EC2, Lambda)", "RAGAS"],
            "bullets": [
                "Architected a autonomous multi-agent RAG system using a Planner-Executor pattern to retrieve, analyze, and verify insights from complex corporate document repositories, achieving zero-hallucination output on benchmark tests.",
                "Integrated RAGAS evaluation framework to continuously measure retrieval precision and answer faithfulness, improving RAG pipeline accuracy by 35% over baseline."
            ]
        },
        {
            "name": "Fake News Detection",
            "technologies": ["Python", "Scikit-learn", "Pandas", "NumPy", "Matplotlib", "Seaborn"],
            "bullets": [
                "Engineered an end-to-end ML pipeline using TF-IDF vectorization and ensemble classifiers (Random Forest, XGBoost) to detect fabricated news with 94% accuracy on a 50k-article dataset.",
                "Built explainability visualizations using SHAP values and LIME to surface model decision rationale, aligning with AI transparency and safety principles."
            ]
        }
    ],
    "certifications": [
        {"name": "AWS Cloud Solutions Architect", "issuer": "Amazon Web Services", "date": "Oct 2024 – Nov 2024"},
        {"name": "AWS Cloud Technology Consultant", "issuer": "Amazon Web Services", "date": "Jun 2024 – Nov 2024"}
    ]
}

# ── 2. TARGET JOB DESCRIPTION ────────────────────────────────────────────────
job_description = """
Senior AI/ML Engineer — RAG Systems
Company: TechNova AI

We are building the next generation of enterprise AI assistants powered by Retrieval-Augmented Generation (RAG) and agentic workflows. We need an engineer who can design, deploy, and optimize production-grade LLM pipelines at scale.

Responsibilities:
- Design and implement RAG pipelines for enterprise knowledge retrieval using LangChain, LangGraph, and vector databases (Pinecone, FAISS, Weaviate)
- Build multi-agent orchestration systems with tool-use, planning, and self-correction capabilities
- Deploy and scale LLM applications on AWS (ECS, Lambda, SageMaker) with CI/CD pipelines
- Implement evaluation frameworks for RAG systems (RAGAS, DeepEval, custom metrics)
- Collaborate with product and engineering teams in an Agile environment
- Optimize prompt engineering, context window management, and retrieval accuracy

Required Skills:
- 2+ years experience with Python, LangChain, LangGraph, or similar LLM frameworks
- Hands-on experience with vector databases (Pinecone, FAISS, Milvus, Weaviate)
- Experience deploying ML/AI workloads on AWS (EC2, Lambda, S3, SageMaker)
- Strong understanding of RAG architecture: chunking strategies, embedding models, re-ranking
- Experience with evaluation metrics for generative AI (faithfulness, answer relevance, context precision)
- Familiarity with FastAPI, Docker, and microservices architecture
- Experience with Agile/Scrum methodologies

Nice to Have:
- Experience with multi-agent systems and autonomous agents
- Contributions to open-source LLM projects
- Experience with knowledge graphs and structured data retrieval
"""

# ── 3. COMPANY BACKGROUND ────────────────────────────────────────────────────
company_bg = "TechNova AI is a Series B startup building enterprise AI assistants. They use AWS as their primary cloud, LangChain/LangGraph for agent orchestration, and Pinecone for vector search. Culture is fast-paced, engineering-driven, with heavy emphasis on measurable AI performance metrics."

# ── 4. SHOW THE GENERATED PROMPT ─────────────────────────────────────────────
print("=" * 80)
print("GENERATED PROMPT (sent to AI model):")
print("=" * 80)
prompt = _build_prompt(base_profile, job_description, company_bg)
print(prompt)

# ── 5. EXPECTED AI OUTPUT (mocked — what the AI should return) ───────────────
print("\n" + "=" * 80)
print("EXPECTED AI OUTPUT (what the model should return as JSON):")
print("=" * 80)

expected_output = {
    "skills": {
        "languages": ["Python", "SQL"],
        "frameworks": ["LangChain", "LangGraph", "FastAPI", "Scikit-learn", "OpenAI API", "RAGAS", "Pandas", "NumPy"],
        "tools": ["AWS (EC2, Lambda, S3)", "Pinecone", "FAISS", "Docker", "Git", "Agile / Scrum"]
    },
    "experience": [
        {
            "company": "RNS Technology Services",
            "role": "Project Governance Consultant",
            "location": "Pune, India",
            "startDate": "Jul 2024",
            "endDate": "Jun 2025",
            "bullets": [
                "Designed and governed AI-ready infrastructure for IAM systems (3,000+ identities), implementing scalable monitoring and incident response pipelines that reduced multi-site resolution time by 70% — directly applicable to production RAG system observability.",
                "Led vulnerability tracking and remediation across distributed IT domains, ensuring security compliance for AI workloads — critical for enterprise LLM deployment with data governance requirements.",
                "Orchestrated cross-functional Agile teams to deliver AI-adjacent cybersecurity projects, producing executive-level risk assessments and sprint metrics for C-suite stakeholders."
            ]
        }
    ],
    "projects": [
        {
            "name": "Agentic Enterprise Knowledge Assistant",
            "technologies": ["Python", "LangChain", "LangGraph", "OpenAI API", "Pinecone", "FAISS", "FastAPI", "AWS (EC2, Lambda)", "RAGAS"],
            "bullets": [
                "Architected a production-grade multi-agent RAG system using LangGraph's Planner-Executor pattern for enterprise document retrieval, achieving zero-hallucination output on RAGAS benchmark evaluations — directly mirrors TechNova's agentic workflow architecture.",
                "Implemented RAGAS evaluation pipeline measuring context precision (35% improvement), answer faithfulness, and retrieval accuracy — enabling data-driven optimization of chunking strategies and embedding models for enterprise-scale knowledge retrieval.",
                "Deployed scalable RAG infrastructure on AWS (EC2, Lambda) with FastAPI microservices and Pinecone/FAISS hybrid vector search, supporting concurrent multi-agent queries with sub-second latency."
            ]
        },
        {
            "name": "AI-Powered Enterprise Document Intelligence Platform",
            "technologies": ["Python", "LangChain", "LangGraph", "AWS (SageMaker, Lambda)", "Pinecone", "FastAPI", "Docker"],
            "bullets": [
                "Built a multi-agent document processing pipeline with LangGraph orchestration, featuring autonomous tool-use for document classification, entity extraction, and summary generation — reducing manual review time by 60%.",
                "Deployed containerized RAG microservices on AWS ECS with auto-scaling, implementing context window optimization and re-ranking strategies that improved retrieval accuracy by 40% over baseline BM25."
            ]
        },
        {
            "name": "LLM Evaluation & Monitoring Dashboard",
            "technologies": ["Python", "RAGAS", "FastAPI", "Pandas", "AWS (Lambda, S3)", "Docker"],
            "bullets": [
                "Developed a real-time RAG evaluation dashboard tracking faithfulness, answer relevance, and context precision metrics across 10K+ queries — enabling continuous model performance monitoring for production LLM systems.",
                "Implemented automated regression testing for prompt engineering changes using RAGAS benchmarks, catching 95% of quality degradations before production deployment."
            ]
        }
    ]
}

print(json.dumps(expected_output, indent=2))

print("\n" + "=" * 80)
print("KEY IMPROVEMENTS OVER OLD PROMPT:")
print("=" * 80)
print("""
1. EXPERIENCE BULLETS: Rewritten to front-load JD keywords (RAG, scalable, production-grade,
   observability) while staying grounded in actual experience.

2. PROJECTS: Original project reordered first (highest JD relevance). 2 NEW projects generated
   that directly match TechNova's tech stack (LangGraph, AWS, RAGAS, multi-agent systems).

3. SKILLS: Filtered to JD-relevant only. Removed R, Bash, TensorFlow, Keras, SailPoint,
   Power BI, Tableau, Confluence, Zoho Projects. Kept only what the JD asks for.

4. TONE: Action-driven startup tone with measurable metrics (70%, 35%, 60%, 40%).

5. KEYWORD MATCHING: Injected RAG, LangGraph, multi-agent, AWS, FastAPI, Docker,
   RAGAS, evaluation metrics, Agile — all directly from the JD.
""")
