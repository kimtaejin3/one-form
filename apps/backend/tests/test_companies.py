"""기업 인텔리전스 — 정규화·캐시·부분 실패·근거 검증.

외부 사이트는 절대 호출하지 않는다. provider 경계(service._PROVIDERS)에 fixture를 주입한다.
"""
import asyncio
from datetime import datetime, timezone

import pytest

from app.ai import llm as llm_module
from app.companies import repository, service
from app.companies.schemas import AnalysisStatus, SourceKind, TrustLevel
from app.companies.sources.base import SourceDocument
# conftest의 _no_outbound_fetch가 base.fetch를 막기 전에 원본을 잡아둔다 —
# fetch 자체(재시도·PDF 분기)를 검증하는 테스트만 이걸 쓰고, 네트워크는 _get 스텁으로 끊는다.
from app.companies.sources.base import fetch as REAL_FETCH

HTML_DOC = SourceDocument(
    url="https://example.com",
    kind=SourceKind.official_site,
    trust_level=TrustLevel.primary,
    title="예시 주식회사",
    publisher="example.com",
    text="예시는 물류 자동화 소프트웨어를 만드는 회사입니다. 2026년 로봇 사업을 시작했습니다.",
    published_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
)


class FakeProvider:
    """호출 횟수를 세는 목 provider — 캐시·중복 실행 검증에 쓴다."""

    def __init__(self, name="fake", docs=None, error=None):
        self.name = name
        self._docs = [HTML_DOC] if docs is None else docs
        self._error = error
        self.calls = 0

    async def collect(self, query):
        self.calls += 1
        if self._error:
            raise self._error
        return list(self._docs)


@pytest.fixture
def providers(monkeypatch):
    """기본 provider 1개를 심고 리스트를 돌려준다 — 테스트가 자유롭게 갈아끼운다."""
    def _install(*ps):
        monkeypatch.setattr(service, "_PROVIDERS", list(ps))
        return ps

    return _install


@pytest.fixture
def llm_json(monkeypatch):
    """MockLlm.complete_json 응답을 테스트가 지정한다(기본은 빈 dict = 구조화 실패)."""
    def _install(payload):
        async def fake(self, prompt, schema):
            return payload

        monkeypatch.setattr(llm_module.MockLlm, "complete_json", fake)

    return _install


JOB_DOC = SourceDocument(
    url="https://jobs.example.com/1",
    kind=SourceKind.job_posting,
    trust_level=TrustLevel.user_provided,
    title="백엔드 엔지니어 채용",
    publisher="jobs.example.com",
    text="대용량 트래픽을 다루는 결제 시스템을 만듭니다. Python, PostgreSQL 경험 필수.",
)

GOOD_LLM = {
    "summary": {"text": "물류 자동화 소프트웨어 기업.", "source_ids": [1]},
    "stage": {"text": "비상장", "source_ids": [1]},
    "business_areas": [{"text": "물류 자동화", "source_ids": [1]}],
    "products": [{"text": "로봇 WMS", "source_ids": [1]}],
    "signals": [
        {
            "label": "로봇 사업 진출",
            "detail": "2026년 로봇 사업을 시작했다.",
            "signal_type": "business",
            "confidence": 0.8,
            "evidence_quote": "2026년 로봇 사업을 시작했습니다.",
            "source_ids": [1],
        }
    ],
    "jobs": [],
}

# 공고 문서가 S2로 들어왔을 때의 JD 구조화 응답
JOB_LLM = {
    **GOOD_LLM,
    "jobs": [
        {
            "source_id": 2,
            "title": "백엔드 엔지니어",
            "role_category": "백엔드 개발",
            "location": "서울",
            "employment": "정규직",
            "deadline": "상시채용",
            "description": "결제 시스템 개발",
            "requirements": ["Python", "PostgreSQL"],
            "preferred": ["Kubernetes"],
            "core_skills": ["Python", "PostgreSQL", "대용량 트래픽", "Kubernetes"],
            "problem_types": ["대용량 트래픽 처리"],
        }
    ],
}


