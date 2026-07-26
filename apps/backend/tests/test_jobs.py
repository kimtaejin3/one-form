"""jobs 도메인 — 유일하게 로직(필터·페이지네이션·상세)이 있어 통합 테스트의 핵심."""
from app.jobs import repository
from app.profile.repository import _PROFILE

JOB_FIELDS = {
    "id", "company", "domain", "conditions", "title", "tags", "dday", "source",
    "match_rate", "match_reason",
}
DETAIL_FIELDS = JOB_FIELDS | {
    "description", "responsibilities", "requirements", "preferred", "company_info",
    "match_analysis",
}


def test_feed_shape_and_size(client):
    r = client.get("/api/jobs?page=1&size=3")
    assert r.status_code == 200
    body = r.json()
    assert {"role", "total", "page", "size", "jobs"} <= body.keys()
    assert body["total"] == 40  # 필터 없으면 전체 40건 (회사 20 × 직무 2)
    assert len(body["jobs"]) == 3
    assert JOB_FIELDS <= body["jobs"][0].keys()  # 프론트 계약 필드 보존


def test_mock_jobs_are_unique_and_in_seoul():
    """§2 목 재정비 — (회사×직무) 중복 없음, 전부 서울, 8직무가 모두 등장."""
    jobs = repository.all_jobs()
    pairs = [(j["company"], j["role_category"]) for j in jobs]
    assert len(pairs) == len(set(pairs)) == 40
    assert {j["location"] for j in jobs} == {"서울"}
    assert len({j["role_category"] for j in jobs}) == 8


def test_second_page_differs(client):
    p1 = client.get("/api/jobs?page=1&size=5").json()["jobs"]
    p2 = client.get("/api/jobs?page=2&size=5").json()["jobs"]
    assert len(p2) == 5
    assert [j["id"] for j in p1] != [j["id"] for j in p2]  # 오프셋이 실제로 이동


def test_role_filter_narrows(client):
    total = client.get("/api/jobs").json()["total"]
    backend = client.get("/api/jobs", params={"role": "백엔드"}).json()["total"]
    assert 0 < backend < total  # 필터가 실제로 좁힌다


def test_combined_filters_reduce_further(client):
    role_only = client.get("/api/jobs", params={"role": "백엔드"}).json()["total"]
    combined = client.get(
        "/api/jobs", params={"role": "백엔드", "employment": "정규직"}
    ).json()["total"]
    assert combined <= role_only


# --- 상세 (GET /api/jobs/{id}) ---

def test_job_detail_shape(client):
    body = client.get("/api/jobs/1").json()
    assert DETAIL_FIELDS <= body.keys()
    assert body["id"] == 1
    assert body["description"] and body["company_info"]
    assert body["responsibilities"] and body["requirements"] and body["preferred"]
    assert body["match_reason"] and 0 <= body["match_rate"] <= 100


def test_job_detail_unknown_id_404(client):
    assert client.get("/api/jobs/9999").status_code == 404


def test_detail_match_rate_agrees_with_feed(client):
    """카드에 뜬 매칭률·근거가 상세에서 그대로여야 한다 — 두 경로가 같은 텍스트로 계산하는지.

    피드는 소스(_job_text)로, 상세는 repository로 각각 계산한다. 한쪽만 상세를 텍스트에
    넣거나 LLM 보정을 건너뛰면 같은 공고가 목록 77% / 상세 62%로 갈린다.
    """
    for job in client.get("/api/jobs?page=1&size=5").json()["jobs"]:
        detail = client.get(f"/api/jobs/{job['id']}").json()
        assert detail["match_rate"] == job["match_rate"], job["id"]
        assert detail["match_reason"] == job["match_reason"], job["id"]


def test_job_detail_match_analysis_splits_requirements(client):
    """매칭 분석 = 요구 스킬을 프로필 스택 기준으로 충족/부족으로 가른다(프론트엔드 공고 기준)."""
    job_id = client.get("/api/jobs", params={"role": "프론트엔드"}).json()["jobs"][0]["id"]
    body = client.get(f"/api/jobs/{job_id}").json()
    analysis = body["match_analysis"]
    assert analysis.keys() == {"matched_skills", "missing_skills"}
    assert {"React", "TypeScript"} <= set(analysis["matched_skills"])  # 목 프로필 보유
    # 충족 + 부족 = 요구 스킬 전체(누락·중복 없음).
    assert sorted(analysis["matched_skills"] + analysis["missing_skills"]) == sorted(
        body["requirements"]
    )


