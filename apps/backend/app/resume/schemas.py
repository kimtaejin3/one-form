"""이력서 빌더 도메인 스키마. 클래스명은 전역 유일해야 함(Resume 프리픽스)."""
import re
from enum import Enum

from pydantic import BaseModel, field_validator

_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{3,8}$")


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


# 입사지원서(형식 템플릿)용 인적사항 — 표준·포트폴리오 템플릿은 사용하지 않는다.
class ResumePersonal(BaseModel):
    photo: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    birth: str = ""
    nationality: str = ""
    military_status: str = ""
    military_branch: str = ""
    military_period: str = ""
    veteran: str = ""
    discharge: str = ""


class ResumeSection(BaseModel):
    id: str
    type: SectionType
    title: str
    order: int
    visible: bool = True
    # ponytail: items는 타입별 자유 dict — 렌더 템플릿이 title·org·period·bullets·note·stack·name
    #   키를 읽는다. 타입별 항목 모델은 phase 2(지금은 dict로 충분).
    items: list[dict] = []


# 자소서 항목 — 기업별 세트로 묶여 문서(ResumeDoc)에 포함된다.
class ResumeEssay(BaseModel):
    question: str
    answer: str = ""
    char_limit: int | None = None


class ResumeDoc(BaseModel):
    header: ResumeHeader
    personal: ResumePersonal = ResumePersonal()
    summary: str = ""
    sections: list[ResumeSection] = []
    company: str = ""  # 지원 기업 — 자소서 세트의 기준이자 AI 초안의 기업 분석 대상
    essays: list[ResumeEssay] = []
    include_essays: bool = True  # PDF·미리보기에 자소서를 포함할지


class ResumeStyle(BaseModel):
    template: str = "classic"
    font: str = "Pretendard"
    accent_color: str = "#334155"
    density: Density = Density.normal
    heading_style: HeadingStyle = HeadingStyle.bar
    font_scale: FontScale = FontScale.M

    @field_validator("accent_color")
    @classmethod
    def _valid_hex(cls, v: str) -> str:
        # ponytail: LLM이 이상한 값을 줘도 500 대신 기본색으로 폴백
        return v if _HEX_COLOR.match(v) else "#334155"


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
    kind: str = "resume"  # resume | portfolio — 빌더가 이 값으로 템플릿을 거른다
    thumbnail: str
    preset: ResumeStyle


# 자소서 질문뱅크 — 기업별 추천 세트를 고르면 그 기업 자소서 세트가 구성된다.
class ResumeEssayQuestion(BaseModel):
    id: int
    tag: str
    prompt: str
    char_limit: int | None = None


class ResumeEssaySet(BaseModel):
    company: str
    deadline: str = ""
    questions: list[ResumeEssayQuestion] = []


class ResumeEssayDraftRequest(BaseModel):
    company: str
    question: str
    char_limit: int | None = None
    state: ResumeState


class ResumeEssayDraftResponse(BaseModel):
    draft: str
    note: str = ""


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
