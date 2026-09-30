import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class DatasetMergeHistory(Base):
    __tablename__ = "dataset_merge_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    retained_record_id = Column(
        String(36),
        ForeignKey("dataset_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    merged_record_ids = Column(JSON, nullable=False, default=list)
    merge_configuration = Column(JSON, nullable=False, default=dict)
    created_by = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    dataset = relationship("Dataset", back_populates="merge_histories")
    retained_record = relationship("DatasetRecord")
    user = relationship("User")
