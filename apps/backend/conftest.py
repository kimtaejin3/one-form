import pytest
from fastapi.testclient import TestClient

from app.core import mock as mock_module
from app.essays import repository as essays_repository
from app.main import app


@pytest.fixture(autouse=True)
def _no_delay(monkeypatch):
    # 목의 1초 sleep 제거 — 테스트를 밀리초로. 실제 로직/계약만 검증.
    monkeypatch.setattr(mock_module, "MOCK_DELAY_SECONDS", 0)


@pytest.fixture(autouse=True)
def _clean_answers():
    # essays _ANSWERS는 모듈-레벨 in-memory — 전 테스트에 걸쳐 격리(파일 무관).
    essays_repository._ANSWERS.clear()
    yield
    essays_repository._ANSWERS.clear()


@pytest.fixture
def client():
    return TestClient(app)
