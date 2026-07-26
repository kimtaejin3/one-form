"""profile 테이블 생성

Revision ID: 0003_profile
Revises: 0002_essays
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_profile"
down_revision = "0002_essays"
branch_labels = None
depends_on = None

_JSON_COLS = ["personal", "links", "educations", "awards", "languages",
              "certificates", "careers", "projects", "activities"]


def upgrade() -> None:
    op.create_table(
        "profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("registered", sa.Boolean(), nullable=False),
        *[sa.Column(c, postgresql.JSONB(), nullable=False) for c in _JSON_COLS],
    )


def downgrade() -> None:
    op.drop_table("profile")
