"""essays 테이블 — 문항·기업(참조) + 답변(유저 상태). JSONB 하이브리드."""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class EssayQuestion(Base):
    __tablename__ = "essay_question"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tag: Mapped[str] = mapped_column(Text)
    prompt: Mapped[str] = mapped_column(Text)
    char_limit: Mapped[int] = mapped_column(Integer)


class EssayCompany(Base):
    __tablename__ = "essay_company"
    name: Mapped[str] = mapped_column(String(80), primary_key=True)
    deadline: Mapped[str] = mapped_column(Text)
    question_ids: Mapped[list] = mapped_column(JSONB)


class EssayAnswer(Base):
    __tablename__ = "essay_answer"
    company: Mapped[str] = mapped_column(String(80), primary_key=True)
    question_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
