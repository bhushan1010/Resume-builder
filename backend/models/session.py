from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from ..database import Base

class RewriteSession(Base):
    __tablename__ = "rewrite_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_resume = Column(Text, nullable=False)
    job_description = Column(Text, nullable=False)
    rewritten_resume_json = Column(Text, nullable=False)  # Store as JSON string
    ats_score_before = Column(Float, nullable=False)
    ats_score_after = Column(Float, nullable=False)
    section_scores_before = Column(Text, nullable=False)  # JSON string
    section_scores_after = Column(Text, nullable=False)   # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())