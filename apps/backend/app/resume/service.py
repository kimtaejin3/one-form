"""입사지원서 빌더 서비스 — 문서별 시드·챗·렌더·추출. 저장(DB) 없음."""
from io import BytesIO
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pypdf import PdfReader, PdfWriter
from pydantic import ValidationError

from app.ai.llm import get_llm
from app.core.pdf import pdf_pages
from app.profile.repository import get_profile
from app.resume.render import html_to_pdf
from app.resume.schemas import (
    ResumeApplicationDocuments, ResumeDoc, ResumeDocumentKind, ResumeEssayQuestion,
    ResumeHeader, ResumeLink, ResumePersonal, ResumeSection,
    ResumeState, ResumeStyle, ResumeTemplate,
)

_TPL_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(_TPL_DIR),
    autoescape=select_autoescape(["html"]),
)

_DENSITY_GAP = {"compact": 8, "normal": 14, "relaxed": 22}
_SCALE_PT = {"S": 10, "M": 11, "L": 12}
_DENSITY_MARGIN = {"compact": "12mm", "normal": "16mm", "relaxed": "20mm"}

# 이력서 스타일 프리셋. 경력기술서·자기소개서는 각각 전용 문서 템플릿을 사용한다.
_PRESETS = {
    "classic": ResumeStyle(template="classic", heading_style="plain", accent_color="#1f4fd8"),
    "formal": ResumeStyle(
        template="formal", heading_style="plain", accent_color="#374151", density="compact",
    ),
    "ats": ResumeStyle(
        template="ats", heading_style="underline", accent_color="#111827", density="compact",
    ),
    "modern": ResumeStyle(
        template="modern", heading_style="bar", accent_color="#3157c8", density="normal",
    ),
    "sidebar": ResumeStyle(
        template="sidebar", heading_style="plain", accent_color="#0f766e", density="normal",
    ),
}
_KINDS = {name: "resume" for name in _PRESETS}
_NAMES = {
    "classic": "표준",
    "formal": "국문 표 양식",
    "ats": "ATS · 단일 컬럼",
    "modern": "모던 · 강조 헤더",
    "sidebar": "사이드바 · 기술 중심",
}

_CHAT_PROMPT = (
    "너는 이력서 편집기다. 아래 현재 이력서 상태(JSON)와 사용자 명령을 받아,\n"
    "명령이 요구하는 최소 변경만 적용한 '전체 ResumeState JSON'을 반환하라.\n"
    "- 내용 명령이면 doc를, 스타일 명령이면 style를 고친다. 나머지는 그대로 둔다.\n"
    "- style 값은 스키마 enum만 사용한다(임의 CSS 금지).\n"
    "- 참고 자료가 있으면 내용 보강에 활용하되 사실을 지어내지 않는다.\n\n"
    "[현재 상태]\n{state}\n\n[참고 자료]\n{materials}\n\n[명령]\n{message}"
)


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
         "note": e["status"] + (f' · GPA {e["gpa"]}' if e.get("gpa") else ''),
         # 입사지원서 학력 표용 세부(형식 템플릿이 사용)
         "admission": e.get("admission", ""), "graduation": e.get("graduation", ""),
         "degree": e.get("degree", ""), "status": e["status"]}
        for e in p["educations"]
    ])
    stacks = list(dict.fromkeys(
        s for c in p["careers"] for s in c["stack"]
    ) | dict.fromkeys(s for pr in p["projects"] for s in pr["stack"]))
    # 스킬은 한 항목의 칩 묶음으로 — 스킬마다 한 줄 차지하지 않게.
    add("skill", "스킬", [{"stack": stacks}] if stacks else [])
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
    personal = ResumePersonal(
        photo=per.get("photo", ""), email=per.get("email", ""), phone=per.get("phone", ""),
        address=per.get("address", ""), birth=per.get("birth", ""), nationality=per.get("nationality", ""),
        military_status=per.get("military_status", ""), military_branch=per.get("military_branch", ""),
        military_period=per.get("military_period", ""), veteran=per.get("veteran", ""),
        discharge=per.get("discharge", ""),
    )
    return ResumeState(
        doc=ResumeDoc(header=header, personal=personal, sections=_sections_from_profile(p))
    )


async def seed_documents() -> ResumeApplicationDocuments:
    base = await seed_state()
    resume = base.model_copy(deep=True)
    resume.doc.essays = []

    career = base.model_copy(deep=True)
    career.doc.summary = ""
    career.doc.sections = [
        section for section in career.doc.sections
        if section.type.value in {"career", "project"}
    ]
    career.doc.essays = []

    essay = base.model_copy(deep=True)
    essay.doc.summary = ""
    essay.doc.sections = []
    essay.doc.essays = []
    return ResumeApplicationDocuments(resume=resume, career=career, essay=essay)


