# 이력서 빌더 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 챗으로 내용·스타일을 편집해 이력서를 이쁜 PDF로 만드는 페이지를 백엔드 도메인 + 프론트 3-컬럼 페이지로 구현한다.

**Architecture:** 단일 진실원천은 `ResumeState = {doc, style}`(저장 없이 프론트 상태). 챗 turn은 `{state, materials, message}`를 받아 LLM(`complete_json`)이 수정한 `state`를 반환하고, `weasyprint(템플릿+state)`가 미리보기 HTML·PDF를 재생성한다. PDF를 직접 편집하지 않는다.

**Tech Stack:** FastAPI + uv, weasyprint(신규), Jinja2, Pydantic; React 19 + Vite + TanStack Query(FSD); OpenAPI→TS 타입 생성.

**Spec:** `docs/superpowers/specs/2026-08-19-resume-builder-design.md`

## Global Constraints

- **Node 22 필수** — JS 명령 전 `export PATH=~/.nvm/versions/node/v22.22.2/bin:$PATH`.
- **Python은 uv** — 의존성 추가 `uv add`, 실행 `uv run`(`apps/backend`에서).
- **API는 `/api` 프리픽스** — 새 라우터 `APIRouter(prefix="/api/resume", tags=["resume"])`.
- **도메인 4파일 패턴** — router·schemas·service(+templates). **repository 없음**(저장 안 함).
- **FE↔BE 타입은 백엔드 Pydantic이 원천** — 프론트에 타입 손으로 쓰지 말 것. 라우터에 `response_model=` 지정 후 루트에서 `pnpm gen:api`로 `schema.ts` 생성. entities가 `components['schemas'][...]`를 재-export.
- **OpenAPI 스키마 클래스명은 전역 유일** — profile에 이미 `Link`가 있으므로 resume는 **`Resume` 프리픽스**(`ResumeLink`·`ResumeSection`·`ResumeTemplate`·`ResumeMaterial`…).
- **FSD** — 슬라이스는 `index.ts`로만 노출, `@/<layer>/<slice>`로 임포트. 상위 레이어 임포트 금지(oxlint 강제). 조회는 `queryOptions`+`useSuspenseQuery`, 변경은 `useMutation`. `useEffect`로 fetch 금지.
- **커밋** — `type(scope): 제목`, 한국어 명령형 ≤50자, scope `resume`(백엔드/프론트 공통). 트레일러 `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- **weasyprint 네이티브 의존** — pango·cairo·gdk-pixbuf 필요. mac은 `brew install pango`.
- **CORS 포트 고정** — 3000/3001(변경 금지).

---

## File Structure

**백엔드 (`apps/backend/`)**
- `app/resume/__init__.py` — 빈 패키지
- `app/resume/schemas.py` — `ResumeDoc`·`ResumeStyle`·`ResumeState` + 요청/응답 + enum
- `app/resume/service.py` — `seed_state`·`chat`·`render_html`·`render_pdf`·`extract_material`·`list_templates`
- `app/resume/render.py` — weasyprint 얇은 래퍼 `html_to_pdf(html)->bytes`
- `app/resume/templates/classic.html`, `modern.html` — Jinja2 이력서 템플릿
- `app/resume/router.py` — 엔드포인트
- `app/main.py` — 라우터 등록(수정)
- `tests/test_resume.py` — 도메인 테스트

**프론트 (`apps/web/src/`)**
- `entities/resume/{model.ts,api.ts,index.ts}` — 타입 재-export + templatesQuery
- `features/resume-materials/{model.ts,ui/MaterialsPanel.tsx,index.ts}` — 자료·템플릿 패널
- `features/resume-chat/{model.ts,ui/ChatPanel.tsx,index.ts}` — 챗
- `pages/resume-builder/{ui/ResumeBuilderPage.tsx,index.ts}` — 3-컬럼 조립 + 미리보기 + PDF
- `app/App.tsx`, `widgets/header/ui/TabBar.tsx` — 라우트·탭(수정)

---

## Task 1: weasyprint 의존성 + 원시 PDF 렌더

네이티브 의존 리스크를 가장 먼저 제거한다.

**Files:**
- Modify: `apps/backend/pyproject.toml` (의존성)
- Create: `apps/backend/app/resume/__init__.py` (빈 파일)
- Create: `apps/backend/app/resume/render.py`
- Test: `apps/backend/tests/test_resume.py`

**Interfaces:**
- Produces: `app.resume.render.html_to_pdf(html: str) -> bytes`

- [ ] **Step 1: 의존성 추가**

`apps/backend`에서:
```bash
uv add weasyprint
```
설치 실패 시(pango 없음) mac: `brew install pango`, 재시도.

- [ ] **Step 2: 실패 테스트 작성** — `apps/backend/tests/test_resume.py`

```python
from app.resume.render import html_to_pdf


def test_html_to_pdf_returns_pdf_bytes():
    pdf = html_to_pdf("<h1>홍길동</h1>")
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 500
```

- [ ] **Step 3: 실패 확인**

```bash
uv run pytest tests/test_resume.py::test_html_to_pdf_returns_pdf_bytes -q
```
Expected: FAIL (`ModuleNotFoundError: app.resume.render`)

- [ ] **Step 4: 구현** — `apps/backend/app/resume/render.py`

```python
"""weasyprint 얇은 래퍼 — HTML 문자열 → PDF 바이트. state→HTML은 service가 담당."""
from weasyprint import HTML


def html_to_pdf(html: str) -> bytes:
    return HTML(string=html).write_pdf()
