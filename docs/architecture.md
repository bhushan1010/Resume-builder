# Resume Builder System Architecture

This system allows job seekers to rewrite their resumes using AI to match job descriptions.

## Components

- **Authentication (auth.py)**: Handles user signup, login, and JWT generation.
- **Database (database.py)**: Manages SQLite/PostgreSQL connection pool and schema definitions.
- **Rewriting Engine (gemini.py)**: Calls Gemini, Ollama, or OpenRouter for section-by-section rewriting.
- **PDF Extraction (pdf_extractor.py)**: Extracts text from uploaded PDF resumes.
- **ATS Scorer (ats_scorer.py)**: Scores the rewritten resume against a job description.

## Rationale
We chose a section-by-section rewriting approach rather than rewriting the whole resume at once to avoid hallucinating facts and to keep layout structures intact.
