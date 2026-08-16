"""profile 테이블 — 단일 행. 통째로 읽고 쓰므로 중첩은 전부 JSONB."""
from sqlalchemy import Boolean, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Profile(Base):
    __tablename__ = "profile"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    registered: Mapped[bool] = mapped_column(Boolean)
    personal: Mapped[dict] = mapped_column(JSONB)
    links: Mapped[list] = mapped_column(JSONB)
    educations: Mapped[list] = mapped_column(JSONB)
    awards: Mapped[list] = mapped_column(JSONB)
    languages: Mapped[list] = mapped_column(JSONB)
    certificates: Mapped[list] = mapped_column(JSONB)
    careers: Mapped[list] = mapped_column(JSONB)
    projects: Mapped[list] = mapped_column(JSONB)
    activities: Mapped[list] = mapped_column(JSONB)
    skill_groups: Mapped[list] = mapped_column(JSONB)
    open_source_contributions: Mapped[list] = mapped_column(JSONB)