```
그리고 `apps/backend/app/resume/__init__.py`를 빈 파일로 생성.

- [ ] **Step 5: 통과 확인**

```bash
uv run pytest tests/test_resume.py -q
```
Expected: PASS

- [ ] **Step 6: 커밋**

```bash
git add apps/backend/pyproject.toml apps/backend/uv.lock apps/backend/app/resume/ apps/backend/tests/test_resume.py
git commit -m "feat(resume): weasyprint 의존성·PDF 렌더 래퍼 추가"
```

---

## Task 2: 스키마 (`ResumeDoc`·`ResumeStyle`·`ResumeState`)

**Files:**
- Create: `apps/backend/app/resume/schemas.py`
- Test: `apps/backend/tests/test_resume.py`

**Interfaces:**
- Produces: `ResumeState`, `ResumeDoc`, `ResumeStyle`, `ResumeHeader`, `ResumeLink`, `ResumeSection`, `ResumeMaterial`, `ResumeTemplate`, `ResumeChatRequest`, `ResumeChatResponse`, `ResumeRenderRequest`, `ResumeExtractResponse`, enum `SectionType`·`Density`·`HeadingStyle`·`Layout`·`FontScale`.

- [ ] **Step 1: 실패 테스트 작성** — `tests/test_resume.py`에 추가

```python
from app.resume.schemas import ResumeState, ResumeStyle, Density
import pytest
from pydantic import ValidationError


def test_default_state_uses_classic_normal():
    s = ResumeState(doc={"header": {"name": "홍길동"}})
    assert s.style.template == "classic"
    assert s.style.density == Density.normal


def test_invalid_density_rejected():
    with pytest.raises(ValidationError):
        ResumeStyle(density="huge")
```

- [ ] **Step 2: 실패 확인**

```bash
uv run pytest tests/test_resume.py -q
```
Expected: FAIL (`app.resume.schemas` 없음)

- [ ] **Step 3: 구현** — `apps/backend/app/resume/schemas.py`

```python
"""이력서 빌더 도메인 스키마. 클래스명은 전역 유일해야 함(Resume 프리픽스)."""
from enum import Enum

from pydantic import BaseModel


class SectionType(str, Enum):
    career = "career"
    project = "project"
    education = "education"
    skill = "skill"
    award = "award"
    certificate = "certificate"
    language = "language"
    activity = "activity"
    custom = "custom"


class Density(str, Enum):
    compact = "compact"
    normal = "normal"
    relaxed = "relaxed"


class HeadingStyle(str, Enum):
    plain = "plain"
    bar = "bar"
    underline = "underline"


class Layout(str, Enum):
    single = "single"
    two_column = "two-column"


class FontScale(str, Enum):
    S = "S"
    M = "M"
    L = "L"


class ResumeLink(BaseModel):
    label: str
    url: str


class ResumeHeader(BaseModel):
    name: str
    contact: list[str] = []
    links: list[ResumeLink] = []


class ResumeSection(BaseModel):
    id: str
    type: SectionType
    title: str
    order: int
    visible: bool = True
    # ponytail: items는 타입별 자유 dict — 렌더 템플릿이 title·org·period·bullets·note·stack·name
    #   키를 읽는다. 타입별 항목 모델은 phase 2(지금은 dict로 충분).
    items: list[dict] = []


class ResumeDoc(BaseModel):
    header: ResumeHeader
    summary: str = ""
    sections: list[ResumeSection] = []


class ResumeStyle(BaseModel):
    template: str = "classic"
    font: str = "Pretendard"
    accent_color: str = "#334155"
    density: Density = Density.normal
    heading_style: HeadingStyle = HeadingStyle.bar
    layout: Layout = Layout.single
    font_scale: FontScale = FontScale.M


class ResumeState(BaseModel):
    doc: ResumeDoc
    style: ResumeStyle = ResumeStyle()


class ResumeMaterial(BaseModel):
    kind: str  # file | note | link
    label: str = ""
    text: str


class ResumeTemplate(BaseModel):
    id: str
    name: str
    thumbnail: str
    preset: ResumeStyle


class ResumeChatRequest(BaseModel):
    state: ResumeState
    materials: list[ResumeMaterial] = []
    message: str


class ResumeChatResponse(BaseModel):
    state: ResumeState
    reply: str


class ResumeRenderRequest(BaseModel):
    state: ResumeState


class ResumeExtractResponse(BaseModel):
    text: str
```

- [ ] **Step 4: 통과 확인**

```bash
uv run pytest tests/test_resume.py -q
```
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add apps/backend/app/resume/schemas.py apps/backend/tests/test_resume.py
git commit -m "feat(resume): ResumeState 스키마 정의"
```

---

## Task 3: 시드 서비스 (프로필 → `ResumeState`)

**Files:**
- Create: `apps/backend/app/resume/service.py`
- Test: `apps/backend/tests/test_resume.py`

**Interfaces:**
- Consumes: `app.profile.repository.get_profile() -> dict` (async), `app.resume.schemas.*`
- Produces: `app.resume.service.seed_state() -> ResumeState`

- [ ] **Step 1: 실패 테스트 작성** — `tests/test_resume.py`에 추가

```python
import asyncio
from app.resume.service import seed_state


def test_seed_state_maps_profile_header_and_sections():
    s = asyncio.run(seed_state())
    assert s.doc.header.name  # 프로필 목이 등록돼 있으므로 이름이 있다
    types = {sec.type.value for sec in s.doc.sections}
    assert "career" in types
    # 섹션 순서는 0..n 연속
    orders = [sec.order for sec in s.doc.sections]
    assert orders == sorted(orders)
```

