# 목데이터 → Postgres 마이그레이션 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 5개 도메인(essays·profile·jobs·activities·notifications)의 `repository` 목을 Postgres 실 쿼리로 교체한다. JSONB 하이브리드(검색 필드=컬럼, 나머지=JSONB). `DATABASE_URL` 없으면 목 폴백(테스트·CI 무영향).

**Architecture:** DB 토대(`app/core/db.py`의 `Base`/`get_sessionmaker`)는 refine 캐시 작업에서 이미 구축됨. 각 repository는 `get_sessionmaker()`가 None이면 기존 목, 아니면 실 쿼리. 기존 목 dict/빌더를 시드 소스로 재사용해 `python -m app.seed`로 테이블을 채운다. router·service·schemas는 불변.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async) + asyncpg, Alembic, pytest.

## Global Constraints

- **게이팅**: 각 repository 함수는 `sm = get_sessionmaker()`; `if sm is None: <기존 목 반환>`; else 실 쿼리. 목 경로 반환 shape는 현재와 **완전히 동일**해야 한다(router `response_model`·프론트 계약 불변).
- **시드 소스 = 기존 목**: 현재 목 dict/빌더(`_QUESTIONS`·`_COMPANIES`·`_PROFILE`·`_build_jobs()`·`_ACTIVITIES`·`_NOTIFICATIONS`)를 삭제하지 말고 **시드 함수의 데이터 소스로 재사용**한다. 목 값을 플랜에 다시 옮겨쓰지 않는다.
- **에러 처리**: 캐시와 달리 주 데이터 경로 — DB 오류를 삼키지 않는다. 게이팅(`sm is None`)만 목으로 분기, DB가 있는데 쿼리 실패는 예외를 그대로 전파(500이 맞다).
- **모델**: `app/<domain>/models.py`, `app/core/db.py`의 `Base` 상속. Alembic env.py는 이미 `import app.jobs.cache`로 모델을 등록하는 패턴 — 각 도메인 모델도 env.py에 import 추가.
- **시드**: `app/seed.py`에 도메인별 `seed_<domain>(session)` 함수 누적 + `python -m app.seed` 엔트리. 멱등(`ON CONFLICT DO NOTHING`). 유저 상태(essay_answer)는 시드하지 않음.
- **테스트**: 목 경로(DATABASE_URL 없음)로 기존 도메인 테스트가 그대로 통과해야 함. DB 경로는 로컬 pg 수동 검증(CI엔 DB 없음).
- **커밋**: `type(scope): 제목`(한국어 명령형), 끝에 `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`. 도메인당 1커밋.
- **리비전 번호**: refine 캐시가 `0001_match_cache`. 이어서 `0002_essays` → `0003_profile` → `0004_jobs` → `0005_activities` → `0006_notifications`. 각 리비전의 `down_revision`은 직전 리비전.

---

### Task 1: essays — 게이팅·시드 패턴 확립 + 답변 영속

가장 가치 큰 도메인(유저 답변 영속). 공유 `app/seed.py` 스캐폴드를 여기서 만든다.

**Files:**
- Create: `apps/backend/app/essays/models.py`
- Create: `apps/backend/app/seed.py`
- Create: `apps/backend/alembic/versions/0002_essays.py`
- Modify: `apps/backend/app/essays/repository.py`
- Modify: `apps/backend/alembic/env.py` (모델 import 추가)

**Interfaces:**
- Consumes: `app.core.db.Base`, `app.core.db.get_sessionmaker`.
- Produces: `EssayQuestion`/`EssayCompany`/`EssayAnswer` 모델; `app.seed.seed_essays(session)`; `app.seed`의 `main()`. repository 공개 함수(`list_questions`/`save_answer`/`generate_draft`) 시그니처·반환 shape 불변.

- [ ] **Step 1: 모델 작성**

