import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class CollectionJobEvent(Base):
    __tablename__ = "collection_job_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_job_id = Column(
        String(36), ForeignKey("collection_jobs.id", ondelete="CASCADE"), nullable=False
    )
    event_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    event_metadata = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    collection_job = relationship("CollectionJob", back_populates="events")

    __table_args__ = (
        Index("ix_job_events_job_id_created", "collection_job_id", "created_at"),
        Index("ix_job_events_type", "event_type"),
    )
