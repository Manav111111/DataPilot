"""Create collection_plans table

Revision ID: 002_collection_plans
Revises: 001_initial
Create Date: 2026-09-28 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_collection_plans"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "collection_plans",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("original_request", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ready_for_review"),
        sa.Column("plan_data", sa.JSON(), nullable=False),
        sa.Column("provider_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_collection_plans_project_id", "collection_plans", ["project_id"])
    op.create_index("ix_collection_plans_user_id_status", "collection_plans", ["user_id", "status"])


def downgrade() -> None:
    op.drop_table("collection_plans")
