import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id = Column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dataset_id = Column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String(255), nullable=False, default="Analysis Conversation")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User")
    project = relationship("Project")
    dataset = relationship("Dataset", back_populates="analysis_sessions")
    messages = relationship(
        "AnalysisMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AnalysisMessage.created_at",
    )

    __table_args__ = (
        Index("ix_analysis_sessions_user_dataset", "user_id", "dataset_id"),
    )
