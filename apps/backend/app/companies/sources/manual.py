"""사용자가 직접 넣은 URL(채용공고 등). 신뢰도는 user_provided.

스킴·주소 검증은 base.fetch 안의 assert_public_url이 한다 — 검증을 provider마다 두면
새 provider가 빠뜨린다(SSRF는 한 곳에서 막는다).
"""
from app.companies.schemas import SourceKind, TrustLevel
from app.companies.sources import base
from app.companies.sources.base import SourceDocument


class ManualUrlSource:
    name = "manual"

    async def collect(self, query: dict) -> list[SourceDocument]:
        docs = []
        for url in query.get("job_urls") or []:
            docs.append(
                await base.fetch(
                    url.strip(),
                    kind=SourceKind.job_posting,
                    trust_level=TrustLevel.user_provided,
                )
            )
        return docs
