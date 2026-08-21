from fastapi import APIRouter, File, Response, UploadFile

from app.resume import service
from app.resume.schemas import (
    ResumeChatRequest, ResumeChatResponse, ResumeExtractResponse,
    ResumeRenderRequest, ResumeState, ResumeTemplate,
)

router = APIRouter(prefix="/api/resume", tags=["resume"])


@router.get("/templates", response_model=list[ResumeTemplate])
def templates() -> list[ResumeTemplate]:
    return service.list_templates()


@router.get("/seed", response_model=ResumeState)
async def seed() -> ResumeState:
    return await service.seed_state()


@router.post("/materials/extract", response_model=ResumeExtractResponse)
async def extract(file: UploadFile = File(...)) -> ResumeExtractResponse:
    data = await file.read()
    return ResumeExtractResponse(text=service.extract_material(file.filename or "", data))


@router.post("/chat", response_model=ResumeChatResponse)
async def chat(req: ResumeChatRequest) -> ResumeChatResponse:
    state, reply = await service.chat(req.state, req.materials, req.message)
    return ResumeChatResponse(state=state, reply=reply)


@router.post("/preview")
def preview(req: ResumeRenderRequest) -> Response:
    return Response(content=service.render_html(req.state), media_type="text/html")


@router.post("/render")
def render(req: ResumeRenderRequest) -> Response:
    return Response(
        content=service.render_pdf(req.state),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="resume.pdf"'},
    )
