"""매칭 파이프라인 — 랭킹·키 게이팅·계약(match_rate)·프로필 게이트."""
import asyncio
import inspect
import re
import sys

from app.ai import embedder as embedder_module
from app.ai import llm as llm_module
from app.jobs.sources import jobkorea, saramin, wanted
from app.jobs.sources.selector import active_sources
from app.profile import repository as profile_repository

KEYS = [
    "SARAMIN_API_KEY", "JOBKOREA_API_KEY", "WANTED_API_KEY",
    "VOYAGE_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
]


def _set_keys(monkeypatch, only: str | None = None):
    """env·settings 양쪽을 갈아끼운다(설정은 프로세스 시작 시 로드되므로).

    only가 None이면 전부 비우고, 키 이름을 주면 그 키 하나만 채운다.
    """
    from app.core import config

    for key in KEYS:
        monkeypatch.delenv(key, raising=False)
    if only:
        monkeypatch.setenv(only, "test-key")
    monkeypatch.setattr(config, "settings", config.Settings(_env_file=None))
    for module in (embedder_module, llm_module, saramin, jobkorea, wanted):
        monkeypatch.setattr(module, "settings", config.settings)


def _no_keys(monkeypatch):
    _set_keys(monkeypatch)


# --- (a) 파이프라인 흐름 (목 어댑터) ---

def test_feed_sorted_by_match_rate(client):
    jobs = client.get("/api/jobs?page=1&size=10").json()["jobs"]
    rates = [j["match_rate"] for j in jobs]
    assert rates == sorted(rates, reverse=True)  # 매칭률 내림차순


def test_page_two_has_lower_or_equal_rates(client):
    page1 = client.get("/api/jobs?page=1&size=5").json()["jobs"]
    page2 = client.get("/api/jobs?page=2&size=5").json()["jobs"]
    # LLM 보정은 1페이지만 — 2페이지는 임베딩 점수 + 소스 근거 그대로.
    assert [j["id"] for j in page1] != [j["id"] for j in page2]
    assert min(j["match_rate"] for j in page1) >= max(j["match_rate"] for j in page2) - 5


def test_pipeline_ranks_profile_relevant_jobs_on_top(client, monkeypatch):
    """§6의 목적("관련 공고를 위로 올리는가")을 실제 파이프라인으로 확인.

    scripts/eval_matching.py는 자기 픽스처 문자열만 임베딩해 랭킹을 재므로 service의 텍스트
    빌더(_profile_text·_job_text)·소스·정렬을 전혀 지나지 않는다 — 그쪽이 신호를 잃어도
    recall은 1.00로 남는다. 여기선 프로필 repository→피드 응답까지 전 구간을 태운다.
    """
    ios_profile = {
        **profile_repository._PROFILE,
        "careers": [
            {"role": "iOS 개발자", "highlights": ["Swift 앱 출시"], "stack": ["Swift", "SwiftUI"]}
        ],
        "projects": [],
    }
    monkeypatch.setattr(profile_repository, "_PROFILE", ios_profile)
    titles = [j["title"] for j in client.get("/api/jobs?page=1&size=7").json()["jobs"]]
    # 목 공고 40건 중 iOS는 5건 — 전부 상위 7위 안에 들어와야 한다.
    assert sum("iOS 개발자" in t for t in titles) == 5, titles


def test_match_reason_cites_job_specific_skills(client):
    """근거가 공고마다 달라야 한다 — 직무 공통 스킬만 인용하면 전 공고가 같은 문장이 된다.

    근거를 겹치는 '토큰'(react·typescript…)으로 만들면 프론트 5건이 전부
    "프로필의 프론트엔드 · react · typescript 경험이…"로 나온다. 그래서 근거가 그 공고의
    세부 매칭 스킬(디자인 시스템·상태관리…)을 실제로 인용하는지까지 본다.
    """
    ids = [j["id"] for j in client.get("/api/jobs", params={"role": "프론트엔드"}).json()["jobs"]]
    details = [client.get(f"/api/jobs/{i}").json() for i in ids]
    reasons = [d["match_reason"] for d in details]
    assert len(set(reasons)) == len(reasons), reasons  # 5건 모두 다른 근거

    for detail, reason in zip(details, reasons):
        # core(React·TypeScript)는 모든 프론트 공고 공통 — 근거를 구별하는 건 나머지 세부다.
        specific = [
            s for s in detail["match_analysis"]["matched_skills"]
            if s not in ("React", "TypeScript")
        ]
        assert specific, detail["id"]  # 전제: 세부 충족 스킬이 있는 공고들
        assert any(s in reason for s in specific), (detail["id"], reason, specific)


