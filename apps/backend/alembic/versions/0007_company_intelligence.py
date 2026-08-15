"""기업 인텔리전스 테이블 생성(기업·출처·신호·공고)

Revision ID: 0007_company_intel
Revises: 0006_notifications

매칭(계획서 §5.5)은 테이블을 두지 않는다 — 프로필이 바뀌면 즉시 낡는 파생 데이터라
조회 시점에 규칙 기반으로 계산한다(app/companies/matching.py).
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_company_intel"
down_revision = "0006_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_intelligence",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False, unique=True),
        sa.Column("domain", sa.Text(), nullable=False, server_default=""),
        # 사실 필드는 {text, source_ids} — 근거를 값과 같은 칸에 둔다
        sa.Column("summary", postgresql.JSONB(), nullable=True),
        sa.Column("stage", postgresql.JSONB(), nullable=True),
        sa.Column("business_areas", postgresql.JSONB(), nullable=False),
        sa.Column("products", postgresql.JSONB(), nullable=False),
        sa.Column("manual_urls", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("warnings", postgresql.JSONB(), nullable=False),
        sa.Column("needs_review", postgresql.JSONB(), nullable=False),
        sa.Column("last_analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_company_intelligence_normalized_name", "company_intelligence", ["normalized_name"]
    )

    op.create_table(
        "intelligence_source",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("company_intelligence.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False, server_default=""),
        sa.Column("publisher", sa.Text(), nullable=False, server_default=""),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("trust_level", sa.Text(), nullable=False),
        sa.Column("changed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("raw_text", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_intelligence_source_company_id", "intelligence_source", ["company_id"])

    op.create_table(
        "intelligence_signal",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("company_intelligence.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("signal_type", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_quote", sa.Text(), nullable=True),
        sa.Column("source_ids", postgresql.JSONB(), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_intelligence_signal_company_id", "intelligence_signal", ["company_id"])

    op.create_table(
        "intelligence_job",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("company_intelligence.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("intelligence_source.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *[
            sa.Column(c, sa.Text(), nullable=False, server_default="")
            for c in ("title", "role_category", "location", "employment", "deadline", "description")
        ],
        *[
            sa.Column(c, postgresql.JSONB(), nullable=False)
            for c in ("requirements", "preferred", "core_skills", "problem_types")
        ],
    )
    op.create_index("ix_intelligence_job_company_id", "intelligence_job", ["company_id"])


def downgrade() -> None:
    op.drop_table("intelligence_job")
    op.drop_table("intelligence_signal")
    op.drop_table("intelligence_source")
    op.drop_table("company_intelligence")
