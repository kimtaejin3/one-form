from pydantic import BaseModel


class Essay(BaseModel):
    id: int
    company: str
    question: str
    char_limit: int
    deadline: str
    status: str


class DraftRequest(BaseModel):
    essay_id: int