Create `apps/backend/app/essays/models.py`:
```python
"""essays 테이블 — 문항·기업(참조) + 답변(유저 상태). JSONB 하이브리드."""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class EssayQuestion(Base):
    __tablename__ = "essay_question"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tag: Mapped[str] = mapped_column(Text)
    prompt: Mapped[str] = mapped_column(Text)
    char_limit: Mapped[int] = mapped_column(Integer)


class EssayCompany(Base):
    __tablename__ = "essay_company"
    name: Mapped[str] = mapped_column(String(80), primary_key=True)
    deadline: Mapped[str] = mapped_column(Text)
    question_ids: Mapped[list] = mapped_column(JSONB)


class EssayAnswer(Base):
    __tablename__ = "essay_answer"
    company: Mapped[str] = mapped_column(String(80), primary_key=True)
    question_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

- [ ] **Step 2: 마이그레이션 작성**

Create `apps/backend/alembic/versions/0002_essays.py`:
```python
"""essays 테이블 3개 생성

Revision ID: 0002_essays
Revises: 0001_match_cache
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_essays"
down_revision = "0001_match_cache"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "essay_question",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tag", sa.Text(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("char_limit", sa.Integer(), nullable=False),
    )
    op.create_table(
        "essay_company",
        sa.Column("name", sa.String(length=80), primary_key=True),
        sa.Column("deadline", sa.Text(), nullable=False),
        sa.Column("question_ids", postgresql.JSONB(), nullable=False),
    )
    op.create_table(
        "essay_answer",
        sa.Column("company", sa.String(length=80), primary_key=True),
        sa.Column("question_id", sa.Integer(), primary_key=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("essay_answer")
    op.drop_table("essay_company")
    op.drop_table("essay_question")
```

- [ ] **Step 3: env.py에 모델 import 추가**

Modify `apps/backend/alembic/env.py` — 기존 `import app.jobs.cache  # noqa` 줄 아래에:
```python
import app.essays.models  # noqa: F401 — 모델을 Base.metadata에 등록
```

- [ ] **Step 4: 시드 엔트리 + essays 시드 작성**

Create `apps/backend/app/seed.py`:
```python
"""python -m app.seed — 목데이터를 DB에 시드(멱등). DATABASE_URL 필요.