# 국내 취업지원 자료에서 반복되는 유형을 기업명 없이 정리한 공통 질문은행.
_ESSAY_QUESTIONS: list[dict] = [
    {"id": 1, "tag": "지원동기", "prompt": "지원한 직무를 선택한 이유와 해당 직무에서 이루고 싶은 목표를 작성해 주세요.", "char_limit": 1000},
    {"id": 2, "tag": "성장과정", "prompt": "현재의 가치관과 업무 태도에 가장 큰 영향을 준 경험을 중심으로 성장과정을 작성해 주세요.", "char_limit": 1000},
    {"id": 3, "tag": "직무역량", "prompt": "지원 직무와 관련한 전문지식과 경험, 이를 통해 만든 성과를 구체적으로 작성해 주세요.", "char_limit": 1000},
    {"id": 4, "tag": "협업", "prompt": "공동의 목표를 위해 다른 사람과 협업한 경험과 본인의 역할을 작성해 주세요.", "char_limit": 1000},
    {"id": 5, "tag": "문제해결", "prompt": "예상하지 못한 문제를 발견하고 원인을 분석해 해결한 경험을 작성해 주세요.", "char_limit": 1000},
    {"id": 6, "tag": "도전", "prompt": "높은 목표에 도전하며 어려움을 극복한 경험과 배운 점을 작성해 주세요.", "char_limit": 1000},
    {"id": 7, "tag": "실패경험", "prompt": "실패하거나 기대한 결과를 얻지 못한 경험과 이후 개선한 과정을 작성해 주세요.", "char_limit": 1000},
    {"id": 8, "tag": "강점·약점", "prompt": "직무 수행에 도움이 되는 강점과 보완 중인 약점을 실제 사례와 함께 작성해 주세요.", "char_limit": 1000},
    {"id": 9, "tag": "입사후포부", "prompt": "입사 후 기여하고 싶은 부분과 단계별 성장 계획을 작성해 주세요.", "char_limit": 1000},
    {"id": 10, "tag": "자유양식", "prompt": "자유 형식으로 자신을 소개해 주세요.", "char_limit": None},
]

_ESSAY_PROMPT = (
    "너는 자기소개서 작성 코치다. 문항과 지원자 프로필을 받아 초안을 쓴다.\n"
    "- 프로필의 실제 경험만 근거로 쓴다. 없는 경험을 만들지 않는다.\n"
    "- 한국어, 문단 2~3개, 구체적인 수치·사례 중심.\n"
    "{limit}\n\n[문항]\n{question}\n\n[지원자 프로필]\n{profile}"
)


def list_essay_questions() -> list[ResumeEssayQuestion]:
    return [ResumeEssayQuestion(**question) for question in _ESSAY_QUESTIONS]


async def essay_draft(question: str, char_limit, state: ResumeState) -> tuple:
    """자소서 초안 — 문항과 프로필을 LLM에 넘긴다. 목이면 안내만."""
    doc = state.doc
    profile_text = "\n".join(
        [f"- {s.title}: " + "; ".join(
            f"{i.get('title', '')} {i.get('org', '')} {' '.join(i.get('bullets', []))}".strip()
            for i in s.items
        ) for s in doc.sections if s.visible]
    ) or "(프로필 없음)"
    prompt = _ESSAY_PROMPT.format(
        question=question,
        limit=f"- {char_limit}자 이내로 쓴다." if char_limit else "",
        profile=profile_text[:4000],
    )
    raw = await get_llm().complete_json(prompt, {
        "type": "object", "properties": {"draft": {"type": "string"}}, "required": ["draft"],
    })
    draft = (raw or {}).get("draft", "")
    if not draft:
        return "", "지금은 목 모드예요 — API 키를 넣으면 기업 분석을 반영해 초안을 씁니다."
    return draft, ""


def list_templates() -> list[ResumeTemplate]:
    return [
        ResumeTemplate(id=k, name=_NAMES[k], kind=_KINDS[k], thumbnail=f"/thumbs/{k}.png", preset=v)
        for k, v in _PRESETS.items()
    ]


def render_html(
    state: ResumeState,
    kind: ResumeDocumentKind = ResumeDocumentKind.resume,
) -> str:
    style = state.style
    if kind == ResumeDocumentKind.resume:
        name = style.template if style.template in _PRESETS else "classic"
    else:
        name = kind.value
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


def render_pdf(
    state: ResumeState,
    kind: ResumeDocumentKind = ResumeDocumentKind.resume,
) -> bytes:
    return html_to_pdf(render_html(state, kind))


def render_bundle_pdf(
    documents: ResumeApplicationDocuments,
    included: list[ResumeDocumentKind],
) -> bytes:
    writer = PdfWriter()
    for kind in ResumeDocumentKind:
        if kind not in included:
            continue
        reader = PdfReader(BytesIO(render_pdf(getattr(documents, kind.value), kind)))
        for page in reader.pages:
            writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


async def chat(state, materials, message) -> tuple:
    llm = get_llm()
    prompt = _CHAT_PROMPT.format(
        state=state.model_dump_json(),
        materials="\n".join(f"- {m.label or m.kind}: {m.text}" for m in materials) or "(없음)",
        message=message,
    )
    raw = await llm.complete_json(prompt, ResumeState.model_json_schema())
    if not raw:
        return state, "지금은 목 모드예요 — API 키를 넣으면 실제로 편집합니다."
    try:
        return ResumeState.model_validate(raw), "반영했어요."
    except ValidationError:
        return state, "요청을 반영하지 못했어요. 다시 시도해 주세요."


def extract_material(filename: str, data: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        return "\n".join(pdf_pages(data))
    return data.decode("utf-8", errors="ignore")