# --- 문서 추출 (§6.3) -----------------------------------------------------


def test_extract_html_pulls_title_body_and_date():
    from app.companies.extraction import extract_html

    doc = extract_html(
        """
        <html><head>
          <title>예시 — 물류 자동화</title>
          <meta property="og:description" content="로봇으로 창고를 자동화합니다.">
          <meta property="article:published_time" content="2026-05-01T09:00:00Z">
          <script>var tracking = "이건 본문이 아니다";</script>
          <style>.a { color: red }</style>
        </head><body>
          <h1>회사 소개</h1>
          <p>2026년 로봇 사업을 시작했습니다.</p>
        </body></html>
        """
    )

    assert doc.title == "예시 — 물류 자동화"
    assert doc.text.startswith("로봇으로 창고를 자동화합니다.")  # meta description이 맨 앞
    assert "2026년 로봇 사업을 시작했습니다." in doc.text
    assert "tracking" not in doc.text and "color: red" not in doc.text  # script/style 제외
    assert doc.published_at == datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc)
    assert doc.headings == ["회사 소개"]


def test_extract_html_survives_broken_markup():
    from app.companies.extraction import extract_html

    doc = extract_html("<html><body><p>닫히지 않은 태그<div>다음 블록")

    assert "닫히지 않은 태그" in doc.text
    assert doc.published_at is None


def test_content_hash_detects_identical_text():
    same = SourceDocument(
        url="https://other.example",  # URL이 달라도 본문이 같으면 같은 문서
        kind=SourceKind.official_site,
        trust_level=TrustLevel.primary,
        text=HTML_DOC.text,
    )
    assert same.content_hash == HTML_DOC.content_hash


# --- 정규화 (계획서 §6.1) -------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    ["삼성전자", "삼성전자(주)", "주식회사 삼성전자", " 삼성 전자 ", "삼성전자㈜"],
)
def test_normalize_collapses_company_affixes(raw):
    assert service.normalize(raw) == "삼성전자"


def test_normalize_is_case_insensitive_for_latin_names():
    assert service.normalize("Toss Inc.") == service.normalize("toss")
    assert service.normalize("Example Co., Ltd.") == "example"


@pytest.mark.parametrize("raw", ["Lincoln", "Corpus", "Incheon", "주식회사우리"])
def test_normalize_does_not_eat_affixes_inside_names(raw):
    """접미사는 앞뒤 끝에서만 뗀다 — 부분 문자열로 지우면 Lincoln→loln이 된다."""
    assert service.normalize(raw) == raw.lower().replace("주식회사", "", 1)


def test_normalize_strips_stacked_affixes():
    assert service.normalize("주식회사 예시(주)") == "예시"


def test_empty_name_is_rejected(client):
    assert client.post("/api/companies/analyze", json={"name": "   "}).status_code == 422


# --- 캐시·중복 실행 방지 (§7) ---------------------------------------------


def test_same_company_uses_cache(providers, llm_json):
    llm_json(GOOD_LLM)
    (fake,) = providers(FakeProvider())

    first = asyncio.run(service.analyze("예시"))
    second = asyncio.run(service.analyze("예시(주)"))  # 정규화되면 같은 기업

    assert fake.calls == 1  # 두 번째는 수집하지 않았다
    assert second.last_analyzed_at == first.last_analyzed_at


def test_force_refresh_recollects(providers, llm_json):
    llm_json(GOOD_LLM)
    (fake,) = providers(FakeProvider())

    asyncio.run(service.analyze("예시"))
    asyncio.run(service.analyze("예시", force_refresh=True))

    assert fake.calls == 2


def test_stale_cache_is_reanalyzed(providers, llm_json, monkeypatch):
    llm_json(GOOD_LLM)
    (fake,) = providers(FakeProvider())
    monkeypatch.setattr(repository, "FRESH_HOURS", 0)  # 저장 즉시 만료

    asyncio.run(service.analyze("예시"))
    asyncio.run(service.analyze("예시"))

    assert fake.calls == 2


