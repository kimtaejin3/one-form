from app.core.mock import mock

_ESSAYS = [
    {"id": 1, "company": "네이버", "question": "본인이 주도적으로 문제를 해결한 경험을 서술하시오.", "char_limit": 1000, "deadline": "2026-07-28", "status": "작성 중"},
    {"id": 2, "company": "토스", "question": "지원 직무에 필요한 역량을 갖추기 위해 노력한 과정을 서술하시오.", "char_limit": 1500, "deadline": "2026-07-25", "status": "초안 완료"},
    {"id": 3, "company": "카카오", "question": "카카오 서비스 중 개선하고 싶은 것과 그 이유는?", "char_limit": 800, "deadline": "2026-07-30", "status": "미작성"},
]


async def list_essays():
    return await mock(_ESSAYS)


async def generate_draft(essay_id: int):
    return await mock({
        "essay_id": essay_id,
        "draft": "[AI 초안] 지난해 교내 해커톤에서 실시간 협업 노트 서비스를 개발하며 CRDT 동기화라는 낯선 문제를 24시간 안에 풀어야 했습니다. 문서를 뒤지는 대신 실패 케이스를 좁혀가는 실험을 반복했고, 결국 안정적인 동시 편집을 구현해 대상을 받았습니다. 이 문제 해결 방식은 귀사가 집중하는 실시간 데이터 처리 과제에 그대로 기여할 수 있는 역량이라 확신합니다.",
    })
