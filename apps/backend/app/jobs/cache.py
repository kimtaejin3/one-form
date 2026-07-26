"""refine 결과 캐시. DATABASE_URL 있으면 Postgres, 없으면 _MEM 폴백.

# ponytail: 키가 content 해시라 무효화 로직 없음 — 프로필·공고·모델이 바뀌면 새 키(미스)로
#   자동 재생성. 옛 행은 무해하게 남는다(축출은 후속).
# ponytail: DB 오류는 미스로 강등 — 캐시는 최적화지 필수 경로가 아니다.
"""
import hashlib
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, get_sessionmaker

# 폴백 저장소(프로세스 한정). DATABASE_URL 없을 때만 쓰인다.
_MEM: dict[str, tuple[int, str]] = {}


class MatchCache(Base):
    __tablename__ = "match_cache"

    cache_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    rate: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


def model_id(llm) -> str:
    return f"{type(llm).__name__}:{getattr(llm, 'MODEL', '')}"


def cache_key(model_id: str, profile_text: str, job_text: str) -> str:
    raw = f"{model_id}|{profile_text}|{job_text}".encode()
    return hashlib.blake2b(raw, digest_size=16).hexdigest()  # 32자 hex


async def get(key: str) -> tuple[int, str] | None:
    sm = get_sessionmaker()
    if sm is None:
        return _MEM.get(key)
    try:
        async with sm() as session:
            row = await session.get(MatchCache, key)
            return (row.rate, row.reason) if row else None
    except Exception:
        return None  # 미스로 강등 — 피드는 재계산으로 계속


async def set(key: str, rate: int, reason: str) -> None:
    sm = get_sessionmaker()
    if sm is None:
        _MEM[key] = (rate, reason)
        return
    try:
        async with sm() as session:
            stmt = (
                pg_insert(MatchCache)
                .values(cache_key=key, rate=rate, reason=reason)
                .on_conflict_do_nothing(index_elements=["cache_key"])
            )
            await session.execute(stmt)
            await session.commit()
    except Exception:
        pass  # 저장 실패는 조용히 — 다음 요청에 재계산
