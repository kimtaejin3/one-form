"""사람인 공개 채용정보 API 어댑터. SARAMIN_API_KEY가 있을 때만 활성.

# ponytail: 응답 필드 매핑은 무료 키 발급 후 실응답으로 검증해야 한다(지금은 문서 기준 + .get 폴백).
"""
from app.core.config import settings
from app.jobs.sources.base import matches

URL = "https://oapi.saramin.co.kr/job-search"


def _normalize(raw: dict, index: int) -> dict:
    position = raw.get("position", {})
    company = raw.get("company", {}).get("detail", {})
    return {
        "id": int(raw.get("id") or index + 1),
        "company": company.get("name", ""),
        "domain": company.get("href", ""),
        "role_category": position.get("job-code", {}).get("name", ""),
        "title": position.get("title", ""),
        "tags": [k for k in position.get("keyword", "").split(",") if k],
        "experience": position.get("experience-level", {}).get("name", ""),
        "employment": position.get("job-type", {}).get("name", ""),
        "location": position.get("location", {}).get("name", ""),
        "dday": raw.get("expiration-timestamp", ""),
        "source": "사람인",
        "match_reason": "",
    }


class SaraminSource:
    def __init__(self, api_key: str):
        self._api_key = api_key

    async def fetch(self, query: dict) -> list[dict]:
        import httpx  # lazy — 키 없으면 이 경로 자체가 안 돈다

        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.get(
                URL,
                params={
                    "access-key": self._api_key,
                    "keywords": query.get("role", ""),
                    "loc_cd": query.get("location", ""),
                    "count": 100,
                },
            )
            res.raise_for_status()
            raw = res.json().get("jobs", {}).get("job", [])
        jobs = [_normalize(j, i) for i, j in enumerate(raw)]
        return [j for j in jobs if matches(j, query)]


def get_source() -> SaraminSource | None:
    return SaraminSource(settings.SARAMIN_API_KEY) if settings.SARAMIN_API_KEY else None
