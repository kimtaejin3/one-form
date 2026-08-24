from fastapi import APIRouter, File, Response, UploadFile

from app.resume import service
from app.resume.schemas import (
    ResumeApplicationDocuments, ResumeBundleRenderRequest, ResumeChatRequest,
    ResumeChatResponse, ResumeEssayDraftRequest, ResumeEssayDraftResponse,
    ResumeEssayQuestion, ResumeExtractResponse, ResumeRenderRequest, ResumeTemplate,
)

router = APIRouter(prefix="/api/resume", tags=["resume"])


@router.get("/templates", response_model=list[ResumeTemplate])
def templates() -> list[ResumeTemplate]:
    return service.list_templates()


@router.get("/seed", response_model=ResumeApplicationDocuments)
async def seed() -> ResumeApplicationDocuments:
    return await service.seed_documents()


@router.post("/materials/extract", response_model=ResumeExtractResponse)
async def extract(file: UploadFile = File(...)) -> ResumeExtractResponse:
    data = await file.read()
    return ResumeExtractResponse(text=service.extract_material(file.filename or "", data))


@router.get("/essay-questions", response_model=list[ResumeEssayQuestion])
def essay_questions() -> list[ResumeEssayQuestion]:
    return service.list_essay_questions()


@router.post("/essay-draft", response_model=ResumeEssayDraftResponse)
async def essay_draft(req: ResumeEssayDraftRequest) -> ResumeEssayDraftResponse:
    draft, note = await service.essay_draft(req.question, req.char_limit, req.state)
    return ResumeEssayDraftResponse(draft=draft, note=note)


@router.post("/chat", response_model=ResumeChatResponse)
async def chat(req: ResumeChatRequest) -> ResumeChatResponse:
    state, reply = await service.chat(req.state, req.materials, req.message)
    return ResumeChatResponse(state=state, reply=reply)


@router.post("/preview")
def preview(req: ResumeRenderRequest) -> Response:
    return Response(content=service.render_html(req.state, req.kind), media_type="text/html")


@router.post("/render")
def render(req: ResumeRenderRequest) -> Response:
    return Response(
        content=service.render_pdf(req.state, req.kind),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{req.kind.value}.pdf"'},
    )


@router.post("/render-bundle")
def render_bundle(req: ResumeBundleRenderRequest) -> Response:
    return Response(
        content=service.render_bundle_pdf(req.documents, req.included),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="application.pdf"'},
    )
