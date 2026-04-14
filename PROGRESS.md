# Project Progress & Roadmap

## Completed Changes

### 1. Resume Layout & Formatting (resume_builder.py)

| # | Issue | Fix Applied |
|---|-------|-------------|
| 1 | Contact line overflow using ideographic space (`&#12288;`) | Replaced with thin ` | ` separator |
| 2 | `_two_col()` ignored `l_width` param, hardcoded 74/26 split | Fixed to use `l_width` parameter properly with `(l_width, 1.0 - l_width)` |
| 3 | Heavy solid navy section bars wasting ~16mm vertical space | Replaced with thin horizontal rules (Jake's Resume `\titlerule` style) |
| 4 | Bullet spacing too loose — manual `<bullet>` tags with 12pt leading | Replaced with `ListFlowable` for proper indent control, reduced leading to 11pt |
| 5 | Skills table with fragile 20/80 column split causing overflow | Replaced with inline styled text: `**Languages:** Python, SQL, Bash` |
| 6 | Project name and tech list on separate lines wasting space | Combined into single `_two_col` row with 55/45 split |
| 7 | Margins too wide (14mm sides, 12mm top/bottom) | Tightened to 12mm sides, 10mm top/bottom — gains ~8mm vertical space |
| 8 | No visual separator between experience entries | Added `_thin_rule()` between entries |
| 9 | Font sizes too large for single-page constraint | Name 20→18pt, job title 9.5→9pt, dates 8.5→8pt, bullets 8.5→8pt |
| 10 | Education spacer too large | Reduced from 3pt to 2pt |

### 2. Folder Structure Reorganization

| Before | After |
|--------|-------|
| `base_profile.yaml` (root) | `config/base_profile.yaml` |
| `sample_profile.yaml` (root) | `config/sample_profile.yaml` |
| `output_resume.pdf` (root) | `output/output_resume.pdf` |
| `test_output.pdf` (root) | `output/test_output.pdf` |
| `test_tailored.pdf` (root) | `output/test_tailored.pdf` |
| `output_resume.tex` (root) | `output/output_resume.tex` |
| `test_ai.py` (root) | `tests/test_ai.py` |
| `__pycache__/` (root) | Removed (stale) |

### 3. Application Updates (app.py)

- Added `BASE_PROFILE_PATH` constant pointing to `config/base_profile.yaml`
- Added `OUTPUT_DIR` constant pointing to `output/`
- Output PDF now saved to `output/tailored_resume.pdf` with auto-created directory
- Fixed log message from "Writing to LaTeX..." to "Writing to PDF..."

### 4. LaTeX Template Fix (templates/resume_template.tex)

- Converted all `<VAR>...</VAR>` placeholders to Jinja2 `{{ ... }}` syntax
- Converted all `<BLOCK>...</BLOCK>` to Jinja2 `{% for %}` / `{% endfor %}` syntax
- Template is now ready to be wired into a LaTeX-based PDF build pipeline (requires `pdflatex`/`xelatex`)

### 5. Single-Page Overflow Detection & Auto-Scaling (resume_builder.py)

- Added 3-tier font scaling system (normal → medium → small)
- After building PDF, checks page count using PyPDF2
- If content exceeds 1 page, automatically rebuilds with smaller fonts
- Falls back to smallest tier if all tiers overflow
- Refactored `build_resume_pdf()` to use `_build_story()` helper with injectable styles dict

### 6. Empty Section Handling (resume_builder.py)

- Education, Experience, Projects, Skills, and Certifications sections are now conditionally rendered
- Empty sections are completely skipped (no header, no whitespace)
- Minimal profiles (name only) generate valid single-page PDFs

### 7. Certifications Section Rendering (resume_builder.py)

- Added full certifications section rendering from `base_profile.yaml` data
- Format: **Certification Name** — Issuer (Date)
- Section only appears if certifications exist in profile

### 8. Long URL Truncation in Contact Line (resume_builder.py)

- Added `_truncate_url()` function with configurable max length (default 30 chars)
- Applied to LinkedIn, GitHub, and LeetCode URLs in contact line
- Truncated URLs show `...` suffix (e.g., `linkedin.com/in/very-long...`)

### 9. AI Engine Improvements (ai_engine.py)

- Added retry logic with exponential backoff (3 retries per model)
- Added model fallback chain: `gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-1.5-flash`
- Added `_validate_base_profile()` input validation (checks basics dict, name presence)
- Added `_build_prompt()` helper for cleaner prompt construction
- Added Pydantic validation on AI response before merging
- Graceful error handling: JSON parse errors, schema validation errors, API failures
- All errors logged with model name and attempt number

### 10. App Enhancements (app.py)

- Added `/preview` endpoint for HTML resume preview without PDF generation
- Added file type validation (`.yaml`, `.yml` only)
- Added file size limit (2 MB max)
- Added request logging with timestamps, IP addresses, and response codes
- Added `after_request` hook for per-request logging
- Added structured error logging with elapsed time

### 11. HTML Preview Integration (templates/index.html)

- Added "Preview Resume (HTML)" button below the generate button
- Added modal overlay for resume preview with close button and backdrop click dismissal
- Preview fetches `/preview` endpoint and renders HTML inline
- Hero "Start Tailoring Now" button now scrolls to the form

### 12. Unit Tests

- **tests/test_resume_builder.py** — 30 tests covering:
  - URL truncation (short, long, default max)
  - PDF page count detection (valid PDF, invalid file)
  - Basic profile generation
  - Empty section handling (education, experience, projects, skills)
  - Certifications rendering
  - Minimal profile (name only)
  - Long bullets (280+ characters)
  - Many projects (5 projects with 8 technologies each)
  - Nested output directory creation
  - Integration with `config/base_profile.yaml`
  - Template selection (jakes, classic, modern, invalid)
  - Multi-page resume (2 pages with page headers)
  - Profile schema validation (8 tests)

- **tests/test_ai_engine.py** — 13 tests covering:
  - Input validation (missing basics, non-dict basics, missing name, empty name, valid profile)
  - Prompt building (company, JD, profile JSON presence)
  - Successful generation (mocked Gemini response)
  - Retry on error (verifies retry count across all fallback models)
  - Model fallback chain (verifies all models attempted)
  - Constants validation

**Total: 43 tests, all passing.**

### 13. Dependencies

- Added `PyPDF2` to `requirements.txt` for page count detection
- Added `reportlab` explicitly to `requirements.txt`

### 14. Multi-Page Support (resume_builder.py)

- Added `max_pages` parameter to `build_resume_pdf()` (default 1, supports 2)
- Created `_ResumeDocTemplate` custom document template for multi-page output
- Page 2+ includes compact header with name, contact info, thin rule, and page number
- Uses ReportLab `BaseDocTemplate` with `PageTemplate` for first/later page differentiation
- Overflow auto-scaling still applies before deciding to use 2 pages

### 15. Template Selection (resume_builder.py)

- Added 3 template styles via `template` parameter:
  - **`jakes`** (default): Thin horizontal rules under section headers, compact spacing — industry standard
  - **`classic`**: Plain black text, no accent colors, thicker rules, larger fonts — clean and minimal
  - **`modern`**: Solid navy accent bars with white text (original style) — bold and modern
- Refactored styles into `_make_styles(template, scale)` factory function
- Section headers adapt to template style via `_section_header(title, styles, template)`
- Added `VALID_TEMPLATES` constant for validation

### 16. Profile Schema Validation (profile_schema.py)

- Created `profile_schema.py` with `PROFILE_SCHEMA` dict and `validate_profile()` function
- Validates: basics (name required, email format), experience (company/role/bullets required), projects (name/technologies/bullets required), skills (categories must be lists)
- Returns list of human-readable error messages
- Integrated into `app.py` — rejects invalid profiles with 400 status and descriptive errors
- UI receives validation errors for display

### 17. UI Enhancements (templates/index.html)

- Added template style selector dropdown (Jake's Resume, Classic, Modern)
- Added page count selector (Single Page, Up to 2 Pages)
- Added dynamic template description that updates on selection change
- Form now sends `template` and `max_pages` fields to `/api/generate`
- Template descriptions:
  - Jake's: "Thin rules, compact spacing — industry standard"
  - Classic: "Plain text, no accent colors — clean and simple"
  - Modern: "Solid accent bars with white text — bold and modern"

### 18. Resume Analytics — ATS Score Estimation (ats_analytics.py)

- Created `ats_analytics.py` with `analyze_ats_score()` function
- Extracts keywords from both JD and profile using stop-word filtering and tech pattern detection
- Computes weighted overall score (0-100): keyword match (35%), experience (30%), skills (20%), projects (15%)
- Returns per-section scores, matched/missing keywords, strengths, and actionable suggestions
- Integrated into the analytics pipeline for pre-generation assessment

### 19. pypdf Migration (resume_builder.py)

- Replaced deprecated `PyPDF2` with `pypdf` library
- Updated `requirements.txt` — removed `PyPDF2`, added `pypdf`
- Updated `tests/test_resume_builder.py` import from `PyPDF2` to `pypdf`
- All 63 tests pass with new library

### 20. Awards & Publications Section (resume_builder.py)

- Added `awards` section support: title, organization, date, optional description
- Added `publications` section support: title, venue, date
- Both sections are conditionally rendered (only if data exists)
- Awards with descriptions render as bold title + description bullet
- Publications render as bold title, italic venue, and date
- Works across all 3 template styles (jakes, classic, modern)

### 21. Extended Test Suite

- Added `tests/test_ats_analytics.py` — 20 tests covering:
  - Keyword extraction (basic, stop-word filtering, short words, case insensitivity)
  - Tech keyword detection (AWS, API, CI/CD, capitalized terms)
  - ATS score structure, range, high/low match profiles
  - Keyword match tracking, section scores, suggestions, strengths
  - Empty JD handling
  - Awards and publications PDF rendering

### 22. User Accounts & Session Management (database.py)

- Created `database.py` with SQLite-backed user management:
  - **Users**: email/password (SHA-256 + salt), name, timestamps
  - **Sessions**: secure random tokens, 72-hour TTL, auto-refresh on validation
  - **Profiles**: per-user profile storage with JSON data, default flag
  - **Resumes**: generation history with company, JD, template, ATS score, PDF path
- Password hashing with per-user salt via `_hash_password()`
- `init_db()` creates all tables and indexes on startup
- Full CRUD: `create_user`, `authenticate_user`, `create_session`, `validate_session`, `delete_session`
- Profile CRUD: `save_profile`, `get_profiles`, `get_profile`, `delete_profile`
- Resume tracking: `save_resume`, `get_resumes`, `get_resume`
- Foreign key constraints and indexes for performance

### 23. Authenticated Web App (app.py)

- Added `/login` and `/register` routes with form-based auth
- Added `/dashboard` route showing saved profiles and resume history
- Added `/logout` route (cookie deletion + session invalidation)
- Session stored in `session_token` httpOnly cookie
- `generate` endpoint now saves resume records with ATS score to DB
- Profile selection via `profile_id` form field
- `dashboard.html` shows profile cards, resume history table with ATS score badges

### 24. Export Formats (export_formats.py)

- **DOCX**: `export_to_docx()` — formatted Word document with name header, contact line, sections, bullets
- **Plain Text**: `export_to_text()` — ASCII-formatted resume with `=`/`-` section dividers
- **Markdown**: `export_to_markdown()` — full Markdown with headers, bold, italic, links
- All three support every section: education, experience, projects, skills, certifications, awards, publications
- Added `/api/export/<format>` endpoint (docx, txt, md)
- Dashboard has DOCX/TXT/MD export buttons per resume record

### 25. Test Suite Expansion

- Added `tests/test_database.py` — 13 tests covering user CRUD, session lifecycle, profile CRUD, resume tracking, password hashing
- Added `tests/test_export_formats.py` — 3 tests covering DOCX, TXT, MD export creation and content verification
- **Total: 79 tests, all passing.**

### 26. AI Engine: Multi-Backend + Streaming + google.genai Migration

- Migrated from deprecated `google.generativeai` to `google.genai` SDK
  - Uses `genai.Client(api_key)` instead of `genai.configure()` + `GenerativeModel`
  - Uses `types.GenerateContentConfig(response_mime_type, response_schema)` for structured output
  - Uses `generate_content_stream()` for streaming responses
- Added **OpenAI backend** with `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo` model fallback
  - Uses `response_format={"type": "json_schema"}` for structured output
  - Supports streaming via `stream=True`
- Added **Anthropic Claude backend** with `claude-sonnet-4`, `claude-3-5-sonnet` model fallback
  - Uses tool calling for structured JSON output
  - Supports streaming via `client.messages.stream()`
- Added `generate_tailored_profile_stream()` generator function for real-time chunk streaming
- All three backends share: retry logic (3 attempts), model fallback chain, Pydantic validation
- Environment variables: `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- Backend selected via `backend` parameter: `'gemini'` (default), `'openai'`, `'anthropic'`
- Updated requirements.txt: replaced `google-generativeai` with `google-genai`, added `openai`, `anthropic`
- Updated tests: 24 new/updated tests covering all 3 backends + streaming + constants
- **Total: 90 tests, all passing.**

---

## Goals Ahead

### Long-Term (Remaining)

1. **CI/CD** — Add automated tests, linting, and deployment pipeline.

---

## Pending Code Changes

### app.py
- [ ] Add rate limiting to prevent abuse
- [ ] Add CORS headers if frontend is separated
- [ ] Add streaming generation progress to UI

### config/
- [ ] Add more sample profiles for different industries (SWE, Data Science, PM, etc.)

---

## Architecture Overview

```
User Input (Web UI)
    │
    ├── API Key + Company + JD + Optional Profile Upload
    ├── Template Selector (jakes/classic/modern)
    └── Page Count (1 or 2 pages)
    │
    ▼
app.py (Flask)
    │
    ├── /login, /register, /logout ──► database.py (SQLite)
    │                                     │
    │                                     ├── Users (email, hashed password, salt)
    │                                     ├── Sessions (token, TTL, auto-refresh)
    │                                     ├── Profiles (per-user, JSON data)
    │                                     └── Resumes (history, ATS score, PDF path)
    │
    ├── /dashboard ──► dashboard.html (profiles + resume history)
    │
    ├── /api/generate ──► profile_schema.validate_profile() ──► reject or proceed
    │                      │
    │                      ▼
    │                   ai_engine.py ──► Multi-Backend AI
    │                      │
    │                      ├── Gemini (google.genai) — gemini-2.5-flash, 2.0-flash, 1.5-flash
    │                      ├── OpenAI — gpt-4o, gpt-4o-mini, gpt-4-turbo
    │                      └── Anthropic — claude-sonnet-4, claude-3-5-sonnet
    │                      │
    │                      ├── Retry logic (3 attempts per model)
    │                      ├── Model fallback chain per backend
    │                      ├── Streaming responses (generate_tailored_profile_stream)
    │                      ├── Structured JSON output (Pydantic schema)
    │                      └── Input validation
    │                      │
    │                      ▼
    │                   ats_analytics.py ──► ATS Score + Suggestions
    │                      │
    │                      ├── Keyword extraction & matching
    │                      ├── Weighted scoring (35/30/20/15)
    │                      └── Actionable improvement tips
    │                      │
    │                      ▼
    │                   resume_builder.py ──► ReportLab ──► PDF Output
    │                                           │
    │                                           ├── Template style (jakes/classic/modern)
    │                                           ├── Multi-page support (page headers)
    │                                           ├── Empty section detection
    │                                           ├── Overflow auto-scaling (3 tiers)
    │                                           ├── URL truncation
    │                                           ├── Certifications rendering
    │                                           ├── Awards & Honors rendering
    │                                           └── Publications rendering
    │                                           │
    │                                           ▼
    │                                   output/tailored_resume.pdf
    │
    ├── /api/export/<format> ──► export_formats.py
    │                               ├── DOCX (python-docx)
    │                               ├── TXT (plain text)
    │                               └── MD (Markdown)
    │
    ├── /preview ──► resume_template.html (Jinja2)
    │
    └── after_request ──► Per-request logging
```
