import os
import time
import shutil
import logging
import subprocess
import tempfile
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "outputs")
)
SAVE_OUTPUTS = os.getenv("SAVE_PDF_OUTPUTS", "true").lower() == "true"
OUTPUT_RETENTION_DAYS = int(os.getenv("PDF_OUTPUT_RETENTION_DAYS", "7"))
MAX_LATEX_SIZE = int(os.getenv("MAX_LATEX_SIZE", str(500 * 1024)))  # 500KB
LATEX_TIMEOUT = int(os.getenv("LATEX_TIMEOUT_SECONDS", "120"))


def _ensure_outputs_dir():
    """Create outputs directory if missing (lazy — avoids import-time crash)."""
    try:
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create outputs dir {OUTPUTS_DIR}: {e}")


def _cleanup_old_outputs(max_age_days: int = None):
    """Delete output PDFs older than max_age_days. Best-effort, never raises."""
    if max_age_days is None:
        max_age_days = OUTPUT_RETENTION_DAYS
    if max_age_days <= 0:
        return  # 0 or negative disables cleanup

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
    """
    Save PDF bytes to the outputs folder.
    Returns the absolute path of the saved file.
    """
    _ensure_outputs_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"session_{session_id}_" if session_id is not None else "resume_"
    filename = f"{prefix}{timestamp}.pdf"
    filepath = os.path.join(OUTPUTS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)
    return filepath


def escape_latex(text: str) -> str:
    """
    Escape LaTeX special characters in the given text.
    Self-contained — does not import from latex_escape.py.

    FIXED: Backslash is replaced FIRST so that backslashes introduced by
    other escape sequences (e.g. \\&) are not re-escaped into
    \\textbackslash{}&. Previously, "AT&T" became "AT\\textbackslash{}&T".
    """
    if text is None:
        return ""

    text = str(text)

    # CRITICAL ORDER: backslash must be processed before any replacement
    # that introduces new backslashes.
    text = text.replace('\\', r'\textbackslash{}')

    # Now safe to escape the rest
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }

    for char, escape in replacements.items():
        text = text.replace(char, escape)

    return text


