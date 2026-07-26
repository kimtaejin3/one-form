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


class MatchAnalysis(BaseModel):
    matched_skills: list[str]  # 요구 스킬 ∩ 프로필 스택
    missing_skills: list[str]  # 요구 스킬 − 프로필 스택


class JobDetail(Job):
    description: str
    responsibilities: list[str]
    requirements: list[str]
    preferred: list[str]
    company_info: str
    match_analysis: MatchAnalysis


class JobFeed(BaseModel):
    role: str
    total: int
    page: int
    size: int
    jobs: list[Job]
