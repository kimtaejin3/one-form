"""job 테이블 생성

Revision ID: 0004_jobs
Revises: 0003_profile
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_jobs"
down_revision = "0003_profile"
branch_labels = None
depends_on = None

_TEXT_COLS = [
    "company", "domain", "role_category", "experience", "employment", "location",
    "title", "dday", "source", "description", "company_info", "match_reason",
]
_JSON_COLS = ["tags", "responsibilities", "requirements", "preferred"]


def upgrade() -> None:
    op.create_table(
        "job",
        sa.Column("id", sa.Integer(), primary_key=True),
        *[sa.Column(c, sa.Text(), nullable=False) for c in _TEXT_COLS],
        *[sa.Column(c, postgresql.JSONB(), nullable=False) for c in _JSON_COLS],
    )


def downgrade() -> None:
    op.drop_table("job")