기존 목 dict/빌더를 시드 소스로 재사용. 유저 상태(essay_answer)는 시드하지 않는다.
"""
import asyncio

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.db import get_sessionmaker
from app.essays import repository as essays_repo
from app.essays.models import EssayCompany, EssayQuestion


async def seed_essays(session) -> None:
    for q in essays_repo._QUESTIONS:
        await session.execute(
            pg_insert(EssayQuestion).values(**q).on_conflict_do_nothing(index_elements=["id"])
        )
    for c in essays_repo._COMPANIES:
        await session.execute(
            pg_insert(EssayCompany).values(
                name=c["name"], deadline=c["deadline"], question_ids=c["question_ids"]
            ).on_conflict_do_nothing(index_elements=["name"])
        )


async def main() -> None:
    sm = get_sessionmaker()
    if sm is None:
        raise SystemExit("DATABASE_URL이 설정돼 있어야 시드할 수 있습니다.")
    async with sm() as session:
        await seed_essays(session)
        await session.commit()
    print("seed 완료")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 5: repository 게이팅**

Modify `apps/backend/app/essays/repository.py`. `_QUESTIONS`·`_COMPANIES`·`_ANSWERS`는 **그대로 두고**(시드 소스·목 폴백), import·로더·게이팅을 추가한다. 상단 import:
```python
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import func

from app.core.db import get_sessionmaker
from app.essays.models import EssayAnswer, EssayCompany, EssayQuestion
```
`_slots`/`_merged`를 로드된 데이터를 받도록 바꾸고 로더를 추가:
```python
async def _load_ref() -> tuple[list[dict], list[dict]]:
    """문항·기업 참조 — DB 있으면 DB, 없으면 목."""
    sm = get_sessionmaker()
    if sm is None:
        return _QUESTIONS, _COMPANIES
    async with sm() as s:
        qs = (await s.execute(select(EssayQuestion))).scalars().all()
        cs = (await s.execute(select(EssayCompany))).scalars().all()
        questions = [{"id": q.id, "tag": q.tag, "prompt": q.prompt, "char_limit": q.char_limit} for q in qs]
        companies = [{"name": c.name, "deadline": c.deadline, "question_ids": c.question_ids} for c in cs]
        return questions, companies


async def _load_answers() -> dict:
    sm = get_sessionmaker()
    if sm is None:
        return _ANSWERS
    async with sm() as s:
        rows = (await s.execute(select(EssayAnswer))).scalars().all()
        return {(r.company, r.question_id): {"content": r.content, "status": r.status} for r in rows}


def _slots(question_id: int, companies: list[dict], answers: dict) -> list[dict]:
    used_by = [c for c in companies if question_id in c["question_ids"]]
    if not used_by:
        used_by = [{"name": "공통", "deadline": ""}]
    return [
        {
            "company": c["name"],
            "deadline": c["deadline"],
            **answers.get((c["name"], question_id), {"content": "", "status": "미작성"}),
        }
        for c in used_by
    ]
```
공개 함수 교체:
```python
async def list_questions():
    questions, companies = await _load_ref()
    answers = await _load_answers()
    return [{**q, "slots": _slots(q["id"], companies, answers)} for q in questions]


async def save_answer(question_id: int, company: str, content: str, status: str):
    questions, companies = await _load_ref()
    answers = await _load_answers()
    question = next((q for q in questions if q["id"] == question_id), None)
    if question is None or company not in {s["company"] for s in _slots(question_id, companies, answers)}:
        raise KeyError((company, question_id))
    sm = get_sessionmaker()
    if sm is None:
        _ANSWERS[(company, question_id)] = {"content": content, "status": status}
    else:
        async with sm() as s:
            stmt = pg_insert(EssayAnswer).values(
                company=company, question_id=question_id, content=content, status=status
            ).on_conflict_do_update(
                index_elements=["company", "question_id"],
                set_={"content": content, "status": status, "updated_at": func.now()},
            )
            await s.execute(stmt)
            await s.commit()
    answers = await _load_answers()
    return {**question, "slots": _slots(question_id, companies, answers)}
```
`generate_draft`는 그대로(목 유지 — AI 초안은 이 스펙 밖). `_merged`는 삭제(위 로직에 흡수).

- [ ] **Step 6: 목 경로 회귀 테스트 확인**

Run: `cd apps/backend && uv run pytest tests/ -q`
Expected: 기존 essays 테스트 전부 통과(DATABASE_URL 미설정 → 목 경로, shape 불변). 회귀 없음.

- [ ] **Step 7: 커밋**

```bash
cd /Users/kimtaejin/dev/one-form
git add apps/backend/app/essays/models.py apps/backend/app/seed.py apps/backend/alembic/versions/0002_essays.py apps/backend/app/essays/repository.py apps/backend/alembic/env.py
git commit -m "$(cat <<'MSG'
feat(backend): essays를 Postgres로(문항·기업 시드 + 답변 영속), seed 엔트리 추가

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

- [ ] **Step 8: 로컬 pg 검증 (컨트롤러가 수행 — 구현자는 스킵)**

`DATABASE_URL` 환경변수로 `alembic upgrade head` → `python -m app.seed` → 백엔드 기동 → 답변 PUT 후 서버 재시작 → GET으로 답변이 유지되는지(영속) 확인. `psql oneform -c 'select * from essay_answer'`.

---

### Task 2: profile — JSONB 문서

**Files:**
- Create: `apps/backend/app/profile/models.py`
- Create: `apps/backend/alembic/versions/0003_profile.py`
- Modify: `apps/backend/app/profile/repository.py`
- Modify: `apps/backend/app/seed.py` (seed_profile 추가 + main에서 호출)
- Modify: `apps/backend/alembic/env.py` (`import app.profile.models  # noqa`)

**Interfaces:**
- Consumes: `Base`, `get_sessionmaker`, 기존 `_PROFILE` dict(시드 소스·목 폴백).
- Produces: `Profile` 모델; `app.seed.seed_profile(session)`. `get_profile()`·`upload_resume()` 반환 shape 불변.

- [ ] **Step 1: 모델 작성**

Create `apps/backend/app/profile/models.py`:
```python
"""profile 테이블 — 단일 행. 통째로 읽고 쓰므로 중첩은 전부 JSONB."""
from sqlalchemy import Boolean, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Profile(Base):
    __tablename__ = "profile"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    registered: Mapped[bool] = mapped_column(Boolean)
    personal: Mapped[dict] = mapped_column(JSONB)
    links: Mapped[list] = mapped_column(JSONB)
    educations: Mapped[list] = mapped_column(JSONB)
    awards: Mapped[list] = mapped_column(JSONB)
    languages: Mapped[list] = mapped_column(JSONB)
    certificates: Mapped[list] = mapped_column(JSONB)
    careers: Mapped[list] = mapped_column(JSONB)
    projects: Mapped[list] = mapped_column(JSONB)
    activities: Mapped[list] = mapped_column(JSONB)
```

- [ ] **Step 2: 마이그레이션 작성**

Create `apps/backend/alembic/versions/0003_profile.py`:
```python
"""profile 테이블 생성

