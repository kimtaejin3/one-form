"""분석 오케스트레이션 — 정규화 → 수집 → 구조화 → 저장. 라우터는 이것만 호출한다.

# ponytail: 분석을 인라인으로 돌린다(큐 없음). 요청당 수집 문서가 한 자릿수라 수 초면 끝나고,
#   워커·큐를 넣으면 배포 대상이 하나 늘어난다. 문서 수가 늘어 응답이 길어지면 그때
#   status=queued + 백그라운드 작업으로 옮긴다(스키마는 이미 queued를 갖고 있다).
"""
import asyncio
import logging
import re

from app.ai.llm import get_llm
from app.companies import repository
from app.companies.analysis import analyze as analyze_docs
from app.companies.matching import match_company
from app.companies.schemas import (
    AnalysisJobStatus,
    AnalysisStatus,
    CompanyIntelligence,
    CompanyJob,
    CompanyMatch,
    SourceSummary,
)
from app.profile.repository import get_profile
from app.companies.sources.base import SourceDocument, SourceProvider
from app.companies.sources.manual import ManualUrlSource
from app.companies.sources.official import OfficialSiteSource, domain_for

# 법인 접미사 — "삼성전자(주)"와 "주식회사 삼성전자"를 같은 기업으로 본다(계획서 §6.1).
# 앞/뒤 끝에서만 떼어낸다. 부분 문자열로 지우면 Lincoln→loln, Corpus→us처럼 이름이 망가진다.
_AFFIX_RE = re.compile(
    r"^\s*(?:주식회사|유한회사)\s*"
    r"|\s*(?:주식회사|유한회사|\(주\)|㈜|\(유\)|co\.,?\s*ltd\.?|ltd\.?|inc\.?|corp\.?|llc)\s*$",
    re.IGNORECASE,
)

# ponytail: 프로세스 한정 락 — 같은 기업 동시 분석의 중복 실행을 막는다. 인스턴스가 여러 개가
#   되면 Postgres advisory lock(pg_advisory_xact_lock)으로 바꾼다.
_LOCKS: dict[str, asyncio.Lock] = {}

_PROVIDERS: list[SourceProvider] = [OfficialSiteSource(), ManualUrlSource()]

logger = logging.getLogger(__name__)


def normalize(name: str) -> str:
    """표시용 이름 → 저장·조회 키. 공백·대소문자·법인 접미사를 제거한다."""
    text = name.strip().lower()
    while True:  # "주식회사 예시(주)"처럼 앞뒤에 겹쳐 붙는 경우까지
        stripped = _AFFIX_RE.sub("", text, count=1).strip()
        if stripped == text or not stripped:
            break
        text = stripped
    return re.sub(r"\s+", "", text)


async def _collect(query: dict) -> tuple[dict[int, SourceDocument], list[str]]:
    """provider별로 수집. 하나가 죽어도 나머지는 살린다(계획서 §4)."""
    docs: dict[int, SourceDocument] = {}
    warnings: list[str] = []
    seen_hashes: set[str] = set()

    for provider in _PROVIDERS:
        try:
            collected = await provider.collect(query)
        except Exception as exc:  # 네트워크·robots·잘못된 URL — 전체 실패로 만들지 않는다
            warnings.append(f"{provider.name} 출처 수집 실패: {exc}")
            continue
        for doc in collected:
            if doc.content_hash in seen_hashes:  # 중복 문서 제거(§6.3)
                continue
            seen_hashes.add(doc.content_hash)
            docs[len(docs) + 1] = doc
    return docs, warnings


def _manual_urls(brief: CompanyIntelligence | None) -> list[str]:
    """저장된 요청 URL을 쓴다 — 수집에 성공한 출처만 보면 한 번 실패한 URL이 영영 사라진다."""
    return list(brief.manual_urls) if brief else []


