import asyncio
from app.resume.render import html_to_pdf
from app.resume.schemas import ResumeDocumentKind, ResumeState, ResumeStyle, Density
from app.resume.service import (
    extract_material,
    list_templates,
    render_bundle_pdf,
    render_html,
    render_pdf,
    seed_documents,
    seed_state,
)
import pytest
from pydantic import ValidationError


def test_html_to_pdf_returns_pdf_bytes():
    pdf = html_to_pdf("<h1>홍길동</h1>")
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 500


def test_default_state_uses_classic_normal():
    s = ResumeState(doc={"header": {"name": "홍길동"}})
    assert s.style.template == "classic"
    assert s.style.density == Density.normal


def test_invalid_density_rejected():
    with pytest.raises(ValidationError):
        ResumeStyle(density="huge")


def test_seed_state_maps_profile_header_and_sections():
    s = asyncio.run(seed_state())
    assert s.doc.header.name  # 프로필 목이 등록돼 있으므로 이름이 있다
    types = {sec.type.value for sec in s.doc.sections}
    assert "career" in types
    # 섹션 순서는 0..n 연속
    orders = [sec.order for sec in s.doc.sections]
    assert orders == sorted(orders)


def test_render_html_interpolates_name_and_accent():
    s = asyncio.run(seed_state())
    s.style.accent_color = "#1a3a6b"
    html = render_html(s)
    assert s.doc.header.name in html
    assert "#1a3a6b" in html  # 스타일 토큰이 CSS에 보간됨


def test_render_pdf_returns_pdf():
    s = asyncio.run(seed_state())
    assert render_pdf(s)[:4] == b"%PDF"


def test_document_templates_are_separate():
    docs = asyncio.run(seed_documents())
    docs.essay.doc.essays = [{"question": "지원 동기", "answer": "답변"}]

    resume = render_html(docs.resume, ResumeDocumentKind.resume)
    career = render_html(docs.career, ResumeDocumentKind.career)
    essay = render_html(docs.essay, ResumeDocumentKind.essay)

    assert "자기소개서" not in resume
    assert "경력기술서" in career
    assert "자기소개서" in essay
    assert "지원 동기" in essay and "답변" in essay


def test_bundle_pdf_merges_only_selected_documents():
    docs = asyncio.run(seed_documents())
    pdf = render_bundle_pdf(docs, [ResumeDocumentKind.resume, ResumeDocumentKind.career])
    assert pdf[:4] == b"%PDF"


def test_list_templates_are_resume_styles():
    tpls = list_templates()
    ids = {t.id for t in tpls}
    assert ids == {"classic", "formal", "ats", "modern", "sidebar"}
    # 빌더가 kind로 거를 수 있어야 한다
    assert {t.kind for t in tpls} == {"resume"}
    state = asyncio.run(seed_state())
    for template in tpls:
        state.style = template.preset
        assert state.doc.header.name in render_html(state)


def test_chat_with_mock_keeps_state():
    from app.resume.service import chat

    s = asyncio.run(seed_state())
    new_state, reply = asyncio.run(chat(s, [], "요약 써줘"))
    assert new_state == s          # 목은 변경 없음
    assert reply                    # 안내 문구는 있음


def test_chat_applies_valid_llm_output(monkeypatch):
    from app.resume.service import chat

    s = asyncio.run(seed_state())
    edited = s.model_copy(deep=True)
    edited.doc.summary = "성과 지향 백엔드 개발자"

    class FakeLlm:
        async def complete_json(self, prompt, schema):
            return edited.model_dump()

    monkeypatch.setattr("app.resume.service.get_llm", lambda: FakeLlm())
    new_state, reply = asyncio.run(chat(s, [], "요약 추가"))
    assert new_state.doc.summary == "성과 지향 백엔드 개발자"


def test_chat_rejects_invalid_llm_output(monkeypatch):
    from app.resume.service import chat

    s = asyncio.run(seed_state())

    class BadLlm:
        async def complete_json(self, prompt, schema):
            return {"doc": {"header": {}}}  # name 누락 → 검증 실패

    monkeypatch.setattr("app.resume.service.get_llm", lambda: BadLlm())
    new_state, reply = asyncio.run(chat(s, [], "망가뜨려"))
    assert new_state == s  # 옛 state 유지


def test_extract_text_file():
    assert extract_material("memo.txt", "안녕 이력".encode()) == "안녕 이력"


def test_endpoints_smoke(client):
    assert client.get("/api/resume/templates").json()[0]["id"]
    documents = client.get("/api/resume/seed").json()
    assert set(documents) == {"resume", "career", "essay"}
    state = documents["resume"]
    html = client.post("/api/resume/preview", json={"state": state, "kind": "resume"})
    assert html.status_code == 200 and state["doc"]["header"]["name"] in html.text
    pdf = client.post("/api/resume/render", json={"state": state, "kind": "resume"})
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    bundle = client.post(
        "/api/resume/render-bundle",
        json={"documents": documents, "included": ["resume", "career"]},
    )
    assert bundle.status_code == 200 and bundle.content[:4] == b"%PDF"
    chat = client.post("/api/resume/chat", json={"state": state, "materials": [], "message": "요약 써줘"})
    assert "state" in chat.json() and "reply" in chat.json()