# 프론트엔드 세부 역량 — 목 프로필이 '일부만' 보유한다(전부 보유면 부족이 안 생겨 세부 매칭이 안 보인다).
PROFILE_HAS = {"HTML/CSS", "상태관리(TanStack Query)", "웹 성능 최적화", "디자인 시스템", "모노레포 개발환경"}
PROFILE_LACKS = {
    "SSR(Next.js)", "웹뷰(WebView) 연동", "웹 접근성(a11y)", "프론트엔드 테스팅(Playwright)",
}


def test_match_analysis_splits_detail_skills(client):
    """세부 역량 단위로 갈리는가 — 프로필 표기와 공고 요구 스킬 문자열이 어긋나면 여기서 깨진다.

    'React·TypeScript는 충족'까지만 맞고 세부(SSR·웹뷰·접근성)가 전부 부족/전부 충족으로 쏠리면
    상세페이지의 충족/부족 리스트가 무의미해진다.
    """
    ids = [j["id"] for j in client.get("/api/jobs", params={"role": "프론트엔드"}).json()["jobs"]]
    details = [client.get(f"/api/jobs/{i}").json() for i in ids]
    for d in details:
        required, analysis = set(d["requirements"]), d["match_analysis"]
        assert PROFILE_HAS & required <= set(analysis["matched_skills"]), d["id"]
        assert PROFILE_LACKS & required <= set(analysis["missing_skills"]), d["id"]
        assert analysis["missing_skills"], d["id"]  # 프로필이 전부는 못 갖춘다

    # 같은 직무라도 공고마다 요구 세부가 달라 충족/부족 조합이 구분된다.
    assert len({tuple(d["requirements"]) for d in details}) == len(details)
    assert len({tuple(d["match_analysis"]["missing_skills"]) for d in details}) == len(details)
    assert set().union(*(set(d["requirements"]) for d in details)) & PROFILE_LACKS


# 프로필에 없는 게 확실한 스킬 — 있으면 이 테스트의 전제가 무너지므로 아래서 먼저 검사한다.
PROFILE_NEVER_HAS = {
    "Swift", "SwiftUI", "Kotlin", "Android SDK", "Java", "Spring Boot",
    "SSR(Next.js)", "웹 접근성(a11y)", "웹뷰(WebView) 연동",
}


def test_matched_missing_follow_profile_stack(client):
    """전 40건 불변식 — 프로필이 가진 스킬은 충족, 없는 스킬은 부족.

    위 프론트엔드 테스트는 리터럴 5건만 본다. 표기가 한쪽에서만 바뀌면
    (프로필 "상태관리(TanStack Query)" ↔ 요구 "상태관리(React Query)") 충족이 부족으로
    통째로 쓸려 나가는데, 공고별 assert는 교집합이 비어도 조용히 통과한다 —
    그래서 "겹치는 공고 수"까지 같이 못박는다.
    """
    stack = {s for c in _PROFILE["careers"] for s in c["stack"]}
    stack |= {s for p in _PROFILE["projects"] for s in p["stack"]}
    assert not (PROFILE_NEVER_HAS & stack)  # 전제: 목 프로필은 이것들을 안 가졌다

    overlapping = 0
    for job in repository.all_jobs():
        analysis = client.get(f"/api/jobs/{job['id']}").json()["match_analysis"]
        matched, missing = set(analysis["matched_skills"]), set(analysis["missing_skills"])
        required = set(job["requirements"])
        assert stack & required <= matched, job["id"]  # 보유 → 충족
        assert PROFILE_NEVER_HAS & required <= missing, job["id"]  # 미보유 → 부족
        assert matched | missing == required and not (matched & missing), job["id"]
        assert missing, job["id"]  # 전부 충족인 공고는 없다 — 있으면 세부화가 무의미
        overlapping += bool(matched)

    # 모바일 10건(Swift·Kotlin — 프로필과 접점 0)을 뺀 30건은 반드시 겹친다.
    # 표기가 어긋나면 여기가 0에 수렴한다.
    assert overlapping == 30
