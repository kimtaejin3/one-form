"""async DB 엔진·세션. DATABASE_URL 없으면 세션메이커 None → 캐시가 인메모리 폴백.

# ponytail: URL별 지연 싱글턴 — 모듈 로드 시점이 아니라 호출 시점의 settings를 본다.
#   테스트가 monkeypatch로 URL을 켰다 껐다 해도 반영된다.
"""
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker | None = None
_url: str | None = None


def get_sessionmaker() -> async_sessionmaker | None:
    global _engine, _sessionmaker, _url
    url = settings.DATABASE_URL
    if url != _url:
        _url = url
        _engine = create_async_engine(url) if url else None
        _sessionmaker = (
            async_sessionmaker(_engine, expire_on_commit=False) if _engine else None
        )
    return _sessionmaker