def test_concurrent_analyze_runs_once(providers, llm_json):
    """동일 기업 동시 요청 — 락 뒤에서 두 번째가 캐시를 만나 재분석하지 않는다."""
    llm_json(GOOD_LLM)
    (fake,) = providers(FakeProvider())

    async def both():
        return await asyncio.gather(service.analyze("예시"), service.analyze("예시"))

    left, right = asyncio.run(both())

    assert fake.calls == 1
    assert left.last_analyzed_at == right.last_analyzed_at


# --- 부분 성공·실패 (§4·§7) -----------------------------------------------


def test_provider_failure_is_partial_not_fatal(providers, llm_json):
    llm_json(GOOD_LLM)
    providers(
        FakeProvider(name="official"),
        FakeProvider(name="manual", error=TimeoutError("연결 시간 초과")),
    )

    brief = asyncio.run(service.analyze("예시"))

    assert brief.status is AnalysisStatus.partial
    assert brief.source_count == 1  # 살아남은 provider 결과는 유지
    assert any("manual" in w for w in brief.warnings)


def test_no_sources_is_failed_with_guidance(providers):
    providers(FakeProvider(docs=[]))

    brief = asyncio.run(service.analyze("듣도보도못한기업"))

    assert brief.status is AnalysisStatus.failed
    assert brief.source_count == 0
    assert brief.summary is None  # 출처가 없으면 사실을 만들지 않는다
    assert brief.business_areas == [] and brief.products == []
    assert any("URL" in w for w in brief.warnings)


def test_duplicate_documents_are_deduped(providers, llm_json):
    llm_json(GOOD_LLM)
    providers(FakeProvider(name="a"), FakeProvider(name="b"))  # 같은 문서를 두 번

    brief = asyncio.run(service.analyze("예시"))

    assert brief.source_count == 1


# --- 근거 검증 (§6.4) -----------------------------------------------------


def test_signal_without_sources_is_dropped(providers, llm_json):
    payload = {**GOOD_LLM, "signals": [{**GOOD_LLM["signals"][0], "source_ids": []}]}
    llm_json(payload)
    providers(FakeProvider())

    brief = asyncio.run(service.analyze("예시"))

    assert brief.signals == []
    assert any("근거 출처가 없어" in n for n in brief.needs_review)


def test_signal_citing_unknown_source_is_dropped(providers, llm_json):
    payload = {**GOOD_LLM, "signals": [{**GOOD_LLM["signals"][0], "source_ids": [99]}]}
    llm_json(payload)
    providers(FakeProvider())

    assert asyncio.run(service.analyze("예시")).signals == []


def test_summary_without_sources_is_dropped(providers, llm_json):
    llm_json({**GOOD_LLM, "summary": {"text": "근거 없는 요약", "source_ids": []}})
    providers(FakeProvider())

    brief = asyncio.run(service.analyze("예시"))

    assert brief.summary is None
    assert any("기업 요약" in n for n in brief.needs_review)


@pytest.mark.parametrize("field", ["stage", "business_areas", "products"])
def test_every_fact_field_requires_sources(providers, llm_json, field):
    """요약·신호만이 아니라 모든 사실 필드가 근거 검증을 받는다."""
    unsourced = {"text": "근거 없는 값", "source_ids": []}
    llm_json({**GOOD_LLM, field: unsourced if field == "stage" else [unsourced]})
    providers(FakeProvider())

    brief = asyncio.run(service.analyze("예시"))

    assert getattr(brief, field) in (None, [])
    assert any("근거 출처가 없어" in n for n in brief.needs_review)


@pytest.mark.parametrize("field", ["stage", "business_areas", "products"])
def test_fact_field_citing_unknown_source_is_dropped(providers, llm_json, field):
    ghost = {"text": "유령 근거", "source_ids": [99]}
    llm_json({**GOOD_LLM, field: ghost if field == "stage" else [ghost]})
    providers(FakeProvider())

    assert getattr(asyncio.run(service.analyze("예시")), field) in (None, [])


