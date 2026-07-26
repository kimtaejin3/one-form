"""notification 테이블 생성

Revision ID: 0006_notifications
Revises: 0005_activities
"""
import sqlalchemy as sa
from alembic import op

revision = "0006_notifications"
down_revision = "0005_activities"
branch_labels = None
depends_on = None

_TEXT_COLS = ["type", "title", "message", "time"]


def upgrade() -> None:
    op.create_table(
        "notification",
        sa.Column("id", sa.Integer(), primary_key=True),
        *[sa.Column(c, sa.Text(), nullable=False) for c in _TEXT_COLS],
        sa.Column("unread", sa.Boolean(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("notification")
