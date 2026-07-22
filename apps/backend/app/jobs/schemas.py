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
    match_reason: str


class JobFeed(BaseModel):
    role: str
    total: int
    page: int
    size: int
    jobs: list[Job]
