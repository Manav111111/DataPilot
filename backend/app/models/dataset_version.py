import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number = Column(Integer, nullable=False)
    change_type = Column(String(50), default="edit")  # initial, cleaning, transformation, edit, merge, bulk_delete, restore
    change_summary = Column(Text, nullable=False, default="")
    schema_snapshot = Column(JSON, nullable=False, default=dict)
    record_count = Column(Integer, default=0)
    snapshot_data = Column(JSON, nullable=False, default=list)  # records snapshot for safe rollback
    created_by = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    dataset = relationship("Dataset", back_populates="versions")
    user = relationship("User")
