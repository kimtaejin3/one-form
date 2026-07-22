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


class Link(BaseModel):
    label: str
    url: str


class Education(BaseModel):
    school: str
    major: str
    period: str
    status: str
    gpa: str


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
    personal: Personal
    links: list[Link]
    educations: list[Education]
    languages: list[Language]
    awards: list[Award]
    certificates: list[Certificate]
    careers: list[Career]
    projects: list[Project]
    activities: list[ProfileActivity]
