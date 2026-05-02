"""
History routes — list, retrieve, export, and delete past rewrite sessions.

Security:
    - Every endpoint requires authentication via Depends(get_current_user).
    - Every query is IDOR-safe (filters by user_id == current_user.id).
    - 404 returned for both "not found" and "not yours" to avoid info leakage.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import get_db
from routes.auth import get_current_user
import models.user as user_model
import models.session as session_model

logger = logging.getLogger(__name__)

router = APIRouter(tags=["history"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JOB_DESC_PREVIEW_LEN = 100
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    ats_score_before: float
    ats_score_after: float
    job_description: str  # Truncated preview


class SessionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_resume: str
    job_description: str
    rewritten_resume_json: dict
    ats_score_before: float
    ats_score_after: float
    section_scores_before: dict
    section_scores_after: dict
    created_at: datetime


class DeleteResponse(BaseModel):
    detail: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_json_loads(raw: Optional[str], default: Any, field_name: str, session_id: int) -> Any:
    """
    Safely parse a JSON column. Logs and returns `default` on failure
    instead of leaking a 500 to the client.
    """
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError) as e:
        logger.warning(
            "Malformed JSON in field '%s' for session_id=%s: %s",
            field_name, session_id, e,
        )
        return default


def _truncate_preview(text: Optional[str], max_len: int = JOB_DESC_PREVIEW_LEN) -> str:
    """None-safe, word-boundary-aware truncation for list previews."""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    # Truncate on word boundary when possible
    cut = text[:max_len].rsplit(" ", 1)[0] or text[:max_len]
    return cut + "..."


def _get_user_session(
    db: Session,
    session_id: int,
    current_user: user_model.User,
) -> session_model.RewriteSession:
    """
    Fetch a session belonging to the current user, or raise 404.
    Centralizes the IDOR-safe lookup pattern.
    """
    session = (
        db.query(session_model.RewriteSession)
        .filter(
            session_model.RewriteSession.id == session_id,
            session_model.RewriteSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        # 404 (not 403) so we don't leak existence of other users' sessions
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[SessionResponse])
async def get_history(
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    """
    Return the current user's rewrite history, newest first.
    Paginated via `limit` (1..100, default 20) and `offset`.
    """
    def _query():
        return (
            db.query(session_model.RewriteSession)
            .filter(session_model.RewriteSession.user_id == current_user.id)
            .order_by(session_model.RewriteSession.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    sessions = await run_in_threadpool(_query)

    return [
        SessionResponse(
            id=s.id,
            created_at=s.created_at,
            ats_score_before=s.ats_score_before,
            ats_score_after=s.ats_score_after,
            job_description=_truncate_preview(s.job_description),
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    """Return full detail for a single rewrite session owned by the current user."""
    session = await run_in_threadpool(_get_user_session, db, session_id, current_user)

    return SessionDetailResponse(
        id=session.id,
        original_resume=session.original_resume or "",
        job_description=session.job_description or "",
        rewritten_resume_json=_safe_json_loads(
            session.rewritten_resume_json, default={}, field_name="rewritten_resume_json", session_id=session_id
        ),
        ats_score_before=session.ats_score_before,
        ats_score_after=session.ats_score_after,
        section_scores_before=_safe_json_loads(
            session.section_scores_before, default={}, field_name="section_scores_before", session_id=session_id
        ),
        section_scores_after=_safe_json_loads(
            session.section_scores_after, default={}, field_name="section_scores_after", session_id=session_id
        ),
        created_at=session.created_at,
    )


@router.get("/{session_id}/export")
async def export_session_pdf(
    session_id: int,
    save: bool = Query(False, description="If true, also persist the PDF to the outputs/ folder."),
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    """
    Re-generate and download the PDF for a past rewrite session.

    Switched from POST -> GET (idempotent, browser-friendly download links).
    Disk persistence to outputs/ is now opt-in via `?save=true`.
    """
    session = await run_in_threadpool(_get_user_session, db, session_id, current_user)

    # Lazy import to avoid circular imports
    from services import pdf_generator

    rewritten_json = _safe_json_loads(
        session.rewritten_resume_json,
        default=None,
        field_name="rewritten_resume_json",
        session_id=session_id,
    )
    if rewritten_json is None:
        logger.error("Cannot export session_id=%s: rewritten_resume_json is missing/invalid", session_id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Stored resume data is missing or corrupted; cannot regenerate PDF.",
        )

    # Generate PDF (subprocess -> Tectonic/pdflatex; runs in threadpool)
    try:
        pdf_bytes = await run_in_threadpool(pdf_generator.generate, rewritten_json)
    except Exception as e:
        logger.exception("PDF generation failed for session_id=%s: %s", session_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF generation failed.",
        )

    # Optional disk persistence
    if save:
        try:
            await run_in_threadpool(pdf_generator.save_to_outputs, pdf_bytes, session_id=session_id)
        except Exception as e:
            # Don't fail the download just because the disk write failed
            logger.warning("save_to_outputs failed for session_id=%s: %s", session_id, e)

    # Use Response (not StreamingResponse) — we have all bytes in memory,
    # and Response sets Content-Length automatically for proper progress UX.
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="resume_{session_id}.pdf"'},
    )


@router.delete("/{session_id}", response_model=DeleteResponse)
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    """
    Delete a rewrite session and any associated generated PDF on disk.
    Provided for privacy / GDPR compliance — resumes contain PII.
    """
    session = await run_in_threadpool(_get_user_session, db, session_id, current_user)

    def _delete():
        db.delete(session)
        db.commit()

    try:
        await run_in_threadpool(_delete)
    except Exception as e:
        logger.exception("Failed to delete session_id=%s: %s", session_id, e)
        # Roll back the session so the connection isn't left in a bad state
        await run_in_threadpool(db.rollback)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session.",
        )

    # Best-effort cleanup of the generated PDF on disk (if it exists)
    try:
        from services import pdf_generator
        outputs_dir = getattr(pdf_generator, "OUTPUTS_DIR", "outputs")
        pdf_path = os.path.join(outputs_dir, f"resume_{session_id}.pdf")
        if os.path.isfile(pdf_path):
            await run_in_threadpool(os.remove, pdf_path)
            logger.info("Deleted on-disk PDF for session_id=%s", session_id)
    except Exception as e:
        # Disk cleanup is non-critical
        logger.warning("Could not clean up PDF on disk for session_id=%s: %s", session_id, e)

    logger.info("User user_id=%s deleted session_id=%s", current_user.id, session_id)
    return DeleteResponse(detail="Session deleted")