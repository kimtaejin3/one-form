from app.jobs import service


class CountingLlm:
    """MockLlm이 아니므로 캐시 경로를 탄다. refine 호출 수를 센다."""

    def __init__(self):
        self.calls = 0

    async def refine(self, profile_text, job_text, base_rate, matched):
        self.calls += 1
        return 88, f"근거-{job_text[:8]}"


def test_second_request_is_all_cache_hits(client, monkeypatch):
    llm = CountingLlm()
    monkeypatch.setattr(service, "get_llm", lambda: llm)

    r1 = client.get("/api/jobs?page=1")
    assert r1.status_code == 200
    first = llm.calls
    assert first > 0  # 1페이지 refine 발생

    r2 = client.get("/api/jobs?page=1")
    assert r2.status_code == 200
    assert llm.calls == first  # 2회차는 전부 캐시 히트 → 증가 없음


def test_profile_text_change_invalidates(client, monkeypatch):
    llm = CountingLlm()
    monkeypatch.setattr(service, "get_llm", lambda: llm)

    client.get("/api/jobs?page=1")
    first = llm.calls

    # 프로필 텍스트가 바뀌면 캐시 키가 달라져 다시 refine.
    orig = service._profile_text
    monkeypatch.setattr(service, "_profile_text", lambda p: orig(p) + " 새로운스택")
    client.get("/api/jobs?page=1")
    assert llm.calls > first
