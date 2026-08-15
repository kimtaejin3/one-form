"""전 엔드포인트 스모크 — 200 + 최소 shape. 목이라도 응답 계약이 깨지면 잡는다."""


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_get_endpoints(client):
    assert client.get("/api/profile").json()["personal"]["name"]
    assert len(client.get("/api/activities").json()) == 20
    assert len(client.get("/api/notifications").json()) == 8
    assert client.get("/api/jobs/1").json()["match_analysis"]["matched_skills"] is not None
    questions = client.get("/api/essays/questions").json()
    assert len(questions) == 10
    assert all(q["prompt"] and q["tag"] and q["slots"] for q in questions)


def test_post_endpoints(client):
    assert client.post("/api/essays/draft", json={"question_id": 1}).json()["question_id"] == 1
    # companies/analyze는 수집기를 타므로 여기선 제외 — provider 목이 필요하다(test_companies.py).
    assert len(client.post("/api/forms/convert").json()["mappings"]) == 5
    response = client.post("/api/profile/resume")
    assert response.status_code == 422  # 파일 없는 multipart 업로드는 거절
