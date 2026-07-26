"""job 테이블 — 필터 필드는 컬럼, 중첩은 JSONB."""
from sqlalchemy import Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Job(Base):
    __tablename__ = "job"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[str] = mapped_column(Text)
    domain: Mapped[str] = mapped_column(Text)
    role_category: Mapped[str] = mapped_column(Text)   # 필터
    experience: Mapped[str] = mapped_column(Text)      # 필터
    employment: Mapped[str] = mapped_column(Text)      # 필터
    location: Mapped[str] = mapped_column(Text)        # 필터
    title: Mapped[str] = mapped_column(Text)
    dday: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    company_info: Mapped[str] = mapped_column(Text)
    match_reason: Mapped[str] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSONB)
    responsibilities: Mapped[list] = mapped_column(JSONB)
    requirements: Mapped[list] = mapped_column(JSONB)
    preferred: Mapped[list] = mapped_column(JSONB)
