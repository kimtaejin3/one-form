"""매칭 파이프라인 — 프로필 ↔ 공고 임베딩 랭킹 + 상위 K개 LLM 보정·근거.

# ponytail: 인메모리 코사인(DB/pgvector 없음) — 요청마다 fetch한 N개만 임베딩해 비교한다.
#   코퍼스가 커지면 pgvector로.
# ponytail: LLM 보정은 1페이지(상위 size개)만 — page 2+는 임베딩 점수 + 소스 근거 그대로.
# ponytail: 다중 소스는 concat만(중복 공고 병합 없음) — sources/selector.py 참고.
"""
from app.ai.embedder import cosine, get_embedder
from app.ai.llm import get_llm
from app.jobs.schemas import JobFeed
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
    return " ".join(
        [job["title"], job["role_category"], *job["tags"], job["experience"], job["employment"]]
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
    jobs = []
    for rate, j in scored[start:start + size]:
        reason = j["match_reason"]
        if page == 1:  # 상위 K(=size)개만 LLM 보정·근거
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
