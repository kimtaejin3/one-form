from fastapi import APIRouter

from app.notifications import repository

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def list_notifications():
    return await repository.list_notifications()