def _escape_resume_data(data):
    """
    Recursively apply latex_escape to every string value in a nested
    dict / list / scalar structure.

    FIXED: Defense-in-depth against LaTeX injection. Even if the Jinja2
    template forgets to apply the |latex_escape filter on a field,
    the data is already escaped here.
    """
    if isinstance(data, str):
        return escape_latex(data)
    if isinstance(data, dict):
        return {k: _escape_resume_data(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_escape_resume_data(item) for item in data]
    return data


# ---------------------------------------------------------------------------
# LaTeX engine detection (cached)
# ---------------------------------------------------------------------------
_engine_cache: tuple[str, str] | None = None


def _find_latex_engine() -> tuple[str, str]:
    """
    Locate a usable LaTeX engine.
    Returns (engine_path, engine_type) where engine_type is 'tectonic' or 'pdflatex'.
    Tries Tectonic first (preferred in Docker), then falls back to pdflatex.
    Result is cached after first successful detection.
    """
    global _engine_cache
    if _engine_cache is not None:
        return _engine_cache

    # --- Try Tectonic ---
    tectonic_candidates = [
        shutil.which("tectonic"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "tectonic", "tectonic.exe"),
        os.path.join(os.environ.get("USERPROFILE", ""), ".cargo", "bin", "tectonic.exe"),
    ]
    for candidate in tectonic_candidates:
        if candidate and os.path.isfile(candidate):
            # Quick sanity check — make sure the binary actually runs
            try:
                probe = subprocess.run(
                    [candidate, "--help"],
                    capture_output=True, timeout=5,
                )
                if probe.returncode == 0:
                    logger.info(f"Detected LaTeX engine: tectonic ({candidate})")
                    _engine_cache = (candidate, "tectonic")
                    return _engine_cache
            except Exception as e:
                logger.warning(f"Tectonic at {candidate} failed sanity check: {e}")
                # binary exists but is broken (DLL issues on Windows)
                continue

    # --- Try pdflatex (MiKTeX / TeX Live) ---
    pdflatex_candidates = [
        shutil.which("pdflatex"),
        os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Programs", "MiKTeX", "miktex", "bin", "x64", "pdflatex.exe",
        ),
    ]
    for candidate in pdflatex_candidates:
        if candidate and os.path.isfile(candidate):
            logger.info(f"Detected LaTeX engine: pdflatex ({candidate})")
            _engine_cache = (candidate, "pdflatex")
            return _engine_cache

    raise FileNotFoundError(
        "No LaTeX engine found. Install MiKTeX (Windows) or Tectonic (Docker/Linux)."
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def generate(
    resume_json: dict,
    session_id: int | None = None,
    template_name: str = "resume.tex.j2",
) -> bytes:
    """
    Generate PDF from resume JSON using the best available LaTeX engine.
    Returns PDF as bytes.
    """
    try:
        engine_bin, engine_type = _find_latex_engine()

        # Set up Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        env = Environment(loader=FileSystemLoader(template_dir))
        env.filters["latex_escape"] = escape_latex

        template = env.get_template(template_name)

        # FIXED: pre-escape ALL string values in resume data as defense-in-depth.
        # Even if template forgets {{ x | latex_escape }}, we're safe.
        safe_resume = _escape_resume_data(resume_json)

        # Render LaTeX template with resume data
        latex_content = template.render(**safe_resume)

        # Sanity check on size
        if len(latex_content) > MAX_LATEX_SIZE:
            logger.error(
                f"LaTeX content too large: {len(latex_content)} bytes "
                f"(max {MAX_LATEX_SIZE})"
            )
            raise HTTPException(
                status_code=400,
                detail="Resume content too large to render. Please shorten it.",
            )

        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = os.path.join(temp_dir, "resume.tex")
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(latex_content)

            # Build the command based on engine type
            if engine_type == "tectonic":
                cmd = [engine_bin, tex_file, "--outdir", temp_dir]
            else:  # pdflatex
                cmd = [
                    engine_bin,
                    "-interaction=nonstopmode",
                    "-output-directory", temp_dir,
                    tex_file,
                ]

            logger.info(f"Running LaTeX compilation with {engine_type}")

            # Run LaTeX engine
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=LATEX_TIMEOUT,
            )

            # Read generated PDF
            pdf_file = os.path.join(temp_dir, "resume.pdf")

            # pdflatex may return non-zero for warnings but still produce a PDF
            if not os.path.exists(pdf_file):
                # FIXED: log full error server-side, return generic message to client
                logger.error(
                    f"LaTeX compilation failed ({engine_type}). "
                    f"Return code: {result.returncode}\n"
                    f"STDERR:\n{result.stderr}\n"
                    f"STDOUT (last 2000 chars):\n{result.stdout[-2000:]}"
                )
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "PDF compilation failed. "
                        "Please check your resume content for unsupported characters."
                    ),
                )

            with open(pdf_file, "rb") as f:
                pdf_bytes = f.read()

            logger.info(
                f"Successfully generated PDF "
                f"(engine={engine_type}, size={len(pdf_bytes)} bytes, "
                f"session_id={session_id})"
            )

            # Persist to outputs/ folder (best-effort, non-fatal on failure)
            if SAVE_OUTPUTS:
                try:
                    save_to_outputs(pdf_bytes, session_id=session_id)
                except Exception as e:
                    logger.warning(f"Failed to persist PDF to outputs/: {e}")

                # Best-effort cleanup of old PDFs (run occasionally)
                _cleanup_old_outputs()

            return pdf_bytes

    except subprocess.TimeoutExpired:
        logger.error(f"LaTeX compilation timed out after {LATEX_TIMEOUT}s")
        raise HTTPException(
            status_code=500,
            detail="PDF generation timed out",
        )
    except HTTPException:
        raise
    except FileNotFoundError as e:
        # No LaTeX engine installed
        logger.error(f"LaTeX engine not available: {e}")
        raise HTTPException(
            status_code=500,
            detail="PDF generation is not available on this server (LaTeX engine missing).",
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="PDF generation failed. Please try again.",
        )