"""전 엔드포인트 스모크 — 200 + 최소 shape. 목이라도 응답 계약이 깨지면 잡는다."""


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_get_endpoints(client):
    assert client.get("/api/profile").json()["personal"]["name"]
    assert len(client.get("/api/activities").json()) == 20
    assert len(client.get("/api/notifications").json()) == 8
    assert len(client.get("/api/essays").json()) == 3


def test_post_endpoints(client):
    assert client.post("/api/essays/draft", json={"essay_id": 1}).json()["essay_id"] == 1
    assert client.post("/api/companies/analyze", json={"name": "쿠팡"}).json()["name"] == "쿠팡"
    assert len(client.post("/api/forms/convert").json()["mappings"]) == 5
    assert client.post("/api/profile/resume").json()["parsed_fields"] == 12