def test_bare_string_fact_is_treated_as_unsourced_not_fatal(providers, llm_json):
    """필드 하나가 형식을 어겨도 분석 전체가 폴백되면 안 된다."""
    llm_json({**GOOD_LLM, "stage": "비상장"})  # {text, source_ids}가 아닌 맨 문자열
    providers(FakeProvider())

    brief = asyncio.run(service.analyze("예시"))

    assert brief.stage is None  # 근거가 없으니 버린다
    assert brief.summary is not None  # 나머지는 살아남는다
    assert brief.business_areas[0].text == "물류 자동화"


def test_broken_llm_json_falls_back_without_fabricating(providers, llm_json):
    llm_json({"summary": 12345, "signals": "이건 배열이 아니다"})
    providers(FakeProvider())

    brief = asyncio.run(service.analyze("예시"))

    assert brief.status is AnalysisStatus.partial  # 죽지 않는다
    assert brief.signals == []
    assert brief.business_areas == []  # 지어내지 않는다
    assert any("스키마" in n for n in brief.needs_review)


def test_no_llm_key_returns_excerpt_only(providers):
    """MockLlm은 {}를 준다 — 원문 발췌만 남고 구조화 항목은 비어야 한다."""
    providers(FakeProvider())

    brief = asyncio.run(service.analyze("예시"))

    assert brief.summary is not None
    assert brief.summary.text.startswith("예시는 물류 자동화")
    assert brief.summary.source_ids == [1]  # 발췌도 근거를 단다
    assert brief.business_areas == []
    assert brief.signals == []
    assert any("LLM" in n for n in brief.needs_review)


def test_good_llm_output_is_structured_with_evidence(providers, llm_json):
    llm_json(GOOD_LLM)
    providers(FakeProvider())

    brief = asyncio.run(service.analyze("예시"))

    assert brief.status is AnalysisStatus.ready
    assert [b.text for b in brief.business_areas] == ["물류 자동화"]
    assert brief.summary is not None and brief.summary.source_ids == [1]
    assert brief.stage is not None and brief.stage.source_ids == [1]
    signal = brief.signals[0]
    assert signal.source_ids == [1]
    assert signal.evidence_quote in HTML_DOC.text

    # 모든 사실 필드의 근거가 실재하는 출처를 가리켜야 한다
    valid = {s.id for s in brief.sources}
    cited = {
        *brief.summary.source_ids,
        *brief.stage.source_ids,
        *(i for b in brief.business_areas for i in b.source_ids),
        *(i for p in brief.products for i in p.source_ids),
        *(i for s in brief.signals for i in s.source_ids),
    }
    assert cited <= valid and cited


# --- API 계약 -------------------------------------------------------------


def test_analyze_endpoint_returns_intelligence(client, providers, llm_json):
    llm_json(GOOD_LLM)
    providers(FakeProvider())

    body = client.post("/api/companies/analyze", json={"name": "예시"}).json()

    assert body["name"] == "예시"
    assert body["normalized_name"] == "예시"
    assert body["status"] == "ready"
    assert body["source_count"] == 1
    assert body["sources"][0]["url"] == HTML_DOC.url
    assert body["sources"][0]["trust_level"] == "primary"
    assert body["fresh_until"] > body["last_analyzed_at"]


def test_get_and_sources_and_refresh_roundtrip(client, providers, llm_json):
    llm_json(GOOD_LLM)
    (fake,) = providers(FakeProvider())
    client.post("/api/companies/analyze", json={"name": "예시(주)"})

    assert client.get("/api/companies/예시").json()["normalized_name"] == "예시"
    assert len(client.get("/api/companies/예시/sources").json()) == 1

    refreshed = client.post("/api/companies/예시/refresh").json()
    assert refreshed["status"] == "ready"
    assert fake.calls == 2  # refresh는 캐시를 무시한다