Revision ID: 0003_profile
Revises: 0002_essays
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_profile"
down_revision = "0002_essays"
branch_labels = None
depends_on = None

_JSON_COLS = ["personal", "links", "educations", "awards", "languages",
              "certificates", "careers", "projects", "activities"]


def upgrade() -> None:
    op.create_table(
        "profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("registered", sa.Boolean(), nullable=False),
        *[sa.Column(c, postgresql.JSONB(), nullable=False) for c in _JSON_COLS],
    )


def downgrade() -> None:
    op.drop_table("profile")
```

- [ ] **Step 3: env.py + seed 추가**

Modify `alembic/env.py`: add `import app.profile.models  # noqa: F401`.
Modify `app/seed.py`: import `from app.profile import repository as profile_repo` + `from app.profile.models import Profile`, add:
```python
async def seed_profile(session) -> None:
    p = profile_repo._PROFILE
    await session.execute(
        pg_insert(Profile).values(
            id=1,
            registered=p["registered"],
            personal=p["personal"], links=p["links"], educations=p["educations"],
            awards=p["awards"], languages=p["languages"], certificates=p["certificates"],
            careers=p["careers"], projects=p["projects"], activities=p["activities"],
        ).on_conflict_do_nothing(index_elements=["id"])
    )
```
And call `await seed_profile(session)` in `main()` before commit.

- [ ] **Step 4: repository 게이팅**

Modify `apps/backend/app/profile/repository.py`. Keep `_PROFILE` (seed source / mock fallback). Add:
```python
from sqlalchemy import select
from app.core.db import get_sessionmaker
from app.profile.models import Profile
```
Replace `get_profile`:
```python
async def get_profile():
    sm = get_sessionmaker()
    if sm is None:
        return _PROFILE
    async with sm() as s:
        row = await s.get(Profile, 1)
        if row is None:
            return _PROFILE  # 시드 전이면 목으로(빈 화면 방지)
        return {
            "registered": row.registered,
            "personal": row.personal, "links": row.links, "educations": row.educations,
            "awards": row.awards, "languages": row.languages, "certificates": row.certificates,
            "careers": row.careers, "projects": row.projects, "activities": row.activities,
        }
```
`upload_resume()`는 그대로(목 — 파싱 미구현).

- [ ] **Step 5: 회귀 테스트**

Run: `cd apps/backend && uv run pytest -q`
Expected: 전체 통과(목 경로 shape 불변).

