from typing import Literal

from pydantic import BaseModel

EssayStatus = Literal["미작성", "작성 중", "초안 완료"]


class AnswerSlot(BaseModel):
    company: str  # 기업명. 어떤 기업도 안 쓰는 문항은 "공통"
    deadline: str  # 공통 슬롯은 ""
    content: str = ""
    status: EssayStatus = "미작성"


class Question(BaseModel):
    id: int
    tag: str  # 문항 유형: 지원동기·경험·역량·성장과정·포부·자기소개
    prompt: str
    char_limit: int
    slots: list[AnswerSlot]  # (기업 × 문항) 단위 답변. 기업마다 독립


class DraftRequest(BaseModel):
    question_id: int


class DraftResponse(BaseModel):
    question_id: int
    draft: str


class AnswerUpdate(BaseModel):
    company: str
    content: str
    status: EssayStatus
