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
