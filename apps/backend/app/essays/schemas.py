from typing import Literal

from pydantic import BaseModel

EssayStatus = Literal["미작성", "작성 중", "초안 완료"]


class Essay(BaseModel):
    id: int
    company: str
    tag: str  # 문항 유형: 지원동기·경험·역량·성장과정·포부
    question: str
    char_limit: int
    deadline: str
    status: EssayStatus
    answer: str = ""


class DraftRequest(BaseModel):
    essay_id: int


class DraftResponse(BaseModel):
    essay_id: int
    draft: str


class AnswerUpdate(BaseModel):
    content: str
    status: EssayStatus
