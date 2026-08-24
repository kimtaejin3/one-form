"""이력서 빌더 서비스 — 시드·챗·렌더·추출. 저장(DB) 없음."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import ValidationError

from app.ai.llm import get_llm
from app.core.pdf import pdf_pages
from app.profile.repository import get_profile
from app.resume.render import html_to_pdf
from app.resume.schemas import (
    ResumeDoc, ResumeEssayQuestion, ResumeEssaySet, ResumeHeader, ResumeLink,
    ResumePersonal, ResumeSection, ResumeState, ResumeStyle, ResumeTemplate,
)

_TPL_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(_TPL_DIR),
    autoescape=select_autoescape(["html"]),
)

_DENSITY_GAP = {"compact": 8, "normal": 14, "relaxed": 22}
_SCALE_PT = {"S": 10, "M": 11, "L": 12}
_DENSITY_MARGIN = {"compact": "12mm", "normal": "16mm", "relaxed": "20mm"}

# dev/resume 의 실제 테마를 이식: style.css → 표준, application.css → 형식, portfolio.css → 포트폴리오
_PRESETS = {
    "classic": ResumeStyle(template="classic", heading_style="plain", accent_color="#1f4fd8"),
    "formal": ResumeStyle(
        template="formal", heading_style="plain", accent_color="#374151", density="compact",
    ),
    "portfolio": ResumeStyle(
        template="portfolio", heading_style="plain", accent_color="#2b52e8", density="relaxed",
    ),
}
_KINDS = {"classic": "resume", "formal": "resume", "portfolio": "portfolio"}
_NAMES = {"classic": "표준", "formal": "형식 · 입사지원서", "portfolio": "포트폴리오"}

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


# 자소서 질문뱅크 — 기업별 세트. 세트를 고르면 그 기업의 자소서 문항이 문서에 구성된다.
_ESSAY_SETS: list[dict] = [
    {"company": "삼성전자", "deadline": "2025-09-03", "questions": [
        {"id": 1, "tag": "지원동기", "prompt": "삼성전자를 지원한 이유와 입사 후 회사에서 이루고 싶은 꿈을 기술하십시오.", "char_limit": 700},
        {"id": 2, "tag": "성장과정", "prompt": "본인의 성장과정을 간략히 기술하되 현재의 자신에게 가장 큰 영향을 끼친 사건, 인물 등을 포함하여 기술하시기 바랍니다.", "char_limit": 1500},
        {"id": 3, "tag": "사회이슈", "prompt": "최근 사회 이슈 중 중요하다고 생각되는 한 가지를 선택하고 이에 관한 자신의 견해를 기술해 주시기 바랍니다.", "char_limit": 1000},
        {"id": 4, "tag": "직무역량", "prompt": "지원한 직무 관련 본인의 전문지식과 경험을 작성하고, 본인이 지원 직무에 적합한 사유를 기술하시기 바랍니다.", "char_limit": 1000},
    ]},
    {"company": "현대오토에버", "deadline": "2025-08-04", "questions": [
        {"id": 5, "tag": "지원동기", "prompt": "현대오토에버의 해당 직무에 지원한 이유와 앞으로 키워 나갈 커리어 계획을 작성해 주시기 바랍니다.", "char_limit": 1000},
        {"id": 6, "tag": "직무역량", "prompt": "지원 직무와 관련하여 어떠한 역량을(지식/기술 등) 강점으로 가지고 있는지, 그 역량을 갖추기 위해 무슨 노력과 경험을 했는지 구체적으로 작성해 주시기 바랍니다.", "char_limit": 1500},
    ]},
    {"company": "포스코DX", "deadline": "2026-04-27", "questions": [
        {"id": 7, "tag": "지원동기", "prompt": "포스코DX에 지원하게 된 계기와 해당 분야에 관심을 가지게 된 이유를 구체적으로 설명해 주시길 바랍니다.", "char_limit": 600},
        {"id": 8, "tag": "직무역량", "prompt": "해당 분야에서 타인과 차별화될 수 있는 전문역량은 무엇인지 구체적으로 설명해 주시길 바랍니다.", "char_limit": 600},
        {"id": 9, "tag": "AI활용", "prompt": "생성형 AI 도구를 활용하여 생산성을 높이거나 더 나은 결과물을 만들어본 경험을 구체적으로 설명해 주시길 바랍니다.", "char_limit": 600},
    ]},
    {"company": "공통 · 자유양식", "deadline": "", "questions": [
        {"id": 10, "tag": "자유양식", "prompt": "자기소개서 (자유양식)", "char_limit": None},
        {"id": 11, "tag": "지원동기", "prompt": "지원 동기와 입사 후 포부를 작성해 주세요.", "char_limit": 1000},
        {"id": 12, "tag": "직무역량", "prompt": "직무와 관련한 본인의 강점과 그것을 보여준 경험을 작성해 주세요.", "char_limit": 1000},
    ]},
]

_ESSAY_PROMPT = (
    "너는 자기소개서 작성 코치다. 지원 기업과 문항, 지원자 프로필을 받아 초안을 쓴다.\n"
    "- 먼저 그 기업이 어떤 회사인지(사업·기술·인재상) 아는 범위에서 고려하되, 확실하지 않은 사실은 지어내지 않는다.\n"
    "- 프로필의 실제 경험만 근거로 쓴다. 없는 경험을 만들지 않는다.\n"
    "- 한국어, 문단 2~3개, 구체적인 수치·사례 중심.\n"
    "{limit}\n\n[지원 기업]\n{company}\n\n[문항]\n{question}\n\n[지원자 프로필]\n{profile}"
)


def list_essay_sets() -> list[ResumeEssaySet]:
    return [
        ResumeEssaySet(
            company=s["company"], deadline=s["deadline"],
            questions=[ResumeEssayQuestion(**q) for q in s["questions"]],
        )
        for s in _ESSAY_SETS
    ]


async def essay_draft(company: str, question: str, char_limit, state: ResumeState) -> tuple:
    """자소서 초안 — 기업(분석 대상)+문항+프로필을 LLM에 넘긴다. 목이면 안내만."""
    doc = state.doc
    profile_text = "\n".join(
        [f"- {s.title}: " + "; ".join(
            f"{i.get('title', '')} {i.get('org', '')} {' '.join(i.get('bullets', []))}".strip()
            for i in s.items
        ) for s in doc.sections if s.visible]
    ) or "(프로필 없음)"
    prompt = _ESSAY_PROMPT.format(
        company=company or "(미지정)", question=question,
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
