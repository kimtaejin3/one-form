"""잡코리아 제휴 API 어댑터. JOBKOREA_API_KEY가 있을 때만 활성.

# ponytail: 엔드포인트·응답 필드는 제휴 계약 문서 기준으로 확정해야 한다(키 발급 시 검증).
"""
from app.core.config import settings
from app.jobs.sources.base import matches

URL = "https://api.jobkorea.co.kr/partner/v1/recruits"


def _normalize(raw: dict, index: int) -> dict:
    return {
        "id": int(raw.get("id") or index + 1),
        "company": raw.get("companyName", ""),
        "domain": raw.get("companyHomepage", ""),
        "role_category": raw.get("jobCategory", ""),
        "title": raw.get("title", ""),
        "tags": raw.get("keywords", []),
        "experience": raw.get("careerType", ""),
        "employment": raw.get("employmentType", ""),
        "location": raw.get("location", ""),
        "dday": raw.get("closeDate", ""),
        "source": "잡코리아",
        "match_reason": "",
    }


class JobkoreaSource:
    def __init__(self, api_key: str):
        self._api_key = api_key

    async def fetch(self, query: dict) -> list[dict]:
        import httpx  # lazy

        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.get(
                URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                params={
                    "keyword": query.get("role", ""),
                    "location": query.get("location", ""),
                    "size": 100,
                },
            )
            res.raise_for_status()
            raw = res.json().get("items", [])
        jobs = [_normalize(j, i) for i, j in enumerate(raw)]
        return [j for j in jobs if matches(j, query)]


def get_source() -> JobkoreaSource | None:
    return JobkoreaSource(settings.JOBKOREA_API_KEY) if settings.JOBKOREA_API_KEY else None
