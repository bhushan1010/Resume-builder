# ATS Pro — AI Resume Engine

AI-powered resume tailoring engine that customizes your base profile to match any job description. Generates professional, ATS-friendly PDFs in multiple template styles with a modern web interface.

## Features

- **AI-Powered Tailoring** — Uses Google Gemini to rewrite experience bullets, filter skills, and generate JD-relevant projects
- **ATS Score Analytics** — Real-time scoring with keyword matching and actionable improvement suggestions
- **Multi-Template Export** — Classic, Modern, and Jake's templates in PDF, DOCX, TXT, and Markdown
- **User Accounts** — Registration, login, session management, and resume history
- **Profile Management** — Save, edit, and switch between multiple professional profiles
- **Modern Landing Page** — Animated landing page with anime.js, particle backgrounds, and scroll reveals
- **Multi-Language Support** — Generate resumes in English, German, French, and more

## Project Structure

```
Resume-builder/
├── app.py                        # Flask web application (entry point)
├── app/                          # Application package
│   ├── __init__.py               # Package exports
│   ├── ai_engine.py              # Gemini AI integration & profile tailoring
│   ├── resume_builder.py         # ReportLab PDF generator
│   ├── database.py               # SQLite user/profile/resume storage
│   ├── profile_schema.py         # Profile validation
│   ├── export_formats.py         # DOCX, TXT, Markdown export
│   └── ats_analytics.py          # ATS scoring & keyword analysis
├── config/
│   ├── base_profile.yaml         # Default user profile (edit this!)
│   └── sample_profile.yaml       # Example profile for reference
├── data/                         # SQLite database (app.db)
├── output/                       # Generated files land here
├── static/                       # Static assets
│   ├── css/                      # Stylesheets
│   ├── js/                       # JavaScript files
│   └── images/                   # Images
├── templates/
│   ├── index.html                # Main web UI
│   ├── landing.html              # Animated landing page
│   ├── dashboard.html            # User dashboard
│   ├── login.html                # Login page
│   ├── register.html             # Registration page
│   └── resume_template.html      # HTML resume preview
├── tests/
│   ├── test_ai_engine.py         # AI engine tests
│   ├── test_database.py          # Database tests
│   ├── test_resume_builder.py    # PDF generator tests
│   ├── test_export_formats.py    # Export format tests
│   └── test_ats_analytics.py     # ATS analytics tests
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
├── .env.example                  # Environment variable template
└── PROGRESS.md                   # Changelog, roadmap, and pending tasks
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Configure Your Profile

Edit `config/base_profile.yaml` with your personal information, education, skills, experience, and projects. This is your single source of truth.

### 4. Run the Application

```bash
python app.py
```

The app starts at `http://localhost:8501`.

### 5. Generate a Resume

1. Open `http://localhost:8501` in your browser
2. Enter your **Google Gemini API key**
3. Enter the **target company name**
4. Paste the **job description**
5. (Optional) Upload a custom YAML profile
6. Click **Generate** — your tailored PDF downloads automatically

## How It Works

```
Your Base Profile (YAML)
        │
        │  +  Job Description + Company Name
        ▼
┌─────────────────────────┐
│   app/ai_engine.py      │
│   Google Gemini API     │
│                         │
│   • Selects relevant    │
│     experiences         │
│   • Rewrites bullets    │
│     with ATS keywords   │
│   • Filters skills      │
│   • Generates new       │
│     JD-relevant projects│
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   app/resume_builder.py │
│   ReportLab PDF Engine  │
│                         │
│   • A4 single-page      │
│   • Multiple templates  │
│   • Thin section rules  │
│   • Compact spacing     │
└───────────┬─────────────┘
            │
            ▼
    tailored_resume.pdf
```

## Configuration

### Profile Schema (`config/base_profile.yaml`)

```yaml
basics:
  name: "Your Name"
  email: "your@email.com"
  phone: "+1 234 567 890"
  linkedin: "linkedin.com/in/yourprofile"   # No https://
  github: "github.com/yourusername"          # No https://
  leetcode: "leetcode.com/yourusername"      # No https://

education:
  - institution: "University Name"
    location: "City, Country"
    degree: "B.S. in Computer Science"
    startDate: "2020"
    endDate: "2024"

skills:
  languages: ["Python", "JavaScript", "SQL"]
  frameworks: ["React", "FastAPI", "TensorFlow"]
  tools: ["Git", "Docker", "AWS", "PostgreSQL"]

experience:
  - company: "Company Name"
    role: "Software Engineer"
    location: "City, Country"
    startDate: "Jan 2023"
    endDate: "Present"
    bullets:
      - "Built a feature that improved X by Y%."
      - "Led a team of Z engineers to deliver..."

projects:
  - name: "Project Name"
    technologies: ["Python", "FastAPI", "Docker"]
    bullets:
      - "Description of what you built and its impact."
```

## API Endpoints

### Public Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Main web UI |
| GET/POST | `/login` | User login |
| GET/POST | `/register` | User registration |
| GET | `/logout` | User logout |
| POST | `/preview` | HTML resume preview |
| POST | `/api/generate` | Generate tailored PDF |

### Authenticated Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard` | User dashboard |
| GET | `/api/profiles` | List profiles |
| POST | `/api/profiles` | Save profile |
| GET | `/api/profiles/<id>` | Get profile |
| DELETE | `/api/profiles/<id>` | Delete profile |
| GET | `/api/resumes` | List resumes |
| POST | `/api/export/<format>` | Export (docx, txt, md) |

### `POST /api/generate`

Generates a tailored resume PDF.

**Form Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `api_key` | string | Yes | Google Gemini API key |
| `company` | string | Yes | Target company name |
| `jd` | string | Yes | Full job description text |
| `template` | string | No | Template style (classic, modern, jakes) |
| `max_pages` | int | No | Page count (1 or 2, default 1) |
| `profile` | file | No | Custom YAML profile |
| `profile_id` | int | No | Saved profile ID |

**Response:** Downloads `tailored_resume.pdf`

## Running Tests

```bash
python -m pytest tests/ -v
```

## Tech Stack

- **Backend:** Flask (Python)
- **AI:** Google Gemini 2.5 Flash (structured JSON output)
- **PDF Engine:** ReportLab (Platypus)
- **Database:** SQLite
- **Frontend:** HTML + CSS + JavaScript (Jinja2 templates)
- **Animations:** anime.js v4

## License

MIT