def _status(docs: dict, warnings: list[str], needs_review: list[str]) -> AnalysisStatus:
    if not docs:
        return AnalysisStatus.failed
    return AnalysisStatus.partial if (warnings or needs_review) else AnalysisStatus.ready


async def analyze(
    name: str, job_url: str | None = None, force_refresh: bool = False
) -> CompanyIntelligence:
    normalized = normalize(name)
    if not normalized:
        raise ValueError("기업명이 비어 있습니다.")

    lock = _LOCKS.setdefault(normalized, asyncio.Lock())
    async with lock:
        cached = await repository.get(normalized)
        # 락을 기다린 두 번째 요청은 여기서 방금 저장된 결과를 만나 재분석하지 않는다.
        if cached and not force_refresh and repository.is_fresh(cached):
            if not job_url or job_url in {s.url for s in cached.sources}:
                return cached

        # 사용자가 직접 넣은 URL은 재분석에서도 유지한다 — refresh 한 번에 사라지면
        # 공식 도메인을 모르는 기업은 매번 URL을 다시 입력해야 한다.
        job_urls = list(
            dict.fromkeys(
                _manual_urls(cached) + ([job_url.strip()] if job_url and job_url.strip() else [])
            )
        )
        query = {"name": name, "normalized_name": normalized, "job_urls": job_urls}
        docs, warnings = await _collect(query)
        if not docs:
            warnings.append(
                "공식 출처를 찾지 못했습니다. 기업 공식 홈페이지나 채용공고 URL을 입력해 주세요."
            )
        result = await analyze_docs(name, docs)

        changed = repository.changed_urls(await repository.source_hashes(normalized), docs)
        if changed:
            warnings.append(
                f"직전 분석 이후 원문이 바뀐 출처 {len(changed)}건이 있습니다: "
                + ", ".join(sorted(changed))
            )

        # 비용·호출량 로깅(계획서 §4). 원문·프로필·키는 남기지 않는다(§11).
        logger.info(
            "기업 분석 완료 name=%s docs=%d providers=%d 실패=%d 신호=%d 공고=%d 변경=%d llm=%s",
            normalized,
            len(docs),
            len(_PROVIDERS),
            len(warnings),
            len(result.signals),
            len(result.jobs),
            len(changed),
            type(get_llm()).__name__,
        )

        return await repository.save(
            name=name.strip(),
            normalized_name=normalized,
            domain=domain_for(normalized),
            status=_status(docs, warnings, result.needs_review),
            result=result,
            docs=docs,
            manual_urls=job_urls,  # 수집 실패와 무관하게 요청된 URL을 남긴다
            warnings=warnings,
        )


async def get(normalized_name: str) -> CompanyIntelligence | None:
    return await repository.get(normalize(normalized_name))


async def refresh(normalized_name: str) -> AnalysisJobStatus | None:
    """저장된 기업만 재분석한다 — 없는 기업은 analyze로 새로 만든다."""
    existing = await repository.get(normalize(normalized_name))
    if existing is None:
        return None
    brief = await analyze(existing.name, force_refresh=True)
    return AnalysisJobStatus(
        normalized_name=brief.normalized_name,
        status=brief.status,
        warnings=brief.warnings,
        last_analyzed_at=brief.last_analyzed_at,
    )


async def list_sources(normalized_name: str) -> list[SourceSummary] | None:
    brief = await repository.get(normalize(normalized_name))
    return brief.sources if brief else None


async def list_jobs(normalized_name: str) -> list[CompanyJob] | None:
    brief = await repository.get(normalize(normalized_name))
    return brief.jobs if brief else None


async def list_matches(
    normalized_name: str, job_id: int | None = None
) -> list[CompanyMatch] | None:
    """조회 시점에 현재 프로필로 계산한다 — 저장된 매칭은 프로필 수정 즉시 낡는다."""
    brief = await repository.get(normalize(normalized_name))
    if brief is None:
        return None
    profile = await get_profile()
    return match_company(brief.jobs, profile, job_id)