- [ ] **Step 6: 커밋**

```bash
cd /Users/kimtaejin/dev/one-form
git add apps/backend/app/profile/models.py apps/backend/alembic/versions/0003_profile.py apps/backend/app/profile/repository.py apps/backend/app/seed.py apps/backend/alembic/env.py
git commit -m "$(cat <<'MSG'
feat(backend): profile을 Postgres로(단일 행 JSONB 문서)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
)"
```

---

### Task 3: jobs — 필터 컬럼 + JSONB, 40건 시드

`repository.all_jobs()`(동기)를 DB 조회로 바꾼다. service의 필터·임베딩·캐시는 불변.

**Files:**
- Create: `apps/backend/app/jobs/models.py` (`Job` 모델 — `cache.py`의 `MatchCache`와 별개 파일)
- Create: `apps/backend/alembic/versions/0004_jobs.py`
- Modify: `apps/backend/app/jobs/repository.py`
- Modify: `apps/backend/app/seed.py`
- Modify: `apps/backend/alembic/env.py`

**Interfaces:**
- Consumes: `Base`, `get_sessionmaker`, 기존 `_build_jobs()`/`_ALL_JOBS`(시드 소스·목 폴백).
- Produces: `Job` 모델; `seed_jobs(session)`. `repository.all_jobs()` 반환 shape(dict 리스트) 불변.

- [ ] **Step 1: 모델**

Create `apps/backend/app/jobs/models.py`:
```python
"""job 테이블 — 필터 필드는 컬럼, 중첩은 JSONB."""
from sqlalchemy import Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Job(Base):
    __tablename__ = "job"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[str] = mapped_column(Text)
    domain: Mapped[str] = mapped_column(Text)
    role_category: Mapped[str] = mapped_column(Text)   # 필터
    experience: Mapped[str] = mapped_column(Text)      # 필터
    employment: Mapped[str] = mapped_column(Text)      # 필터
    location: Mapped[str] = mapped_column(Text)        # 필터
    title: Mapped[str] = mapped_column(Text)
    dday: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    company_info: Mapped[str] = mapped_column(Text)
    match_reason: Mapped[str] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSONB)
    responsibilities: Mapped[list] = mapped_column(JSONB)
    requirements: Mapped[list] = mapped_column(JSONB)
    preferred: Mapped[list] = mapped_column(JSONB)
```

- [ ] **Step 2: 마이그레이션**

Create `apps/backend/alembic/versions/0004_jobs.py` (down_revision `0003_profile`). `op.create_table("job", ...)`로 위 컬럼 그대로 생성(텍스트 컬럼 nullable=False, JSONB nullable=False). Task 2의 마이그레이션 패턴을 따를 것.

- [ ] **Step 3: env.py + seed**

`alembic/env.py`: `import app.jobs.models  # noqa`.
`app/seed.py`: `from app.jobs.repository import _build_jobs` + `from app.jobs.models import Job`, add:
```python
async def seed_jobs(session) -> None:
    for j in _build_jobs():
        await session.execute(
            pg_insert(Job).values(
                id=j["id"], company=j["company"], domain=j["domain"],
                role_category=j["role_category"], experience=j["experience"],
                employment=j["employment"], location=j["location"], title=j["title"],
                dday=j["dday"], source=j["source"], description=j["description"],
                company_info=j["company_info"], match_reason=j["match_reason"],
                tags=j["tags"], responsibilities=j["responsibilities"],
                requirements=j["requirements"], preferred=j["preferred"],
            ).on_conflict_do_nothing(index_elements=["id"])
        )
```
Call in `main()`.

- [ ] **Step 4: repository 게이팅 — 동기→비동기 주의**

현재 `all_jobs()`는 **동기**다. service(`get_job_feed`/`get_job_detail`)가 `repository.all_jobs()`를 동기로 부른다(`app/jobs/service.py:80`, `123`의 `active_sources().fetch`는 별개). 확인: `all_jobs()`를 async로 바꾸면 호출부도 `await` 필요.

