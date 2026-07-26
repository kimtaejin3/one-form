"""activity 테이블 생성

Revision ID: 0005_activities
Revises: 0004_jobs
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_activities"
down_revision = "0004_jobs"
branch_labels = None
depends_on = None

_TEXT_COLS = ["name", "category", "organizer", "period", "dday", "expected_experience"]
_JSON_COLS = ["fills_gap", "connections"]


def upgrade() -> None:
    op.create_table(
        "activity",
        sa.Column("id", sa.Integer(), primary_key=True),
        *[sa.Column(c, sa.Text(), nullable=False) for c in _TEXT_COLS],
        sa.Column("fit", sa.Integer(), nullable=False),
        *[sa.Column(c, postgresql.JSONB(), nullable=False) for c in _JSON_COLS],
    )


def downgrade() -> None:
    op.drop_table("activity")
