# DB 기반 + refine 캐시 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 실 LLM refine 결과(rate·reason)를 Postgres에 content 해시로 캐시해 채용공고 피드 새로고침 시 재분석을 없애고, 이후 도메인 영속화가 얹힐 DB 토대(엔진·세션·게이팅·Alembic)를 세운다.

**Architecture:** `DATABASE_URL`이 있으면 Postgres, 없으면 인메모리 dict로 폴백하는 캐시-어사이드. `service.get_job_feed`의 refine 루프가 실 LLM 호출 직전 캐시를 조회하고 미스면 저장한다. 목 LLM은 캐시 경로를 타지 않아 테스트는 DB 없이 돈다.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async) + asyncpg, Alembic, pytest (TestClient).

## Global Constraints

- Python 3.11+, 백엔드 의존성은 uv로 관리(`apps/backend`에서 `uv add`).
- API 경로는 `/api` 프리픽스(기존 규칙). 이 작업은 새 엔드포인트 없음.
- 캐시는 최적화지 필수 경로가 아니다 — DB 오류/연결 실패는 미스로 강등, 피드는 계속 동작.
- 목 LLM(MockLlm)은 캐시 경로를 타지 않는다(공짜·결정적). 캐시는 실 LLM에만.
- 캐시 키 = `blake2b(model_id | profile_text | job_text)`, `model_id = f"{type(llm).__name__}:{getattr(llm,'MODEL','')}"`.
- 테스트는 `DATABASE_URL` 미설정(인메모리 폴백)으로 도는 기존 계약 유지 — CI에 DB 불필요.
- 커밋 규칙: `type(scope): 제목`(한국어 명령형), 커밋 메시지 끝에
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

### Task 1: DB 설정·엔진·세션 토대 (`core/db.py`)

**Files:**
- Modify: `apps/backend/pyproject.toml` (의존성 추가)
- Modify: `apps/backend/app/core/config.py` (DATABASE_URL 필드)
- Create: `apps/backend/app/core/db.py`
- Modify: `apps/backend/conftest.py` (DATABASE_URL 리셋)
- Test: `apps/backend/tests/test_db.py`

**Interfaces:**
- Produces:
  - `app.core.db.Base` — SQLAlchemy `DeclarativeBase` 서브클래스(모델의 부모).
  - `app.core.db.get_sessionmaker() -> async_sessionmaker | None` — `settings.DATABASE_URL`이
    있으면 세션메이커, 없으면 `None`. URL이 바뀌면 재생성(테스트에서 monkeypatch 토글 대응).
  - `settings.DATABASE_URL: str | None`.

- [ ] **Step 1: 의존성 추가**

Run:
```bash
cd apps/backend && uv add "sqlalchemy[asyncio]" asyncpg alembic
```
Expected: `pyproject.toml`에 세 패키지 추가, `uv.lock` 갱신.

- [ ] **Step 2: config에 DATABASE_URL 추가**

Modify `apps/backend/app/core/config.py` — `EMBEDDING_PROVIDER` 아래에 추가:
```python
    # DB 연결 문자열. 있으면 Postgres 캐시, 없으면 인메모리 폴백.
    DATABASE_URL: str | None = None
```

- [ ] **Step 3: 실패하는 테스트 작성**

Create `apps/backend/tests/test_db.py`:
```python
from app.core import db
from app.core.config import settings


def test_no_sessionmaker_without_url(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", None)
    assert db.get_sessionmaker() is None


def test_sessionmaker_built_when_url_present(monkeypatch):
    # 실제 연결은 안 하고 세션메이커 객체 생성만 확인(asyncpg 드라이버 파싱까지).
    monkeypatch.setattr(
        settings, "DATABASE_URL", "postgresql+asyncpg://u@localhost/x"
    )
    sm = db.get_sessionmaker()
    assert sm is not None
```

- [ ] **Step 4: 테스트 실패 확인**

Run: `cd apps/backend && uv run pytest tests/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError: app.core.db` (아직 없음).

- [ ] **Step 5: db.py 구현**

Create `apps/backend/app/core/db.py`:
```python
"""async DB 엔진·세션. DATABASE_URL 없으면 세션메이커 None → 캐시가 인메모리 폴백.

# ponytail: URL별 지연 싱글턴 — 모듈 로드 시점이 아니라 호출 시점의 settings를 본다.
#   테스트가 monkeypatch로 URL을 켰다 껐다 해도 반영된다.
"""
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker | None = None
_url: str | None = None


def get_sessionmaker() -> async_sessionmaker | None:
    global _engine, _sessionmaker, _url
    url = settings.DATABASE_URL
    if url != _url:
        _url = url
        _engine = create_async_engine(url) if url else None
        _sessionmaker = (
            async_sessionmaker(_engine, expire_on_commit=False) if _engine else None
        )
    return _sessionmaker
```

