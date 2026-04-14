import os
import yaml
import logging
import time
from flask import Flask, request, render_template, send_file, jsonify, redirect, url_for, make_response
from dotenv import load_dotenv
from app.ai_engine import generate_tailored_profile
from app.resume_builder import build_resume_pdf, VALID_TEMPLATES
from app.profile_schema import validate_profile
from app.database import init_db, create_user, authenticate_user, create_session, validate_session, delete_session
from app.database import save_profile, get_profiles, get_profile, delete_profile
from app.database import save_resume, get_resumes, get_resume
from app.export_formats import export_to_docx, export_to_text, export_to_markdown
from app.ats_analytics import analyze_ats_score

load_dotenv()

# Configure request logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

BASE_PROFILE_PATH = os.path.join("config", "base_profile.yaml")
OUTPUT_DIR = "output"
MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2 MB
ALLOWED_EXTENSIONS = {'.yaml', '.yml'}

# Initialize database on startup
init_db()


def _allowed_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def _get_current_user():
    """Get current user from session cookie."""
    token = request.cookies.get('session_token')
    if not token:
        return None
    return validate_session(token)


# ── Public Routes ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    user = _get_current_user()
    return render_template('index.html', templates=VALID_TEMPLATES, user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = authenticate_user(email, password)
        if user:
            token = create_session(user['id'])
            resp = make_response(redirect(url_for('dashboard')))
            resp.set_cookie('session_token', token, httponly=True, samesite='Lax', max_age=72*3600)
            return resp
        return render_template('login.html', error='Invalid email or password')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not name or not email or not password:
            return render_template('register.html', error='All fields are required.')
        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters.')
        try:
            user = create_user(email, password, name)
            token = create_session(user['id'])
            resp = make_response(redirect(url_for('dashboard')))
            resp.set_cookie('session_token', token, httponly=True, samesite='Lax', max_age=72*3600)
            return resp
        except ValueError as e:
            return render_template('register.html', error=str(e))
    return render_template('register.html')


@app.route('/logout')
def logout():
    token = request.cookies.get('session_token')
    if token:
        delete_session(token)
    resp = make_response(redirect(url_for('index')))
    resp.delete_cookie('session_token')
    return resp


# ── Authenticated Routes ─────────────────────────────────────────────────────

@app.route('/dashboard')
def dashboard():
    user = _get_current_user()
    if not user:
        return redirect(url_for('login'))
    profiles = get_profiles(user['id'])
    resumes = get_resumes(user['id'], limit=20)
    return render_template('dashboard.html', user=user, profiles=profiles, resumes=resumes)


@app.route('/api/profiles', methods=['GET'])
def api_profiles():
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify(get_profiles(user['id']))


@app.route('/api/profiles', methods=['POST'])
def api_save_profile():
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    name = data.get('name', 'My Profile')
    profile_data = data.get('profile_data')
    is_default = data.get('is_default', False)

    if not profile_data:
        return jsonify({"error": "profile_data is required"}), 400

    errors = validate_profile(profile_data)
    if errors:
        return jsonify({"error": f"Profile validation failed: {'; '.join(errors)}"}), 400

    profile_id = save_profile(user['id'], name, profile_data, is_default)
    return jsonify({"id": profile_id, "name": name}), 201


@app.route('/api/profiles/<int:profile_id>', methods=['GET'])
def api_get_profile(profile_id):
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    profile = get_profile(user['id'], profile_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(profile)


@app.route('/api/profiles/<int:profile_id>', methods=['DELETE'])
def api_delete_profile(profile_id):
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    if delete_profile(user['id'], profile_id):
        return jsonify({"message": "Profile deleted"})
    return jsonify({"error": "Profile not found"}), 404


@app.route('/api/resumes', methods=['GET'])
def api_resumes():
    user = _get_current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify(get_resumes(user['id']))


# ── Resume Generation ────────────────────────────────────────────────────────

@app.route('/preview', methods=['POST'])
def preview():
    """Render an HTML preview of the resume without generating a PDF."""
    try:
        uploaded_file = request.files.get('profile')
        if uploaded_file and uploaded_file.filename and _allowed_file(uploaded_file.filename):
            raw_bytes = uploaded_file.stream.read()
            try:
                content = raw_bytes.decode('utf-8')
            except UnicodeDecodeError:
                content = raw_bytes.decode('latin-1')
            profile = yaml.safe_load(content)
        else:
            with open(BASE_PROFILE_PATH, "r", encoding="utf-8") as f:
                profile = yaml.safe_load(f)

        return render_template('resume_template.html',
                               basics=profile.get('basics', {}),
                               education=profile.get('education', []),
                               experience=profile.get('experience', []),
                               projects=profile.get('projects', []),
                               skills=profile.get('skills', {}))
    except Exception as e:
        logger.error(f"Preview error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate', methods=['POST'])
def generate():
    start_time = time.time()
    logger.info(f"Received request from {request.remote_addr}")

    api_key = request.form.get('api_key')
    company = request.form.get('company')
    jd = request.form.get('jd')
    uploaded_file = request.files.get('profile')
    template = request.form.get('template', 'jakes')
    max_pages = int(request.form.get('max_pages', 1))
    profile_id = request.form.get('profile_id', type=int)

    if not api_key or not company or not jd:
        return jsonify({"error": "Missing required fields: api_key, company, and jd are all required."}), 400

    if template not in VALID_TEMPLATES:
        return jsonify({"error": f"Invalid template '{template}'. Must be one of {VALID_TEMPLATES}"}), 400

    if max_pages not in (1, 2):
        return jsonify({"error": "max_pages must be 1 or 2."}), 400

    # Validate uploaded file
    if uploaded_file and uploaded_file.filename:
        if not _allowed_file(uploaded_file.filename):
            return jsonify({"error": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
        uploaded_file.stream.seek(0, 2)
        file_size = uploaded_file.stream.tell()
        uploaded_file.stream.seek(0)
        if file_size > MAX_UPLOAD_SIZE:
            return jsonify({"error": f"File too large. Maximum size: {MAX_UPLOAD_SIZE // (1024*1024)} MB"}), 400
        logger.info(f"Using uploaded profile: {uploaded_file.filename} ({file_size} bytes)")
    else:
        logger.info("Using default base_profile.yaml")

    os.environ["GEMINI_API_KEY"] = api_key

    try:
        if uploaded_file and uploaded_file.filename:
            raw_bytes = uploaded_file.stream.read()
            try:
                content = raw_bytes.decode('utf-8')
            except UnicodeDecodeError:
                content = raw_bytes.decode('latin-1')
            base_profile_dict = yaml.safe_load(content)
        elif profile_id:
            user = _get_current_user()
            if not user:
                return jsonify({"error": "Not authenticated"}), 401
            profile = get_profile(user['id'], profile_id)
            if not profile:
                return jsonify({"error": "Profile not found"}), 404
            base_profile_dict = profile['profile_data']
        else:
            with open(BASE_PROFILE_PATH, "r", encoding="utf-8") as f:
                base_profile_dict = yaml.safe_load(f)

        # Validate profile structure
        errors = validate_profile(base_profile_dict)
        if errors:
            return jsonify({"error": f"Profile validation failed: {'; '.join(errors)}"}), 400

        logger.info(f"Calling Gemini AI for company: {company}")
        tailored_profile = generate_tailored_profile(base_profile_dict, jd, company)
        logger.info("Received profile from Gemini. Building PDF...")

        # ATS analysis
        ats_result = analyze_ats_score(tailored_profile, jd, company)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, "tailored_resume.pdf")
        build_resume_pdf(tailored_profile, output_path, max_pages=max_pages, template=template)

        elapsed = time.time() - start_time
        logger.info(f"Resume generated in {elapsed:.2f}s -> {output_path}")

        # Save to database if user is authenticated
        user = _get_current_user()
        resume_id = None
        if user:
            resume_id = save_resume(
                user['id'], company, jd, template, max_pages,
                profile_id=profile_id if profile_id else 0, ats_score=ats_result['overall_score'],
                pdf_path=output_path,
            )

        response_data = {
            "ats_score": ats_result['overall_score'],
            "keyword_match": ats_result['keyword_match']['percentage'],
            "suggestions": ats_result['suggestions'][:3],
            "strengths": ats_result['strengths'][:3],
        }
        if resume_id:
            response_data["resume_id"] = resume_id

        return send_file(output_path, as_attachment=True, download_name="tailored_resume.pdf")

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Generation failed after {elapsed:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── Export Endpoints ─────────────────────────────────────────────────────────

@app.route('/api/export/<format>', methods=['POST'])
def export_resume(format: str):
    """Export resume in different formats: docx, txt, md"""
    if format not in ('docx', 'txt', 'md'):
        return jsonify({"error": "Invalid format. Use: docx, txt, md"}), 400

    user = _get_current_user()
    if user:
        resume_id = request.form.get('resume_id', type=int)
        if resume_id:
            resume = get_resume(user['id'], resume_id)
            if resume and resume.get('profile_data'):
                profile_data = resume['profile_data']
            else:
                return jsonify({"error": "Resume not found"}), 404
        else:
            profile_id = request.form.get('profile_id', type=int)
            if profile_id:
                profile = get_profile(user['id'], profile_id)
                if profile:
                    profile_data = profile['profile_data']
                else:
                    return jsonify({"error": "Profile not found"}), 404
            else:
                return jsonify({"error": "resume_id or profile_id required"}), 400
    else:
        uploaded_file = request.files.get('profile')
        if uploaded_file and uploaded_file.filename:
            raw_bytes = uploaded_file.stream.read()
            try:
                content = raw_bytes.decode('utf-8')
            except UnicodeDecodeError:
                content = raw_bytes.decode('latin-1')
            profile_data = yaml.safe_load(content)
        else:
            with open(BASE_PROFILE_PATH, "r", encoding="utf-8") as f:
                profile_data = yaml.safe_load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if format == 'docx':
        output_path = os.path.join(OUTPUT_DIR, "resume.docx")
        export_to_docx(profile_data, output_path)
        return send_file(output_path, as_attachment=True, download_name="resume.docx")
    elif format == 'txt':
        output_path = os.path.join(OUTPUT_DIR, "resume.txt")
        export_to_text(profile_data, output_path)
        return send_file(output_path, as_attachment=True, download_name="resume.txt")
    else:  # format == 'md'
        output_path = os.path.join(OUTPUT_DIR, "resume.md")
        export_to_markdown(profile_data, output_path)
        return send_file(output_path, as_attachment=True, download_name="resume.md")


# ── Middleware ────────────────────────────────────────────────────────────────

@app.after_request
def log_request(response):
    logger.info(f"{request.method} {request.path} -> {response.status_code}")
    return response


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=8501)
