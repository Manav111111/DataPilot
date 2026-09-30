"""Create data collection engine tables

Revision ID: 003_data_collection_engine
Revises: 002_collection_plans
Create Date: 2026-09-28 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_data_collection_engine"
down_revision: Union[str, None] = "002_collection_plans"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. collection_jobs table
    op.create_table(
        "collection_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("plan_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("current_stage", sa.String(length=50), nullable=False, server_default="initializing"),
        sa.Column("progress_percentage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_queries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_queries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_sources", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_sources", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_extracted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_saved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["collection_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_collection_jobs_project_id", "collection_jobs", ["project_id"])
    op.create_index("ix_collection_jobs_user_id_status", "collection_jobs", ["user_id", "status"])
    op.create_index("ix_collection_jobs_dataset_id", "collection_jobs", ["dataset_id"])
    op.create_index("ix_collection_jobs_plan_id", "collection_jobs", ["plan_id"])

    # 2. dataset_records table
    op.create_table(
        "dataset_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("record_data", sa.JSON(), nullable=False),
        sa.Column("normalized_data", sa.JSON(), nullable=False),
        sa.Column("record_hash", sa.String(length=64), nullable=True),
        sa.Column("validation_status", sa.String(length=50), nullable=False, server_default="valid"),
        sa.Column("validation_errors", sa.JSON(), nullable=True),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dataset_records_dataset_id", "dataset_records", ["dataset_id"])
    op.create_index("ix_dataset_records_status", "dataset_records", ["dataset_id", "validation_status"])
    op.create_index("ix_dataset_records_hash", "dataset_records", ["dataset_id", "record_hash"])

    # 3. data_sources table
    op.create_table(
        "data_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("collection_job_id", sa.String(length=36), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=True),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("page_title", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="web"),
        sa.Column("retrieval_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("search_query", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["collection_job_id"], ["collection_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_sources_dataset_id", "data_sources", ["dataset_id"])
    op.create_index("ix_data_sources_collection_job_id", "data_sources", ["collection_job_id"])
    op.create_index("ix_data_sources_domain", "data_sources", ["domain"])
    op.create_index("ix_data_sources_retrieval_status", "data_sources", ["retrieval_status"])

    # 4. record_sources table
    op.create_table(
        "record_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_record_id", sa.String(length=36), nullable=False),
        sa.Column("data_source_id", sa.String(length=36), nullable=False),
        sa.Column("evidence_excerpt", sa.Text(), nullable=True),
        sa.Column("evidence_field", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_record_id"], ["dataset_records.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["data_source_id"], ["data_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_record_sources_record_id", "record_sources", ["dataset_record_id"])
    op.create_index("ix_record_sources_source_id", "record_sources", ["data_source_id"])
    op.create_index("ix_record_sources_field", "record_sources", ["evidence_field"])

    # 5. collection_job_events table
    op.create_table(
        "collection_job_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("collection_job_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("event_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["collection_job_id"], ["collection_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_events_job_id_created", "collection_job_events", ["collection_job_id", "created_at"])
    op.create_index("ix_job_events_type", "collection_job_events", ["event_type"])


def downgrade() -> None:
    op.drop_table("collection_job_events")
    op.drop_table("record_sources")
    op.drop_table("data_sources")
    op.drop_table("dataset_records")
    op.drop_table("collection_jobs")
