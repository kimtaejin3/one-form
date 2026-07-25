from fastapi import APIRouter, HTTPException

from app.essays import repository
from app.essays.schemas import AnswerUpdate, DraftRequest, DraftResponse, Essay

router = APIRouter(prefix="/api/essays", tags=["essays"])


@router.get("", response_model=list[Essay])
async def list_essays():
    return await repository.list_essays()


@router.post("/draft", response_model=DraftResponse)
async def generate_draft(req: DraftRequest):
    return await repository.generate_draft(req.essay_id)


@router.put("/{essay_id}/answer", response_model=Essay)
async def save_answer(essay_id: int, body: AnswerUpdate):
    try:
        return await repository.save_answer(essay_id, body.content, body.status)
    except KeyError:
        raise HTTPException(status_code=404, detail="문항을 찾을 수 없습니다.") from None
