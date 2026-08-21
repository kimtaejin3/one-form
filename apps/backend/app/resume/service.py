"""이력서 빌더 서비스 — 시드·챗·렌더·추출. 저장(DB) 없음."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.profile.repository import get_profile
from app.resume.render import html_to_pdf
from app.resume.schemas import (
    ResumeDoc, ResumeHeader, ResumeLink, ResumeSection, ResumeState,
    ResumeStyle, ResumeTemplate,
)

_TPL_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(_TPL_DIR),
    autoescape=select_autoescape(["html"]),
)

_DENSITY_GAP = {"compact": 8, "normal": 14, "relaxed": 22}
_SCALE_PT = {"S": 10, "M": 11, "L": 12}
_DENSITY_MARGIN = {"compact": "12mm", "normal": "16mm", "relaxed": "20mm"}

_PRESETS = {
    "classic": ResumeStyle(template="classic", heading_style="bar", accent_color="#334155"),
    "modern": ResumeStyle(template="modern", heading_style="plain", accent_color="#2563eb", font="Pretendard"),
}


def _sections_from_profile(p: dict) -> list[ResumeSection]:
    out: list[ResumeSection] = []

    def add(type_: str, title: str, items: list[dict]) -> None:
        if items:
            out.append(ResumeSection(
                id=type_, type=type_, title=title, order=len(out), items=items,
            ))

    add("career", "경력", [
        {"title": c["role"], "org": c["company"], "period": c["period"],
         "bullets": c["highlights"], "stack": c["stack"]}
        for c in p["careers"]
    ])
    add("project", "프로젝트", [
        {"title": pr["name"], "org": pr["role"], "period": pr["period"],
         "note": pr["summary"], "bullets": pr["highlights"], "stack": pr["stack"]}
        for pr in p["projects"]
    ])
    add("education", "학력", [
        {"title": e["school"], "org": e["major"], "period": e["period"],
         "note": f'{e["status"]} · GPA {e["gpa"]}'}
        for e in p["educations"]
    ])
    stacks = list(dict.fromkeys(
        s for c in p["careers"] for s in c["stack"]
    ) | dict.fromkeys(s for pr in p["projects"] for s in pr["stack"]))
    add("skill", "스킬", [{"name": s} for s in stacks])
    add("certificate", "자격증", [
        {"title": c["name"], "org": c["issuer"], "period": c["date"]} for c in p["certificates"]
    ])
    add("award", "수상", [
        {"title": a["title"], "org": a["org"], "period": a["date"]} for a in p["awards"]
    ])
    add("language", "어학", [
        {"title": l["language"], "org": l["test"], "note": f'{l["score"]} ({l["date"]})'}
        for l in p["languages"]
    ])
    add("activity", "대외활동", [
        {"title": a["title"], "org": a["org"], "period": a["period"], "note": a["description"]}
        for a in p["activities"]
    ])
    return out


async def seed_state() -> ResumeState:
    p = await get_profile()
    if not p["registered"]:
        return ResumeState(doc=ResumeDoc(header=ResumeHeader(name="")))
    per = p["personal"]
    header = ResumeHeader(
        name=per["name"],
        contact=[x for x in (per["email"], per["phone"], per["address"]) if x],
        links=[ResumeLink(label=l["label"], url=l["url"]) for l in p["links"]],
    )
    return ResumeState(doc=ResumeDoc(header=header, sections=_sections_from_profile(p)))


def list_templates() -> list[ResumeTemplate]:
    names = {"classic": "클래식", "modern": "모던"}
    return [
        ResumeTemplate(id=k, name=names[k], thumbnail=f"/thumbs/{k}.png", preset=v)
        for k, v in _PRESETS.items()
    ]


def render_html(state: ResumeState) -> str:
    style = state.style
    name = style.template if (_TPL_DIR / f"{style.template}.html").exists() else "classic"
    tpl = _env.get_template(f"{name}.html")
    visible = sorted([s for s in state.doc.sections if s.visible], key=lambda s: s.order)
    return tpl.render(
        doc=state.doc,
        style=style,
        sections=visible,
        base_pt=_SCALE_PT[style.font_scale.value],
        gap=_DENSITY_GAP[style.density.value],
        margin=_DENSITY_MARGIN[style.density.value],
    )


def render_pdf(state: ResumeState) -> bytes:
    return html_to_pdf(render_html(state))
