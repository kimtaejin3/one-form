from app.core import db
from app.core.config import settings


def test_no_sessionmaker_without_url(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", None)
    assert db.get_sessionmaker() is None


def test_sessionmaker_built_when_url_present(monkeypatch):
    # 실제 연결은 안 하고 세션메이커 객체 생성만 확인(asyncpg 드라이버 파싱까지).
    monkeypatch.setattr(
        settings, "DATABASE_URL", "postgresql+asyncpg://u@localhost/x"
    )
    sm = db.get_sessionmaker()
    assert sm is not None
