import asyncio
from app.resume.render import html_to_pdf
from app.resume.schemas import ResumeState, ResumeStyle, Density
from app.resume.service import seed_state, render_html, render_pdf, list_templates
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


def test_list_templates_has_classic_and_modern():
    ids = {t.id for t in list_templates()}
    assert {"classic", "modern"} <= ids
