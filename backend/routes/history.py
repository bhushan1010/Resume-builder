from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from routes.auth import get_current_user
import models.user as user_model
import models.session as session_model
from pydantic import BaseModel
import json

router = APIRouter()

# Pydantic models
class SessionResponse(BaseModel):
    id: int
    created_at: str
    ats_score_before: float
    ats_score_after: float
    job_description: str

class SessionDetailResponse(BaseModel):
    id: int
    original_resume: str
    job_description: str
    rewritten_resume_json: dict
    ats_score_before: float
    ats_score_after: float
    section_scores_before: dict
    section_scores_after: dict
    created_at: str

@router.get("/", response_model=list[SessionResponse])
async def get_history(
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    sessions = db.query(session_model.RewriteSession).filter(
        session_model.RewriteSession.user_id == current_user.id
    ).order_by(session_model.RewriteSession.created_at.desc()).all()
    
    result = []
    for session in sessions:
        result.append(SessionResponse(
            id=session.id,
            created_at=session.created_at.isoformat(),
            ats_score_before=session.ats_score_before,
            ats_score_after=session.ats_score_after,
            job_description=(session.job_description[:100] + "...") if len(session.job_description) > 100 else session.job_description
        ))
    
    return result

@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    session = db.query(session_model.RewriteSession).filter(
        session_model.RewriteSession.id == session_id,
        session_model.RewriteSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionDetailResponse(
        id=session.id,
        original_resume=session.original_resume,
        job_description=session.job_description,
        rewritten_resume_json=json.loads(session.rewritten_resume_json),
        ats_score_before=session.ats_score_before,
        ats_score_after=session.ats_score_after,
        section_scores_before=json.loads(session.section_scores_before),
        section_scores_after=json.loads(session.section_scores_after),
        created_at=session.created_at.isoformat()
    )

@router.post("/{session_id}/export")
async def export_session_pdf(
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
    
    # Import here to avoid circular imports
    from services import pdf_generator
    
    # Parse rewritten resume JSON
    rewritten_json = json.loads(session.rewritten_resume_json)
    
    # Generate PDF and save to outputs/ folder
    pdf_bytes = pdf_generator.generate(rewritten_json)
    pdf_generator.save_to_outputs(pdf_bytes, session_id=session_id)
    
    # Return PDF as streaming response
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=resume_{session_id}.pdf"}
    )