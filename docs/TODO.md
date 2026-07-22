# 구현 백로그

아직 안 했지만 해야 할 것들. 완료 시 이 목록에서 지우고 필요하면 CLAUDE.md/IA.md에 반영.

## CI / 품질

- [ ] **OpenAPI 타입 드리프트 방지** — CI에 아래를 넣어 "백엔드 스키마를 바꾸고 `gen:api`를 안 돌린" 커밋을 막는다.
  ```bash
  pnpm gen:api && git diff --exit-code apps/web/src/shared/api/schema.ts
  ```
  스키마가 재생성됐는데 커밋된 `schema.ts`와 다르면 diff가 비-0 종료 → CI 실패.
- [ ] **백엔드 테스트(pytest)** — `uv add --dev pytest httpx` 후 jobs 필터·페이지네이션(유일한 로직)과
  전 엔드포인트 스모크(200 + 최소 shape). `conftest.py`에서 `MOCK_DELAY_SECONDS=0`으로 sleep 제거.
- [ ] **프론트 테스트(vitest)** — 로직 있는 컴포넌트만(필터·페이지네이션·파생 상태). 순수 표시용은 skip.
- [ ] **E2E 스모크 1개(Playwright)** — 앱 로드 → 탭 이동 → 데이터 렌더. 프록시·라우팅·쿼리 배선 통합 검증.

## AI 백본 (핵심 차별점)

- [ ] **임베딩 백본** — 경험↔공고 임베딩 시맨틱 매칭 1개 vertical부터 실제 구현.
  Voyage/OpenAI 임베딩 + pgvector + 인제스트 스크립트 + 검색 쿼리 2개. `jobs/repository.py`의
  `mock()`을 벡터 검색으로 교체, `app/embeddings/`를 공용 도메인으로 신설.
- [ ] **작은 eval** — 라벨링한 "나에게 맞는 공고 N개"에 대해 recall@10 측정, rerank 전후 비교.
- [ ] 기업 분석 RAG(인용 기반), 자소서 초안 생성 — 백본 위에 순차 확장.
