"""Create data quality, analytics, transformations, versions, and export tables

Revision ID: 004_data_quality_and_analytics
Revises: 003_data_collection_engine
Create Date: 2026-09-28 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_data_quality_and_analytics"
down_revision: Union[str, None] = "003_data_collection_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. dataset_versions
    op.create_table(
        "dataset_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("change_type", sa.String(length=50), nullable=False, server_default="edit"),
        sa.Column("change_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("schema_snapshot", sa.JSON(), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("snapshot_data", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dataset_versions_dataset_id", "dataset_versions", ["dataset_id"])

    # 2. dataset_quality_reports
    op.create_table(
        "dataset_quality_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("version_id", sa.String(length=36), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("dimension_scores", sa.JSON(), nullable=False),
        sa.Column("report_data", sa.JSON(), nullable=False),
        sa.Column("scoring_method_version", sa.String(length=50), nullable=False, server_default="v1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["version_id"], ["dataset_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dataset_quality_reports_dataset_id", "dataset_quality_reports", ["dataset_id"])

    # 3. dataset_transformations
    op.create_table(
        "dataset_transformations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("operation_type", sa.String(length=100), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="completed"),
        sa.Column("records_affected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("initiated_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["initiated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dataset_transformations_dataset_id", "dataset_transformations", ["dataset_id"])

    # 4. dataset_charts
    op.create_table(
        "dataset_charts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("chart_name", sa.String(length=255), nullable=False),
        sa.Column("chart_type", sa.String(length=50), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dataset_charts_dataset_id", "dataset_charts", ["dataset_id"])

    # 5. dataset_merge_history
    op.create_table(
        "dataset_merge_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("retained_record_id", sa.String(length=36), nullable=False),
        sa.Column("merged_record_ids", sa.JSON(), nullable=False),
        sa.Column("merge_configuration", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["retained_record_id"], ["dataset_records.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dataset_merge_history_dataset_id", "dataset_merge_history", ["dataset_id"])

    # 6. dataset_exports
    op.create_table(
        "dataset_exports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("export_configuration", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="completed"),
        sa.Column("file_reference", sa.String(length=500), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("record_count", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dataset_exports_dataset_id", "dataset_exports", ["dataset_id"])


def downgrade() -> None:
    op.drop_table("dataset_exports")
    op.drop_table("dataset_merge_history")
    op.drop_table("dataset_charts")
    op.drop_table("dataset_transformations")
    op.drop_table("dataset_quality_reports")
    op.drop_table("dataset_versions")