Modify `apps/backend/app/jobs/repository.py`: keep `_build_jobs`/`_ALL_JOBS`. Replace:
```python
async def all_jobs() -> list[dict]:
    sm = get_sessionmaker()
    if sm is None:
        return _ALL_JOBS
    async with sm() as s:
        rows = (await s.execute(select(Job).order_by(Job.id))).scalars().all()
        if not rows:
            return _ALL_JOBS  # 시드 전이면 목
        return [
            {
                "id": r.id, "company": r.company, "domain": r.domain,
                "role_category": r.role_category, "experience": r.experience,
                "employment": r.employment, "location": r.location, "title": r.title,
                "dday": r.dday, "source": r.source, "description": r.description,
                "company_info": r.company_info, "match_reason": r.match_reason,
                "tags": r.tags, "responsibilities": r.responsibilities,
                "requirements": r.requirements, "preferred": r.preferred,
            }
            for r in rows
        ]
```
(imports: `from sqlalchemy import select`, `from app.core.db import get_sessionmaker`, `from app.jobs.models import Job`.)

**호출부 갱신** — `all_jobs()`가 async가 됐으므로 `app/jobs/service.py`의 `get_job_detail`에서
`repository.all_jobs()` → `await repository.all_jobs()`로. (`get_job_feed`는 `active_sources()`로 fetch하므로 `all_jobs`를 직접 안 쓸 수 있음 — grep으로 모든 `all_jobs()` 호출부를 찾아 `await` 처리.)

- [ ] **Step 5: 회귀 테스트**

Run: `cd apps/backend && uv run pytest -q`
Expected: 전체 통과. jobs 필터·페이지네이션 테스트(`test_matching.py` 등)가 목 경로에서 그대로 통과하는지 특히 확인. `all_jobs` async 전환으로 인한 미await 누락이 없어야 함.

- [ ] **Step 6: 커밋**

```bash
git add apps/backend/app/jobs/models.py apps/backend/alembic/versions/0004_jobs.py apps/backend/app/jobs/repository.py apps/backend/app/seed.py apps/backend/alembic/env.py apps/backend/app/jobs/service.py
git commit -m "feat(backend): jobs를 Postgres로(필터 컬럼+JSONB, 40건 시드)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: activities — 참조 리스트

**Files:** `app/activities/models.py`, `alembic/versions/0005_activities.py`, `app/activities/repository.py`, `app/seed.py`, `alembic/env.py`.

**Interfaces:** `Activity` 모델; `seed_activities`. `list_activities()` 반환 shape 불변.

- [ ] **Step 1: 모델** — Create `app/activities/models.py`:
```python
from sqlalchemy import Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class Activity(Base):
    __tablename__ = "activity"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text)
    organizer: Mapped[str] = mapped_column(Text)
    period: Mapped[str] = mapped_column(Text)
    dday: Mapped[str] = mapped_column(Text)
    fit: Mapped[int] = mapped_column(Integer)
    expected_experience: Mapped[str] = mapped_column(Text)
    fills_gap: Mapped[list] = mapped_column(JSONB)
    connections: Mapped[list] = mapped_column(JSONB)
```

- [ ] **Step 2: 마이그레이션** — Create `alembic/versions/0005_activities.py` (down_revision `0004_jobs`), `op.create_table("activity", ...)` 위 컬럼대로(텍스트/Integer nullable=False, JSONB nullable=False).

- [ ] **Step 3: env.py + seed** — `import app.activities.models  # noqa`. seed.py에:
```python
async def seed_activities(session) -> None:
    from app.activities.repository import _ACTIVITIES
    from app.activities.models import Activity
    for a in _ACTIVITIES:
        await session.execute(
            pg_insert(Activity).values(
                id=a["id"], name=a["name"], category=a["category"], organizer=a["organizer"],
                period=a["period"], dday=a["dday"], fit=a["fit"],
                expected_experience=a["expected_experience"],
                fills_gap=a["fills_gap"], connections=a["connections"],
            ).on_conflict_do_nothing(index_elements=["id"])
        )
```
Call in `main()`.

