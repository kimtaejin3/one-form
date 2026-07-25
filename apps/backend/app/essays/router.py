from fastapi import APIRouter, HTTPException

from app.essays import repository
from app.essays.schemas import AnswerUpdate, DraftRequest, DraftResponse, Question

router = APIRouter(prefix="/api/essays", tags=["essays"])


@router.get("/questions", response_model=list[Question])
async def list_questions():
    return await repository.list_questions()


@router.post("/draft", response_model=DraftResponse)
async def generate_draft(req: DraftRequest):
    return await repository.generate_draft(req.question_id)


@router.put("/questions/{question_id}/answer", response_model=Question)
async def save_answer(question_id: int, body: AnswerUpdate):
    try:
        return await repository.save_answer(question_id, body.content, body.status)
    except KeyError:
        raise HTTPException(status_code=404, detail="문항을 찾을 수 없습니다.") from None
