# ATS Resume Rewriter

A complete, production-ready web application that helps job seekers optimize their resumes for Applicant Tracking Systems (ATS) using AI-powered analysis and rewriting.

## Overview

The ATS Resume Rewriter analyzes your resume against a job description, provides weighted ATS scores, rewrites your resume to better match the job requirements using Google's Gemini AI, and generates a professional PDF output.

## Tech Stack

- **Frontend**: React + Vite (deployed on Vercel)
- **Backend**: FastAPI (Python) (deployed on Render, Dockerized)
- **AI**: Google Gemini 1.5 Flash API (free tier)
- **Database**: SQLite + SQLAlchemy
- **PDF Generation**: Tectonic (LaTeX engine) + Jinja2
- **Authentication**: JWT + bcrypt

## Features

- User registration and login with JWT authentication
- Resume analysis with weighted ATS scoring (Summary, Education, Projects, Internship, Skills, Certifications)
- AI-powered resume rewriting using Google Gemini 1.5 Flash
- Section-by-section resume preview before and after rewriting
- Professional PDF generation using LaTeX and Tectonic
- History tracking of all resume optimization sessions
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
│   │   ├── ats_scorer.py       # ATS scoring logic
│   │   ├── gemini.py           # Gemini AI integration
│   │   ├── key_manager.py      # API key management
│   │   ├── latex_escape.py     # LaTeX text escaping
│   │   ├── pdf_extractor.py    # PDF text extraction
│   │   └── pdf_generator.py    # PDF generation service
│   └── templates/              # Jinja2 templates
│       ├── resume.tex.j2       # LaTeX resume template
│       └── warmup.tex          # LaTeX warmup file
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

3. Create a `.env` file in the backend directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   JWT_SECRET=your_secret_key_here
   DATABASE_URL=sqlite:///./resume_rewriter.db
   ```

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
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET=your_secret_key_here
DATABASE_URL=sqlite:///./resume_rewriter.db
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
   - `GEMINI_API_KEY` (from your Google AI Studio)
   - `JWT_SECRET` (a strong random string)
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
│   Local Storage │    │   Database       │    │   LaTeX Engine   │
│   (JWT Token)   │    │   (SQLite)       │◄──►│   (Tectonic)     │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and receive JWT token

### Resume Operations
- `POST /resume/analyze` - Analyze resume against job description
- `POST /resume/rewrite` - Rewrite resume using AI
- `POST /resume/export/{session_id}` - Export resume as PDF

### History
- `GET /history` - Get all sessions for current user
- `GET /history/{session_id}` - Get specific session details
- `POST /history/{session_id}/export` - Re-export PDF for past session

## How It Works

1. **User Authentication**: Users register and log in to access the application
2. **Resume Analysis**: 
   - User pastes resume text and job description
   - System extracts keywords from job description (weighted by importance)
   - Resume is split into sections and scored based on keyword matches
   - Overall and section scores are returned (0-100 scale)
3. **Resume Rewriting**:
   - Original resume is parsed into structured JSON using Gemini AI
   - Each section is rewritten to better match the job description while preserving facts
   - Keywords from job description are naturally injected
   - Rewritten resume is scored again for comparison
4. **PDF Generation**:
   - Rewritten resume JSON is passed to a Jinja2 LaTeX template
   - All text is properly escaped for LaTeX
   - Template is compiled to PDF using Tectonic
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
- Tectonic for modern LaTeX engine
- FastAPI for high-performance Python backend
- React and Vite for modern frontend development