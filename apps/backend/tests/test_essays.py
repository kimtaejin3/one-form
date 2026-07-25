"""답변 저장 — 저장→GET 반영, 없는 id 404, draft 응답 shape."""


def test_save_answer_reflected_in_list(client):
    saved = client.put(
        "/api/essays/3/answer", json={"content": "카카오맵의 길찾기를…", "status": "작성 중"}
    )
    assert saved.status_code == 200
    assert saved.json()["answer"] == "카카오맵의 길찾기를…"
    assert saved.json()["status"] == "작성 중"

    essay = next(e for e in client.get("/api/essays").json() if e["id"] == 3)
    assert essay["answer"] == "카카오맵의 길찾기를…"
    assert essay["status"] == "작성 중"


def test_save_answer_unknown_id_404(client):
    assert client.put("/api/essays/999/answer", json={"content": "", "status": "미작성"}).status_code == 404


def test_save_answer_rejects_unknown_status(client):
    assert client.put("/api/essays/1/answer", json={"content": "x", "status": "완료"}).status_code == 422


def test_list_defaults_answer_empty(client):
    assert all(e["answer"] == "" for e in client.get("/api/essays").json())


def test_draft_response_shape(client):
    body = client.post("/api/essays/draft", json={"essay_id": 2}).json()
    assert body["essay_id"] == 2
    assert body["draft"]
