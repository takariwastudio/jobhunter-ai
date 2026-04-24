"""add saved_jobs table

Revision ID: 001
Revises:
Create Date: 2026-04-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("salary_range", sa.String(), nullable=True),
        sa.Column("job_type", sa.String(), nullable=True),
        sa.Column("remote", sa.Boolean(), nullable=True),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("posted_date", sa.DateTime(), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("saved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_saved_jobs_user_id", "saved_jobs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_saved_jobs_user_id", table_name="saved_jobs")
    op.drop_table("saved_jobs")
