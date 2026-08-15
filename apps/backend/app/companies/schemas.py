"""기업 인텔리전스 API DTO. 모든 사실 항목은 source_ids로 근거를 가리킨다.

# ponytail: 클래스명은 OpenAPI 전역에서 유일해야 한다(CLAUDE.md) — Company/Intelligence 접두.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AnalysisStatus(str, Enum):
    """단계별 상태 — 수집 실패를 전체 실패로 만들지 않는다(계획서 §4)."""

    queued = "queued"
    collecting = "collecting"
    analyzing = "analyzing"
    ready = "ready"
    partial = "partial"
    failed = "failed"


class SourceKind(str, Enum):
    official_site = "official_site"
    careers = "careers"
    dart = "dart"
    newsroom = "newsroom"
    job_posting = "job_posting"
    user_url = "user_url"


class TrustLevel(str, Enum):
    primary = "primary"  # 공식 홈페이지·채용 페이지·공시
    secondary = "secondary"  # 보조 매체·채용 플랫폼
    user_provided = "user_provided"  # 사용자가 직접 넣은 URL


class SignalType(str, Enum):
    business = "business"
    product = "product"
    hiring = "hiring"
    technology = "technology"
    risk = "risk"
    culture = "culture"


class CompanyAnalyzeRequest(BaseModel):
    name: str
    job_url: str | None = None
    force_refresh: bool = False


class SourceSummary(BaseModel):
    id: int
    kind: SourceKind
    url: str
    title: str
    publisher: str  # 출처 도메인. UI가 칩으로 표시
    published_at: datetime | None
    fetched_at: datetime
    trust_level: TrustLevel
    changed: bool  # 직전 분석 이후 원문이 바뀌었는지(content_hash 비교)


class SourcedText(BaseModel):
    """근거를 달고 다니는 사실 한 조각. source_ids가 비면 저장하지 않는다(계획서 §6.4).

    요약·규모·사업 영역·제품 — 모든 사실 필드가 이 형태다. 평범한 str로 두면
    "근거 없는 문장"이 조용히 섞여 들어온다.
    """

    text: str
    source_ids: list[int]


class MatchType(str, Enum):
    strength = "strength"
    gap = "gap"
    question = "question"


class IntelligenceSignal(BaseModel):
    label: str
    detail: str
    signal_type: SignalType
    confidence: float = Field(ge=0, le=1)
    evidence_quote: str | None
    source_ids: list[int]


class CompanyJob(BaseModel):
    """공고/JD 구조화 결과. 모든 항목이 원문 공고(source_id) 하나에서 나온다."""

    id: int
    source_id: int
    title: str
    role_category: str
    location: str
    employment: str
    deadline: str  # "상시채용"·"채용 시 마감"이 흔해 date로 강제하지 않는다
    description: str
    requirements: list[str]
    preferred: list[str]
    core_skills: list[str]  # JD가 요구하는 핵심 역량 3~5개
    problem_types: list[str]  # 이 직무가 푸는 문제 유형


class CompanyMatch(BaseModel):
    """기업 요구 → 내 경험 → 근거. 점수보다 설명이 먼저다(계획서 §8)."""

    job_id: int | None
    company_need: str
    profile_evidence: str  # 프로필 원문을 복제하지 않고 어느 경력/프로젝트인지만
    match_type: MatchType
    score: float = Field(ge=0, le=100)
    reason: str
    source_ids: list[int]


class CompanyIntelligence(BaseModel):
    name: str
    normalized_name: str
    domain: str  # 로고(favicon)·출처 판별용. 미상이면 빈 문자열
    summary: SourcedText | None  # 근거 없으면 None — 채워 넣지 않는다
    stage: SourcedText | None
    business_areas: list[SourcedText]
    products: list[SourcedText]
    signals: list[IntelligenceSignal]
    jobs: list[CompanyJob]
    sources: list[SourceSummary]
    source_count: int
    manual_urls: list[str]  # 사용자가 등록한 URL — 수집 실패와 무관하게 유지된다
    status: AnalysisStatus
    warnings: list[str]  # 실패한 provider·건너뛴 단계
    needs_review: list[str]  # 근거가 약해 저장하지 않은 항목(계획서 §6.4)
    last_analyzed_at: datetime | None
    fresh_until: datetime | None
    is_stale: bool  # fresh_until이 지났다 — 판단 규칙을 프론트에 복제하지 않는다


class AnalysisJobStatus(BaseModel):
    normalized_name: str
    status: AnalysisStatus
    warnings: list[str]
    last_analyzed_at: datetime | None