- [ ] **Step 4: repository 게이팅** — Modify `app/activities/repository.py`, keep `_ACTIVITIES`:
```python
async def list_activities():
    sm = get_sessionmaker()
    if sm is None:
        return _ACTIVITIES
    async with sm() as s:
        rows = (await s.execute(select(Activity).order_by(Activity.id))).scalars().all()
        if not rows:
            return _ACTIVITIES
        return [
            {"id": r.id, "name": r.name, "category": r.category, "organizer": r.organizer,
             "period": r.period, "dday": r.dday, "fit": r.fit,
             "expected_experience": r.expected_experience,
             "fills_gap": r.fills_gap, "connections": r.connections}
            for r in rows
        ]
```
(imports: select, get_sessionmaker, Activity.)

- [ ] **Step 5: 회귀 테스트** — `cd apps/backend && uv run pytest -q` → 전체 통과.

- [ ] **Step 6: 커밋** — `feat(backend): activities를 Postgres로(참조 리스트 시드)` + 트레일러.

---

### Task 5: notifications — 참조 리스트

**Files:** `app/notifications/models.py`, `alembic/versions/0006_notifications.py`, `app/notifications/repository.py`, `app/seed.py`, `alembic/env.py`.

- [ ] **Step 1: 모델** — Create `app/notifications/models.py`:
```python
from sqlalchemy import Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class Notification(Base):
    __tablename__ = "notification"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    message: Mapped[str] = mapped_column(Text)
    time: Mapped[str] = mapped_column(Text)
    unread: Mapped[bool] = mapped_column(Boolean)
```
(중첩 없음 → JSONB 불필요.)

- [ ] **Step 2: 마이그레이션** — Create `alembic/versions/0006_notifications.py` (down_revision `0005_activities`), `op.create_table("notification", ...)` 위 컬럼대로.

- [ ] **Step 3: env.py + seed** — `import app.notifications.models  # noqa`. seed.py에:
```python
async def seed_notifications(session) -> None:
    from app.notifications.repository import _NOTIFICATIONS
    from app.notifications.models import Notification
    for n in _NOTIFICATIONS:
        await session.execute(
            pg_insert(Notification).values(**n).on_conflict_do_nothing(index_elements=["id"])
        )
```
Call in `main()`.

- [ ] **Step 4: repository 게이팅** — Modify `app/notifications/repository.py`, keep `_NOTIFICATIONS`:
```python
async def list_notifications():
    sm = get_sessionmaker()
    if sm is None:
        return _NOTIFICATIONS
    async with sm() as s:
        rows = (await s.execute(select(Notification).order_by(Notification.id))).scalars().all()
        if not rows:
            return _NOTIFICATIONS
        return [
            {"id": r.id, "type": r.type, "title": r.title, "message": r.message,
             "time": r.time, "unread": r.unread}
            for r in rows
        ]
```

- [ ] **Step 5: 회귀 테스트** — `cd apps/backend && uv run pytest -q` → 전체 통과.

- [ ] **Step 6: 커밋** — `feat(backend): notifications를 Postgres로(참조 리스트 시드)` + 트레일러.

---

## 최종 로컬 검증 (모든 태스크 후, 컨트롤러 수행)

```bash
cd apps/backend
export DATABASE_URL="postgresql+asyncpg://kimtaejin@localhost/oneform"
uv run alembic upgrade head        # 0002~0006 적용
uv run python -m app.seed          # 5개 도메인 시드(essay_answer 제외)
# 백엔드 기동 후 각 엔드포인트가 DB 데이터를 반환하는지 + essays 답변 저장→재시작→유지 확인
```
`psql oneform -c '\dt'` → match_cache·essay_*·profile·job·activity·notification.
