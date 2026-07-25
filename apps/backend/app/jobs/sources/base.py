"""JobSource 포트. 어댑터는 조건(query)으로 공고를 가져와 내부 dict 형태로 정규화한다.

내부 형태(응답 모델 아님 — OpenAPI를 더럽히지 않게 dict로 둔다):
    id, company, domain, role_category, title, tags, experience,
    employment, location, dday, source, match_reason
"""
from typing import Protocol

# query 키: role·experience·employment·location (빈 문자열이면 필터 없음)


class JobSource(Protocol):
    async def fetch(self, query: dict) -> list[dict]: ...


def matches(job: dict, query: dict) -> bool:
    """실 API가 필터를 못 거는 경우를 위한 공통 후처리 필터."""
    return (
        (not query.get("role") or job["role_category"] == query["role"])
        and (not query.get("experience") or job["experience"] == query["experience"])
        and (not query.get("employment") or job["employment"] == query["employment"])
        and (not query.get("location") or job["location"] == query["location"])
    )
