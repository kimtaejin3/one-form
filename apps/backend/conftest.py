import pytest
from fastapi.testclient import TestClient

from app.core import mock as mock_module
from app.main import app


@pytest.fixture(autouse=True)
def _no_delay(monkeypatch):
    # 목의 1초 sleep 제거 — 테스트를 밀리초로. 실제 로직/계약만 검증.
    monkeypatch.setattr(mock_module, "MOCK_DELAY_SECONDS", 0)


@pytest.fixture
def client():
    return TestClient(app)
