import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(
        String(36),
        ForeignKey("analysis_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    analysis_type = Column(String(50), nullable=False)  # "chat_query", "auto_insights", "statistics"
    structured_result = Column(JSON, nullable=False, default=dict)
    summary = Column(Text, nullable=True)
    dataset_version = Column(Integer, nullable=False, default=1)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    dataset = relationship("Dataset")
    session = relationship("AnalysisSession")
