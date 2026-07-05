# ATS Resume Rewriter

A complete, production-ready web application that helps job seekers optimize their resumes for Applicant Tracking Systems (ATS) using AI-powered analysis and rewriting.

## Overview

The ATS Resume Rewriter analyzes your resume against a job description, provides weighted ATS scores, rewrites your resume to better match the job requirements using an AI model (Google Gemini by default, with OpenRouter and local Ollama also supported), and generates a professional PDF output.

## Tech Stack

- **Frontend**: React + Vite (deployed on Vercel)
- **Backend**: FastAPI (Python) (deployed on Render, Dockerized)
- **AI**: Multi-provider LLM routing — Google Gemini (default, with API-key rotation), OpenRouter, or local Ollama
- **ATS Scoring**: sentence-transformers (`all-MiniLM-L6-v2`) semantic similarity + weighted keyword matching
- **Database**: SQLite + SQLAlchemy (Postgres-ready via `DATABASE_URL`)
- **PDF Generation**: Jinja2 HTML template + wkhtmltopdf (via `pdfkit`)
- **Authentication**: JWT + pbkdf2_sha256 password hashing

## Features

- User registration and login with JWT authentication
- Resume analysis with weighted ATS scoring (Summary, Education, Projects, Internship, Skills, Certifications), combining semantic similarity and keyword matching
- AI-powered resume rewriting with **multi-provider LLM routing** — Google Gemini (default), OpenRouter, or a local Ollama model
- Resilient Gemini **API-key rotation** that handles per-minute rate limits, daily-quota exhaustion, and permanently suspended/invalid keys (dead keys are skipped automatically)
- Optional per-request **personal Gemini key** (sent via the `X-Personal-Gemini-Key` header) to bypass shared-key limits
- Fact-locking during rewrites (URLs, dates, numbers, names are preserved verbatim) plus keyword-coverage retries
- Upload a **PDF resume** and have its text extracted automatically (PyMuPDF)
- Section-by-section resume preview before and after rewriting
- Professional PDF generation from an HTML template using wkhtmltopdf
- History tracking with paginated listing, detail view, re-export, and deletion (GDPR-friendly)
- Feedback loop: session ratings feed an industry-aware prompt learner that adapts future rewrites
- Responsive design for mobile and desktop

## Project Structure

```
resume-builder/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # Database configuration
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Docker configuration
│   ├── .env                    # Environment variables
│   ├── resume_rewriter.db      # SQLite database
│   ├── models/                 # SQLAlchemy models
│   │   ├── user.py             # User model
│   │   └── session.py          # Session model
│   ├── routes/                 # API route handlers
│   │   ├── auth.py             # Authentication routes
│   │   ├── resume.py           # Resume processing routes
│   │   ├── history.py          # History routes
│   │   └── status.py           # Health check routes
│   ├── services/               # Business logic services
│   │   ├── ats_scorer.py       # Semantic + keyword ATS scoring
│   │   ├── gemini.py           # Multi-provider LLM routing (Gemini/Ollama/OpenRouter)
│   │   ├── key_manager.py      # Gemini API key rotation (rate-limit / suspended-key aware)
│   │   ├── pattern_learner.py  # Industry detection + feedback-driven prompt adaptation
│   │   ├── latex_escape.py     # Text escaping helpers
│   │   ├── pdf_extractor.py    # PDF text extraction (PyMuPDF)
│   │   └── pdf_generator.py    # HTML→PDF generation (Jinja2 + wkhtmltopdf)
│   └── templates/              # Jinja2 templates
│       └── resume.html.j2      # HTML resume template (rendered to PDF)
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main React app with routing
│   │   ├── main.jsx            # React entry point
│   │   ├── index.css           # Global styles
│   │   ├── api/                # API service layer
│   │   │   └── client.js       # HTTP client configuration
│   │   ├── components/         # Reusable UI components
│   │   │   ├── Navbar.jsx      # Navigation bar
│   │   │   ├── ResumeInput.jsx # Resume input form
│   │   │   ├── RewrittenPreview.jsx # Rewritten resume preview
│   │   │   ├── ATSScoreCard.jsx # ATS score display
│   │   │   └── HistoryCard.jsx # History item card
│   │   └── pages/              # Page components
│   │       ├── Dashboard.jsx   # Main resume processing page
│   │       ├── History.jsx     # Session history page
│   │       ├── Login.jsx       # Login page
│   │       └── Register.jsx    # Registration page
│   ├── public/
│   │   └── index.html          # HTML template
│   ├── package.json            # Frontend dependencies
│   ├── vite.config.js          # Vite configuration
│   ├── vercel.json             # Vercel deployment config
│   └── .env                    # Frontend environment variables
└── README.md                   # This file
```

## Local Development Setup

### Prerequisites

- Node.js (v16+)
- Python (v3.11+)
- Git

### Backend Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd resume-builder
   ```

2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix/MacOS:
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the backend directory (see `backend/.env.example` for the
   full list, including OpenRouter/Ollama options):
   ```env
   # One or more rotating Gemini keys (GEMINI_KEY_1 .. GEMINI_KEY_N)
   GEMINI_KEY_1=your_gemini_api_key_here
   JWT_SECRET=at_least_32_characters_random_string
   DATABASE_URL=sqlite:///./resume_rewriter.db
   LLM_PROVIDER=gemini
   ```
   > **Note:** `JWT_SECRET` must be at least 32 characters or the backend refuses to start.
   > PDF export requires the `wkhtmltopdf` binary — set `WKHTMLTOPDF_PATH` if it isn't on
   > your PATH or in the bundled `wkhtmltox/bin/` folder.

4. Initialize the database:
   ```bash
   python -c "from database import Base, engine; import models; Base.metadata.create_all(bind=engine)"
   ```

5. Start the backend server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup

1. Set up the frontend:
   ```bash
   cd ../frontend
   npm install
   ```

2. Create a `.env` file in the frontend directory:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

3. Start the frontend development server:
   ```bash
   npm run dev
   ```

The application will be available at `http://localhost:5173`.

