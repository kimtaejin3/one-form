from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.db import get_sessionmaker
from app.core.mock import mock
from app.essays.models import EssayAnswer, EssayCompany, EssayQuestion

# 공고별 실문항 스냅샷. 출처·회차는 docs/자소서-허브-실데이터-스냅샷.md.
_QUESTIONS = [
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

_COMPANIES = [
    {"name": "삼성전자", "deadline": "2025-09-03", "question_ids": [1, 2, 3, 4]},
    {"name": "현대오토에버", "deadline": "2025-08-04", "question_ids": [5, 6]},
    {"name": "포스코DX", "deadline": "2026-04-27", "question_ids": [7, 8, 9]},
    {"name": "오큘러스에쿼티파트너스", "deadline": "", "question_ids": [10]},
]

# ponytail: in-memory 저장 — 서버 재시작 시 소실. DB 도입 시 이 모듈만 교체(router/schemas 불변).
_ANSWERS: dict[tuple[str, int], dict] = {}


async def _load_ref() -> tuple[list[dict], list[dict]]:
    """문항·기업 참조 — DB 있으면 DB, 없으면 목."""
    sm = get_sessionmaker()
    if sm is None:
        return _QUESTIONS, _COMPANIES
    async with sm() as s:
        qs = (await s.execute(select(EssayQuestion).order_by(EssayQuestion.id))).scalars().all()
        cs = (await s.execute(select(EssayCompany))).scalars().all()
        if not qs and not cs:  # DB 떠 있지만 미시드 → 목 폴백(다른 도메인과 동일 불변식)
            return _QUESTIONS, _COMPANIES
        questions = [{"id": q.id, "tag": q.tag, "prompt": q.prompt, "char_limit": q.char_limit} for q in qs]
        companies = [{"name": c.name, "deadline": c.deadline, "question_ids": c.question_ids} for c in cs]
        # 목 _COMPANIES 큐레이션 순서로 정렬 — DB엔 순서 정보가 없어 목 리스트 순서로 파리티 맞춤.
        _order = {c["name"]: i for i, c in enumerate(_COMPANIES)}
        companies.sort(key=lambda c: _order.get(c["name"], len(_order)))
        return questions, companies


async def _load_answers() -> dict:
    sm = get_sessionmaker()
    if sm is None:
        return _ANSWERS
    async with sm() as s:
        rows = (await s.execute(select(EssayAnswer))).scalars().all()
        return {(r.company, r.question_id): {"content": r.content, "status": r.status} for r in rows}


def _slots(question_id: int, companies: list[dict], answers: dict) -> list[dict]:
    used_by = [c for c in companies if question_id in c["question_ids"]]
    if not used_by:
        used_by = [{"name": "공통", "deadline": ""}]
    return [
        {
            "company": c["name"],
            "deadline": c["deadline"],
            **answers.get((c["name"], question_id), {"content": "", "status": "미작성"}),
        }
        for c in used_by
    ]


async def list_questions():
    questions, companies = await _load_ref()
    answers = await _load_answers()
    return [{**q, "slots": _slots(q["id"], companies, answers)} for q in questions]


async def save_answer(question_id: int, company: str, content: str, status: str):
    questions, companies = await _load_ref()
    answers = await _load_answers()
    question = next((q for q in questions if q["id"] == question_id), None)
    if question is None or company not in {s["company"] for s in _slots(question_id, companies, answers)}:
        raise KeyError((company, question_id))
    sm = get_sessionmaker()
    if sm is None:
        _ANSWERS[(company, question_id)] = {"content": content, "status": status}
    else:
        async with sm() as s:
            stmt = pg_insert(EssayAnswer).values(
                company=company, question_id=question_id, content=content, status=status
            ).on_conflict_do_update(
                index_elements=["company", "question_id"],
                set_={"content": content, "status": status, "updated_at": func.now()},
            )
            await s.execute(stmt)
            await s.commit()
    answers = await _load_answers()
    return {**question, "slots": _slots(question_id, companies, answers)}


async def generate_draft(question_id: int):
    return await mock({
        "question_id": question_id,
        "draft": "[AI 초안] 지난해 교내 해커톤에서 실시간 협업 노트 서비스를 개발하며 CRDT 동기화라는 낯선 문제를 24시간 안에 풀어야 했습니다. 문서를 뒤지는 대신 실패 케이스를 좁혀가는 실험을 반복했고, 결국 안정적인 동시 편집을 구현해 대상을 받았습니다. 이 문제 해결 방식은 실시간 데이터 처리 과제에 그대로 기여할 수 있는 역량이라 확신합니다.",
    })