- [ ] **Step 6: conftest에 DATABASE_URL 리셋 추가**

Modify `apps/backend/conftest.py` — `_no_live_keys` 픽스처의 `EMBEDDING_PROVIDER` 줄 아래에:
```python
    monkeypatch.setattr(settings, "DATABASE_URL", None)  # 캐시도 인메모리 폴백으로
```
(로컬 `.env`에 DATABASE_URL을 넣어도 테스트가 실 DB를 안 건드리게.)

- [ ] **Step 7: 테스트 통과 확인**

Run: `cd apps/backend && uv run pytest tests/test_db.py -v`
Expected: PASS (2 passed).

- [ ] **Step 8: 전체 스위트 회귀 확인**

Run: `cd apps/backend && uv run pytest -q`
Expected: 기존 39 + 2 = 41 passed.

- [ ] **Step 9: 커밋**

```bash
cd /Users/kimtaejin/dev/one-form
git add apps/backend/pyproject.toml apps/backend/uv.lock apps/backend/app/core/config.py apps/backend/app/core/db.py apps/backend/conftest.py apps/backend/tests/test_db.py
git commit -m "$(cat <<'MSG'
feat(backend): DB 엔진·세션 토대 + DATABASE_URL 게이팅

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 2: refine 캐시 모듈 (`jobs/cache.py`)

**Files:**
- Create: `apps/backend/app/jobs/cache.py`
- Modify: `apps/backend/conftest.py` (`_MEM` 격리 픽스처)
- Test: `apps/backend/tests/test_refine_cache.py` (키·라운드트립 단위 테스트)

**Interfaces:**
- Consumes: `app.core.db.Base`, `app.core.db.get_sessionmaker`.
- Produces:
  - `app.jobs.cache.MatchCache` — `match_cache` 테이블 모델(`cache_key` PK, `rate`, `reason`, `created_at`).
  - `app.jobs.cache.model_id(llm) -> str`.
  - `app.jobs.cache.cache_key(model_id: str, profile_text: str, job_text: str) -> str` (blake2b 32자 hex).
  - `async app.jobs.cache.get(key: str) -> tuple[int, str] | None`.
  - `async app.jobs.cache.set(key: str, rate: int, reason: str) -> None`.
  - `app.jobs.cache._MEM: dict[str, tuple[int, str]]` (폴백 저장소; 테스트가 비운다).

- [ ] **Step 1: 실패하는 단위 테스트 작성**

Create `apps/backend/tests/test_refine_cache.py`:
```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd apps/backend && uv run pytest tests/test_refine_cache.py -v`
Expected: FAIL — `ModuleNotFoundError: app.jobs.cache`.

- [ ] **Step 3: cache.py 구현**

Create `apps/backend/app/jobs/cache.py`:
```python
"""refine 결과 캐시. DATABASE_URL 있으면 Postgres, 없으면 _MEM 폴백.

# ponytail: 키가 content 해시라 무효화 로직 없음 — 프로필·공고·모델이 바뀌면 새 키(미스)로
#   자동 재생성. 옛 행은 무해하게 남는다(축출은 후속).
# ponytail: DB 오류는 미스로 강등 — 캐시는 최적화지 필수 경로가 아니다.
"""
import hashlib
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, get_sessionmaker

# 폴백 저장소(프로세스 한정). DATABASE_URL 없을 때만 쓰인다.
_MEM: dict[str, tuple[int, str]] = {}


class MatchCache(Base):
    __tablename__ = "match_cache"

    cache_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    rate: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


def model_id(llm) -> str:
    return f"{type(llm).__name__}:{getattr(llm, 'MODEL', '')}"


def cache_key(model_id: str, profile_text: str, job_text: str) -> str:
    raw = f"{model_id}|{profile_text}|{job_text}".encode()
    return hashlib.blake2b(raw, digest_size=16).hexdigest()  # 32자 hex


async def get(key: str) -> tuple[int, str] | None:
    sm = get_sessionmaker()
    if sm is None:
        return _MEM.get(key)
    try:
        async with sm() as session:
            row = await session.get(MatchCache, key)
            return (row.rate, row.reason) if row else None
    except Exception:
        return None  # 미스로 강등 — 피드는 재계산으로 계속


async def set(key: str, rate: int, reason: str) -> None:
    sm = get_sessionmaker()
    if sm is None:
        _MEM[key] = (rate, reason)
        return
    try:
        async with sm() as session:
            stmt = (
                pg_insert(MatchCache)
                .values(cache_key=key, rate=rate, reason=reason)
                .on_conflict_do_nothing(index_elements=["cache_key"])
            )
            await session.execute(stmt)
            await session.commit()
    except Exception:
        pass  # 저장 실패는 조용히 — 다음 요청에 재계산
