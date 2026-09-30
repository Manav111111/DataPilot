import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class DatasetRecord(Base):
    __tablename__ = "dataset_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    record_data = Column(JSON, nullable=False)
    normalized_data = Column(JSON, nullable=False)
    record_hash = Column(String(64), nullable=True)
    validation_status = Column(String(50), default="valid", nullable=False)
    validation_errors = Column(JSON, nullable=True)
    source_count = Column(Integer, default=1, nullable=False)
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

    dataset = relationship("Dataset", back_populates="records")
    record_sources = relationship(
        "RecordSource", back_populates="dataset_record", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_dataset_records_dataset_id", "dataset_id"),
        Index("ix_dataset_records_status", "dataset_id", "validation_status"),
        Index("ix_dataset_records_hash", "dataset_id", "record_hash"),
    )
