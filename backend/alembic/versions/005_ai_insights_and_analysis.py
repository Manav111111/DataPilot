"""Create AI insights, analysis sessions, messages, and reports tables

Revision ID: 005_ai_insights_and_analysis
Revises: 004_data_quality_and_analytics
Create Date: 2026-09-28 04:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005_ai_insights_and_analysis"
down_revision: Union[str, None] = "004_data_quality_and_analytics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. analysis_sessions
    op.create_table(
        "analysis_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False, server_default="Analysis Conversation"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_sessions_user_id", "analysis_sessions", ["user_id"])
    op.create_index("ix_analysis_sessions_project_id", "analysis_sessions", ["project_id"])
    op.create_index("ix_analysis_sessions_dataset_id", "analysis_sessions", ["dataset_id"])
    op.create_index("ix_analysis_sessions_user_dataset", "analysis_sessions", ["user_id", "dataset_id"])

    # 2. analysis_messages
    op.create_table(
        "analysis_messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("analytical_plan", sa.JSON(), nullable=True),
        sa.Column("execution_result", sa.JSON(), nullable=True),
        sa.Column("dataset_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["analysis_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_messages_session_id", "analysis_messages", ["session_id"])

    # 3. analysis_results
    op.create_table(
        "analysis_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=True),
        sa.Column("analysis_type", sa.String(length=50), nullable=False),
        sa.Column("structured_result", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("dataset_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["analysis_sessions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_results_dataset_id", "analysis_results", ["dataset_id"])
    op.create_index("ix_analysis_results_session_id", "analysis_results", ["session_id"])

    # 4. analysis_reports
    op.create_table(
        "analysis_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False, server_default="html"),
        sa.Column("report_data", sa.JSON(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("dataset_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_reports_dataset_id", "analysis_reports", ["dataset_id"])
    op.create_index("ix_analysis_reports_user_id", "analysis_reports", ["user_id"])


def downgrade() -> None:
    op.drop_table("analysis_reports")
    op.drop_table("analysis_results")
    op.drop_table("analysis_messages")
    op.drop_table("analysis_sessions")
