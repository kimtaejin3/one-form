"""(기업 × 문항) 슬롯 — 슬롯 생성·저장 독립성·없는 (기업,문항) 404·status 422·draft shape."""


def _question(client, qid: int):
    return next(q for q in client.get("/api/essays/questions").json() if q["id"] == qid)


def _slot(question: dict, company: str):
    return next(s for s in question["slots"] if s["company"] == company)


def test_slots_one_per_using_company(client):
    by_id = {q["id"]: q for q in client.get("/api/essays/questions").json()}
    assert len(by_id) == 10

    assert [s["company"] for s in by_id[1]["slots"]] == ["삼성전자"]
    assert _slot(by_id[1], "삼성전자")["deadline"] == "2025-09-03"

    companies = {s["company"] for q in by_id.values() for s in q["slots"]}
    assert companies == {"삼성전자", "현대오토에버", "포스코DX", "오큘러스에쿼티파트너스"}
    assert by_id[10]["tag"] == "자유양식"
    assert by_id[10]["char_limit"] is None


def test_slots_default_empty(client):
    assert all(
        s["content"] == "" and s["status"] == "미작성"
        for q in client.get("/api/essays/questions").json()
        for s in q["slots"]
    )


def test_save_answer_is_per_company(client):
    saved = client.put(
        "/api/essays/questions/1/answer",
        json={"company": "삼성전자", "content": "반도체 공정 자동화에…", "status": "작성 중"},
    )
    assert saved.status_code == 200
    assert _slot(saved.json(), "삼성전자") == {
        "company": "삼성전자",
        "deadline": "2025-09-03",
        "content": "반도체 공정 자동화에…",
        "status": "작성 중",
    }
    # 같은 문항이라도 다른 기업 슬롯은 그대로 — 재사용 아님.
    question = _question(client, 1)
    assert _slot(question, "삼성전자")["content"] == "반도체 공정 자동화에…"


def test_save_answer_company_not_using_question_404(client):
    # 등록되지 않은 기업은 문항을 쓰지 않는다.
    assert (
        client.put(
            "/api/essays/questions/1/answer",
            json={"company": "토스", "content": "x", "status": "작성 중"},
        ).status_code
        == 404
    )


def test_save_answer_unknown_question_404(client):
    assert (
        client.put(
            "/api/essays/questions/999/answer",
            json={"company": "토스", "content": "", "status": "미작성"},
        ).status_code
        == 404
    )


def test_save_answer_rejects_unknown_status(client):
    assert (
        client.put(
            "/api/essays/questions/1/answer",
            json={"company": "삼성전자", "content": "x", "status": "완료"},
        ).status_code
        == 422
    )


def test_draft_response_shape(client):
    body = client.post("/api/essays/draft", json={"question_id": 2}).json()
    assert body["question_id"] == 2
    assert body["draft"]
