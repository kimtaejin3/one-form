from pydantic import BaseModel


class Essay(BaseModel):
    id: int
    company: str
    tag: str  # 문항 유형: 지원동기·경험·역량·성장과정·포부
    question: str
    char_limit: int
    deadline: str
    status: str


class DraftRequest(BaseModel):
    essay_id: int
