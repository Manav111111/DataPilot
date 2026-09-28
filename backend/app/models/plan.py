import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class CollectionPlan(Base):
    __tablename__ = "collection_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    project_id = Column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    original_request = Column(Text, nullable=False)
    status = Column(String(50), default="ready_for_review", nullable=False)
    plan_data = Column(JSON, nullable=False)
    provider_metadata = Column(JSON, nullable=True)
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

    user = relationship("User", back_populates="collection_plans")
    project = relationship("Project", back_populates="collection_plans")

    __table_args__ = (
        Index("ix_collection_plans_project_id", "project_id"),
        Index("ix_collection_plans_user_id_status", "user_id", "status"),
    )
