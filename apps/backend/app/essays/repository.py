from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.db import get_sessionmaker
from app.core.mock import mock
from app.essays.models import EssayAnswer, EssayCompany, EssayQuestion

# 유니크 문항 풀. prompt는 제네릭(회사명 없는 표현) — 답변에 회사명을 리터럴로 쓴다.
_QUESTIONS = [
    {"id": 1, "tag": "지원동기", "prompt": "지원한 이유와 입사 후 이루고 싶은 목표를 구체적으로 서술하시오.", "char_limit": 700},
    {"id": 2, "tag": "지원동기", "prompt": "지원한 회사의 서비스 중 개선하고 싶은 것과 그 이유는 무엇입니까?", "char_limit": 800},
    {"id": 3, "tag": "경험", "prompt": "본인이 주도적으로 문제를 해결한 경험을 서술하시오.", "char_limit": 1000},
    {"id": 4, "tag": "경험", "prompt": "팀으로 협업하며 갈등을 겪었던 경험과 이를 해결한 과정을 서술하시오.", "char_limit": 800},
    {"id": 5, "tag": "경험", "prompt": "새로운 목표를 세우고 이를 달성하기 위해 끈기 있게 노력했던 경험을 서술하시오.", "char_limit": 1000},
    {"id": 6, "tag": "역량", "prompt": "지원 직무에 필요한 역량을 갖추기 위해 노력한 과정을 서술하시오.", "char_limit": 1500},
    {"id": 7, "tag": "역량", "prompt": "지원 분야와 관련해 본인이 갖춘 전문성을 사례와 함께 기술하시오.", "char_limit": 1000},
    {"id": 8, "tag": "성장과정", "prompt": "본인의 성장과정에서 가장 큰 영향을 준 사건과 그로 인해 변화한 점을 서술하시오.", "char_limit": 1500},
    {"id": 9, "tag": "포부", "prompt": "입사 후 10년간의 커리어 계획과 회사에 기여할 수 있는 바를 서술하시오.", "char_limit": 1200},
    {"id": 10, "tag": "자기소개", "prompt": "본인을 한 문장으로 소개하고, 그렇게 표현한 이유를 경험에 기반해 서술하시오.", "char_limit": 500},
    {"id": 11, "tag": "역량", "prompt": "글로벌 환경에서 일하기 위해 준비해온 것과 앞으로의 계획을 서술하시오.", "char_limit": 1000},
    {"id": 12, "tag": "포부", "prompt": "본인이 생각하는 좋은 개발 문화란 무엇이며, 그것을 위해 어떤 기여를 할 수 있습니까?", "char_limit": 800},
]

# 기업 → 문항 참조. 여러 기업이 같은 문항 id를 공유한다(문항은 유니크, 답변은 기업별로 별개).
# 어떤 기업도 참조하지 않는 문항(10·12) = 공통 슬롯 1개로 작성.
_COMPANIES = [
    {"name": "네이버", "deadline": "2026-07-28", "question_ids": [1, 3, 6]},
    {"name": "토스", "deadline": "2026-07-25", "question_ids": [3, 6, 9]},
    {"name": "카카오", "deadline": "2026-07-30", "question_ids": [2, 4, 8]},
    {"name": "삼성전자", "deadline": "2026-08-03", "question_ids": [1, 5, 8]},
    {"name": "SK하이닉스", "deadline": "2026-08-07", "question_ids": [5, 7]},
    {"name": "현대자동차", "deadline": "2026-07-31", "question_ids": [1, 7, 9]},
    {"name": "LG전자", "deadline": "2026-08-10", "question_ids": [4, 8]},
    {"name": "쿠팡", "deadline": "2026-08-05", "question_ids": [3, 9]},
    {"name": "당근", "deadline": "2026-07-29", "question_ids": [2, 11]},
    {"name": "라인", "deadline": "2026-08-14", "question_ids": [6, 11]},
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
        cs = (await s.execute(select(EssayCompany).order_by(EssayCompany.name))).scalars().all()
        questions = [{"id": q.id, "tag": q.tag, "prompt": q.prompt, "char_limit": q.char_limit} for q in qs]
        companies = [{"name": c.name, "deadline": c.deadline, "question_ids": c.question_ids} for c in cs]
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