- [ ] **Step 2: 실패 확인**

```bash
uv run pytest tests/test_resume.py -q
```
Expected: FAIL (`app.resume.service` 없음)

- [ ] **Step 3: 구현** — `apps/backend/app/resume/service.py`

```python
"""이력서 빌더 서비스 — 시드·챗·렌더·추출. 저장(DB) 없음."""
from app.profile.repository import get_profile
from app.resume.schemas import (
    ResumeDoc, ResumeHeader, ResumeLink, ResumeSection, ResumeState,
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
```

- [ ] **Step 4: 통과 확인**

```bash
uv run pytest tests/test_resume.py -q
```
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add apps/backend/app/resume/service.py apps/backend/tests/test_resume.py
git commit -m "feat(resume): 프로필→ResumeState 시드"
```

---

## Task 4: 템플릿 + 렌더 (`render_html`·`render_pdf`·`list_templates`)

**Files:**
- Create: `apps/backend/app/resume/templates/classic.html`
- Create: `apps/backend/app/resume/templates/modern.html`
- Modify: `apps/backend/app/resume/service.py`
- Modify: `apps/backend/pyproject.toml` (jinja2 — 이미 있으면 생략)
- Test: `apps/backend/tests/test_resume.py`

**Interfaces:**
- Consumes: `seed_state`, `app.resume.render.html_to_pdf`, `ResumeState`
- Produces: `service.render_html(state: ResumeState) -> str`, `service.render_pdf(state: ResumeState) -> bytes`, `service.list_templates() -> list[ResumeTemplate]`

- [ ] **Step 1: jinja2 확인/추가**

```bash
uv run python -c "import jinja2" || uv add jinja2
```

- [ ] **Step 2: 실패 테스트 작성** — `tests/test_resume.py`에 추가

```python
from app.resume.service import render_html, render_pdf, list_templates


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
```

- [ ] **Step 3: 실패 확인**

```bash
uv run pytest tests/test_resume.py -q
```
Expected: FAIL (`render_html` 없음)

- [ ] **Step 4: 템플릿 작성** — `apps/backend/app/resume/templates/classic.html`

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<style>
  @page { size: A4; margin: {{ margin }}; }
  :root { }
  body {
    font-family: "{{ style.font }}", -apple-system, "Apple SD Gothic Neo", sans-serif;
    font-size: {{ base_pt }}pt; color: #1f2937; line-height: 1.5; margin: 0;
  }
  h1 { font-size: {{ base_pt + 8 }}pt; margin: 0 0 2px; color: {{ style.accent_color }}; }
  .contact { color: #6b7280; font-size: {{ base_pt - 1 }}pt; margin-bottom: {{ gap }}px; }
  .summary { margin-bottom: {{ gap }}px; }
  section { margin-bottom: {{ gap }}px; }
  h2 {
    font-size: {{ base_pt + 2 }}pt; margin: 0 0 6px; color: {{ style.accent_color }};
    {% if style.heading_style.value == 'bar' %}border-left: 3px solid {{ style.accent_color }}; padding-left: 6px;{% endif %}
    {% if style.heading_style.value == 'underline' %}border-bottom: 1px solid {{ style.accent_color }}; padding-bottom: 2px;{% endif %}
  }
  .item { margin-bottom: {{ gap // 2 }}px; }
  .item .row { display: flex; justify-content: space-between; }
  .item strong { font-weight: 600; }
  .item .org { color: #4b5563; }
  .item .period { color: #9ca3af; font-size: {{ base_pt - 1 }}pt; }
  ul { margin: 3px 0 0; padding-left: 16px; }
  .stack { color: #6b7280; font-size: {{ base_pt - 1 }}pt; }
</style>
</head>
<body>
  <h1>{{ doc.header.name }}</h1>
  <div class="contact">
    {{ doc.header.contact | join(' · ') }}
    {% for l in doc.header.links %} · {{ l.label }}{% endfor %}
  </div>
  {% if doc.summary %}<div class="summary">{{ doc.summary }}</div>{% endif %}
  {% for sec in sections %}
  <section>
    <h2>{{ sec.title }}</h2>
    {% for it in sec.items %}
    <div class="item">
      <div class="row">
        <span><strong>{{ it.title }}</strong>{% if it.org %} <span class="org">· {{ it.org }}</span>{% endif %}{% if it.name %}{{ it.name }}{% endif %}</span>
        {% if it.period %}<span class="period">{{ it.period }}</span>{% endif %}
      </div>
      {% if it.note %}<div>{{ it.note }}</div>{% endif %}
      {% if it.bullets %}<ul>{% for b in it.bullets %}<li>{{ b }}</li>{% endfor %}</ul>{% endif %}
      {% if it.stack %}<div class="stack">{{ it.stack | join(' · ') }}</div>{% endif %}
    </div>
    {% endfor %}
  </section>
  {% endfor %}
</body>
</html>
```

- [ ] **Step 5: modern 템플릿 작성** — `apps/backend/app/resume/templates/modern.html`

