"""essays·companies 도메인 테이블 제거 — 자소서를 이력서 도메인으로 흡수

Revision ID: 0010_drop_essays_companies
Revises: 0009_drop_activities
"""
from alembic import op

revision = "0010_drop_essays_companies"
down_revision = "0009_drop_activities"
branch_labels = None
depends_on = None

# 자식 → 부모 순. CASCADE로 남은 FK까지 정리한다.
_TABLES = [
    "essay_answer",
    "essay_company",
    "essay_question",
    "intelligence_signal",
    "intelligence_source",
    "intelligence_job",
    "company_intelligence",
]


def upgrade() -> None:
    for t in _TABLES:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")


def downgrade() -> None:
    # 모델·도메인 코드가 함께 삭제돼 스키마를 되살릴 원본이 없다.
    # 되돌리려면 0009 시점의 코드로 체크아웃해 0002·0007을 다시 적용해야 한다.
    raise NotImplementedError("essays·companies 도메인은 코드와 함께 제거됨 — 되돌리기 불가")
