from app.core.mock import mock

_ESSAYS = [
    {"id": 1, "company": "네이버", "tag": "경험", "question": "본인이 주도적으로 문제를 해결한 경험을 서술하시오.", "char_limit": 1000, "deadline": "2026-07-28", "status": "작성 중"},
    {"id": 2, "company": "토스", "tag": "역량", "question": "지원 직무에 필요한 역량을 갖추기 위해 노력한 과정을 서술하시오.", "char_limit": 1500, "deadline": "2026-07-25", "status": "초안 완료"},
    {"id": 3, "company": "카카오", "tag": "지원동기", "question": "카카오 서비스 중 개선하고 싶은 것과 그 이유는?", "char_limit": 800, "deadline": "2026-07-30", "status": "미작성"},
    {"id": 4, "company": "삼성전자", "tag": "지원동기", "question": "삼성전자를 지원한 이유와 입사 후 이루고 싶은 목표를 구체적으로 서술하시오.", "char_limit": 700, "deadline": "2026-08-03", "status": "미작성"},
    {"id": 5, "company": "삼성전자", "tag": "성장과정", "question": "본인의 성장과정에서 가장 큰 영향을 준 사건과 그로 인해 변화한 점을 서술하시오.", "char_limit": 1500, "deadline": "2026-08-03", "status": "미작성"},
    {"id": 6, "company": "SK하이닉스", "tag": "경험", "question": "새로운 목표를 세우고 이를 달성하기 위해 끈기 있게 노력했던 경험을 서술하시오.", "char_limit": 1000, "deadline": "2026-08-07", "status": "작성 중"},
    {"id": 7, "company": "현대자동차", "tag": "역량", "question": "지원 분야와 관련해 본인이 갖춘 전문성을 사례와 함께 기술하시오.", "char_limit": 1000, "deadline": "2026-07-31", "status": "미작성"},
    {"id": 8, "company": "LG전자", "tag": "경험", "question": "팀으로 협업하며 갈등을 겪었던 경험과 이를 해결한 과정을 서술하시오.", "char_limit": 800, "deadline": "2026-08-10", "status": "미작성"},
    {"id": 9, "company": "쿠팡", "tag": "포부", "question": "입사 후 10년간의 커리어 계획과 회사에 기여할 수 있는 바를 서술하시오.", "char_limit": 1200, "deadline": "2026-08-05", "status": "미작성"},
    {"id": 10, "company": "당근", "tag": "지원동기", "question": "당근의 프로덕트를 사용하며 느낀 점과 함께 지원 동기를 서술하시오.", "char_limit": 600, "deadline": "2026-07-29", "status": "작성 중"},
    {"id": 11, "company": "배달의민족", "tag": "성장과정", "question": "본인을 한 문장으로 소개하고, 그렇게 표현한 이유를 경험에 기반해 서술하시오.", "char_limit": 500, "deadline": "2026-08-12", "status": "미작성"},
    {"id": 12, "company": "라인", "tag": "포부", "question": "글로벌 환경에서 일하기 위해 준비해온 것과 앞으로의 계획을 서술하시오.", "char_limit": 1000, "deadline": "2026-08-14", "status": "미작성"},
]


async def list_essays():
    return await mock(_ESSAYS)


async def generate_draft(essay_id: int):
    return await mock({
        "essay_id": essay_id,
        "draft": "[AI 초안] 지난해 교내 해커톤에서 실시간 협업 노트 서비스를 개발하며 CRDT 동기화라는 낯선 문제를 24시간 안에 풀어야 했습니다. 문서를 뒤지는 대신 실패 케이스를 좁혀가는 실험을 반복했고, 결국 안정적인 동시 편집을 구현해 대상을 받았습니다. 이 문제 해결 방식은 귀사가 집중하는 실시간 데이터 처리 과제에 그대로 기여할 수 있는 역량이라 확신합니다.",
    })
