from pydantic import BaseModel


class Personal(BaseModel):
    photo: str
    name: str
    name_en: str
    name_cn: str
    address: str
    phone: str
    email: str
    emergency_phone: str
    emergency_relation: str
    # 입사지원서용 확장 필드(기본값 "") — 표준 이력서 템플릿은 무시, 형식(입사지원서)만 사용
    birth: str = ""  # 생년월일
    nationality: str = ""  # 국적
    military_status: str = ""  # 병역구분
    military_branch: str = ""  # 군별/병과
    military_period: str = ""  # 군복무기간
    veteran: str = ""  # 보훈대상
    discharge: str = ""  # 전역사유


class Link(BaseModel):
    label: str
    url: str


class Education(BaseModel):
    school: str
    major: str
    period: str
    status: str
    gpa: str
    # 입사지원서 학력사항 표용(기본값 "")
    admission: str = ""  # 입학년월
    graduation: str = ""  # 졸업년월
    degree: str = ""  # 학위구분


class Language(BaseModel):
    language: str
    test: str
    score: str
    date: str


class Award(BaseModel):
    title: str
    org: str
    date: str


class Certificate(BaseModel):
    name: str
    issuer: str
    date: str


class Career(BaseModel):
    company: str
    role: str
    period: str
    highlights: list[str]
    stack: list[str]


class Project(BaseModel):
    name: str
    role: str
    period: str
    summary: str
    highlights: list[str]
    stack: list[str]


# ponytail: activities 도메인의 Activity와 이름 충돌 방지 — OpenAPI 스키마명이 겹치면 안 됨.
class ProfileActivity(BaseModel):
    type: str
    title: str
    org: str
    period: str
    description: str


class Profile(BaseModel):
    registered: bool  # 마스터 프로필 등록 여부 — 미등록이면 프론트가 채용공고를 숨긴다
    personal: Personal
    links: list[Link]
    educations: list[Education]
    languages: list[Language]
    awards: list[Award]
    certificates: list[Certificate]
    careers: list[Career]
    projects: list[Project]
    activities: list[ProfileActivity]


class ResumeUploadResponse(BaseModel):
    profile: Profile
    parsed_fields: int
    message: str
