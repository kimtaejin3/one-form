"""프로필 이력서 v3 항목 추가

Revision ID: 0009_profile_resume_v3
Revises: 0008_essay_char_limit
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009_profile_resume_v3"
down_revision = "0008_essay_char_limit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profile", sa.Column("skill_groups", postgresql.JSONB(), nullable=False, server_default="[]"))
    op.add_column("profile", sa.Column("open_source_contributions", postgresql.JSONB(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("profile", "open_source_contributions")
    op.drop_column("profile", "skill_groups")
