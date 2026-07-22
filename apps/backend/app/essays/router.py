from fastapi import APIRouter

from app.essays import repository
from app.essays.schemas import DraftRequest, Essay

router = APIRouter(prefix="/api/essays", tags=["essays"])


@router.get("", response_model=list[Essay])
async def list_essays():
    return await repository.list_essays()


@router.post("/draft")
async def generate_draft(req: DraftRequest):
    return await repository.generate_draft(req.essay_id)
