import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class DatasetQualityReport(Base):
    __tablename__ = "dataset_quality_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_id = Column(
        String(36),
        ForeignKey("dataset_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    quality_score = Column(Float, nullable=False, default=0.0)
    dimension_scores = Column(JSON, nullable=False, default=dict)
    report_data = Column(JSON, nullable=False, default=dict)
    scoring_method_version = Column(String(50), default="v1.0")
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    dataset = relationship("Dataset", back_populates="quality_reports")
