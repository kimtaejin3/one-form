"""자유양식 문항의 글자 수 제한을 선택값으로 변경

Revision ID: 0008_essay_char_limit
Revises: 0007_company_intel
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_essay_char_limit"
down_revision = "0007_company_intel"
branch_labels = None
depends_on = None

essay_question = sa.table(
    "essay_question",
    sa.column("id", sa.Integer()),
    sa.column("tag", sa.Text()),
    sa.column("prompt", sa.Text()),
    sa.column("char_limit", sa.Integer()),
)
essay_company = sa.table(
    "essay_company",
    sa.column("name", sa.String(80)),
    sa.column("deadline", sa.Text()),
    sa.column("question_ids", postgresql.JSONB()),
)

QUESTIONS = [
    {"id": 1, "tag": "지원동기", "prompt": "삼성전자를 지원한 이유와 입사 후 회사에서 이루고 싶은 꿈을 기술하십시오.", "char_limit": 700},
    {"id": 2, "tag": "성장과정", "prompt": "본인의 성장과정을 간략히 기술하되 현재의 자신에게 가장 큰 영향을 끼친 사건, 인물 등을 포함하여 기술하시기 바랍니다. (※작품 속 가상인물도 가능)", "char_limit": 1500},
    {"id": 3, "tag": "사회이슈", "prompt": "최근 사회 이슈 중 중요하다고 생각되는 한 가지를 선택하고 이에 관한 자신의 견해를 기술해 주시기 바랍니다.", "char_limit": 1000},
    {"id": 4, "tag": "직무역량", "prompt": "지원한 직무 관련 본인의 전문지식과 경험을 작성하고, 본인이 지원 직무에 적합한 사유를 삼성전자 제품과 서비스 사용 경험을 기반으로 기술하시기 바랍니다.", "char_limit": 1000},
    {"id": 5, "tag": "지원동기", "prompt": "현대오토에버의 해당 직무에 지원한 이유와 앞으로 현대오토에버에서 키워 나갈 커리어 계획을 작성해 주시기 바랍니다.", "char_limit": 1000},
    {"id": 6, "tag": "직무역량", "prompt": "지원 직무와 관련하여 어떠한 역량을(지식/기술 등) 강점으로 가지고 있는지, 그 역량을 갖추기 위해 무슨 노력과 경험을 했는지 구체적으로 작성해 주시기 바랍니다. (학내외 활동/프로젝트/교육 이수 과정 등 본인의 경험을 기반으로 작성해 주시기 바랍니다.)", "char_limit": 1500},
    {"id": 7, "tag": "지원동기", "prompt": "포스코DX에 지원하게 된 계기와 해당 분야에 관심을 가지게 된 이유를 구체적으로 설명해 주시길 바랍니다.", "char_limit": 600},
    {"id": 8, "tag": "직무역량", "prompt": "해당 분야에서 타인과 차별화될 수 있는 전문역량은 무엇인지 구체적으로 설명해 주시길 바랍니다.", "char_limit": 600},
    {"id": 9, "tag": "AI활용", "prompt": "생성형 AI 도구를 활용하여 생산성을 높이거나 더 나은 결과물을 만들어본 경험을 구체적으로 설명해 주시길 바랍니다.", "char_limit": 600},
    {"id": 10, "tag": "자유양식", "prompt": "이력서 및 자기소개서 (자유양식)", "char_limit": None},
]
COMPANIES = [
    {"name": "삼성전자", "deadline": "2025-09-03", "question_ids": [1, 2, 3, 4]},
    {"name": "현대오토에버", "deadline": "2025-08-04", "question_ids": [5, 6]},
    {"name": "포스코DX", "deadline": "2026-04-27", "question_ids": [7, 8, 9]},
    {"name": "오큘러스에쿼티파트너스", "deadline": "", "question_ids": [10]},
]


def upgrade() -> None:
    op.alter_column("essay_question", "char_limit", nullable=True)
    op.execute(essay_company.delete())
    op.execute(essay_question.delete())
    op.bulk_insert(essay_question, QUESTIONS)
    op.bulk_insert(essay_company, COMPANIES)


def downgrade() -> None:
    op.execute(essay_company.delete().where(essay_company.c.name == "오큘러스에쿼티파트너스"))
    op.execute(essay_question.delete().where(essay_question.c.char_limit.is_(None)))
    op.alter_column("essay_question", "char_limit", nullable=False)
