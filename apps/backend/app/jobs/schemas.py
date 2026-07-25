from pydantic import BaseModel


class Job(BaseModel):
    id: int
    company: str
    domain: str
    conditions: str
    title: str
    tags: list[str]
    dday: str
    source: str
    match_rate: int  # 0~100 — 프로필↔공고 임베딩 코사인(상위 K개는 LLM 보정)
    match_reason: str


class JobFeed(BaseModel):
    role: str
    total: int
    page: int
    size: int
    jobs: list[Job]