def test_unknown_company_is_404_before_analysis(client):
    assert client.get("/api/companies/없는기업").status_code == 404
    assert client.post("/api/companies/없는기업/refresh").status_code == 404
    assert client.get("/api/companies/없는기업/sources").status_code == 404


# --- SSRF 차단 (§11) ------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",  # http(s)가 아닌 스킴
        "file:///etc/passwd",
        "http://localhost:8000/api/health",  # 자기 자신
        "http://127.0.0.1/",
        "http://10.0.0.5/internal",  # 사설 대역
        "http://192.168.0.1/",
        "http://172.16.0.1/",
        "http://169.254.169.254/latest/meta-data/",  # 클라우드 메타데이터
        "http://[::1]/",
        "https://[fd00::1]/",  # IPv6 unique-local
        "http:///path-without-host",
    ],
)
def test_internal_and_non_http_urls_are_blocked(url):
    from app.companies.sources.base import BlockedUrlError, assert_public_url

    with pytest.raises(BlockedUrlError):
        asyncio.run(assert_public_url(url))


def test_public_url_passes_the_guard():
    from app.companies.sources.base import assert_public_url

    asyncio.run(assert_public_url("https://example.com/path"))  # 예외가 없으면 통과


def test_blocked_url_becomes_warning_not_500(providers, client):
    """사용자가 내부 URL을 넣어도 provider 경계에서 warning으로 흡수된다."""
    from app.companies.sources.manual import ManualUrlSource

    providers(ManualUrlSource())
    body = client.post(
        "/api/companies/analyze",
        json={"name": "예시", "job_url": "http://169.254.169.254/latest/meta-data/"},
    )

    assert body.status_code == 200
    assert body.json()["status"] == "failed"
    assert any("manual" in w for w in body.json()["warnings"])


# --- 사용자 URL 보존 -------------------------------------------------------


class UrlEchoProvider:
    """전달받은 job_urls를 기록하는 provider — URL 보존 검증용."""

    name = "manual"

    def __init__(self, docs=None, error=None):
        self.seen: list[list[str]] = []
        self._docs = docs
        self._error = error

    async def collect(self, query):
        urls = list(query.get("job_urls") or [])
        self.seen.append(urls)
        if self._error:
            raise self._error
        return list(self._docs if self._docs is not None else ([JOB_DOC] if urls else []))


def test_refresh_keeps_user_provided_urls(providers, llm_json):
    """refresh는 사용자가 넣은 공고 URL을 다시 수집한다 — 한 번 넣으면 유지된다."""
    llm_json(GOOD_LLM)
    echo = UrlEchoProvider()
    providers(echo)

    asyncio.run(service.analyze("예시", job_url="https://jobs.example.com/1"))
    refreshed = asyncio.run(service.refresh("예시"))

    assert echo.seen == [["https://jobs.example.com/1"], ["https://jobs.example.com/1"]]
    assert refreshed is not None


def test_manual_url_survives_a_failed_fetch(providers, llm_json):
    """수집이 실패한 URL도 보존된다 — 일시적 장애로 사용자 입력이 사라지면 안 된다."""
    llm_json(GOOD_LLM)
    failing = UrlEchoProvider(error=TimeoutError("연결 시간 초과"))
    providers(failing)

    first = asyncio.run(service.analyze("예시", job_url="https://jobs.example.com/1"))
    assert first.source_count == 0  # 수집은 실패했지만
    assert first.manual_urls == ["https://jobs.example.com/1"]  # URL은 남는다

    asyncio.run(service.refresh("예시"))
    assert failing.seen[1] == ["https://jobs.example.com/1"]  # 다시 시도한다


def test_new_job_url_is_added_to_kept_urls(providers, llm_json):
    llm_json(GOOD_LLM)
    echo = UrlEchoProvider(docs=[HTML_DOC])
    providers(echo)

    asyncio.run(service.analyze("예시", job_url="https://a.example.com/1"))
    asyncio.run(service.analyze("예시", job_url="https://b.example.com/2"))

    assert echo.seen[1] == ["https://a.example.com/1", "https://b.example.com/2"]


