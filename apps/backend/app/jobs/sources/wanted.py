"""원티드 오픈 API(https://openapi.wanted.jobs/) 어댑터. WANTED_API_KEY가 있을 때만 활성.

연차·스킬·직군·직무로 필터할 수 있어 조건 검색을 서버 쪽에 넘긴다.
# ponytail: 인증 헤더명·필터 파라미터명은 키 발급 후 실응답으로 확정해야 한다.
"""
from app.core.config import settings
from app.jobs.sources.base import matches

URL = "https://openapi.wanted.jobs/v1/jobs"


def _normalize(raw: dict, index: int) -> dict:
    company = raw.get("company", {})
    return {
        "id": int(raw.get("id") or index + 1),
        "company": company.get("name", ""),
        "domain": company.get("website", ""),
        "role_category": raw.get("job_group", ""),
        "title": raw.get("position", ""),
        "tags": raw.get("skills", []),
        "experience": raw.get("annual", ""),
        "employment": raw.get("employment_type", ""),
        "location": raw.get("location", ""),
        "dday": raw.get("due_time", ""),
        "source": "원티드",
        "match_reason": "",
    }


class WantedSource:
    def __init__(self, api_key: str):
        self._api_key = api_key

    async def fetch(self, query: dict) -> list[dict]:
        import httpx  # lazy

        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.get(
                URL,
                headers={"wanted-client-id": self._api_key},
                params={
                    "job": query.get("role", ""),
                    "annual": query.get("experience", ""),
                    "location": query.get("location", ""),
                    "limit": 100,
                },
            )
            res.raise_for_status()
            raw = res.json().get("data", [])
        jobs = [_normalize(j, i) for i, j in enumerate(raw)]
        return [j for j in jobs if matches(j, query)]


def get_source() -> WantedSource | None:
    return WantedSource(settings.WANTED_API_KEY) if settings.WANTED_API_KEY else None
