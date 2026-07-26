# 목데이터 → Postgres 마이그레이션 설계 (JSONB 하이브리드)

- 날짜: 2026-07-26
- 전제: DB 토대(엔진·세션·`DATABASE_URL` 게이팅·Alembic)는 이미 구축됨(refine 캐시 작업). 이 스펙은
  그 위에 각 도메인 `repository`의 `mock()`을 실 쿼리로 교체한다.
- 모델링 원칙: **JSONB 하이브리드** — "검색·필터·조인에 쓰는 필드만 정규 컬럼, 나머지 중첩 구조는
  JSONB". 통째로 읽고 쓰는 문서는 JSONB, 쿼리 대상은 컬럼.

## 범위

**대상(5개 — 실제 데이터):** essays · profile · jobs · activities · notifications

**제외(2개 — 데이터가 아니라 생성기):** companies(`analyze`)·forms(`convert_form`)는 저장된
데이터가 없고 매번 결과를 생성한다. 실제 구현은 DB SELECT가 아니라 LLM/RAG(companies)·파일
파서(forms)다. DB로 옮기면 가짜 정적 데이터를 넣는 꼴이라 목 유지.

## 공통 패턴 (5개 도메인 전부 동일)

1. **게이팅:** 각 repository는
   ```python
   sm = get_sessionmaker()
   if sm is None:        # DATABASE_URL 없음 → 기존 목 그대로
       return <existing mock>
   async with sm() as session:   # 있음 → 실 쿼리
       ...
   ```
   → 테스트·CI는 `DATABASE_URL` 미설정이라 **목 경로로 그대로 초록**(기존 계약 유지). router·
   service·schemas는 안 건드린다(반환 shape 동일).
2. **시드 소스 = 기존 목:** 현재 목 dict/빌더(`_build_jobs()`·`_PROFILE`·`_QUESTIONS`·`_ACTIVITIES`
   …)를 **시드 데이터로 재사용**한다(DRY). 별도 시드 값을 새로 쓰지 않는다.
3. **시드 적용:** `app/seed.py`에 도메인별 시드 함수 + `python -m app.seed` 엔트리. 멱등
   (`INSERT ... ON CONFLICT DO NOTHING`). `alembic upgrade head` 후 1회 실행하면 테이블이 채워진다.
   유저 상태(essays answers)는 시드하지 않는다(빈 채로 시작).
4. **모델·마이그레이션:** 도메인별 SQLAlchemy 모델(`app/<domain>/models.py`, `Base` 상속) +
   Alembic 리비전 1개. 모델은 `app/core/db.py`의 `Base.metadata`에 등록.
5. **에러 처리:** 캐시와 달리 이건 **주 데이터 경로**다 — DB 오류를 삼키지 않는다(500이 맞다).
   게이팅(`sm is None`)만 목으로 분기하고, DB가 있는데 쿼리가 실패하면 예외를 그대로 올린다.

## 도메인별 테이블

### essays (⭐ 유저 상태 — 핵심)
현재: `_QUESTIONS`(12 참조) + `_COMPANIES`(10, deadline·question_ids 참조) + `_ANSWERS`(유저 상태).

```
table essay_question    -- 참조(시드)
  id          int PK
  tag         text
  prompt      text
  char_limit  int

table essay_company     -- 참조(시드)
  name          text PK
  deadline      text
  question_ids  jsonb     -- [1,3,6]

table essay_answer      -- 유저 상태(시드 안 함, 빈 시작)
  company     text        -- 검색: 기업별 조회
  question_id int         -- 검색: 문항별 조회
  answer      text
  updated_at  timestamptz default now()
  PRIMARY KEY (company, question_id)   -- (기업×문항) 슬롯
```
router·service의 슬롯 조합 로직(`_slots`)은 question/company를 DB에서 읽어 그대로 유지.

### profile (통째로 읽고 씀 → 대부분 JSONB)
```
table profile
  id          int PK        -- 단일 행(id=1)
  registered  bool
  personal    jsonb
  links       jsonb
  educations  jsonb
  awards      jsonb
  languages   jsonb
  certificates jsonb
  careers     jsonb
  projects    jsonb
  activities  jsonb
```
`get_profile()`는 id=1 행을 읽어 dict로 조립. `upload_resume()`는 지금처럼 목 반환(파싱은 미구현
영역 — 이 스펙 밖).

### jobs (필터 컬럼 + JSONB)
```
table job
  id            int PK
  company       text
  domain        text
  role_category text      -- 필터
  experience    text      -- 필터
  employment    text      -- 필터
  location      text      -- 필터
  title         text
  dday          text
  source        text
  description   text
  tags          jsonb
  responsibilities jsonb
  requirements  jsonb
  preferred     jsonb
  company_info  text
  match_reason  text
```
`repository.all_jobs()`(현재 `_build_jobs()`)를 `SELECT * FROM job`으로 교체. service의 필터·
임베딩·매칭·캐시는 그대로. 40건은 `_build_jobs()` 결과를 시드.

### activities (참조 리스트)
```
table activity
  id                  int PK
  name                text
  category            text     -- 필터 가능(현재는 미사용이나 자연 컬럼)
  organizer           text
  period              text
  dday                text
  fit                 int
  expected_experience text
  fills_gap           jsonb
  connections         jsonb
```

### notifications (참조 리스트)
```
table notification
  id       int PK
  type     text
  title    text
  message  text
  time     text
  unread   bool
```

## 파일 구조 (도메인당)
```
app/<domain>/models.py        # SQLAlchemy 모델(Base 상속)
app/<domain>/repository.py     # mock() → 게이팅 + 실 쿼리(목은 시드 소스로 남김)
alembic/versions/000X_<domain>.py  # 테이블 생성
app/seed.py                    # 도메인별 시드 함수 누적(멱등)
```
router·service·schemas는 불변.

## 테스트
- **목 경로**(DATABASE_URL 없음): 기존 도메인 테스트가 그대로 통과해야 한다(반환 shape 불변).
- **DB 경로**: 로컬 pg 수동 검증(`alembic upgrade head` → `python -m app.seed` → 엔드포인트 호출로
  DB 데이터 확인). essays는 답변 저장 후 재조회로 영속 확인. CI엔 DB 없음.
- 새 단위 테스트는 게이팅 분기(sm None→목) 정도만 얕게. 실 쿼리는 로컬 검증.

## 순서 (하나씩, 상태 있는 것부터)
1. **essays** — 유저 답변 영속(최고 가치, 게이팅+시드+answer 저장 패턴 확립)
2. **profile** — JSONB 문서 패턴
3. **jobs** — 필터 컬럼 + 시드 40건 + service 연동(캐시와 공존 확인)
4. **activities** — 참조 리스트(얇음)
5. **notifications** — 참조 리스트(얇음)

각 도메인이 독립적으로 테스트·병합 가능한 단위. 1이 게이팅·시드·모델 패턴을 세우면 2~5는 그 위에
테이블·쿼리만 추가하는 얇은 반복.

## 비목표
- companies·forms의 DB화(생성기 — LLM/파서가 실제 구현).
- upload_resume 실제 파싱, 실 채용 API 소스 연동(별도 작업).
- pgvector·임베딩 캐시(별도).
- profile 정규화(careers 등 자식 테이블) — 통째 접근이라 JSONB로 충분.