# --- 최신성·출처 변경 감지 (Phase 4) ---------------------------------------


def test_fresh_result_is_not_stale(providers, llm_json):
    llm_json(GOOD_LLM)
    providers(FakeProvider())

    assert asyncio.run(service.analyze("예시")).is_stale is False


def test_expired_result_is_marked_stale(providers, llm_json, monkeypatch):
    llm_json(GOOD_LLM)
    providers(FakeProvider())
    monkeypatch.setattr(repository, "FRESH_HOURS", 0)  # 저장 즉시 만료

    brief = asyncio.run(service.analyze("예시"))

    assert brief.is_stale is True
    assert brief.fresh_until is not None


def test_source_change_is_detected_on_reanalysis(providers, llm_json):
    """같은 URL의 본문이 바뀌면 표시한다 — 사용자가 근거가 흔들린 걸 알아야 한다."""
    llm_json(GOOD_LLM)
    provider = FakeProvider()
    providers(provider)

    first = asyncio.run(service.analyze("예시"))
    assert [s.changed for s in first.sources] == [False]  # 첫 수집은 변경이 아니다

    edited = SourceDocument(
        url=HTML_DOC.url,  # URL은 같고 본문만 달라졌다
        kind=HTML_DOC.kind,
        trust_level=HTML_DOC.trust_level,
        title=HTML_DOC.title,
        publisher=HTML_DOC.publisher,
        text="예시는 이제 로봇 회사입니다. 물류 사업을 접었습니다.",
    )
    provider._docs = [edited]
    second = asyncio.run(service.analyze("예시", force_refresh=True))

    assert [s.changed for s in second.sources] == [True]
    assert any("원문이 바뀐 출처 1건" in w for w in second.warnings)


def test_unchanged_source_is_not_flagged(providers, llm_json):
    llm_json(GOOD_LLM)
    providers(FakeProvider())

    asyncio.run(service.analyze("예시"))
    second = asyncio.run(service.analyze("예시", force_refresh=True))

    assert [s.changed for s in second.sources] == [False]
    assert not any("원문이 바뀐" in w for w in second.warnings)


def test_transient_error_is_retried_once(monkeypatch):
    """일시적 네트워크 오류는 1회 재시도하고, 차단은 재시도하지 않는다."""
    import httpx

    from app.companies.sources import base

    calls = {"n": 0}

    async def flaky(client, url):
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("일시적 오류")
        html = "<html><title>OK</title><p>본문입니다 충분히 길게</p></html>"
        return url, html.encode(), "utf-8", "text/html"

    monkeypatch.setattr(base, "_get", flaky)
    monkeypatch.setattr(base, "RETRY_BACKOFF_SECONDS", 0)  # 테스트는 기다리지 않는다

    doc = asyncio.run(REAL_FETCH("https://example.com", SourceKind.official_site, TrustLevel.primary))

    assert calls["n"] == 2
    assert doc.title == "OK"


def test_client_error_is_not_retried(monkeypatch):
    import httpx

    from app.companies.sources import base

    calls = {"n": 0}

    async def forbidden(client, url):
        calls["n"] += 1
        raise httpx.HTTPStatusError(
            "403", request=httpx.Request("GET", url), response=httpx.Response(403)
        )

    monkeypatch.setattr(base, "_get", forbidden)

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(REAL_FETCH("https://example.com", SourceKind.official_site, TrustLevel.primary))
    assert calls["n"] == 1  # 4xx는 재시도해도 같다


