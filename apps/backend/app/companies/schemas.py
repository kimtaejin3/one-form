from pydantic import BaseModel


class CompanyAnalyzeRequest(BaseModel):
    name: str


class StrengthMatch(BaseModel):
    company_issue: str
    my_experience: str
    fit: int


class Signal(BaseModel):
    label: str
    detail: str
    source: str  # 근거/출처 — 임베딩 RAG 붙을 때 인용으로 대체


class InterviewPoint(BaseModel):
    question: str
    hint: str


class CompanyBrief(BaseModel):
    name: str
    domain: str  # 로고(favicon)용. 미상이면 빈 문자열
    summary: str
    stage: str
    business_areas: list[str]
    products: list[str]
    jd_skills: list[str]
    signals: list[Signal]
    strength_matching: list[StrengthMatch]
    interview_points: list[InterviewPoint]
    apply_tips: list[str]
