import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class CollectionJob(Base):
    __tablename__ = "collection_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    project_id = Column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    plan_id = Column(
        String(36), ForeignKey("collection_plans.id", ondelete="CASCADE"), nullable=False
    )
    dataset_id = Column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(String(50), default="queued", nullable=False)
    current_stage = Column(String(50), default="initializing", nullable=False)
    progress_percentage = Column(Integer, default=0, nullable=False)
    total_queries = Column(Integer, default=0, nullable=False)
    completed_queries = Column(Integer, default=0, nullable=False)
    total_sources = Column(Integer, default=0, nullable=False)
    processed_sources = Column(Integer, default=0, nullable=False)
    records_extracted = Column(Integer, default=0, nullable=False)
    records_saved = Column(Integer, default=0, nullable=False)
    records_rejected = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
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

    user = relationship("User", back_populates="collection_jobs")
    project = relationship("Project", back_populates="collection_jobs")
    plan = relationship("CollectionPlan", back_populates="collection_jobs")
    dataset = relationship("Dataset", back_populates="collection_jobs")
    data_sources = relationship(
        "DataSource", back_populates="collection_job", cascade="all, delete-orphan"
    )
    events = relationship(
        "CollectionJobEvent", back_populates="collection_job", cascade="all, delete-orphan", order_by="CollectionJobEvent.created_at"
    )

    __table_args__ = (
        Index("ix_collection_jobs_project_id", "project_id"),
        Index("ix_collection_jobs_user_id_status", "user_id", "status"),
        Index("ix_collection_jobs_dataset_id", "dataset_id"),
        Index("ix_collection_jobs_plan_id", "plan_id"),
    )
