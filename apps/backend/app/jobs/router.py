from fastapi import APIRouter

from app.jobs import service
from app.jobs.schemas import JobFeed

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
