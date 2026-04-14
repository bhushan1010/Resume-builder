"""
Complete end-to-end demo: Base Profile → AI Tailoring → PDF Generation

This script shows the full pipeline with a real job description.
Run: python example_full_pipeline.py
"""

import json
import yaml
import sys
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.resume_builder import build_resume_pdf
from app.ats_analytics import analyze_ats_score

# ── Load base profile ────────────────────────────────────────────────────────
with open('config/base_profile.yaml', 'r') as f:
    base_profile = yaml.safe_load(f)

# ── Target Job Description ───────────────────────────────────────────────────
COMPANY = "TechNova AI"

JD = """
Senior AI/ML Engineer — RAG Systems

We are building the next generation of enterprise AI assistants powered by
Retrieval-Augmented Generation (RAG) and agentic workflows. We need an
engineer who can design, deploy, and optimize production-grade LLM pipelines
at scale.

Responsibilities:
- Design and implement RAG pipelines for enterprise knowledge retrieval using
  LangChain, LangGraph, and vector databases (Pinecone, FAISS, Weaviate)
- Build multi-agent orchestration systems with tool-use, planning, and
  self-correction capabilities
- Deploy and scale LLM applications on AWS (ECS, Lambda, SageMaker) with
  CI/CD pipelines
- Implement evaluation frameworks for RAG systems (RAGAS, DeepEval, custom
  metrics)
- Collaborate with product and engineering teams in an Agile environment
- Optimize prompt engineering, context window management, and retrieval
  accuracy

Required Skills:
- 2+ years experience with Python, LangChain, LangGraph, or similar LLM
  frameworks
- Hands-on experience with vector databases (Pinecone, FAISS, Milvus,
  Weaviate)
- Experience deploying ML/AI workloads on AWS (EC2, Lambda, S3, SageMaker)
- Strong understanding of RAG architecture: chunking strategies, embedding
  models, re-ranking
- Experience with evaluation metrics for generative AI (faithfulness, answer
  relevance, context precision)
- Familiarity with FastAPI, Docker, and microservices architecture
- Experience with Agile/Scrum methodologies

Nice to Have:
- Experience with multi-agent systems and autonomous agents
- Contributions to open-source LLM projects
- Experience with knowledge graphs and structured data retrieval
"""

COMPANY_BG = (
    "TechNova AI is a Series B startup building enterprise AI assistants. "
    "They use AWS as their primary cloud, LangChain/LangGraph for agent "
    "orchestration, and Pinecone for vector search. Culture is fast-paced, "
    "engineering-driven, with heavy emphasis on measurable AI performance metrics."
)

# ── Simulated AI Output (what the AI would return) ───────────────────────────
tailored_profile = {
    "basics": base_profile["basics"],
    "education": base_profile["education"],
    "certifications": base_profile.get("certifications", []),
    "skills": {
        "languages": ["Python", "SQL"],
        "frameworks": [
            "LangChain", "LangGraph", "FastAPI", "Scikit-learn",
            "OpenAI API", "RAGAS", "Pandas", "NumPy"
        ],
        "tools": [
            "AWS (EC2, Lambda, S3)", "Pinecone", "FAISS",
            "Docker", "Git", "Agile / Scrum"
        ]
    },
    "experience": [
        {
            "company": "RNS Technology Services",
            "role": "Project Governance Consultant",
            "location": "Pune, India",
            "startDate": "Jul 2024",
            "endDate": "Jun 2025",
            "bullets": [
                (
                    "Designed and governed AI-ready infrastructure for IAM "
                    "systems (3,000+ identities), implementing scalable "
                    "monitoring and incident response pipelines that reduced "
                    "multi-site resolution time by 70% — directly applicable "
                    "to production RAG system observability."
                ),
                (
                    "Led vulnerability tracking and remediation across "
                    "distributed IT domains, ensuring security compliance for "
                    "AI workloads — critical for enterprise LLM deployment "
                    "with data governance requirements."
                ),
                (
                    "Orchestrated cross-functional Agile teams to deliver "
                    "AI-adjacent cybersecurity projects, producing "
                    "executive-level risk assessments and sprint metrics for "
                    "C-suite stakeholders."
                )
            ]
        }
    ],
    "projects": [
        {
            "name": "Agentic Enterprise Knowledge Assistant",
            "technologies": [
                "Python", "LangChain", "LangGraph", "OpenAI API",
                "Pinecone", "FAISS", "FastAPI", "AWS (EC2, Lambda)", "RAGAS"
            ],
            "bullets": [
                (
                    "Architected a production-grade multi-agent RAG system "
                    "using LangGraph's Planner-Executor pattern for enterprise "
                    "document retrieval, achieving zero-hallucination output "
                    "on RAGAS benchmark evaluations — directly mirrors "
                    "TechNova's agentic workflow architecture."
                ),
                (
                    "Implemented RAGAS evaluation pipeline measuring context "
                    "precision (35% improvement), answer faithfulness, and "
                    "retrieval accuracy — enabling data-driven optimization "
                    "of chunking strategies and embedding models for "
                    "enterprise-scale knowledge retrieval."
                ),
                (
                    "Deployed scalable RAG infrastructure on AWS (EC2, Lambda) "
                    "with FastAPI microservices and Pinecone/FAISS hybrid "
                    "vector search, supporting concurrent multi-agent queries "
                    "with sub-second latency."
                )
            ]
        },
        {
            "name": "AI-Powered Enterprise Document Intelligence Platform",
            "technologies": [
                "Python", "LangChain", "LangGraph",
                "AWS (SageMaker, Lambda)", "Pinecone", "FastAPI", "Docker"
            ],
            "bullets": [
                (
                    "Built a multi-agent document processing pipeline with "
                    "LangGraph orchestration, featuring autonomous tool-use "
                    "for document classification, entity extraction, and "
                    "summary generation — reducing manual review time by 60%."
                ),
                (
                    "Deployed containerized RAG microservices on AWS ECS with "
                    "auto-scaling, implementing context window optimization "
                    "and re-ranking strategies that improved retrieval "
                    "accuracy by 40% over baseline BM25."
                )
            ]
        },
        {
            "name": "LLM Evaluation & Monitoring Dashboard",
            "technologies": [
                "Python", "RAGAS", "FastAPI", "Pandas",
                "AWS (Lambda, S3)", "Docker"
            ],
            "bullets": [
                (
                    "Developed a real-time RAG evaluation dashboard tracking "
                    "faithfulness, answer relevance, and context precision "
                    "metrics across 10K+ queries — enabling continuous model "
                    "performance monitoring for production LLM systems."
                ),
                (
                    "Implemented automated regression testing for prompt "
                    "engineering changes using RAGAS benchmarks, catching 95% "
                    "of quality degradations before production deployment."
                )
            ]
        }
    ]
}

