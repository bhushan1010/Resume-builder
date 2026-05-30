import os
import time
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException
import pdfkit

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "outputs")
)
SAVE_OUTPUTS = os.getenv("SAVE_PDF_OUTPUTS", "true").lower() == "true"
OUTPUT_RETENTION_DAYS = int(os.getenv("PDF_OUTPUT_RETENTION_DAYS", "7"))

# Adjust this path based on where we installed the binary
WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"

def _ensure_outputs_dir():
    try:
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create outputs dir {OUTPUTS_DIR}: {e}")

def _cleanup_old_outputs(max_age_days: int = None):
    if max_age_days is None:
        max_age_days = OUTPUT_RETENTION_DAYS
    if max_age_days <= 0:
        return
    try:
        if not os.path.isdir(OUTPUTS_DIR):
            return
        cutoff = time.time() - (max_age_days * 86400)
        deleted = 0
        for filename in os.listdir(OUTPUTS_DIR):
            filepath = os.path.join(OUTPUTS_DIR, filename)
            try:
                if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)
                    deleted += 1
            except OSError:
                continue
        if deleted:
            logger.info(f"Cleaned up {deleted} old output PDF(s) from {OUTPUTS_DIR}")
    except Exception as e:
        logger.warning(f"Output cleanup failed (non-fatal): {e}")

def save_to_outputs(pdf_bytes: bytes, session_id: int | None = None) -> str:
    _ensure_outputs_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"session_{session_id}_" if session_id is not None else "resume_"
    filename = f"{prefix}{timestamp}.pdf"
    filepath = os.path.join(OUTPUTS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)
    return filepath

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def generate(
    resume_json: dict,
    session_id: int | None = None,
    template_name: str = "resume.html.j2",
) -> bytes:
    """
    Generate PDF from resume JSON using pdfkit.
    Returns PDF as bytes.
    """
    try:
        # Check if the wkhtmltopdf executable exists where we expect it
        if not os.path.exists(WKHTMLTOPDF_PATH):
            logger.error(f"wkhtmltopdf binary not found at {WKHTMLTOPDF_PATH}")
            # As a fallback, try to run without configuration if it's in the system PATH
            try:
                config = pdfkit.configuration()
            except IOError:
                raise HTTPException(
                    status_code=500,
                    detail="PDF generation is not available on this server (wkhtmltopdf engine missing).",
                )
        else:
            config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

        # Set up Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)

        # Normalize URLs to prevent broken relative links in PDF
        import copy
        resume_data = copy.deepcopy(resume_json)
        
        def clean_url(url):
            if not url or not isinstance(url, str):
                return url
            url_str = url.strip()
            if not url_str:
                return url_str
            if url_str.startswith(("http://", "https://", "mailto:", "tel:")):
                return url_str
            return f"https://{url_str}"

        # Clean header links
        header = resume_data.get("header", {})
        for key in ["linkedin", "github", "portfolio", "leetcode"]:
            if key in header:
                header[key] = clean_url(header[key])
        
        # Clean email specifically
        if "email" in header and header["email"]:
            email = header["email"].strip()
            if not email.startswith("mailto:"):
                header["email"] = f"mailto:{email}"

        # Clean projects links
        for proj in resume_data.get("projects", []):
            if "url" in proj:
                proj["url"] = clean_url(proj["url"])

        # Clean internship/experience links
        for exp in resume_data.get("internship", []):
            if "url" in exp:
                exp["url"] = clean_url(exp["url"])

        # Clean certifications links
        for cert in resume_data.get("certifications", []):
            if "url" in cert:
                cert["url"] = clean_url(cert["url"])

        # Render HTML template with normalized resume data
        # Jinja will autoescape strings due to the | e filters in the template
        html_content = template.render(**resume_data)

        # Convert HTML to PDF using pdfkit
        options = {
            'page-size': 'Letter',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None
        }

        logger.info(f"Running pdfkit generation...")
        pdf_bytes = pdfkit.from_string(html_content, False, options=options, configuration=config)

        if not pdf_bytes:
            raise Exception("pdfkit returned empty result.")

        logger.info(
            f"Successfully generated PDF "
            f"(engine=pdfkit, size={len(pdf_bytes)} bytes, "
            f"session_id={session_id})"
        )

        if SAVE_OUTPUTS:
            try:
                save_to_outputs(pdf_bytes, session_id=session_id)
            except Exception as e:
                logger.warning(f"Failed to persist PDF to outputs/: {e}")
            _cleanup_old_outputs()

        return pdf_bytes

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="PDF generation failed. Please try again.",
        )