import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class RecordSource(Base):
    __tablename__ = "record_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_record_id = Column(
        String(36), ForeignKey("dataset_records.id", ondelete="CASCADE"), nullable=False
    )
    data_source_id = Column(
        String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False
    )
    evidence_excerpt = Column(Text, nullable=True)
    evidence_field = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    dataset_record = relationship("DatasetRecord", back_populates="record_sources")
    data_source = relationship("DataSource", back_populates="record_sources")

    __table_args__ = (
        Index("ix_record_sources_record_id", "dataset_record_id"),
        Index("ix_record_sources_source_id", "data_source_id"),
        Index("ix_record_sources_field", "evidence_field"),
    )
