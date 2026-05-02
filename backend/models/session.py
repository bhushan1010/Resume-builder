from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class RewriteSession(Base):
    __tablename__ = "rewrite_sessions"

    id = Column(Integer, primary_key=True, index=True)

    # FIXED: indexed for fast user-session lookups + cascade delete
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    original_resume = Column(Text, nullable=False)
    job_description = Column(Text, nullable=False)
    rewritten_resume_json = Column(Text, nullable=False)

    ats_score_before = Column(Float, nullable=False)
    ats_score_after = Column(Float, nullable=False)
    section_scores_before = Column(Text, nullable=False)
    section_scores_after = Column(Text, nullable=False)

    industry = Column(String(100), nullable=True)
    rating = Column(Integer, nullable=True)
    rating_reason = Column(Text, nullable=True)
    pattern_score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # NEW: bidirectional relationship to user
    user = relationship("User", back_populates="sessions")

    # NEW: composite index for common query pattern
    # ("get user's sessions sorted by date") + rating CHECK constraint
    __table_args__ = (
        Index("ix_session_user_created", "user_id", "created_at"),
        CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)",
            name="check_rating_range",
        ),
    )

    def __repr__(self):
        return (
            f"<RewriteSession(id={self.id}, user_id={self.user_id}, "
            f"score_before={self.ats_score_before}, score_after={self.ats_score_after})>"
        )