classic을 복제하되 헤더를 강조한 변형(같은 변수 사용):
```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<style>
  @page { size: A4; margin: {{ margin }}; }
  body { font-family: "{{ style.font }}", -apple-system, "Apple SD Gothic Neo", sans-serif;
         font-size: {{ base_pt }}pt; color: #111827; line-height: 1.55; margin: 0; }
  header { background: {{ style.accent_color }}; color: #fff; padding: 16px 18px; margin: 0 0 {{ gap }}px; }
  header h1 { margin: 0; font-size: {{ base_pt + 10 }}pt; }
  header .contact { color: rgba(255,255,255,.85); font-size: {{ base_pt - 1 }}pt; }
  section { margin: 0 0 {{ gap }}px; }
  h2 { font-size: {{ base_pt + 2 }}pt; color: {{ style.accent_color }}; margin: 0 0 6px;
       text-transform: uppercase; letter-spacing: .04em; }
  .item { margin-bottom: {{ gap // 2 }}px; }
  .item .row { display: flex; justify-content: space-between; }
  .item strong { font-weight: 600; } .item .org { color: #4b5563; }
  .item .period { color: #9ca3af; font-size: {{ base_pt - 1 }}pt; }
  ul { margin: 3px 0 0; padding-left: 16px; } .stack { color: #6b7280; font-size: {{ base_pt - 1 }}pt; }
</style>
</head>
<body>
  <header>
    <h1>{{ doc.header.name }}</h1>
    <div class="contact">{{ doc.header.contact | join(' · ') }}{% for l in doc.header.links %} · {{ l.label }}{% endfor %}</div>
  </header>
  {% if doc.summary %}<div class="summary" style="margin:0 0 {{ gap }}px">{{ doc.summary }}</div>{% endif %}
  {% for sec in sections %}
  <section>
    <h2>{{ sec.title }}</h2>
    {% for it in sec.items %}
    <div class="item">
      <div class="row">
        <span><strong>{{ it.title }}</strong>{% if it.org %} <span class="org">· {{ it.org }}</span>{% endif %}{% if it.name %}{{ it.name }}{% endif %}</span>
        {% if it.period %}<span class="period">{{ it.period }}</span>{% endif %}
      </div>
      {% if it.note %}<div>{{ it.note }}</div>{% endif %}
      {% if it.bullets %}<ul>{% for b in it.bullets %}<li>{{ b }}</li>{% endfor %}</ul>{% endif %}
      {% if it.stack %}<div class="stack">{{ it.stack | join(' · ') }}</div>{% endif %}
    </div>
    {% endfor %}
  </section>
  {% endfor %}
</body>
</html>
```

- [ ] **Step 6: service에 렌더·템플릿 목록 추가** — `apps/backend/app/resume/service.py`에 추가

```python
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.resume.render import html_to_pdf
from app.resume.schemas import ResumeStyle, ResumeTemplate

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


def list_templates() -> list[ResumeTemplate]:
    names = {"classic": "클래식", "modern": "모던"}
    return [
        ResumeTemplate(id=k, name=names[k], thumbnail=f"/thumbs/{k}.png", preset=v)
        for k, v in _PRESETS.items()
    ]


def render_html(state) -> str:
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


def render_pdf(state) -> bytes:
    return html_to_pdf(render_html(state))
```

- [ ] **Step 7: 통과 확인**

```bash
uv run pytest tests/test_resume.py -q
```
Expected: PASS (3개 추가 테스트 포함 전부)

- [ ] **Step 8: 커밋**

```bash
git add apps/backend/app/resume/ apps/backend/pyproject.toml apps/backend/uv.lock apps/backend/tests/test_resume.py
git commit -m "feat(resume): 파라메트릭 템플릿·HTML/PDF 렌더"
```

---

## Task 5: 챗 서비스 (LLM `complete_json` → 검증된 state)

**Files:**
- Modify: `apps/backend/app/resume/service.py`
- Test: `apps/backend/tests/test_resume.py`

**Interfaces:**
- Consumes: `app.ai.llm.get_llm().complete_json(prompt, schema) -> dict`, `ResumeState`, `ResumeMaterial`
- Produces: `service.chat(state: ResumeState, materials: list[ResumeMaterial], message: str) -> tuple[ResumeState, str]`

- [ ] **Step 1: 실패 테스트 작성** — `tests/test_resume.py`에 추가

목 LLM(키 없음, conftest가 키 제거)은 `complete_json`이 `{}`를 반환 → state 불변.

```python
from app.resume.service import chat


def test_chat_with_mock_keeps_state():
    s = asyncio.run(seed_state())
    new_state, reply = asyncio.run(chat(s, [], "요약 써줘"))
    assert new_state == s          # 목은 변경 없음
    assert reply                    # 안내 문구는 있음


def test_chat_applies_valid_llm_output(monkeypatch):
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
    s = asyncio.run(seed_state())

    class BadLlm:
        async def complete_json(self, prompt, schema):
            return {"doc": {"header": {}}}  # name 누락 → 검증 실패

    monkeypatch.setattr("app.resume.service.get_llm", lambda: BadLlm())
    new_state, reply = asyncio.run(chat(s, [], "망가뜨려"))
    assert new_state == s  # 옛 state 유지
```

- [ ] **Step 2: 실패 확인**

```bash
uv run pytest tests/test_resume.py -q
```
Expected: FAIL (`chat` 없음)

- [ ] **Step 3: 구현** — `apps/backend/app/resume/service.py`에 추가

```python
from pydantic import ValidationError

from app.ai.llm import get_llm

_CHAT_PROMPT = (
    "너는 이력서 편집기다. 아래 현재 이력서 상태(JSON)와 사용자 명령을 받아,\n"
    "명령이 요구하는 최소 변경만 적용한 '전체 ResumeState JSON'을 반환하라.\n"
    "- 내용 명령이면 doc를, 스타일 명령이면 style를 고친다. 나머지는 그대로 둔다.\n"
    "- style 값은 스키마 enum만 사용한다(임의 CSS 금지).\n"
    "- 참고 자료가 있으면 내용 보강에 활용하되 사실을 지어내지 않는다.\n\n"
    "[현재 상태]\n{state}\n\n[참고 자료]\n{materials}\n\n[명령]\n{message}"
)


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
```