# --- (b) 키 게이팅: 키 없으면 목, 실 전송 import 없이 통과 ---

def test_factories_pick_mocks_without_keys(monkeypatch):
    _no_keys(monkeypatch)
    assert isinstance(embedder_module.get_embedder(), embedder_module.MockEmbedder)
    assert isinstance(llm_module.get_llm(), llm_module.MockLlm)
    sources = active_sources()
    assert len(sources) == 1 and type(sources[0]).__name__ == "MockJobSource"


def test_mock_path_runs_without_real_transport(monkeypatch):
    _no_keys(monkeypatch)
    vectors = asyncio.run(embedder_module.get_embedder().embed(["백엔드 FastAPI", "iOS Swift"]))
    rate, reason = asyncio.run(
        llm_module.get_llm().refine("백엔드 FastAPI", "백엔드 FastAPI", 70, ["FastAPI"])
    )
    assert len(vectors) == 2 and 0 <= rate <= 100 and reason
    # 공식 SDK는 아예 쓰지 않고, httpx는 실 어댑터 메서드 안에서만 lazy import.
    assert "anthropic" not in sys.modules and "voyageai" not in sys.modules
    for module in (embedder_module, llm_module, saramin, jobkorea, wanted):
        assert not re.search(r"^import httpx", inspect.getsource(module), re.M)


def test_each_key_activates_only_its_own_adapter(monkeypatch):
    """§3의 핵심 약속: 키를 넣는 순간 그 어댑터만 실작동.

    팩토리가 자기 키를 안 보거나(항상 목) 남의 키를 보면 여기서 깨진다 — 키 없는 테스트만으론
    둘 다 통과해버린다. 생성만 하고 fetch/embed는 부르지 않으므로 네트워크는 타지 않는다.
    """
    _set_keys(monkeypatch, "VOYAGE_API_KEY")
    assert isinstance(embedder_module.get_embedder(), embedder_module.VoyageEmbedder)
    assert isinstance(llm_module.get_llm(), llm_module.MockLlm)  # 남의 키엔 반응 안 함

    _set_keys(monkeypatch, "ANTHROPIC_API_KEY")
    assert isinstance(llm_module.get_llm(), llm_module.AnthropicLlm)
    assert isinstance(embedder_module.get_embedder(), embedder_module.MockEmbedder)

    # GEMINI 키는 LLM·임베더 둘 다 활성화한다(같은 키 공유).
    _set_keys(monkeypatch, "GEMINI_API_KEY")
    assert isinstance(llm_module.get_llm(), llm_module.GeminiLlm)
    assert isinstance(embedder_module.get_embedder(), embedder_module.GeminiEmbedder)

    _set_keys(monkeypatch, "WANTED_API_KEY")
    assert [type(s).__name__ for s in active_sources()] == ["WantedSource"]  # 목 대체


def test_gemini_failure_falls_back_to_mock_reason(monkeypatch):
    """실 호출이 깨져도(인증 실패·네트워크) 피드는 살아야 한다 — 근거만 목으로 폴백.

    연결 거부되는 주소로 호출해 네트워크 없이 실패 경로만 태운다.
    """
    monkeypatch.setattr(llm_module.GeminiLlm, "URL", "http://127.0.0.1:1/{model}")
    rate, reason = asyncio.run(
        llm_module.GeminiLlm("test-key").refine("프로필", "공고", 70, ["Redis 캐싱"])
    )
    assert rate == 71 and "Redis 캐싱" in reason  # 목 근거(base_rate + 겹친 스킬 수)


def test_gemini_key_wins_over_anthropic(monkeypatch):
    """LLM 키가 둘 다 있으면 Gemini — 우선순위가 뒤집히면 의도치 않은 쪽에 과금된다."""
    from app.core import config

    _set_keys(monkeypatch, "GEMINI_API_KEY")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(config, "settings", config.Settings(_env_file=None))
    monkeypatch.setattr(llm_module, "settings", config.settings)
    assert isinstance(llm_module.get_llm(), llm_module.GeminiLlm)


