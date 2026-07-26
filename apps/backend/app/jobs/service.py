"""매칭 파이프라인 — 프로필 ↔ 공고 임베딩 랭킹 + 상위 K개 LLM 보정·근거.

# ponytail: 인메모리 코사인(DB/pgvector 없음) — 요청마다 fetch한 N개만 임베딩해 비교한다.
#   코퍼스가 커지면 pgvector로.
# ponytail: 실 LLM은 비용 때문에 1페이지만 보정 — page 2+ 근거는 소스 그대로(§8, 키 준비 시).
#   목 LLM은 공짜라 전 페이지를 보정해 근거가 실제 공고와 맞게 한다.
# ponytail: 다중 소스는 concat만(중복 공고 병합 없음) — sources/selector.py 참고.
"""
from app.ai.embedder import cosine, get_embedder
from app.ai.llm import get_llm
from app.core.config import settings
from app.jobs import repository
from app.jobs.schemas import JobDetail, JobFeed, MatchAnalysis
from app.jobs.sources.selector import active_sources
from app.profile.repository import get_profile

ROLE_LABEL = "백엔드 개발"


def _profile_text(profile: dict) -> str:
    parts = []
    for career in profile["careers"]:
        parts += [career["role"], *career["highlights"], *career["stack"]]
    for project in profile["projects"]:
        parts += [project["name"], project["summary"], *project["highlights"], *project["stack"]]
    return " ".join(parts)


def _job_text(job: dict) -> str:
    # 상세(주요 업무·요건·소개)까지 넣어야 공고별 임베딩이 구분된다 — 태그만으론 같은 직무가 동점.
    return " ".join([
        job["title"], job["role_category"], *job["tags"], job["experience"], job["employment"],
        job.get("description", ""), *job.get("responsibilities", []),
        *job.get("requirements", []), *job.get("preferred", []),
    ])


def _profile_stack(profile: dict) -> list[str]:
    stacks = [s for c in profile["careers"] for s in c["stack"]]
    stacks += [s for p in profile["projects"] for s in p["stack"]]
    return stacks


def _match_analysis(profile: dict, requirements: list[str]) -> MatchAnalysis:
    # ponytail: 부분 문자열 매칭 — "RDBMS(MySQL/PostgreSQL)"에 프로필의 PostgreSQL이 걸리게.
    #   스킬 동의어(사전)까지는 안 간다.
    stack = [s.lower() for s in _profile_stack(profile)]
    matched = [r for r in requirements if any(s in r.lower() for s in stack)]
    return MatchAnalysis(
        matched_skills=matched,
        missing_skills=[r for r in requirements if r not in matched],
    )


async def get_job_detail(job_id: int) -> JobDetail | None:
    """공고 상세 + 프로필 대비 매칭 분석. 없는 id·프로필 미등록이면 None(라우터가 404)."""
    profile = await get_profile()
    job = next((j for j in repository.all_jobs() if j["id"] == job_id), None)
    if job is None or not profile["registered"]:
        return None  # 프로필 미등록이면 피드와 동일하게 미노출

    profile_text = _profile_text(profile)
    job_text = _job_text(job)
    vectors = await get_embedder().embed([profile_text, job_text])
    rate = round(max(0.0, min(1.0, cosine(vectors[0], vectors[1]))) * 100)
    rate, reason = await get_llm().refine(profile_text, job_text, rate)
    return JobDetail(
        id=job["id"],
        company=job["company"],
        domain=job["domain"],
        conditions=f"{job['experience']} · {job['employment']} · {job['location']}",
        title=job["title"],
        tags=job["tags"],
        dday=job["dday"],
        source=job["source"],
        match_rate=rate,
        match_reason=reason,
        description=job["description"],
        responsibilities=job["responsibilities"],
        requirements=job["requirements"],
        preferred=job["preferred"],
        company_info=job["company_info"],
        match_analysis=_match_analysis(profile, job["requirements"]),
    )


async def get_job_feed(
    page: int, size: int, role: str, experience: str, employment: str, location: str
) -> JobFeed:
    profile = await get_profile()
    if not profile["registered"]:
        # 마스터 프로필 미등록 — 매칭 기준이 없으니 빈 피드(프론트 게이트와 동일).
        return JobFeed(role=ROLE_LABEL, total=0, page=page, size=size, jobs=[])

    query = {
        "role": role, "experience": experience, "employment": employment, "location": location
    }
    raw: list[dict] = []
    for source in active_sources():
        raw += await source.fetch(query)

    profile_text = _profile_text(profile)
    embedder = get_embedder()
    vectors = await embedder.embed([profile_text] + [_job_text(j) for j in raw])
    profile_vector, job_vectors = vectors[0], vectors[1:]

    scored = [
        (round(max(0.0, min(1.0, cosine(profile_vector, v))) * 100), j)
        for v, j in zip(job_vectors, raw)
    ]
    scored.sort(key=lambda pair: (-pair[0], pair[1]["id"]))  # 매칭률 desc, 동점은 id

    start = (page - 1) * size
    llm = get_llm()
    # 목 LLM은 공짜라 전 페이지 근거를 만든다. 실 LLM은 비용 때문에 1페이지만.
    refine_all = settings.ANTHROPIC_API_KEY is None
    jobs = []
    for rate, j in scored[start:start + size]:
        reason = j["match_reason"]
        if page == 1 or refine_all:
            rate, reason = await llm.refine(profile_text, _job_text(j), rate)
        jobs.append({
            "id": j["id"],
            "company": j["company"],
            "domain": j["domain"],
            "conditions": f"{j['experience']} · {j['employment']} · {j['location']}",
            "title": j["title"],
            "tags": j["tags"],
            "dday": j["dday"],
            "source": j["source"],
            "match_rate": rate,
            "match_reason": reason,
        })

    jobs.sort(key=lambda j: (-j["match_rate"], j["id"]))  # LLM 보정 후 다시 매칭률순
    return JobFeed(role=ROLE_LABEL, total=len(scored), page=page, size=size, jobs=jobs)