```

- [ ] **Step 4: conftest에 `_MEM` 격리 픽스처 추가**

Modify `apps/backend/conftest.py` — `_clean_answers` 픽스처 아래에 추가:
```python
@pytest.fixture(autouse=True)
def _clean_cache():
    # refine 캐시 _MEM은 모듈-레벨 — 테스트 간 격리.
    from app.jobs import cache
    cache._MEM.clear()
    yield
    cache._MEM.clear()
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `cd apps/backend && uv run pytest tests/test_refine_cache.py -v`
Expected: PASS (3 passed).

- [ ] **Step 6: 커밋**

```bash
cd /Users/kimtaejin/dev/one-form
git add apps/backend/app/jobs/cache.py apps/backend/conftest.py apps/backend/tests/test_refine_cache.py
git commit -m "$(cat <<'MSG'
feat(backend): refine 캐시 모듈(Postgres·인메모리 폴백)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 3: 캐시를 refine 루프에 배선 (`jobs/service.py`)

**Files:**
- Modify: `apps/backend/app/jobs/service.py` (`get_job_feed`의 `_resolve`)
- Test: `apps/backend/tests/test_refine_cache_feed.py` (엔드투엔드 히트/미스)

**Interfaces:**
- Consumes: `app.jobs.cache.{model_id, cache_key, get, set}`, `app.jobs.service.get_llm`,
  `app.jobs.service._profile_text`, `app.jobs.service._job_text`, `app.jobs.service._matched_skills`.
- Produces: 동작 변경만(공개 시그니처 불변) — 실 LLM일 때 refine 결과가 캐시된다.

- [ ] **Step 1: 실패하는 엔드투엔드 테스트 작성**

Create `apps/backend/tests/test_refine_cache_feed.py`:
```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd apps/backend && uv run pytest tests/test_refine_cache_feed.py -v`
Expected: FAIL — `test_second_request_is_all_cache_hits`에서 `llm.calls`가 2배(캐시 미배선).

- [ ] **Step 3: `_resolve`에 캐시 배선**

Modify `apps/backend/app/jobs/service.py`. 상단 import에 추가:
```python
from app.jobs import cache
```
`_resolve` 함수를 아래로 교체(기존 함수 전체):
```python
    mid = cache.model_id(llm)

    async def _resolve(rate: int, j: dict) -> dict:
        reason = j["match_reason"]
        if page == 1 or refine_all:
            if refine_all:  # 목 LLM — 공짜·결정적, 캐시 안 씀
                rate, reason = await llm.refine(
                    profile_text, _job_text(j), rate, _matched_skills(profile, j)
                )
            else:  # 실 LLM — 캐시-어사이드
                job_text = _job_text(j)
                key = cache.cache_key(mid, profile_text, job_text)
                hit = await cache.get(key)
                if hit is not None:
                    rate, reason = hit
                else:
                    rate, reason = await llm.refine(
                        profile_text, job_text, rate, _matched_skills(profile, j)
                    )
                    await cache.set(key, rate, reason)
        return {
            "id": j["id"],
            "company": j["company"],
            "domain": j["domain"],
            "conditions": f"{j['experience']} · {j['employment']} · {j['location']}",
            "title": j["title"],
            "tags": j["tags"],
            "dday": j["dday"],
            "source": j["source"],
            "match_rate": rate,
            "match_reason": reason,
        }
```
(`refine_all = isinstance(llm, MockLlm)`은 그대로 위에 남는다. 실 LLM이면 `refine_all=False`라
`else` 캐시 경로를 탄다.)

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd apps/backend && uv run pytest tests/test_refine_cache_feed.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: 전체 스위트 회귀 확인**

Run: `cd apps/backend && uv run pytest -q`
Expected: 이전 총합 + 2 passed. 기존 `test_matching.py`의 실-LLM 게이트 테스트가 여전히 통과하는지 확인(목 경로는 캐시 안 타므로 영향 없음).

- [ ] **Step 6: 커밋**

```bash
cd /Users/kimtaejin/dev/one-form
git add apps/backend/app/jobs/service.py apps/backend/tests/test_refine_cache_feed.py
git commit -m "$(cat <<'MSG'
feat(backend): 1페이지 refine을 캐시-어사이드로(새로고침 재분석 제거)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 4: Alembic 마이그레이션 + 로컬 Postgres 검증

**Files:**
- Create: `apps/backend/alembic.ini`, `apps/backend/alembic/env.py`,
  `apps/backend/alembic/versions/0001_match_cache.py` (그 외 alembic 스캐폴드)
- Modify: `apps/backend/.env.example` (DATABASE_URL 항목)

