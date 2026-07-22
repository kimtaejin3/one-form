from fastapi import APIRouter

from app.profile import repository
from app.profile.schemas import Profile

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=Profile)
async def get_profile():
    return await repository.get_profile()


@router.post("/resume")
async def upload_resume():
    return await repository.upload_resume()
