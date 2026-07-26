"""essays 테이블 3개 생성

Revision ID: 0002_essays
Revises: 0001_match_cache
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_essays"
down_revision = "0001_match_cache"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "essay_question",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tag", sa.Text(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("char_limit", sa.Integer(), nullable=False),
    )
    op.create_table(
        "essay_company",
        sa.Column("name", sa.String(length=80), primary_key=True),
        sa.Column("deadline", sa.Text(), nullable=False),
        sa.Column("question_ids", postgresql.JSONB(), nullable=False),
    )
    op.create_table(
        "essay_answer",
        sa.Column("company", sa.String(length=80), primary_key=True),
        sa.Column("question_id", sa.Integer(), primary_key=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("essay_answer")
    op.drop_table("essay_company")
    op.drop_table("essay_question")