@pytest.mark.parametrize(
    "final_url,expected",
    [
        ("https://www.example.com/kr", TrustLevel.primary),  # 같은 호스트(www 차이) — 유지
        ("https://queue.other.net/wait", TrustLevel.secondary),  # 남의 도메인 — 강등
    ],
)
def test_cross_host_redirect_downgrades_trust(monkeypatch, final_url, expected):
    """공식 도메인이 대기열 서비스로 튕기는 실제 사례(samsung.com → queue-it.net) 대비."""
    from app.companies.sources import base

    async def redirected(client, url):
        return final_url, b"<html><title>T</title><p>body</p></html>", "utf-8", "text/html"

    monkeypatch.setattr(base, "_get", redirected)

    doc = asyncio.run(
        REAL_FETCH("https://example.com", SourceKind.official_site, TrustLevel.primary)
    )

    assert doc.trust_level is expected
    assert doc.url == final_url  # 인용은 최종 URL로


def test_pdf_job_posting_is_extracted_with_page_numbers(monkeypatch):
    """PDF 공고도 수집한다 — 페이지 번호를 남겨 인용 위치를 잃지 않는다(§6.3)."""
    from app.companies.sources import base

    async def pdf_response(client, url):
        return url, b"%PDF-fake", "utf-8", "application/pdf"

    monkeypatch.setattr(base, "_get", pdf_response)
    monkeypatch.setattr(
        "app.core.pdf.pdf_pages", lambda body: ["백엔드 채용", "자격요건: Python"]
    )

    doc = asyncio.run(
        REAL_FETCH("https://jobs.example.com/a.pdf", SourceKind.job_posting, TrustLevel.user_provided)
    )

    assert doc.text == "[p.1] 백엔드 채용\n[p.2] 자격요건: Python"
    assert doc.kind is SourceKind.job_posting


# --- JD 저장·분석 (Phase 2) -----------------------------------------------


def test_job_posting_is_structured_and_stored(providers, llm_json):
    llm_json(JOB_LLM)
    providers(FakeProvider(name="official"), UrlEchoProvider())

    brief = asyncio.run(service.analyze("예시", job_url="https://jobs.example.com/1"))

    assert len(brief.jobs) == 1
    job = brief.jobs[0]
    assert job.title == "백엔드 엔지니어"
    assert job.core_skills == ["Python", "PostgreSQL", "대용량 트래픽", "Kubernetes"]
    assert job.problem_types == ["대용량 트래픽 처리"]
    # 공고는 자신을 뽑아낸 원문 출처를 가리킨다
    assert job.source_id in {s.id for s in brief.sources}
    assert next(s for s in brief.sources if s.id == job.source_id).kind == SourceKind.job_posting


def test_job_citing_non_posting_document_is_dropped(providers, llm_json):
    """회사 소개 페이지를 공고라고 우기면 버린다 — 원문 종류와 어긋나는 구조화는 거절."""
    llm_json({**GOOD_LLM, "jobs": [{**JOB_LLM["jobs"][0], "source_id": 1}]})
    providers(FakeProvider())  # S1은 official_site

    brief = asyncio.run(service.analyze("예시"))

    assert brief.jobs == []
    assert any("채용공고가 아닌" in n for n in brief.needs_review)


def test_jobs_endpoint_returns_stored_jobs(client, providers, llm_json):
    llm_json(JOB_LLM)
    providers(FakeProvider(name="official"), UrlEchoProvider())
    client.post(
        "/api/companies/analyze",
        json={"name": "예시", "job_url": "https://jobs.example.com/1"},
    )

    jobs = client.get("/api/companies/예시/jobs").json()

    assert len(jobs) == 1
    assert jobs[0]["role_category"] == "백엔드 개발"


# --- 프로필 매칭 (Phase 3) -------------------------------------------------


def analyze_with_job(providers, llm_json):
    llm_json(JOB_LLM)
    providers(FakeProvider(name="official"), UrlEchoProvider())
    return asyncio.run(service.analyze("예시", job_url="https://jobs.example.com/1"))


