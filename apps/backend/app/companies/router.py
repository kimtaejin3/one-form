from fastapi import APIRouter, HTTPException

from app.companies import service
from app.companies.schemas import (
    AnalysisJobStatus,
    CompanyAnalyzeRequest,
    CompanyIntelligence,
    CompanyJob,
    CompanyMatch,
    SourceSummary,
)

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.post("/analyze", response_model=CompanyIntelligence)
async def analyze_company(req: CompanyAnalyzeRequest):
    try:
        return await service.analyze(req.name, req.job_url, req.force_refresh)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/{normalized_name}", response_model=CompanyIntelligence)
async def get_company(normalized_name: str):
    brief = await service.get(normalized_name)
    if brief is None:
        raise HTTPException(status_code=404, detail="분석된 기업이 없습니다.")
    return brief


@router.post("/{normalized_name}/refresh", response_model=AnalysisJobStatus)
async def refresh_company(normalized_name: str):
    status = await service.refresh(normalized_name)
    if status is None:
        raise HTTPException(status_code=404, detail="분석된 기업이 없습니다.")
    return status


@router.get("/{normalized_name}/sources", response_model=list[SourceSummary])
async def get_sources(normalized_name: str):
    sources = await service.list_sources(normalized_name)
    if sources is None:
        raise HTTPException(status_code=404, detail="분석된 기업이 없습니다.")
    return sources


@router.get("/{normalized_name}/jobs", response_model=list[CompanyJob])
async def get_jobs(normalized_name: str):
    jobs = await service.list_jobs(normalized_name)
    if jobs is None:
        raise HTTPException(status_code=404, detail="분석된 기업이 없습니다.")
    return jobs


@router.get("/{normalized_name}/matches", response_model=list[CompanyMatch])
async def get_matches(normalized_name: str, job_id: int | None = None):
    matches = await service.list_matches(normalized_name, job_id)
    if matches is None:
        raise HTTPException(status_code=404, detail="분석된 기업이 없습니다.")
    return matches
