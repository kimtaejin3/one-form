import pytest
from fastapi.testclient import TestClient

from app.core import mock as mock_module
from app.core.config import settings
from app.essays import repository as essays_repository
from app.main import app

_API_KEYS = (
    "SARAMIN_API_KEY", "JOBKOREA_API_KEY", "WANTED_API_KEY",
    "VOYAGE_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
)


@pytest.fixture(autouse=True)
def _no_delay(monkeypatch):
    # 목의 1초 sleep 제거 — 테스트를 밀리초로. 실제 로직/계약만 검증.
    monkeypatch.setattr(mock_module, "MOCK_DELAY_SECONDS", 0)


@pytest.fixture(autouse=True)
def _no_live_keys(monkeypatch):
    # 로컬 .env의 실 API 키가 새어들면 테스트가 실제 API를 호출한다 — 전부 비워 목으로 격리.
    # 게이팅 테스트는 각자 필요한 키를 이 뒤에 monkeypatch로 다시 설정한다.
    for key in _API_KEYS:
        monkeypatch.setattr(settings, key, None)
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", None)  # 임베더도 자동→목으로
    monkeypatch.setattr(settings, "DATABASE_URL", None)  # 캐시도 인메모리 폴백으로


@pytest.fixture(autouse=True)
def _clean_answers():
    # essays _ANSWERS는 모듈-레벨 in-memory — 전 테스트에 걸쳐 격리(파일 무관).
    essays_repository._ANSWERS.clear()
    yield
    essays_repository._ANSWERS.clear()


class _NetworkBlocked(BaseException):
    """service._collect의 except Exception에 삼켜지지 않도록 BaseException을 상속한다."""


@pytest.fixture(autouse=True)
def _no_outbound_fetch(monkeypatch):
    # 테스트는 실제 사이트를 부르지 않는다(계획서 §10) — provider를 목으로 주입할 것.
    from app.companies.sources import base as sources_base

    async def _blocked(url, *args, **kwargs):
        # SSRF 가드는 그대로 태운다 — 차단돼야 할 URL은 여기서 BlockedUrlError로 끝나고,
        # 통과한 URL만 "네트워크 쓰려 했다"로 잡힌다.
        await sources_base.assert_public_url(url)
        raise _NetworkBlocked(f"테스트에서 외부 URL 수집을 시도했습니다: {url}")

    monkeypatch.setattr(sources_base, "fetch", _blocked)


@pytest.fixture(autouse=True)
def _clean_companies():
    # 기업 인텔리전스 _MEM/_LOCKS도 모듈-레벨 — 테스트 간 격리.
    from app.companies import repository as companies_repository
    from app.companies import service as companies_service

    companies_repository._MEM.clear()
    companies_service._LOCKS.clear()
    yield
    companies_repository._MEM.clear()
    companies_service._LOCKS.clear()


@pytest.fixture(autouse=True)
def _clean_cache():
    # refine 캐시 _MEM은 모듈-레벨 — 테스트 간 격리.
    from app.jobs import cache
    cache._MEM.clear()
    yield
    cache._MEM.clear()


@pytest.fixture
def client():
    return TestClient(app)
