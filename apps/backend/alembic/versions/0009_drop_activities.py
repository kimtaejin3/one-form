"""activity 테이블 제거 — 활동 추천 기능 삭제

Revision ID: 0009_drop_activities
Revises: 0008_essay_char_limit
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009_drop_activities"
down_revision = "0008_essay_char_limit"
branch_labels = None
depends_on = None

# 되돌릴 때 0005_activities 와 동일 스키마로 복원한다.
_TEXT_COLS = ["name", "category", "organizer", "period", "dday", "expected_experience"]
_JSON_COLS = ["fills_gap", "connections"]


def upgrade() -> None:
    op.drop_table("activity")


def downgrade() -> None:
    op.create_table(
        "activity",
        sa.Column("id", sa.Integer(), primary_key=True),
        *[sa.Column(c, sa.Text(), nullable=False) for c in _TEXT_COLS],
        sa.Column("fit", sa.Integer(), nullable=False),
        *[sa.Column(c, postgresql.JSONB(), nullable=False) for c in _JSON_COLS],
    )
