"""(기업 × 문항) 슬롯 — 슬롯 생성·저장 독립성·없는 (기업,문항) 404·status 422·draft shape."""


def _question(client, qid: int):
    return next(q for q in client.get("/api/essays/questions").json() if q["id"] == qid)


def _slot(question: dict, company: str):
    return next(s for s in question["slots"] if s["company"] == company)


def test_slots_one_per_using_company(client):
    by_id = {q["id"]: q for q in client.get("/api/essays/questions").json()}
    assert len(by_id) == 12

    # 문항 1은 세 기업이 공유 → 슬롯 3개(각자 그 회사 마감).
    assert [s["company"] for s in by_id[1]["slots"]] == ["네이버", "삼성전자", "현대자동차"]
    assert _slot(by_id[1], "삼성전자")["deadline"] == "2026-08-03"
    # 어떤 기업도 안 쓰는 문항 → 공통 슬롯 1개.
    assert by_id[10]["slots"] == [
        {"company": "공통", "deadline": "", "content": "", "status": "미작성"}
    ]


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
        "deadline": "2026-08-03",
        "content": "반도체 공정 자동화에…",
        "status": "작성 중",
    }
    # 같은 문항이라도 다른 기업 슬롯은 그대로 — 재사용 아님.
    assert _slot(saved.json(), "네이버")["content"] == ""

    question = _question(client, 1)
    assert _slot(question, "삼성전자")["content"] == "반도체 공정 자동화에…"
    assert _slot(question, "네이버")["status"] == "미작성"


def test_save_answer_common_slot(client):
    saved = client.put(
        "/api/essays/questions/10/answer",
        json={"company": "공통", "content": "저는 기록하는 개발자입니다.", "status": "초안 완료"},
    )
    assert saved.status_code == 200
    assert _slot(saved.json(), "공통")["status"] == "초안 완료"


def test_save_answer_company_not_using_question_404(client):
    # 네이버는 문항 8을 쓰지 않는다.
    assert (
        client.put(
            "/api/essays/questions/8/answer",
            json={"company": "네이버", "content": "x", "status": "작성 중"},
        ).status_code
        == 404
    )


def test_save_answer_unknown_question_404(client):
    assert (
        client.put(
            "/api/essays/questions/999/answer",
            json={"company": "네이버", "content": "", "status": "미작성"},
        ).status_code
        == 404
    )


def test_save_answer_rejects_unknown_status(client):
    assert (
        client.put(
            "/api/essays/questions/1/answer",
            json={"company": "네이버", "content": "x", "status": "완료"},
        ).status_code
        == 422
    )


def test_draft_response_shape(client):
    body = client.post("/api/essays/draft", json={"question_id": 2}).json()
    assert body["question_id"] == 2
    assert body["draft"]
