import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    row_count = Column(Integer, default=0, nullable=False)
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

    project = relationship("Project", back_populates="datasets")
    user = relationship("User", back_populates="datasets")
    collection_jobs = relationship(
        "CollectionJob", back_populates="dataset", cascade="all, delete-orphan"
    )
    records = relationship(
        "DatasetRecord", back_populates="dataset", cascade="all, delete-orphan"
    )
    sources = relationship(
        "DataSource", back_populates="dataset", cascade="all, delete-orphan"
    )
    quality_reports = relationship(
        "DatasetQualityReport", back_populates="dataset", cascade="all, delete-orphan"
    )
    transformations = relationship(
        "DatasetTransformation", back_populates="dataset", cascade="all, delete-orphan"
    )
    versions = relationship(
        "DatasetVersion", back_populates="dataset", cascade="all, delete-orphan"
    )
    charts = relationship(
        "DatasetChart", back_populates="dataset", cascade="all, delete-orphan"
    )
    merge_histories = relationship(
        "DatasetMergeHistory", back_populates="dataset", cascade="all, delete-orphan"
    )
    exports = relationship(
        "DatasetExport", back_populates="dataset", cascade="all, delete-orphan"
    )
    analysis_sessions = relationship(
        "AnalysisSession", back_populates="dataset", cascade="all, delete-orphan"
    )
    analysis_reports = relationship(
        "AnalysisReport", back_populates="dataset", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_datasets_user_id_status", "user_id", "status"),
        Index("ix_datasets_project_id", "project_id"),
    )

