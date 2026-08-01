from fastapi import APIRouter, File, HTTPException, UploadFile

from app.profile import repository, service
from app.profile.schemas import Profile, ResumeUploadResponse

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=Profile)
async def get_profile():
    return await repository.get_profile()


@router.put("", response_model=Profile)
async def update_profile(profile: Profile):
    return await service.update_profile(profile.model_dump())


@router.post("/resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=415, detail="PDF 파일만 업로드할 수 있습니다.")
    try:
        return await service.upload_resume(await file.read(), file.filename or "이력서.pdf")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
