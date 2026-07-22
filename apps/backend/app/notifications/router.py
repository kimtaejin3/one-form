from fastapi import APIRouter

from app.notifications import repository
from app.notifications.schemas import Notification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[Notification])
async def list_notifications():
    return await repository.list_notifications()
