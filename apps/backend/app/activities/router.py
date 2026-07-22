from fastapi import APIRouter

from app.activities import repository
from app.activities.schemas import Activity

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("", response_model=list[Activity])
async def list_activities():
    return await repository.list_activities()
