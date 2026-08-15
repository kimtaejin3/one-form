"""기업 인텔리전스 저장·조회. DATABASE_URL 있으면 Postgres, 없으면 _MEM 폴백.

# ponytail: 다른 도메인과 같은 폴백 패턴(app/core/db.py). 단, 목데이터 폴백은 없다 —
#   분석 결과는 큐레이션 목이 아니라 실제 수집물이라 없으면 "없음"이 정답이다.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.companies.analysis import AnalysisResult
from app.companies.models import Company, CompanyJobRow, CompanySignal, CompanySource
from app.companies.schemas import (
    AnalysisStatus,
    CompanyIntelligence,
    CompanyJob,
    IntelligenceSignal,
    SourcedText,
    SourceKind,
    SourceSummary,
    TrustLevel,
)
from app.companies.sources.base import SourceDocument
from app.core.db import get_sessionmaker

FRESH_HOURS = 24  # 이 시간 안이면 캐시 사용(계획서 §7 fresh_until)

# 폴백 저장소(프로세스 한정). DATABASE_URL 없을 때만 쓰인다.
_MEM: dict[str, CompanyIntelligence] = {}
# 변경 감지용 직전 본문 해시. DTO에 해시를 노출하지 않으려고 따로 둔다.
_MEM_HASHES: dict[str, dict[str, str]] = {}


async def source_hashes(normalized_name: str) -> dict[str, str]:
    """직전 분석의 {url: content_hash}. 변경 감지에만 쓴다."""
    sm = get_sessionmaker()
    if sm is None:
        return _MEM_HASHES.get(normalized_name, {})
    async with sm() as s:
        rows = (
            (
                await s.execute(
                    select(CompanySource.url, CompanySource.content_hash)
                    .join(Company, Company.id == CompanySource.company_id)
                    .where(Company.normalized_name == normalized_name)
                )
            )
            .tuples()
            .all()
        )
    return dict(rows)


def fresh_until(last_analyzed_at: datetime | None) -> datetime | None:
    return last_analyzed_at + timedelta(hours=FRESH_HOURS) if last_analyzed_at else None


def is_fresh(brief: CompanyIntelligence, now: datetime | None = None) -> bool:
    until = brief.fresh_until
    return until is not None and (now or datetime.now(timezone.utc)) < until


def _summary(source_id: int, doc: SourceDocument, changed: bool = False) -> SourceSummary:
    return SourceSummary(
        id=source_id,
        kind=doc.kind,
        url=doc.url,
        title=doc.title,
        publisher=doc.publisher,
        published_at=doc.published_at,
        fetched_at=doc.fetched_at,
        trust_level=doc.trust_level,
        changed=changed,
    )


def changed_urls(previous: dict[str, str], docs: dict[int, SourceDocument]) -> set[str]:
    """직전 분석과 본문 해시가 달라진 URL(계획서 §4 출처 변경 감지). 새 URL은 변경이 아니다."""
    return {d.url for d in docs.values() if d.url in previous and previous[d.url] != d.content_hash}


def _remap_text(item: SourcedText | None, id_map: dict[int, int]) -> SourcedText | None:
    """로컬 문서 번호 → 실제 source id. 근거를 잃은 항목은 통째로 버린다."""
    if item is None:
        return None
    ids = [id_map[i] for i in item.source_ids if i in id_map]
    return SourcedText(text=item.text, source_ids=ids) if ids else None


def _remapped(result: AnalysisResult, id_map: dict[int, int]) -> AnalysisResult:
    """저장 직전 한 번에 다시 매긴다 — 필드별로 흩어놓으면 새 필드가 빠진다."""
    return AnalysisResult(
        summary=_remap_text(result.summary, id_map),
        stage=_remap_text(result.stage, id_map),
        business_areas=[
            t for t in (_remap_text(b, id_map) for b in result.business_areas) if t
        ],
        products=[t for t in (_remap_text(p, id_map) for p in result.products) if t],
        signals=[
            s.model_copy(update={"source_ids": [id_map[i] for i in s.source_ids if i in id_map]})
            for s in result.signals
            if any(i in id_map for i in s.source_ids)
        ],
        jobs=[
            j.model_copy(update={"source_id": id_map[j.source_id]})
            for j in result.jobs
            if j.source_id in id_map
        ],
        needs_review=result.needs_review,
    )


def build(
    *,
    name: str,
    normalized_name: str,
    domain: str,
    status: AnalysisStatus,
    result: AnalysisResult,
    sources: list[SourceSummary],
    manual_urls: list[str],
    warnings: list[str],
    analyzed_at: datetime | None,
) -> CompanyIntelligence:
    until = fresh_until(analyzed_at)
    return CompanyIntelligence(
        name=name,
        normalized_name=normalized_name,
        domain=domain,
        summary=result.summary,
        stage=result.stage,
        business_areas=result.business_areas,
        products=result.products,
        signals=result.signals,
        jobs=result.jobs,
        sources=sources,
        source_count=len(sources),
        manual_urls=manual_urls,
        status=status,
        warnings=warnings,
        needs_review=result.needs_review,
        last_analyzed_at=analyzed_at,
        fresh_until=until,
        is_stale=until is not None and datetime.now(timezone.utc) >= until,
    )


async def get(normalized_name: str) -> CompanyIntelligence | None:
    sm = get_sessionmaker()
    if sm is None:
        return _MEM.get(normalized_name)
    async with sm() as s:
        row = (
            await s.execute(select(Company).where(Company.normalized_name == normalized_name))
        ).scalar_one_or_none()
        if row is None:
            return None
        sources = (
            (
                await s.execute(
                    select(CompanySource)
                    .where(CompanySource.company_id == row.id)
                    .order_by(CompanySource.id)
                )
            )
            .scalars()
            .all()
        )
        signals = (
            (
                await s.execute(
                    select(CompanySignal)
                    .where(CompanySignal.company_id == row.id)
                    .order_by(CompanySignal.id)
                )
            )
            .scalars()
            .all()
        )
        jobs = (
            (
                await s.execute(
                    select(CompanyJobRow)
                    .where(CompanyJobRow.company_id == row.id)
                    .order_by(CompanyJobRow.id)
                )
            )
            .scalars()
            .all()
        )
    # 저장 경로와 같은 build()를 탄다 — 조립을 두 군데 두면 새 필드가 한쪽에서 빠진다.
    return build(
        name=row.name,
        normalized_name=row.normalized_name,
        domain=row.domain,
        status=AnalysisStatus(row.status),
        result=AnalysisResult(
            summary=SourcedText(**row.summary) if row.summary else None,
            stage=SourcedText(**row.stage) if row.stage else None,
            business_areas=[SourcedText(**b) for b in row.business_areas],
            products=[SourcedText(**p) for p in row.products],
            signals=[
                IntelligenceSignal(
                    label=g.label,
                    detail=g.detail,
                    signal_type=g.signal_type,
                    confidence=g.confidence,
                    evidence_quote=g.evidence_quote,
                    source_ids=g.source_ids,
                )
                for g in signals
            ],
            jobs=[
                CompanyJob(
                    id=j.id,
                    source_id=j.source_id,
                    title=j.title,
                    role_category=j.role_category,
                    location=j.location,
                    employment=j.employment,
                    deadline=j.deadline,
                    description=j.description,
                    requirements=j.requirements,
                    preferred=j.preferred,
                    core_skills=j.core_skills,
                    problem_types=j.problem_types,
                )
                for j in jobs
            ],
            needs_review=row.needs_review,
        ),
        sources=[
            SourceSummary(
                id=d.id,
                kind=SourceKind(d.kind),
                url=d.url,
                title=d.title,
                publisher=d.publisher,
                published_at=d.published_at,
                fetched_at=d.fetched_at,
                trust_level=TrustLevel(d.trust_level),
                changed=d.changed,
            )
            for d in sources
        ],
        manual_urls=row.manual_urls,
        warnings=row.warnings,
        analyzed_at=row.last_analyzed_at,
    )


async def save(
    *,
    name: str,
    normalized_name: str,
    domain: str,
    status: AnalysisStatus,
    result: AnalysisResult,
    docs: dict[int, SourceDocument],
    manual_urls: list[str],
    warnings: list[str],
) -> CompanyIntelligence:
    """분석 1회분을 통째로 교체 저장. docs의 키(로컬 번호)를 실제 source id로 다시 매핑한다."""
    analyzed_at = datetime.now(timezone.utc)
    sm = get_sessionmaker()
    previous = await source_hashes(normalized_name)
    changed = changed_urls(previous, docs)

    if sm is None:
        brief = build(
            name=name,
            normalized_name=normalized_name,
            domain=domain,
            status=status,
            result=result,
            sources=[_summary(i, d, d.url in changed) for i, d in docs.items()],
            manual_urls=manual_urls,
            warnings=warnings,
            analyzed_at=analyzed_at,
        )
        _MEM[normalized_name] = brief
        _MEM_HASHES[normalized_name] = {d.url: d.content_hash for d in docs.values()}
        return brief

    async with sm() as s:
        row = (
            await s.execute(select(Company).where(Company.normalized_name == normalized_name))
        ).scalar_one_or_none()
        if row is None:
            row = Company(normalized_name=normalized_name)
            s.add(row)
        row.name = name
        row.domain = domain
        row.manual_urls = manual_urls
        row.status = status.value
        row.warnings = warnings
        row.needs_review = result.needs_review
        row.last_analyzed_at = analyzed_at
        await s.flush()  # row.id 확보

        # 재분석은 이전 출처·신호·공고를 대체한다 — 부분 갱신하면 사라진 근거가 남는다.
        await s.execute(delete(CompanyJobRow).where(CompanyJobRow.company_id == row.id))
        await s.execute(delete(CompanySignal).where(CompanySignal.company_id == row.id))
        await s.execute(delete(CompanySource).where(CompanySource.company_id == row.id))

        id_map: dict[int, int] = {}
        for local_id, doc in docs.items():
            source = CompanySource(
                company_id=row.id,
                kind=doc.kind.value,
                url=doc.url,
                title=doc.title,
                publisher=doc.publisher,
                published_at=doc.published_at,
                fetched_at=doc.fetched_at,
                content_hash=doc.content_hash,
                trust_level=doc.trust_level.value,
                changed=doc.url in changed,
                raw_text=doc.text,
            )
            s.add(source)
            await s.flush()  # source.id 확보 — 근거가 실제 id를 가리켜야 한다
            id_map[local_id] = source.id

        # 사실 필드의 근거를 실제 source id로 한 번에 옮긴다.
        mapped = _remapped(result, id_map)
        row.summary = mapped.summary.model_dump() if mapped.summary else None
        row.stage = mapped.stage.model_dump() if mapped.stage else None
        row.business_areas = [b.model_dump() for b in mapped.business_areas]
        row.products = [p.model_dump() for p in mapped.products]

        for signal in mapped.signals:
            s.add(
                CompanySignal(
                    company_id=row.id,
                    label=signal.label,
                    detail=signal.detail,
                    signal_type=signal.signal_type.value,
                    confidence=signal.confidence,
                    evidence_quote=signal.evidence_quote,
                    source_ids=signal.source_ids,
                )
            )
        for job in mapped.jobs:
            s.add(
                CompanyJobRow(
                    company_id=row.id,
                    source_id=job.source_id,
                    title=job.title,
                    role_category=job.role_category,
                    location=job.location,
                    employment=job.employment,
                    deadline=job.deadline,
                    description=job.description,
                    requirements=job.requirements,
                    preferred=job.preferred,
                    core_skills=job.core_skills,
                    problem_types=job.problem_types,
                )
            )
        await s.commit()

    saved = await get(normalized_name)
    assert saved is not None  # 방금 커밋했다
    return saved
