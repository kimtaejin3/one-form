from fastapi import APIRouter, HTTPException

from app.jobs import service
from app.jobs.schemas import JobDetail, JobFeed

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=JobFeed)
async def list_jobs(
    page: int = 1,
    size: int = 12,
    role: str = "",
    experience: str = "",
    employment: str = "",
    location: str = "",
):
    return await service.get_job_feed(page, size, role, experience, employment, location)


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: int):
    detail = await service.get_job_detail(job_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="공고를 찾을 수 없습니다")
    return detail
