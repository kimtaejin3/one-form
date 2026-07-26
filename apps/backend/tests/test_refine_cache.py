import asyncio

from app.jobs import cache


def test_cache_key_deterministic_and_sensitive():
    a = cache.cache_key("M", "prof", "job")
    b = cache.cache_key("M", "prof", "job")
    assert a == b                                  # 같은 입력 → 같은 키
    assert a != cache.cache_key("M", "prof2", "job")   # 프로필 바뀌면 달라짐
    assert a != cache.cache_key("M", "prof", "job2")   # 공고 바뀌면 달라짐
    assert a != cache.cache_key("M2", "prof", "job")   # 모델 바뀌면 달라짐


def test_model_id_includes_class_and_model():
    class FakeLlm:
        MODEL = "x-1"
    assert cache.model_id(FakeLlm()) == "FakeLlm:x-1"


def test_get_set_roundtrip_in_memory():
    # DATABASE_URL 미설정(conftest) → _MEM 폴백 경로. async 플러그인 없이 asyncio.run으로.
    assert asyncio.run(cache.get("k")) is None
    asyncio.run(cache.set("k", 77, "이유"))
    assert asyncio.run(cache.get("k")) == (77, "이유")


def test_bad_driver_url_degrades_to_miss(monkeypatch):
    from app.core.config import settings

    # 동기 드라이버 URL → create_async_engine이 즉시 예외를 던지는 케이스
    monkeypatch.setattr(settings, "DATABASE_URL", "postgresql://u@localhost/x")
    assert asyncio.run(cache.get("k")) is None   # 예외 대신 미스
    asyncio.run(cache.set("k", 1, "r"))          # 예외 없이 노옵
