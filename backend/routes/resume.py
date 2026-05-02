import json
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from routes.auth import get_current_user
import models.user as user_model
import models.session as session_model
from services import gemini, ats_scorer, pdf_generator, pdf_extractor
from services.pattern_learner import pattern_learner

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB — matches pdf_extractor's MAX_FILE_SIZE_BYTES
UPLOAD_CHUNK_SIZE = 64 * 1024       # 64KB chunks while reading

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    resume_text: str
    job_description: str


class RewriteRequest(BaseModel):
    resume_text: str
    job_description: str


class FeedbackRequest(BaseModel):
    session_id: int
    rating: int
    rating_reason: str = None


class AnalyzeResponse(BaseModel):
    overall_score: float
    section_scores: dict


class RewriteResponse(BaseModel):
    rewritten_json: dict
    ats_before: float
    ats_after: float
    section_scores_before: dict
    section_scores_after: dict
    session_id: int
    improvement_tips: list = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_resume(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    # FIXED: ats_scorer.score is CPU/IO heavy (sentence transformer + Gemini calls).
    # Wrapping in threadpool prevents blocking the event loop.
    result = await run_in_threadpool(
        ats_scorer.score,
        request.resume_text,
        request.job_description
    )

    return AnalyzeResponse(
        overall_score=result["overall"],
        section_scores=result["sections"]
    )


@router.post("/rewrite", response_model=RewriteResponse)
async def rewrite_resume(
    request: RewriteRequest,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    # FIXED: every blocking call below is now wrapped in run_in_threadpool.
    # Without this, a single /rewrite request blocks the entire FastAPI
    # event loop for 30-60+ seconds, freezing all other requests.

    industry = await run_in_threadpool(
        pattern_learner.detect_industry, request.job_description
    )
    learned_patterns = await run_in_threadpool(
        pattern_learner.get_patterns_for_industry, industry
    )
    adapted_prompt = await run_in_threadpool(
        pattern_learner.get_adapted_prompt, industry, learned_patterns
    )

    original_score = await run_in_threadpool(
        ats_scorer.score, request.resume_text, request.job_description
    )
    parsed_resume = await run_in_threadpool(
        gemini.parse_resume, request.resume_text
    )
    rewritten_resume = await run_in_threadpool(
        gemini.rewrite_resume, parsed_resume, request.job_description, adapted_prompt
    )

    rewritten_text = json.dumps(rewritten_resume)
    rewritten_score = await run_in_threadpool(
        ats_scorer.score, rewritten_text, request.job_description
    )

    # FIXED: improvement_tips no longer gated on `learned_patterns`.
    # The function only compares before/after section scores — useful for ALL users,
    # including first-time users who don't have learned patterns yet.
    improvement_tips = pattern_learner.get_improvement_tips(
        original_score["sections"],
        rewritten_score["sections"]
    )

    # FIXED: DB write wrapped in try/except with rollback on failure
    db_session = session_model.RewriteSession(
        user_id=current_user.id,
        original_resume=request.resume_text,
        job_description=request.job_description,
        rewritten_resume_json=json.dumps(rewritten_resume),
        ats_score_before=original_score["overall"],
        ats_score_after=rewritten_score["overall"],
        section_scores_before=json.dumps(original_score["sections"]),
        section_scores_after=json.dumps(rewritten_score["sections"]),
        industry=industry
    )
    try:
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save rewrite session for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save session")

    return RewriteResponse(
        rewritten_json=rewritten_resume,
        ats_before=original_score["overall"],
        ats_after=rewritten_score["overall"],
        section_scores_before=original_score["sections"],
        section_scores_after=rewritten_score["sections"],
        session_id=db_session.id,
        improvement_tips=improvement_tips
    )


@router.post("/export/{session_id}")
async def export_resume_pdf(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    # Get session from database
    session = db.query(session_model.RewriteSession).filter(
        session_model.RewriteSession.id == session_id,
        session_model.RewriteSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Parse rewritten resume JSON
    try:
        rewritten_json = json.loads(session.rewritten_resume_json)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Corrupted session JSON for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Session data is corrupted")

    # Generate PDF — wrapped in threadpool (LaTeX is blocking) + error handling
    try:
        pdf_bytes = await run_in_threadpool(pdf_generator.generate, rewritten_json)
    except Exception as e:
        logger.error(f"PDF generation failed for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate PDF. Please try again.")

    # FIXED: use Response directly instead of fake-streaming with iter([pdf_bytes])
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=resume_{session_id}.pdf"}
    )


@router.post("/extract-pdf")
async def extract_resume_from_pdf_endpoint(
    pdf_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    """
    Extract text from uploaded PDF resume.
    Returns extraction result with confidence assessment.
    """
    # FIXED: stream-read with hard size cap to prevent DoS via huge uploads.
    # Without this, an attacker could upload a 1GB+ file and your server
    # would load the entire thing into RAM before validating.
    pdf_bytes = b""
    while True:
        chunk = await pdf_file.read(UPLOAD_CHUNK_SIZE)
        if not chunk:
            break
        pdf_bytes += chunk
        if len(pdf_bytes) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE // (1024*1024)}MB."
            )

    # FIXED: PDF extraction (PyMuPDF + possibly Gemini Vision) is blocking.
    # Wrap in threadpool.
    result = await run_in_threadpool(pdf_extractor.extract_resume_from_pdf, pdf_bytes)

    return result


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    session = db.query(session_model.RewriteSession).filter(
        session_model.RewriteSession.id == request.session_id,
        session_model.RewriteSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if request.rating < 1 or request.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    session.rating = request.rating
    session.rating_reason = request.rating_reason

    pattern_score = pattern_learner.calculate_pattern_score(
        session.ats_score_before,
        session.ats_score_after,
        request.rating
    )
    session.pattern_score = pattern_score

    # FIXED: DB commit with rollback on failure
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save feedback for session {request.session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save feedback")

    # Update learned patterns (file write — wrap in threadpool)
    if session.industry:
        try:
            await run_in_threadpool(
                pattern_learner.update_patterns,
                session.industry,
                session.ats_score_before,
                session.ats_score_after,
                request.rating
            )
        except Exception as e:
            # Don't fail the feedback request if pattern update fails
            logger.error(f"Failed to update patterns for industry '{session.industry}': {e}", exc_info=True)

    return {"status": "success", "message": "Feedback recorded"}