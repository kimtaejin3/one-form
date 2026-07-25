from typing import Literal

from pydantic import BaseModel

EssayStatus = Literal["미작성", "작성 중", "초안 완료"]


class QuestionCompany(BaseModel):
    name: str
    deadline: str


class Question(BaseModel):
    id: int
    tag: str  # 문항 유형: 지원동기·경험·역량·성장과정·포부·자기소개
    prompt: str  # {회사} 토큰 포함 가능
    char_limit: int
    answer: str = ""
    status: EssayStatus = "미작성"
    companies: list[QuestionCompany]  # 이 문항을 쓰는 기업들. 빈 리스트 = 공통 문항


class DraftRequest(BaseModel):
    question_id: int


class DraftResponse(BaseModel):
    question_id: int
    draft: str


class AnswerUpdate(BaseModel):
    content: str
    status: EssayStatus
