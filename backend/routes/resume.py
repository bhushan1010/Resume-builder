from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from routes.auth import get_current_user
import models.user as user_model
from services import gemini, ats_scorer, pdf_generator, pdf_extractor
import models.session as session_model
from pydantic import BaseModel
import json

router = APIRouter()

# Pydantic models
class AnalyzeRequest(BaseModel):
    resume_text: str
    job_description: str

class RewriteRequest(BaseModel):
    resume_text: str
    job_description: str

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

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_resume(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user)
):
    # Score the resume
    result = ats_scorer.score(request.resume_text, request.job_description)
    
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
    # Score original resume
    original_score = ats_scorer.score(request.resume_text, request.job_description)
    
    # Parse resume with Gemini
    parsed_resume = gemini.parse_resume(request.resume_text)
    
    # Rewrite resume with Gemini
    rewritten_resume = gemini.rewrite_resume(parsed_resume, request.job_description)
    
    # Score rewritten resume
    rewritten_text = json.dumps(rewritten_resume)  # Simplified - in practice you'd convert to text
    rewritten_score = ats_scorer.score(rewritten_text, request.job_description)
    
    # Save session to database
    db_session = session_model.RewriteSession(
        user_id=current_user.id,
        original_resume=request.resume_text,
        job_description=request.job_description,
        rewritten_resume_json=json.dumps(rewritten_resume),
        ats_score_before=original_score["overall"],
        ats_score_after=rewritten_score["overall"],
        section_scores_before=json.dumps(original_score["sections"]),
        section_scores_after=json.dumps(rewritten_score["sections"])
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return RewriteResponse(
        rewritten_json=rewritten_resume,
        ats_before=original_score["overall"],
        ats_after=rewritten_score["overall"],
        section_scores_before=original_score["sections"],
        section_scores_after=rewritten_score["sections"],
        session_id=db_session.id
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
    rewritten_json = json.loads(session.rewritten_resume_json)
    
    # Generate PDF
    pdf_bytes = pdf_generator.generate(rewritten_json)
    
    # Return PDF as streaming response
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        iter([pdf_bytes]),
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
    # Read file bytes
    pdf_bytes = await pdf_file.read()
    
    # Extract text using hybrid approach
    result = pdf_extractor.extract_resume_from_pdf(pdf_bytes)
    
    return result