"""jobs 도메인 — 유일하게 로직(필터·페이지네이션)이 있어 통합 테스트의 핵심."""

JOB_FIELDS = {
    "id", "company", "domain", "conditions", "title", "tags", "dday", "source", "match_reason",
}


def test_feed_shape_and_size(client):
    r = client.get("/api/jobs?page=1&size=3")
    assert r.status_code == 200
    body = r.json()
    assert {"role", "total", "page", "size", "jobs"} <= body.keys()
    assert body["total"] == 100  # 필터 없으면 전체 100건
    assert len(body["jobs"]) == 3
    assert JOB_FIELDS <= body["jobs"][0].keys()  # 프론트 계약 필드 보존


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
