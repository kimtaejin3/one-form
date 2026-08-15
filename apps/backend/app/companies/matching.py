"""마스터 프로필 ↔ JD 매칭. 규칙 기반, 설명 가능(계획서 §6.5).

임베딩은 쓰지 않는다 — 왜 맞았는지 문장으로 설명할 수 있어야 하고, 지금 필요한 정확도는
표기 정규화 + 부분 일치로 충분하다. semantic score는 Phase 5에서 별도 필드로 더한다.

# ponytail: 매칭 결과는 저장하지 않고 조회 때 계산한다. 프로필을 한 줄만 고쳐도 저장된
#   매칭은 전부 낡는데, 규칙 계산은 마이크로초다. LLM/임베딩 점수가 붙어 비싸지면 그때 캐시.
"""
import re

from app.companies.schemas import CompanyJob, CompanyMatch, MatchType

# 표기 흔들림 흡수 — "Node.js"·"nodejs"·"node js"를 같은 스킬로 본다.
_NOISE = re.compile(r"[\s.\-_/()]+")


def _key(skill: str) -> str:
    return _NOISE.sub("", skill.strip().lower())


def _evidence(profile: dict) -> list[dict]:
    """경력·프로젝트를 매칭 단위로 평탄화. 프로필 원문을 복제하지 않고 참조만 남긴다."""
    items = []
    for career in profile.get("careers", []):
        items.append(
            {
                "label": f"{career['company']} · {career['role']}",
                "stack": career.get("stack", []),
                "highlights": career.get("highlights", []),
            }
        )
    for project in profile.get("projects", []):
        items.append(
            {
                "label": project.get("name", "프로젝트"),
                "stack": project.get("stack", []),
                "highlights": project.get("highlights", []),
            }
        )
    return items


def _best_evidence(skill: str, evidence: list[dict]) -> tuple[dict, str] | None:
    """이 스킬을 실제로 쓴 경력/프로젝트 하나와, 그걸 뒷받침하는 하이라이트를 고른다."""
    want = _key(skill)
    for item in evidence:
        for owned in item["stack"]:
            if _key(owned) != want:
                continue
            # 스킬 이름이 들어간 하이라이트가 있으면 그게 가장 구체적인 근거다.
            quote = next(
                (h for h in item["highlights"] if want in _key(h)),
                item["highlights"][0] if item["highlights"] else "",
            )
            return item, quote
    return None


def match_job(job: CompanyJob, profile: dict) -> list[CompanyMatch]:
    """공고 하나에 대한 강점·갭. 점수는 근거의 구체성에서 나온다."""
    if not profile.get("registered"):
        return []

    evidence = _evidence(profile)
    # core_skills가 비면 requirements로 대체 — LLM이 핵심 역량을 못 좁힌 경우.
    needs = list(dict.fromkeys(job.core_skills or job.requirements))
    matches: list[CompanyMatch] = []

    for need in needs:
        found = _best_evidence(need, evidence)
        if found is None:
            matches.append(
                CompanyMatch(
                    job_id=job.id,
                    company_need=need,
                    profile_evidence="",
                    match_type=MatchType.gap,
                    score=0.0,
                    reason=f"'{need}'을(를) 쓴 경력·프로젝트가 프로필에 없습니다.",
                    source_ids=[job.source_id],
                )
            )
            continue
        item, quote = found
        # 하이라이트로 뒷받침되면 90, 스택에만 있으면 65 — 왜 이 점수인지 설명 가능해야 한다.
        score = 90.0 if quote else 65.0
        matches.append(
            CompanyMatch(
                job_id=job.id,
                company_need=need,
                profile_evidence=item["label"],
                match_type=MatchType.strength,
                score=score,
                reason=(
                    f"{item['label']}에서 '{need}' 사용 — {quote}"
                    if quote
                    else f"{item['label']}의 기술 스택에 '{need}'가 있습니다(구체 성과 기술 필요)."
                ),
                source_ids=[job.source_id],
            )
        )

    # 갭은 뒤로 — 강점 먼저 보여주고 점수 높은 순.
    matches.sort(key=lambda m: (m.match_type is MatchType.gap, -m.score))
    return matches


def match_company(jobs: list[CompanyJob], profile: dict, job_id: int | None = None) -> list[CompanyMatch]:
    targets = [j for j in jobs if job_id is None or j.id == job_id]
    return [m for job in targets for m in match_job(job, profile)]
