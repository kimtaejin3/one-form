"""목 소스 — 기존 repository의 공고 100건을 재사용(중복 생성 금지)."""
from app.core.mock import mock
from app.jobs import repository
from app.jobs.sources.base import matches


class MockJobSource:
    async def fetch(self, query: dict) -> list[dict]:
        jobs = [j for j in await repository.all_jobs() if matches(j, query)]
        return await mock(jobs)  # 목 단계의 1초 지연 유지(테스트에선 0)


def get_source() -> MockJobSource:
    return MockJobSource()
