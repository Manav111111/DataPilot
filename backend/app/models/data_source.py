import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    collection_job_id = Column(
        String(36), ForeignKey("collection_jobs.id", ondelete="CASCADE"), nullable=False
    )
    source_url = Column(Text, nullable=False)
    canonical_url = Column(Text, nullable=True)
    domain = Column(String(255), nullable=True)
    page_title = Column(Text, nullable=True)
    source_type = Column(String(50), default="web", nullable=False)
    retrieval_status = Column(String(50), default="pending", nullable=False)
    retrieved_at = Column(DateTime(timezone=True), nullable=True)
    content_hash = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    search_query = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    dataset = relationship("Dataset", back_populates="sources")
    collection_job = relationship("CollectionJob", back_populates="data_sources")
    record_sources = relationship(
        "RecordSource", back_populates="data_source", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_data_sources_dataset_id", "dataset_id"),
        Index("ix_data_sources_collection_job_id", "collection_job_id"),
        Index("ix_data_sources_domain", "domain"),
        Index("ix_data_sources_retrieval_status", "retrieval_status"),
    )
