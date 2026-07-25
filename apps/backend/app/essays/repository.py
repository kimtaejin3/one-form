from app.core.mock import mock

# 유니크 문항 풀. prompt의 {회사}는 기업 맥락에서 회사명으로 치환(치환은 프론트 표시 레벨).
_QUESTIONS = [
    {"id": 1, "tag": "지원동기", "prompt": "{회사}에 지원한 이유와 입사 후 이루고 싶은 목표를 구체적으로 서술하시오.", "char_limit": 700},
    {"id": 2, "tag": "지원동기", "prompt": "{회사}의 서비스 중 개선하고 싶은 것과 그 이유는 무엇입니까?", "char_limit": 800},
    {"id": 3, "tag": "경험", "prompt": "본인이 주도적으로 문제를 해결한 경험을 서술하시오.", "char_limit": 1000},
    {"id": 4, "tag": "경험", "prompt": "팀으로 협업하며 갈등을 겪었던 경험과 이를 해결한 과정을 서술하시오.", "char_limit": 800},
    {"id": 5, "tag": "경험", "prompt": "새로운 목표를 세우고 이를 달성하기 위해 끈기 있게 노력했던 경험을 서술하시오.", "char_limit": 1000},
    {"id": 6, "tag": "역량", "prompt": "지원 직무에 필요한 역량을 갖추기 위해 노력한 과정을 서술하시오.", "char_limit": 1500},
    {"id": 7, "tag": "역량", "prompt": "지원 분야와 관련해 본인이 갖춘 전문성을 사례와 함께 기술하시오.", "char_limit": 1000},
    {"id": 8, "tag": "성장과정", "prompt": "본인의 성장과정에서 가장 큰 영향을 준 사건과 그로 인해 변화한 점을 서술하시오.", "char_limit": 1500},
    {"id": 9, "tag": "포부", "prompt": "입사 후 10년간의 커리어 계획과 {회사}에 기여할 수 있는 바를 서술하시오.", "char_limit": 1200},
    {"id": 10, "tag": "자기소개", "prompt": "본인을 한 문장으로 소개하고, 그렇게 표현한 이유를 경험에 기반해 서술하시오.", "char_limit": 500},
    {"id": 11, "tag": "역량", "prompt": "글로벌 환경에서 일하기 위해 준비해온 것과 앞으로의 계획을 서술하시오.", "char_limit": 1000},
    {"id": 12, "tag": "포부", "prompt": "본인이 생각하는 좋은 개발 문화란 무엇이며, 그것을 위해 어떤 기여를 할 수 있습니까?", "char_limit": 800},
]

# 기업 → 문항 참조. 여러 기업이 같은 문항 id를 공유한다(답변 재사용).
# 어떤 기업도 참조하지 않는 문항(10·12) = 공통/재사용 전용.
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
_ANSWERS: dict[int, dict] = {}


def _merged(question: dict) -> dict:
    answer = _ANSWERS.get(question["id"], {"content": "", "status": "미작성"})
    return {
        **question,
        "answer": answer["content"],
        "status": answer["status"],
        "companies": [
            {"name": c["name"], "deadline": c["deadline"]}
            for c in _COMPANIES
            if question["id"] in c["question_ids"]
        ],
    }


async def list_questions():
    return await mock([_merged(q) for q in _QUESTIONS])


async def save_answer(question_id: int, content: str, status: str):
    question = next((q for q in _QUESTIONS if q["id"] == question_id), None)
    if question is None:
        raise KeyError(question_id)
    _ANSWERS[question_id] = {"content": content, "status": status}
    return await mock(_merged(question))


async def generate_draft(question_id: int):
    return await mock({
        "question_id": question_id,
        "draft": "[AI 초안] 지난해 교내 해커톤에서 실시간 협업 노트 서비스를 개발하며 CRDT 동기화라는 낯선 문제를 24시간 안에 풀어야 했습니다. 문서를 뒤지는 대신 실패 케이스를 좁혀가는 실험을 반복했고, 결국 안정적인 동시 편집을 구현해 대상을 받았습니다. 이 문제 해결 방식은 {회사}가 집중하는 실시간 데이터 처리 과제에 그대로 기여할 수 있는 역량이라 확신합니다.",
    })
