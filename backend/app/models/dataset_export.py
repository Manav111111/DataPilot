import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class DatasetExport(Base):
    __tablename__ = "dataset_exports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    format = Column(String(20), nullable=False)  # csv, xlsx, json
    export_configuration = Column(JSON, nullable=False, default=dict)
    status = Column(String(50), default="completed")  # pending, processing, completed, failed
    file_reference = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    record_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="exports")
    user = relationship("User")
