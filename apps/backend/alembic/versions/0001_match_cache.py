"""match_cache 테이블 생성

Revision ID: 0001_match_cache
Revises:
Create Date: 2026-07-26
"""
import sqlalchemy as sa
from alembic import op

revision = "0001_match_cache"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "match_cache",
        sa.Column("cache_key", sa.String(length=64), primary_key=True),
        sa.Column("rate", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("match_cache")
