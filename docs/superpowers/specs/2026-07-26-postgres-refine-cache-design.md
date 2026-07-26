# DB 기반 + refine 캐시 설계

- 날짜: 2026-07-26
- 범위: 서브프로젝트 **1. DB 기반 + 캐시** (전체 목→DB 마이그레이션의 첫 조각)
- 동기: 채용공고 피드 새로고침 때마다 1페이지 12건을 실 LLM으로 재분석(~10초 + 토큰
  비용). 결과를 영속 캐시해 재분석을 없앤다. 동시에 이후 essays·profile 영속화가 얹힐
  DB 토대(엔진·세션·`DATABASE_URL` 게이팅·Alembic)를 세운다.

## 목표 / 비목표

**목표**
- `DATABASE_URL`이 있으면 Postgres, 없으면 인메모리 폴백으로 도는 DB 토대.
- 실 LLM refine 결과(rate·reason)를 content 해시 키로 캐시 → 새로고침 재분석 제거.
- Alembic 마이그레이션 습관 정착(`match_cache` 테이블 1개).

**비목표(이 조각 아님)**
- 임베딩 캐시(측정 후 별도). pgvector.
- jobs·profile·essays 등 도메인 데이터의 DB 이전(후속 서브프로젝트).
- 캐시 TTL·용량 축출(행이 작고 무해 — 필요해지면 후속).
- 순수 표시용 목(companies·activities·notifications·forms) 이전.

## 아키텍처 / 파일

```
app/core/db.py        # async 엔진·세션 팩토리. DATABASE_URL 없으면 engine=None
app/core/config.py    # + DATABASE_URL: str | None = None
app/jobs/cache.py     # refine 캐시 리포지토리: get(key) / set(key, rate, reason)
app/jobs/service.py   # refine 루프에서 캐시 조회·저장 (수정)
alembic/, alembic.ini # 마이그레이션 (match_cache 생성)
docker-compose.yml    # (선택) 로컬 postgres:16 — 로컬 pg 있으면 불필요
```

캐시는 jobs 도메인이 소비하므로 `app/jobs/cache.py`. DB 엔진·세션은 후속 도메인도 공유하도록
`app/core/db.py`에 둔다.

의존성(uv): `sqlalchemy[asyncio]`, `asyncpg`, `alembic`.

## 데이터 모델 — `match_cache`

| 컬럼 | 타입 | 의미 |
| --- | --- | --- |
| `cache_key` | text PK | `blake2b(model_id \| profile_text \| job_text)` 16진 |
| `rate` | int | 보정된 매칭률(0-100) |
| `reason` | text | 근거 문장 |
| `created_at` | timestamptz | 기본 `now()` |

- **키가 content 해시라 별도 무효화 로직이 필요 없다.** 프로필·공고 텍스트가 바뀌면 해시가
  달라져 자동 미스(→재분석·재저장). 옛 행은 무해하게 남는다(정리는 후속 축출로).
- `model_id`(예: `GeminiLlm:gemini-flash-latest`) 포함 → 모델을 바꾸면 캐시가 자동 갈린다.
  `model_id = f"{type(llm).__name__}:{getattr(llm, 'MODEL', '')}"`.

## 데이터 플로우 (`service.get_job_feed` refine 루프)

```
목 LLM(MockLlm)이면: 캐시 경로를 타지 않고 그냥 refine (공짜·결정적)
실 LLM이면:
    key = blake2b(model_id | profile_text | job_text)
    hit = await cache.get(key)
    hit 있으면: rate, reason = hit           # LLM 호출 0
    미스면:     rate, reason = await llm.refine(...)
                await cache.set(key, rate, reason)   # upsert
```

- 기존 `asyncio.gather` 12병렬 안에서 각 태스크가 get/set. get·set은 각자 짧은 세션을
  열고 닫는다(asyncpg 풀이 동시성 처리).
- 동시 insert 충돌은 `INSERT ... ON CONFLICT (cache_key) DO NOTHING`으로 흡수.
- **목은 캐시 경로를 안 타므로 테스트(전부 목)는 DB를 건드리지 않는다.**

## 게이팅 / 폴백

- `DATABASE_URL` 있음 → `create_async_engine(...)`, 세션으로 Postgres 캐시.
- `DATABASE_URL` 없음 → `engine = None`. `cache.py`가 모듈 dict `_MEM: dict[str, tuple[int, str]]`로
  폴백. 프로세스 한정(재시작 시 소멸)이지만 **CI·로컬은 무설정으로 그대로 초록**.
- 기존 "키 넣으면 코드 수정 없이 실작동" 철학의 확장 — `DATABASE_URL`이 그 키.

## 에러 처리

- `cache.get`/`cache.set`의 DB 오류가 피드를 죽이면 안 된다 → `try/except`로 감싸 **미스로
  강등**(캐시 없이 재계산은 되게). GeminiEmbedder의 목 폴백과 같은 회복 철학.
- 연결 실패도 마찬가지 — 캐시는 최적화지 필수 경로가 아니다.

## 로컬 구동

- 로컬 pg 있음: `.env`에 `DATABASE_URL=postgresql+asyncpg://<user>@localhost/oneform`,
  `createdb oneform`, `alembic upgrade head`.
- 또는 docker-compose(postgres:16) 올려 같은 URL로 연결. 둘 중 택1, 코드는 동일.
- `.env.example`에 `DATABASE_URL=` 주석과 함께 추가.

## 테스트

- **인메모리 경로**(`DATABASE_URL` 없음)로 캐시 의미 검증:
  - 카운팅 페이크 LLM(호출 수 세는) → 같은 피드 2회 요청 시 **2회차는 refine 호출 0**(캐시 히트).
  - 프로필/공고 텍스트를 바꾸면 키가 달라져 **다시 refine 호출**(미스).
- conftest는 이미 키를 비우므로 `DATABASE_URL`도 자연히 미설정 → DB 없이 도는 기존 계약 유지.
- Postgres 실경로는 DB가 필요해 CI에서 제외(로컬 수동 확인).

## 마이그레이션(Alembic)

- `alembic init alembic` 후 `env.py`가 `settings.DATABASE_URL`을 읽도록 배선.
- 리비전 1개: `match_cache` 생성. 적용은 `alembic upgrade head`.
- `alembic.ini`의 `sqlalchemy.url`은 코드에서 주입(설정 단일 소스).

## 후속(이 스펙 밖)

2. essays 영속화 → 3. profile 영속화 → 4. jobs 저장/캐시 정착(외부 소스 연동 시).
각자 이 토대 위에 테이블·리포지토리만 추가하는 얇은 작업.