**Interfaces:**
- Consumes: `app.core.db.Base`, `app.jobs.cache.MatchCache`(메타데이터 등록), `settings.DATABASE_URL`.
- Produces: `match_cache` 테이블을 만드는 마이그레이션. CI 테스트 없음 — 로컬 pg 수동 검증.

> 이 태스크는 실 DB가 필요해 pytest로 검증하지 않는다. 검증은 로컬 Postgres에서 실제
> `alembic upgrade head` + 피드 2회 호출로 한다(Step 6-8).

- [ ] **Step 1: async 템플릿으로 alembic 초기화**

Run:
```bash
cd apps/backend && uv run alembic init -t async alembic
```
Expected: `apps/backend/alembic/`(env.py, script.py.mako, versions/) + `alembic.ini` 생성.

- [ ] **Step 2: env.py를 settings·Base에 배선**

Edit `apps/backend/alembic/env.py`:
- 상단 import 뒤에 추가:
  ```python
  from app.core.config import settings
  from app.core.db import Base
  import app.jobs.cache  # noqa: F401 — MatchCache를 Base.metadata에 등록
  ```
- `target_metadata = None`을 교체:
  ```python
  target_metadata = Base.metadata
  ```
- `run_migrations_online`(async)에서 URL을 settings로 강제. 스캐폴드의
  `connectable = async_engine_from_config(config.get_section(...), ...)` 블록을 아래로 교체:
  ```python
      from sqlalchemy.ext.asyncio import create_async_engine
      connectable = create_async_engine(settings.DATABASE_URL)
  ```
  (오프라인 모드는 쓰지 않으므로 `run_migrations_offline`은 손대지 않아도 된다.)

- [ ] **Step 3: match_cache 리비전 작성**

Create `apps/backend/alembic/versions/0001_match_cache.py`:
```python
"""match_cache 테이블 생성

Revision ID: 0001_match_cache
Revises:
Create Date: 2026-07-26
"""
import sqlalchemy as sa
from alembic import op

revision = "0001_match_cache"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "match_cache",
        sa.Column("cache_key", sa.String(length=64), primary_key=True),
        sa.Column("rate", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("match_cache")
```

- [ ] **Step 4: .env.example에 DATABASE_URL 추가**

Modify `apps/backend/.env.example` — 파일 끝에 추가:
```bash
# DB — 있으면 refine 결과를 Postgres에 캐시(새로고침 재분석 제거), 없으면 인메모리 폴백
# 로컬 네이티브 pg 예: postgresql+asyncpg://<user>@localhost/oneform
DATABASE_URL=
```

- [ ] **Step 5: 커밋**

```bash
cd /Users/kimtaejin/dev/one-form
git add apps/backend/alembic apps/backend/alembic.ini apps/backend/.env.example
git commit -m "$(cat <<'MSG'
feat(backend): Alembic + match_cache 마이그레이션, .env.example에 DATABASE_URL

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

- [ ] **Step 6: 로컬 DB 생성 + 마이그레이션 적용**

Run(로컬 pg 기준, `<user>`는 본인 계정):
```bash
createdb oneform
cd apps/backend
echo 'DATABASE_URL=postgresql+asyncpg://<user>@localhost/oneform' >> .env
uv run alembic upgrade head
```
Expected: `match_cache` 테이블 생성. 확인: `psql oneform -c '\d match_cache'`.

- [ ] **Step 7: 백엔드 기동 + 피드 2회 호출로 캐시 확인**

Run:
```bash
cd apps/backend && pnpm dev   # 또는 uv run uvicorn app.main:app --reload --port 8000
# 다른 터미널에서:
curl -s -o /dev/null -w "1회차 %{time_total}s\n" "http://localhost:8000/api/jobs?page=1"
curl -s -o /dev/null -w "2회차 %{time_total}s\n" "http://localhost:8000/api/jobs?page=1"
```
Expected: 1회차 ~9초(refine+저장), **2회차 1초 미만**(전부 캐시 히트). `psql oneform -c 'select count(*) from match_cache'` → 12행.

- [ ] **Step 8: 최종 회귀 확인**

Run(DATABASE_URL을 임시로 비우거나 별 셸에서): `cd apps/backend && uv run pytest -q`
Expected: 전체 passed (conftest가 DATABASE_URL을 None으로 덮으므로 .env에 값이 있어도 인메모리로 돎).

---

## 실행 순서 메모

Task 1 → 2 → 3은 순차 의존(각각 이전 산출물 소비). Task 4(Alembic)는 Task 2의
`MatchCache` 모델에만 의존하므로 3 이후 아무 때나. Task 1-3은 CI로 검증되고, Task 4는
로컬 pg 수동 검증이다.