def test_matching_uses_real_profile_not_mock_strings(providers, llm_json):
    """목 문자열이 아니라 마스터 프로필의 실제 경력·프로젝트가 근거로 나와야 한다."""
    from app.profile.repository import _PROFILE

    analyze_with_job(providers, llm_json)
    matches = asyncio.run(service.list_matches("예시"))

    assert matches
    strengths = [m for m in matches if m.match_type.value == "strength"]
    assert strengths

    labels = {f"{c['company']} · {c['role']}" for c in _PROFILE["careers"]}
    labels |= {p["name"] for p in _PROFILE["projects"]}
    assert all(m.profile_evidence in labels for m in strengths)

    # 프로필이 실제로 가진 Python/PostgreSQL은 강점, 없는 Kubernetes는 갭
    by_need = {m.company_need: m for m in matches}
    assert by_need["Python"].match_type.value == "strength"
    assert by_need["Kubernetes"].match_type.value == "gap"


def test_matching_explains_with_evidence_and_score_range(providers, llm_json):
    analyze_with_job(providers, llm_json)
    matches = asyncio.run(service.list_matches("예시"))

    for m in matches:
        assert 0 <= m.score <= 100
        assert m.reason  # 점수만 두지 않는다
        assert m.source_ids  # 어느 공고에서 나온 요구인지
    strength = next(m for m in matches if m.match_type.value == "strength")
    assert strength.company_need in strength.reason


def test_matching_follows_profile_changes(providers, llm_json, monkeypatch):
    """저장된 매칭이 아니라 조회 시점 프로필을 쓴다 — 프로필을 고치면 결과가 따라온다."""
    from app.profile import repository as profile_repository

    analyze_with_job(providers, llm_json)
    before = {m.company_need: m.match_type.value for m in asyncio.run(service.list_matches("예시"))}
    assert before["Kubernetes"] == "gap"

    boosted = {
        **profile_repository._PROFILE,
        "projects": [
            *profile_repository._PROFILE["projects"],
            {
                "name": "쿠버네티스 이관",
                "stack": ["Kubernetes"],
                "highlights": ["클러스터를 직접 운영하며 배포 시간을 70% 줄임"],
            },
        ],
    }
    monkeypatch.setattr(profile_repository, "_PROFILE", boosted)

    after = {m.company_need: m for m in asyncio.run(service.list_matches("예시"))}
    assert after["Kubernetes"].match_type.value == "strength"
    assert after["Kubernetes"].profile_evidence == "쿠버네티스 이관"


def test_unregistered_profile_has_no_matches(providers, llm_json, monkeypatch):
    from app.profile import repository as profile_repository

    analyze_with_job(providers, llm_json)
    monkeypatch.setattr(
        profile_repository, "_PROFILE", {**profile_repository._PROFILE, "registered": False}
    )

    assert asyncio.run(service.list_matches("예시")) == []


def test_matches_endpoint_filters_by_job(client, providers, llm_json):
    llm_json(JOB_LLM)
    providers(FakeProvider(name="official"), UrlEchoProvider())
    client.post(
        "/api/companies/analyze",
        json={"name": "예시", "job_url": "https://jobs.example.com/1"},
    )
    job_id = client.get("/api/companies/예시/jobs").json()[0]["id"]

    assert client.get("/api/companies/예시/matches").json()
    assert client.get(f"/api/companies/예시/matches?job_id={job_id}").json()
    assert client.get("/api/companies/예시/matches?job_id=999").json() == []


def test_skill_notation_differences_still_match():
    """표기 흔들림(Node.js/nodejs)을 흡수한다 — 규칙 매칭의 핵심."""
    from app.companies.matching import match_job
    from app.companies.schemas import CompanyJob

    job = CompanyJob(
        id=1, source_id=1, title="t", role_category="", location="", employment="",
        deadline="", description="", requirements=[], preferred=[],
        core_skills=["node.js", "POSTGRE SQL"], problem_types=[],
    )
    profile = {
        "registered": True,
        "careers": [{"company": "A", "role": "B", "stack": ["NodeJS", "postgresql"], "highlights": []}],
        "projects": [],
    }

    assert [m.match_type.value for m in match_job(job, profile)] == ["strength", "strength"]
