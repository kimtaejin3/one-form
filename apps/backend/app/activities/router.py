from fastapi import APIRouter

from app.activities import repository

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("")
async def list_activities():
    return await repository.list_activities()
