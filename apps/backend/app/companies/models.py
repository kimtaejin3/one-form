"""기업 인텔리전스 테이블 — 기업/출처/신호.

# ponytail: enum은 Text 컬럼으로. Postgres enum 타입은 값 추가마다 마이그레이션이 필요한데,
#   signal_type·kind는 아직 늘어난다 — 검증은 Pydantic이 이미 한다.
# ponytail: intelligence_job/intelligence_match(계획서 §5.4·§5.5)는 Phase 2·3에서 추가한다.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Company(Base):
    __tablename__ = "company_intelligence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text)
    normalized_name: Mapped[str] = mapped_column(Text, unique=True, index=True)
    domain: Mapped[str] = mapped_column(Text, default="")
    # 사실 필드는 {text, source_ids} 형태라 전부 JSONB — 근거를 값과 떼어놓지 않는다.
    summary: Mapped[dict | None] = mapped_column(JSONB)
    stage: Mapped[dict | None] = mapped_column(JSONB)
    business_areas: Mapped[list] = mapped_column(JSONB, default=list)
    products: Mapped[list] = mapped_column(JSONB, default=list)
    # 사용자가 등록한 공고 URL. 수집이 실패해도 남아야 다음 refresh에서 다시 시도한다.
    manual_urls: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(Text)
    warnings: Mapped[list] = mapped_column(JSONB, default=list)
    needs_review: Mapped[list] = mapped_column(JSONB, default=list)
    last_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CompanySource(Base):
    __tablename__ = "intelligence_source"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("company_intelligence.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, default="")
    publisher: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[str] = mapped_column(Text)
    trust_level: Mapped[str] = mapped_column(Text)
    changed: Mapped[bool] = mapped_column(Boolean, default=False)
    # 인용 검증·재분석용 정제 텍스트. 개인정보·원본 HTML은 저장하지 않는다(계획서 §5.2).
    raw_text: Mapped[str] = mapped_column(Text, default="")


class CompanyJobRow(Base):
    """공고/JD 구조화 결과(계획서 §5.4). 원문 공고 source 하나에 1:1로 붙는다."""

    __tablename__ = "intelligence_job"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("company_intelligence.id", ondelete="CASCADE"), index=True
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("intelligence_source.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(Text, default="")
    role_category: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(Text, default="")
    employment: Mapped[str] = mapped_column(Text, default="")
    deadline: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    requirements: Mapped[list] = mapped_column(JSONB, default=list)
    preferred: Mapped[list] = mapped_column(JSONB, default=list)
    core_skills: Mapped[list] = mapped_column(JSONB, default=list)
    problem_types: Mapped[list] = mapped_column(JSONB, default=list)


class CompanySignal(Base):
    __tablename__ = "intelligence_signal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("company_intelligence.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(Text)
    detail: Mapped[str] = mapped_column(Text)
    signal_type: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    evidence_quote: Mapped[str | None] = mapped_column(Text)
    source_ids: Mapped[list] = mapped_column(JSONB)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
