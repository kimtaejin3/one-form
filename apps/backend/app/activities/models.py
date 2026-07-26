from sqlalchemy import Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Activity(Base):
    __tablename__ = "activity"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text)
    organizer: Mapped[str] = mapped_column(Text)
    period: Mapped[str] = mapped_column(Text)
    dday: Mapped[str] = mapped_column(Text)
    fit: Mapped[int] = mapped_column(Integer)
    expected_experience: Mapped[str] = mapped_column(Text)
    fills_gap: Mapped[list] = mapped_column(JSONB)
    connections: Mapped[list] = mapped_column(JSONB)