## Environment Variables

### Backend (.env)
```env
GEMINI_KEY_1=your_gemini_api_key_here   # add GEMINI_KEY_2, _3, ... for rotation
JWT_SECRET=at_least_32_characters_random_string
DATABASE_URL=sqlite:///./resume_rewriter.db
ALLOWED_ORIGINS=http://localhost:5173
LLM_PROVIDER=gemini                       # gemini | openrouter | ollama
# WKHTMLTOPDF_PATH=C:\path\to\wkhtmltopdf.exe   # only if not auto-detected
```

### Frontend (.env)
```env
VITE_API_URL=https://your-render-backend-url.onrender.com
```

## How to Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key and paste it into your backend `.env` file

## Deployment

### Backend Deployment (Render)

1. Push your code to a GitHub repository
2. In Render dashboard, click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - Environment: Docker
   - Build Command: (leave empty)
   - Start Command: (leave empty)
   - Dockerfile Path: `./backend/Dockerfile`
5. Add environment variables:
   - `GEMINI_KEY_1` (from Google AI Studio; add `GEMINI_KEY_2`, `_3`, ... for rotation)
   - `JWT_SECRET` (a strong random string, at least 32 characters)
   - `ALLOWED_ORIGINS` (your Vercel frontend URL)
6. Under "Advanced" → "Disk", add:
   - Name: `resume-data`
   - Mount Path: `/app/data`
   - Size: 1 GB
7. Click "Create Web Service"

### Frontend Deployment (Vercel)

1. Push your code to a GitHub repository
2. In Vercel dashboard, click "New Project"
3. Import your GitHub repository
4. Configure the project:
   - Framework: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. Add environment variables:
   - `VITE_API_URL` (your Render backend URL)
6. Click "Deploy"

## Architecture Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Frontend      │    │     Backend      │    │    Services      │
│   (React/Vite)  │◄──►│   (FastAPI)      │◄──►│ (Gemini, ATS,    │
│                 │    │                  │    │  PDF Generator)  │
└─────────────────┘    └──────────────────┘    └──────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   User Interface│    │   API Endpoints  │    │   Business Logic │
│                 │    │                  │    │                  │
└─────────────────┘    └──────────────────┘    └──────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   State Mgmt    │    │   Routing        │    │   AI Processing  │
│   (React Hooks) │    │                  │    │   (Gemini)       │
└─────────────────┘    └──────────────────┘    └──────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Components    │    │   Controllers    │    │   Scoring Engine │
│   (UI Elements) │    │                  │    │   (Keyword-based)│
└─────────────────┘    └──────────────────┘    └──────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Local Storage │    │   Database       │    │   HTML → PDF      │
│   (JWT Token)   │    │   (SQLite)       │◄──►│  (wkhtmltopdf)   │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user (returns a JWT)
- `POST /auth/login` - Login (OAuth2 form) and receive a JWT token
- `GET /auth/me` - Get the current authenticated user's profile

### Resume Operations
- `POST /resume/analyze` - Analyze a resume against a job description (ATS scores + keywords)
- `POST /resume/rewrite` - Rewrite the resume with AI and save a session
- `POST /resume/extract-pdf` - Extract text from an uploaded PDF resume (multipart upload, 5 MB max)
- `POST /resume/export/{session_id}` - Export a session's resume as PDF
- `POST /resume/feedback` - Submit a 1–5 rating for a session (feeds the prompt learner)

### History
- `GET /history` - List the current user's sessions (paginated: `limit`, `offset`)
- `GET /history/{session_id}` - Get full detail for a session
- `GET /history/{session_id}/export` - Re-export a past session's PDF (`?save=true` to persist)
- `DELETE /history/{session_id}` - Delete a session and its generated PDF

### Status
- `GET /health` - Public health check (DB + Gemini key availability)
- `GET /status` - Detailed per-key status (requires `X-Admin-Token` header)

## How It Works

1. **User Authentication**: Users register and log in to access the application
2. **Resume Analysis**: 
   - User pastes resume text and job description
   - System extracts keywords from job description (weighted by importance)
   - Resume is split into sections and scored based on keyword matches
   - Overall and section scores are returned (0-100 scale)
3. **Resume Rewriting**:
   - Original resume is parsed into structured JSON using the configured LLM provider
   - Facts are locked (URLs, dates, numbers, names) so they can't be altered or invented
   - Each section is rewritten to better match the job description while preserving facts
   - Keywords from the job description are naturally injected, with a retry pass if coverage is low
   - Each rewrite is re-scored and rolled back to the original if it would lower the score
   - Rewritten resume is scored again for comparison
4. **PDF Generation**:
   - Rewritten resume JSON is passed to a Jinja2 HTML template (`resume.html.j2`)
   - URLs and contact links are normalized; text is autoescaped by Jinja2
   - The rendered HTML is converted to PDF using wkhtmltopdf (via `pdfkit`)
   - PDF is returned for download
5. **History Tracking**: All sessions are saved to the database for future reference

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for powerful language model capabilities
- wkhtmltopdf for HTML-to-PDF rendering
- FastAPI for high-performance Python backend
- React and Vite for modern frontend development