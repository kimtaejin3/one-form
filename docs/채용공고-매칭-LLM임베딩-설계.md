# 채용공고 매칭 — LLM/임베딩 실구현 설계

작성일: 2026-07-25. 대상: `apps/backend`(jobs 매칭 파이프라인·AI 어댑터) + `apps/web`(매칭률 표시).
관련: [채용공고 API 연동 계획](채용공고-api-연동-계획.md)(정정: 원티드 오픈 API 존재), [IA.md](IA.md) §3.4·§4.5.

## 1. 목표

조건에 맞는 채용공고를 외부 API에서 가져와 **마스터 프로필과 대조**, **매칭률(%) + 매칭 근거("왜 매칭")**
를 산출한다. **API 키가 준비되는 순간 코드 수정 없이 실작동**(포트-어댑터 + 키 게이팅). 지금은 목으로 즉시 작동.

## 2. 아키텍처 (포트-어댑터, "키 준비되면 바로")

```
JobSource(사람인·잡코리아·원티드) ── 조건으로 공고 N개 fetch
        ↓
Embedder(Voyage)  프로필 경험·스택 ↔ 각 공고 JD → 코사인 → 전체 매칭률 랭킹
        ↓  상위 K개만
Llm(Claude)       프로필+공고 → 매칭률 보정 + 근거 서술
        ↓
매칭률순 정렬 반환
```

- **JobSource 포트**: 사람인·잡코리아·원티드 어댑터 + 목. 키 있는 소스만 활성(결과 집계), 없으면 목.
  - 원티드 오픈 API(`https://openapi.wanted.jobs/`): API 키 인증, Jobs 조회를 연차·스킬·직군·직무로 필터.
  - 사람인 공식 무료 키, 잡코리아 제휴 키.
- **Embedder 포트**: Voyage(`voyage-3`, 한국어) + 목(결정적 pseudo-vector). Anthropic엔 임베딩 없음.
- **Llm 포트**: Anthropic(Claude) + 목(템플릿 근거).
- **인메모리 코사인 — DB/pgvector 없음.** 요청마다 fetch한 N개 + 프로필을 임베딩해 코사인만 돈다.
  (pgvector 영구 백본은 대규모 코퍼스 검색용 — 이 기능엔 과함. 이후 확장.)

## 3. "키 준비되면 바로" 규칙 (핵심)

- 각 어댑터 **팩토리가 자기 env 키를 확인** → 있으면 실 어댑터, 없으면 목. **키를 넣는 순간** 그 부분이 실작동.
  - `SARAMIN_API_KEY` / `JOBKOREA_API_KEY` / `WANTED_API_KEY` / `VOYAGE_API_KEY` / `ANTHROPIC_API_KEY`.
- **목은 실 SDK를 모듈 로드 시 import하지 않는다**(실 어댑터 안에서 lazy import) → 키·네트워크 없이 CI·테스트 통과.
- 매칭률·근거는 목이어도 그럴듯하게 나오게(결정적) — 지금 화면이 실제로 돎.

## 4. 백엔드 (`apps/backend/app/`)

- **공유 AI (IA §3.4 백본의 씨앗)**: `app/ai/embedder.py`(Embedder 포트 + Voyage/목), `app/ai/llm.py`(Llm 포트 +
  Anthropic/목), 각 팩토리는 env 키로 실/목 선택. 이후 activities·essays·companies가 재사용.
- **소스**: `app/jobs/sources/`(base 포트 + `saramin.py`·`jobkorea.py`·`wanted.py`·`mock.py`) + 셀렉터(키 있는 소스 집계).
- **파이프라인**: `app/jobs/service.py`가 오케스트레이션 — 마스터 프로필(입력)로 조건 구성 → fetch → 임베딩
  랭킹 → 상위 K개 LLM 매칭률·근거 → 매칭률순. 프로필은 profile repository에서 읽는다.
- **schemas**: `Job`에 `match_rate: int`(0~100) 추가(`match_reason` 유지). `JobFeed` 유지.
- **config**: `app/core/config.py` — env 키 읽기·활성 어댑터 판별(pydantic-settings).
- **의존성(uv add)**: `httpx`(실 API 호출), `anthropic`, `voyageai`(또는 httpx로 Voyage). 실 어댑터에서만 사용.
- **프로필 게이트 유지**: 프로필 미등록이면 공고 없음(기존 `Profile.registered` / 프론트 게이트).
- 계층 규칙 유지: `router`·`service`·`schemas`는 형태 유지, 바뀌는 건 데이터 접근(목→파이프라인).

## 5. 프론트 (`apps/web`)

- `Job`에 `match_rate` 반영(gen:api, 손수정 금지). `entities/job/ui/JobCard`에 **매칭률 표시**(뱃지 또는 바) +
  기존 `match_reason`. 정렬(매칭률순)은 백엔드가 하므로 FE 변경 최소. vitest는 매칭률 렌더만.

## 6. eval (포트폴리오 핵심 산출물)

- 작은 **오프라인 eval**: 라벨된 픽스처(프로필, 공고 몇 개, 관련/비관련)로 매칭 **랭킹 품질**(recall@k 또는
  관련 공고가 상위에 오는지) 측정. **목/픽스처 임베더로 키 없이 실행**. `apps/backend/tests/` 또는
  `scripts/eval_matching.py`. 작게 — 파이프라인이 "관련 공고를 위로 올리는가"를 못박는 수준.

## 7. 테스트

- **pytest**: 파이프라인(목 어댑터로 fetch→랭킹→근거 흐름), **키 게이팅**(키 없으면 목 선택·SDK import 없이 통과),
  `match_rate`·`match_reason` shape, 프로필 게이트, eval 스모크.
- **vitest**: JobCard 매칭률 표시.

## 8. 범위 밖 (노트)

- pgvector 영구 백본(대규모 코퍼스) — 이 기능엔 불필요, 이후 확장.
- 실 API 키·라이브 호출 검증 — 키 준비 시. 지금은 목·게이팅·인터페이스만.
- 매칭률 보정·재순위 튜닝, 캐시 — 이후.

## 9. 구현 순서 (planner가 노드·의존성·태스크 스펙으로 상세화)

backend(AI 어댑터·소스 어댑터·파이프라인·config·schemas·eval·pytest) → web(match_rate 표시) → qa.
하나의 워크트리 순차. QA 통과 → In Review → 확인 → 머지.