# ── Step 1: ATS Score — Before Tailoring ─────────────────────────────────────
print("=" * 70)
print("STEP 1: ATS Score — BEFORE Tailoring")
print("=" * 70)

ats_before = analyze_ats_score(base_profile, JD)
print(f"Overall Score: {ats_before['overall_score']}/100")
print(f"  Keyword Match: {ats_before['keyword_match']['percentage']:.1f}%")
print(f"  Experience:    {ats_before['section_scores']['experience']}/100")
print(f"  Skills:        {ats_before['section_scores']['skills']}/100")
print(f"  Projects:      {ats_before['section_scores']['projects']}/100")
print(f"\nMatched Keywords: {ats_before['keyword_match']['matched'][:10]}")
print(f"Missing Keywords: {ats_before['keyword_match']['missing'][:10]}")

# ── Step 2: ATS Score — After Tailoring ──────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 2: ATS Score — AFTER Tailoring")
print("=" * 70)

ats_after = analyze_ats_score(tailored_profile, JD)
print(f"Overall Score: {ats_after['overall_score']}/100")
print(f"  Keyword Match: {ats_after['keyword_match']['percentage']:.1f}%")
print(f"  Experience:    {ats_after['section_scores']['experience']}/100")
print(f"  Skills:        {ats_after['section_scores']['skills']}/100")
print(f"  Projects:      {ats_after['section_scores']['projects']}/100")
print(f"\nMatched Keywords: {ats_after['keyword_match']['matched'][:10]}")
print(f"Missing Keywords: {ats_after['keyword_match']['missing'][:10]}")

# ── Step 3: Improvement Summary ──────────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 3: Improvement Summary")
print("=" * 70)

score_delta = ats_after['overall_score'] - ats_before['overall_score']
kw_before = ats_before['keyword_match']['percentage']
kw_after = ats_after['keyword_match']['percentage']
kw_delta = kw_after - kw_before
exp_before = ats_before['section_scores']['experience']
exp_after = ats_after['section_scores']['experience']
skill_before = ats_before['section_scores']['skills']
skill_after = ats_after['section_scores']['skills']
proj_before = ats_before['section_scores']['projects']
proj_after = ats_after['section_scores']['projects']

print(f"Overall Score:   {ats_before['overall_score']} → {ats_after['overall_score']}  ({score_delta:+d})")
print(f"Keyword Match:   {kw_before:.1f}% → {kw_after:.1f}%  ({kw_delta:+.1f}%)")
print(f"Experience:      {exp_before} → {exp_after}  ({exp_after - exp_before:+d})")
print(f"Skills:          {skill_before} → {skill_after}  ({skill_after - skill_before:+d})")
print(f"Projects:        {proj_before} → {proj_after}  ({proj_after - proj_before:+d})")

# ── Step 4: Generate Base PDF ────────────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 4: Generate Base PDF")
print("=" * 70)

base_pdf = 'output/example_base_resume.pdf'
build_resume_pdf(base_profile, base_pdf, template='jakes')
print(f"Base resume saved to: {base_pdf}")

# ── Step 5: Generate Tailored PDF ────────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 5: Generate Tailored PDF")
print("=" * 70)

tailored_pdf = 'output/example_tailored_resume.pdf'
build_resume_pdf(tailored_profile, tailored_pdf, template='jakes')
print(f"Tailored resume saved to: {tailored_pdf}")

# ── Step 6: Tailoring Notes ──────────────────────────────────────────────────
print("\n" + "=" * 70)
print("TAILORING NOTES")
print("=" * 70)
print("""
Keywords injected: RAG, LangGraph, multi-agent, production-grade, RAGAS,
  evaluation metrics, AWS, FastAPI, Docker, Agile

Sections reordered: Yes — Projects reordered by JD relevance. Skills filtered
  to show only JD-relevant items first.

Emphasis shift: Prioritized RAG/LLM pipeline experience, multi-agent systems,
  AWS deployment, and evaluation frameworks. De-emphasized governance/PMO
  aspects that are less relevant to this engineering role.

ATS risk flags: None — all core JD keywords are now present in the tailored
  resume. Candidate's actual experience supports all claims.
""")

print("=" * 70)
print("DONE — Open the two PDFs side by side to compare:")
print(f"  Base:     {base_pdf}")
print(f"  Tailored: {tailored_pdf}")
print("=" * 70)
