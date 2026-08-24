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