def test_real_llm_refines_first_page_only(client, monkeypatch):
    """실 LLM은 1페이지만 보정 — 게이트가 키 이름이 아니라 어댑터 타입 기준이어야 한다.

    이전 게이트는 `ANTHROPIC_API_KEY is None`이었다. Gemini 키만 넣으면 "목이구나"로 오인해
    전 페이지를 실 API로 보정한다 — 페이지를 넘길 때마다 size번씩 과금된다.
    `isinstance(llm, MockLlm)` 기준을 못박아 그 회귀를 막는다.
    """
    _set_keys(monkeypatch, "GEMINI_API_KEY")
    assert isinstance(llm_module.get_llm(), llm_module.GeminiLlm)  # 전제

    calls = []

    async def fake_refine(self, profile_text, job_text, base_rate, matched):
        calls.append(base_rate)  # 실 네트워크는 타지 않는다 — 호출 여부만 센다
        return base_rate, "REAL"

    monkeypatch.setattr(llm_module.GeminiLlm, "refine", fake_refine)

    page1 = client.get("/api/jobs?page=1&size=5").json()["jobs"]
    assert len(calls) == 5 and all(j["match_reason"] == "REAL" for j in page1)

    calls.clear()
    page2 = [j["match_reason"] for j in client.get("/api/jobs?page=2&size=5").json()["jobs"]]
    assert calls == []  # 2페이지는 실 API를 부르지 않는다
    assert "REAL" not in page2  # 근거는 소스 원본 그대로

    # 목은 공짜라 반대로 2페이지도 보정한다 — 게이트가 통째로 뒤집히지 않았는지.
    _no_keys(monkeypatch)
    assert [
        j["match_reason"] for j in client.get("/api/jobs?page=2&size=5").json()["jobs"]
    ] != page2


def test_mock_embedder_is_deterministic():
    once = asyncio.run(embedder_module.MockEmbedder().embed(["FastAPI 결제 정산"]))
    twice = asyncio.run(embedder_module.MockEmbedder().embed(["FastAPI 결제 정산"]))
    assert once == twice


# --- (c) 계약: match_rate shape ---

def test_match_rate_shape(client):
    for job in client.get("/api/jobs?page=1&size=12").json()["jobs"]:
        assert isinstance(job["match_rate"], int) and 0 <= job["match_rate"] <= 100
        assert job["match_reason"]


# --- (d) 프로필 게이트 ---

def test_unregistered_profile_returns_empty_feed(client, monkeypatch):
    profile = {**profile_repository._PROFILE, "registered": False}
    monkeypatch.setattr(profile_repository, "_PROFILE", profile)
    body = client.get("/api/jobs").json()
    assert body["total"] == 0 and body["jobs"] == []
    assert client.get("/api/jobs/1").status_code == 404  # 상세도 같은 게이트


# --- 임베더 선택: Voyage 유지 + Gemini 추가 + EMBEDDING_PROVIDER로 전환 ---

def _env(monkeypatch, **kv):
    """지정 env만 세팅하고 config.settings 재빌드(.env 무시) — 임베더 선택 검증용."""
    from app.core import config

    for key in KEYS + ["EMBEDDING_PROVIDER"]:
        monkeypatch.delenv(key, raising=False)
    for k, v in kv.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(config, "settings", config.Settings(_env_file=None))
    for module in (embedder_module, llm_module, saramin, jobkorea, wanted):
        monkeypatch.setattr(module, "settings", config.settings)


def test_embedder_gemini_when_only_gemini_key(monkeypatch):
    # Voyage 키 없이 Gemini 키만 있으면 Gemini 임베딩(같은 키)으로 자동 선택.
    _env(monkeypatch, GEMINI_API_KEY="test-key")
    assert isinstance(embedder_module.get_embedder(), embedder_module.GeminiEmbedder)


def test_embedder_voyage_priority_when_both_keys(monkeypatch):
    # 자동: 둘 다 있으면 Voyage 우선(전문 임베더).
    _env(monkeypatch, VOYAGE_API_KEY="test-key", GEMINI_API_KEY="test-key")
    assert isinstance(embedder_module.get_embedder(), embedder_module.VoyageEmbedder)


def test_embedding_provider_overrides_auto(monkeypatch):
    # EMBEDDING_PROVIDER로 자동을 덮어쓴다 — Voyage 키가 있어도 gemini 강제.
    _env(monkeypatch, VOYAGE_API_KEY="test-key", GEMINI_API_KEY="test-key", EMBEDDING_PROVIDER="gemini")
    assert isinstance(embedder_module.get_embedder(), embedder_module.GeminiEmbedder)
    # mock 강제(키가 있어도).
    _env(monkeypatch, GEMINI_API_KEY="test-key", EMBEDDING_PROVIDER="mock")
    assert isinstance(embedder_module.get_embedder(), embedder_module.MockEmbedder)
