"""문항 중심 모델 — 문항 풀+기업 매핑 합류, 답변 저장(재사용)·404·status 422, draft shape."""


def _question(client, qid: int):
    return next(q for q in client.get("/api/essays/questions").json() if q["id"] == qid)


def test_questions_join_companies(client):
    questions = client.get("/api/essays/questions").json()
    assert len(questions) == 12
    by_id = {q["id"]: q for q in questions}

    # 여러 기업이 같은 문항을 공유한다(재사용).
    assert {c["name"] for c in by_id[1]["companies"]} == {"네이버", "삼성전자", "현대자동차"}
    assert all(c["deadline"] for c in by_id[1]["companies"])
    # 어떤 기업도 안 쓰는 공통 문항.
    assert by_id[10]["companies"] == []


def test_questions_default_answer_empty(client):
    assert all(
        q["answer"] == "" and q["status"] == "미작성"
        for q in client.get("/api/essays/questions").json()
    )


def test_save_answer_reflected_in_questions(client):
    saved = client.put(
        "/api/essays/questions/3/answer",
        json={"content": "해커톤에서 CRDT 동기화를…", "status": "작성 중"},
    )
    assert saved.status_code == 200
    assert saved.json()["answer"] == "해커톤에서 CRDT 동기화를…"
    assert saved.json()["status"] == "작성 중"
    # 저장은 문항 기준이라 그 문항을 쓰는 모든 기업에 공유된다.
    assert {c["name"] for c in saved.json()["companies"]} == {"네이버", "토스", "쿠팡"}

    question = _question(client, 3)
    assert question["answer"] == "해커톤에서 CRDT 동기화를…"
    assert question["status"] == "작성 중"


def test_save_answer_unknown_id_404(client):
    assert (
        client.put(
            "/api/essays/questions/999/answer", json={"content": "", "status": "미작성"}
        ).status_code
        == 404
    )


def test_save_answer_rejects_unknown_status(client):
    assert (
        client.put(
            "/api/essays/questions/1/answer", json={"content": "x", "status": "완료"}
        ).status_code
        == 422
    )


def test_draft_response_shape(client):
    body = client.post("/api/essays/draft", json={"question_id": 2}).json()
    assert body["question_id"] == 2
    assert body["draft"]