- [ ] **Step 4: 통과 확인**

```bash
uv run pytest tests/test_resume.py -q
```
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add apps/backend/app/resume/service.py apps/backend/tests/test_resume.py
git commit -m "feat(resume): LLM 챗 편집 서비스"
```

---

## Task 6: 자료 추출 (`extract_material`)

**Files:**
- Modify: `apps/backend/app/resume/service.py`
- Test: `apps/backend/tests/test_resume.py`

**Interfaces:**
- Consumes: `app.core.pdf.pdf_pages(pdf_bytes: bytes) -> list[str]`
- Produces: `service.extract_material(filename: str, data: bytes) -> str`

- [ ] **Step 1: 실패 테스트 작성** — `tests/test_resume.py`에 추가

```python
from app.resume.service import extract_material


def test_extract_text_file():
    assert extract_material("memo.txt", "안녕 이력".encode()) == "안녕 이력"
```

- [ ] **Step 2: 실패 확인**

```bash
uv run pytest tests/test_resume.py -q
```
Expected: FAIL (`extract_material` 없음)

- [ ] **Step 3: 구현** — `apps/backend/app/resume/service.py`에 추가

```python
from app.core.pdf import pdf_pages


def extract_material(filename: str, data: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        return "\n".join(pdf_pages(data))
    return data.decode("utf-8", errors="ignore")
```

- [ ] **Step 4: 통과 확인**

```bash
uv run pytest tests/test_resume.py -q
```
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add apps/backend/app/resume/service.py apps/backend/tests/test_resume.py
git commit -m "feat(resume): 업로드 자료 텍스트 추출"
```

---

## Task 7: 라우터 + main 등록 + 타입 생성

**Files:**
- Create: `apps/backend/app/resume/router.py`
- Modify: `apps/backend/app/main.py`
- Modify: `apps/web/src/shared/api/schema.ts` (생성물, `pnpm gen:api`)
- Test: `apps/backend/tests/test_resume.py`

**Interfaces:**
- Consumes: `app.resume.service.*`, `app.resume.schemas.*`
- Produces: 엔드포인트 `GET /api/resume/templates`·`GET /api/resume/seed`·`POST /api/resume/materials/extract`·`POST /api/resume/chat`·`POST /api/resume/preview`·`POST /api/resume/render`

> 시드는 입력이 없으므로 **GET**(프론트가 `useSuspenseQuery`로 소비 — 스펙의 POST에서 개선).

- [ ] **Step 1: 실패 테스트 작성** — `tests/test_resume.py`에 추가

```python
def test_endpoints_smoke(client):
    assert client.get("/api/resume/templates").json()[0]["id"]
    state = client.get("/api/resume/seed").json()
    assert "doc" in state and "style" in state
    html = client.post("/api/resume/preview", json={"state": state})
    assert html.status_code == 200 and state["doc"]["header"]["name"] in html.text
    pdf = client.post("/api/resume/render", json={"state": state})
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    chat = client.post("/api/resume/chat", json={"state": state, "materials": [], "message": "요약 써줘"})
    assert "state" in chat.json() and "reply" in chat.json()
```

`client` 픽스처는 기존 `conftest.py` 제공(키 없음 → 목 LLM).

- [ ] **Step 2: 실패 확인**

```bash
uv run pytest tests/test_resume.py::test_endpoints_smoke -q
```
Expected: FAIL (라우터 없음 → 404)

- [ ] **Step 3: 라우터 구현** — `apps/backend/app/resume/router.py`

```python
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
```

- [ ] **Step 4: main.py 등록** — `apps/backend/app/main.py`

import 추가(알파벳 순 위치):
```python
from app.resume.router import router as resume_router
```
include 루프에 추가:
```python
    profile_router,
    resume_router,
    companies_router,
```

- [ ] **Step 5: 통과 확인**

```bash
uv run pytest tests/test_resume.py -q
```
Expected: PASS (전체)

- [ ] **Step 6: 프론트 타입 생성**

루트에서:
```bash
export PATH=~/.nvm/versions/node/v22.22.2/bin:$PATH
pnpm gen:api
grep -c "ResumeState" apps/web/src/shared/api/schema.ts   # >0 이어야 함
```

- [ ] **Step 7: 커밋**

```bash
git add apps/backend/app/resume/router.py apps/backend/app/main.py apps/backend/tests/test_resume.py apps/web/src/shared/api/schema.ts
git commit -m "feat(resume): 라우터·엔드포인트 + 타입 생성"
```

---

## Task 8: 프론트 엔티티 (`entities/resume`)

**Files:**
- Create: `apps/web/src/entities/resume/model.ts`
- Create: `apps/web/src/entities/resume/api.ts`
- Create: `apps/web/src/entities/resume/index.ts`

**Interfaces:**
- Consumes: `components['schemas'][...]`(생성됨), `@/shared/api`의 `api`
- Produces: 타입 `ResumeState`·`ResumeTemplate`·`ResumeMaterial`·`ResumeChatResponse`; `resumeSeedQuery`·`resumeTemplatesQuery`

- [ ] **Step 1: model.ts**

```ts
import type { components } from '@/shared/api'

export type ResumeState = components['schemas']['ResumeState']
export type ResumeStyle = components['schemas']['ResumeStyle']
export type ResumeTemplate = components['schemas']['ResumeTemplate']
export type ResumeMaterial = components['schemas']['ResumeMaterial']
export type ResumeChatResponse = components['schemas']['ResumeChatResponse']
```

- [ ] **Step 2: api.ts**

```ts
import { queryOptions } from '@tanstack/react-query'
import { api } from '@/shared/api'
import type { ResumeState, ResumeTemplate } from './model'

export const resumeSeedQuery = queryOptions({
  queryKey: ['resume-seed'],
  queryFn: () => api<ResumeState>('/resume/seed'),
})

export const resumeTemplatesQuery = queryOptions({
  queryKey: ['resume-templates'],
  queryFn: () => api<ResumeTemplate[]>('/resume/templates'),
})
```

- [ ] **Step 3: index.ts**

```ts
export * from './model'
export { resumeSeedQuery, resumeTemplatesQuery } from './api'
```

- [ ] **Step 4: 타입체크**

```bash
export PATH=~/.nvm/versions/node/v22.22.2/bin:$PATH
pnpm --filter @one-form/web exec tsc -b
```
Expected: 에러 없음

- [ ] **Step 5: 커밋**

```bash
git add apps/web/src/entities/resume/
git commit -m "feat(resume): entities/resume 타입·쿼리"
```

---

## Task 9: 자료·템플릿 패널 (`features/resume-materials`)

**Files:**
- Create: `apps/web/src/features/resume-materials/model.ts`
- Create: `apps/web/src/features/resume-materials/ui/MaterialsPanel.tsx`
- Create: `apps/web/src/features/resume-materials/index.ts`

**Interfaces:**
- Consumes: `@/entities/resume`(`resumeTemplatesQuery`·`ResumeMaterial`·`ResumeState`), `@/shared/ui`의 `Dropzone`, `@/shared/api`의 `post`
- Produces: `MaterialsPanel` 컴포넌트, `useExtractMaterial` 훅

MaterialsPanel props: `{ state, materials, onAddMaterial, onTemplate }`.

- [ ] **Step 1: model.ts** — 파일 추출 훅

```ts
import { useMutation } from '@tanstack/react-query'
import type { ResumeMaterial } from '@/entities/resume'

// 업로드는 multipart라 JSON 헬퍼 대신 fetch(FormData). Vite가 /api를 프록시.
export function useExtractMaterial(onText: (m: ResumeMaterial) => void) {
  return useMutation({
    mutationFn: async (file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch('/api/resume/materials/extract', { method: 'POST', body: fd })
      if (!res.ok) throw new Error('extract failed')
      return (await res.json()) as { text: string }
    },
    onSuccess: (res, file) =>
      onText({ kind: 'file', label: file.name, text: res.text }),
  })
}
```

- [ ] **Step 2: MaterialsPanel.tsx**

```tsx
import { useState } from 'react'
import { useSuspenseQuery } from '@tanstack/react-query'
import { Dropzone } from '@/shared/ui'
import { resumeTemplatesQuery, type ResumeMaterial, type ResumeState } from '@/entities/resume'
import { useExtractMaterial } from '../model'

interface Props {
  state: ResumeState
  materials: ResumeMaterial[]
  onAddMaterial: (m: ResumeMaterial) => void
  onTemplate: (templateId: string) => void
}

export function MaterialsPanel({ state, materials, onAddMaterial, onTemplate }: Props) {
  const { data: templates } = useSuspenseQuery(resumeTemplatesQuery)
  const extract = useExtractMaterial(onAddMaterial)
  const [note, setNote] = useState('')

  return (
    <aside className="resume-materials">
      <section>
        <h3>템플릿</h3>
        <div className="resume-template-list">
          {templates.map((t) => (
            <button
              key={t.id}
              className={state.style.template === t.id ? 'active' : ''}
              onClick={() => onTemplate(t.id)}
            >
              {t.name}
            </button>
          ))}
        </div>
      </section>

      <section>
        <h3>자료 추가</h3>
        <Dropzone onFile={(f) => extract.mutate(f)} accept=".pdf,.txt,.md" />
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="메모·경험을 붙여넣기"
        />
        <button
          disabled={!note.trim()}
          onClick={() => { onAddMaterial({ kind: 'note', label: '메모', text: note }); setNote('') }}
        >
          메모 추가
        </button>
        <ul className="resume-material-chips">
          {materials.map((m, i) => <li key={i}>{m.label || m.kind}</li>)}
        </ul>
      </section>
    </aside>
  )
}
```

> `Dropzone`의 실제 props는 `@/shared/ui/Dropzone`를 열어 확인하고 `onFile`/`accept` 이름을 맞출 것. 시그니처가 다르면 그에 맞게 호출만 수정.

- [ ] **Step 3: index.ts**

```ts
export { MaterialsPanel } from './ui/MaterialsPanel'
```

- [ ] **Step 4: 타입체크·lint**

```bash
export PATH=~/.nvm/versions/node/v22.22.2/bin:$PATH
pnpm --filter @one-form/web exec tsc -b && pnpm --filter @one-form/web lint
```
Expected: 에러 없음(레이어 경계 통과)

- [ ] **Step 5: 커밋**

```bash
git add apps/web/src/features/resume-materials/
git commit -m "feat(resume): 자료·템플릿 패널"
```

---

## Task 10: 챗 패널 (`features/resume-chat`)

**Files:**
- Create: `apps/web/src/features/resume-chat/model.ts`
- Create: `apps/web/src/features/resume-chat/ui/ChatPanel.tsx`
- Create: `apps/web/src/features/resume-chat/index.ts`
- Test: `apps/web/src/features/resume-chat/model.test.ts`

**Interfaces:**
- Consumes: `@/shared/api`의 `post`, `@/entities/resume`
- Produces: `useResumeChat` 훅, `ChatPanel` 컴포넌트

- [ ] **Step 1: 실패 테스트 작성** — `model.test.ts`

```ts
import { describe, it, expect, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useResumeChat } from './model'
import * as apiModule from '@/shared/api'

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient()
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

describe('useResumeChat', () => {
  it('반환된 state·reply를 콜백에 넘긴다', async () => {
    const fakeState = { doc: { header: { name: 'A', contact: [], links: [] }, summary: 'x', sections: [] }, style: {} }
    vi.spyOn(apiModule, 'post').mockResolvedValue({ state: fakeState, reply: '반영했어요.' } as never)
    const onState = vi.fn()
    const { result } = renderHook(() => useResumeChat(onState), { wrapper })

    result.current.mutate({ state: fakeState as never, materials: [], message: '요약' })
    await waitFor(() => expect(onState).toHaveBeenCalledWith(fakeState, '반영했어요.'))
  })
})
```

- [ ] **Step 2: 실패 확인**

```bash
export PATH=~/.nvm/versions/node/v22.22.2/bin:$PATH
pnpm --filter @one-form/web test -- resume-chat
```
Expected: FAIL (`./model` 없음)

- [ ] **Step 3: model.ts**

```ts
import { useMutation } from '@tanstack/react-query'
import { post } from '@/shared/api'
import type { ResumeState, ResumeMaterial, ResumeChatResponse } from '@/entities/resume'

export function useResumeChat(onState: (s: ResumeState, reply: string) => void) {
  return useMutation({
    mutationFn: (v: { state: ResumeState; materials: ResumeMaterial[]; message: string }) =>
      post<ResumeChatResponse>('/resume/chat', v),
    onSuccess: (res) => onState(res.state, res.reply),
  })
}
```

- [ ] **Step 4: ChatPanel.tsx**

```tsx
import { useState } from 'react'
import type { ResumeMaterial, ResumeState } from '@/entities/resume'
import { useResumeChat } from '../model'

interface Msg { role: 'user' | 'ai'; text: string }
interface Props {
  state: ResumeState
  materials: ResumeMaterial[]
  onState: (s: ResumeState) => void
}

export function ChatPanel({ state, materials, onState }: Props) {
  const [log, setLog] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const chat = useResumeChat((s, reply) => {
    onState(s)
    setLog((l) => [...l, { role: 'ai', text: reply }])
  })

  const send = () => {
    const message = input.trim()
    if (!message) return
    setLog((l) => [...l, { role: 'user', text: message }])
    chat.mutate({ state, materials, message })
    setInput('')
  }

  return (
    <aside className="resume-chat">
      <div className="resume-chat-log">
        {log.map((m, i) => <div key={i} className={`msg ${m.role}`}>{m.text}</div>)}
        {chat.isPending && <div className="msg ai">…</div>}
      </div>
      <div className="resume-chat-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
          placeholder="예: 경력을 성과 중심으로 다듬고 제목을 남색으로"
        />
        <button onClick={send} disabled={chat.isPending}>보내기</button>
      </div>
    </aside>
  )
}
```

- [ ] **Step 5: index.ts**

```ts
export { ChatPanel } from './ui/ChatPanel'
export { useResumeChat } from './model'
```

- [ ] **Step 6: 통과 확인**

```bash
pnpm --filter @one-form/web test -- resume-chat
```
Expected: PASS

- [ ] **Step 7: 커밋**

```bash
git add apps/web/src/features/resume-chat/
git commit -m "feat(resume): AI 챗 패널"
```

---

## Task 11: 페이지 조립 + 라우트 + 탭 + 미리보기·PDF

**Files:**
- Create: `apps/web/src/pages/resume-builder/ui/ResumeBuilderPage.tsx`
- Create: `apps/web/src/pages/resume-builder/index.ts`
- Modify: `apps/web/src/app/App.tsx`
- Modify: `apps/web/src/widgets/header/ui/TabBar.tsx`
- Modify: `apps/web/src/app/styles/index.css` (3-컬럼 레이아웃)

**Interfaces:**
- Consumes: `@/entities/resume`(`resumeSeedQuery`), `@/features/resume-materials`, `@/features/resume-chat`

- [ ] **Step 1: ResumeBuilderPage.tsx**

```tsx
import { useMemo, useState } from 'react'
import { useSuspenseQuery } from '@tanstack/react-query'
import { resumeSeedQuery, type ResumeMaterial, type ResumeState } from '@/entities/resume'
import { MaterialsPanel } from '@/features/resume-materials'
import { ChatPanel } from '@/features/resume-chat'

export function ResumeBuilderPage() {
  const { data: seed } = useSuspenseQuery(resumeSeedQuery)
  const [state, setState] = useState<ResumeState>(() => seed)
  const [materials, setMaterials] = useState<ResumeMaterial[]>([])
  const [html, setHtml] = useState('')

  // state가 바뀔 때마다 미리보기 HTML을 서버에서 재렌더. useEffect 대신 파생 트리거로 최소화.
  const stateKey = useMemo(() => JSON.stringify(state), [state])
  useSuspenseQuery({
    queryKey: ['resume-preview', stateKey],
    queryFn: async () => {
      const res = await fetch('/api/resume/preview', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ state }),
      })
      const text = await res.text()
      setHtml(text)
      return text
    },
  })

  const download = async () => {
    const res = await fetch('/api/resume/render', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ state }),
    })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'resume.pdf'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="resume-builder">
      <MaterialsPanel
        state={state}
        materials={materials}
        onAddMaterial={(m) => setMaterials((ms) => [...ms, m])}
        onTemplate={(templateId) => setState((s) => ({ ...s, style: { ...s.style, template: templateId } }))}
      />
      <div className="resume-preview">
        <iframe title="이력서 미리보기" srcDoc={html} />
        <button className="resume-download" onClick={download}>📄 PDF 내려받기</button>
      </div>
      <ChatPanel state={state} materials={materials} onState={setState} />
    </div>
  )
}
```

- [ ] **Step 2: index.ts**

```ts
export { ResumeBuilderPage } from './ui/ResumeBuilderPage'
```

- [ ] **Step 3: App.tsx 라우트 추가**

import:
```tsx
import { ResumeBuilderPage } from '@/pages/resume-builder'
```
ROUTES 배열에(profile 다음):
```tsx
  { path: '/resume', element: <ResumeBuilderPage /> },
```

- [ ] **Step 4: TabBar.tsx 탭 추가**

NAV 배열에(profile 다음). 아이콘은 문서 성격이라 기존 `'description'` 재사용:
```tsx
  { to: '/resume', label: '이력서 빌더', icon: 'description' },
```

- [ ] **Step 5: 레이아웃 CSS** — `apps/web/src/app/styles/index.css` 끝에 추가

```css
.resume-builder { display: grid; grid-template-columns: 280px 1fr 320px; gap: 12px; height: calc(100vh - 120px); }
.resume-materials, .resume-chat { overflow-y: auto; padding: 12px; border: 1px solid var(--of-border); border-radius: 10px; }
.resume-preview { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.resume-preview iframe { flex: 1; width: 100%; border: 1px solid var(--of-border); border-radius: 10px; background: #fff; }
.resume-template-list { display: flex; gap: 6px; flex-wrap: wrap; }
.resume-template-list button.active { border-color: var(--of-primary); color: var(--of-primary); }
.resume-material-chips { list-style: none; padding: 0; display: flex; gap: 6px; flex-wrap: wrap; }
.resume-chat { display: flex; flex-direction: column; }
.resume-chat-log { flex: 1; display: flex; flex-direction: column; gap: 6px; overflow-y: auto; }
.resume-chat-log .msg.user { align-self: flex-end; background: var(--of-surface-alt); border-radius: 8px; padding: 6px 10px; }
.resume-chat-log .msg.ai { align-self: flex-start; color: var(--of-body); }
.resume-chat-input { display: flex; gap: 6px; }
.resume-chat-input textarea { flex: 1; resize: none; }
```

- [ ] **Step 6: 검증 — 타입체크·lint·빌드**

```bash
export PATH=~/.nvm/versions/node/v22.22.2/bin:$PATH
pnpm --filter @one-form/web lint
pnpm --filter @one-form/web build
```
Expected: 둘 다 성공

- [ ] **Step 7: 라이브 확인 (백엔드·web 실행 중)**

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3001/api/resume/seed   # 200
```
브라우저 http://localhost:3001/resume — 3-컬럼, 미리보기에 이력서, PDF 내려받기 동작, 챗 입력 시 목 안내 reply.

- [ ] **Step 8: 커밋**

```bash
git add apps/web/src/pages/resume-builder/ apps/web/src/app/App.tsx apps/web/src/widgets/header/ui/TabBar.tsx apps/web/src/app/styles/index.css
git commit -m "feat(resume): 이력서 빌더 페이지·라우트·탭"
```

---

## Self-Review (작성자 체크)

**Spec coverage:**
- §3 원리(state 수정→재생성) → Task 4·5·7 ✓
- §4 데이터 모델(ResumeDoc/Style/State) → Task 2 ✓
- §5 3-컬럼 UX + 라이브 미리보기 → Task 11 ✓
- §6 백엔드 도메인·6엔드포인트·LLM·weasyprint·pdf.py 재사용 → Task 1·3·4·5·6·7 ✓
- §7 프론트 페이지·피처·엔티티·탭 → Task 8·9·10·11 ✓
- §8 에러 처리(무효 LLM→옛 state, 미등록→빈 doc) → Task 5·3 ✓
- §9 테스트 → 각 Task TDD + 계약(gen:api) Task 7 ✓
- §10 YAGNI(포트폴리오·DB·크롤링 제외) → 계획에 없음 ✓

**Placeholder scan:** 실제 코드·명령 포함, "TBD/적절히 처리" 없음. `Dropzone` props는 파일 확인 지시(1줄) — 실제 시그니처가 코드베이스에 있어 플레이스홀더 아님.

**Type consistency:** 백엔드 `ResumeState/ResumeChatResponse/ResumeTemplate/ResumeMaterial` ↔ 프론트 재-export 동일. `seed_state`/`chat`/`render_html`/`render_pdf`/`extract_material`/`list_templates` 이름 Task 간 일치. `useResumeChat(onState)` 콜백 시그니처 `(state, reply)` Task 10 정의·소비 일치.

**주의 사항(실행자):** weasyprint 네이티브 의존(pango) 설치가 Task 1의 실질 관문. 실패하면 거기서 멈추고 설치 후 진행. `Dropzone` props는 실제 파일 기준으로 맞출 것.
