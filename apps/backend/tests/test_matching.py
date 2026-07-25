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
    "VOYAGE_API_KEY", "ANTHROPIC_API_KEY",
]


def _no_keys(monkeypatch):
    """env·settings 양쪽에서 키를 비운다(설정은 프로세스 시작 시 로드되므로)."""
    from app.core import config

    for key in KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(config, "settings", config.Settings(_env_file=None))
    for module in (embedder_module, llm_module, saramin, jobkorea, wanted):
        monkeypatch.setattr(module, "settings", config.settings)


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
    rate, reason = asyncio.run(llm_module.get_llm().refine("백엔드 FastAPI", "백엔드 FastAPI", 70))
    assert len(vectors) == 2 and 0 <= rate <= 100 and reason
    # 공식 SDK는 아예 쓰지 않고, httpx는 실 어댑터 메서드 안에서만 lazy import.
    assert "anthropic" not in sys.modules and "voyageai" not in sys.modules
    for module in (embedder_module, llm_module, saramin, jobkorea, wanted):
        assert not re.search(r"^import httpx", inspect.getsource(module), re.M)


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
