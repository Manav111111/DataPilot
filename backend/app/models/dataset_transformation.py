import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class DatasetTransformation(Base):
    __tablename__ = "dataset_transformations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    operation_type = Column(String(100), nullable=False)
    configuration = Column(JSON, nullable=False, default=dict)
    status = Column(String(50), default="completed")  # completed, reverted, failed
    records_affected = Column(Integer, default=0)
    initiated_by = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="transformations")
    user = relationship("User")
