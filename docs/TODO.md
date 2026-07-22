# 구현 백로그

아직 안 했지만 해야 할 것들. 완료 시 이 목록에서 지우고 필요하면 CLAUDE.md/IA.md에 반영.

## CI / 품질

- [x] **CI 파이프라인** — `.github/workflows/ci.yml`: web(lint·build·test) / backend(pytest) / contract 3잡.
- [x] **OpenAPI 타입 드리프트 방지** — contract 잡이 `pnpm gen:api` 후
  `git diff --exit-code apps/web/src/shared/api/schema.ts`로 "스키마를 바꾸고 `gen:api`를 안 돌린" 커밋을 막는다.
- [x] **백엔드 테스트(pytest)** — `apps/backend/tests/`: jobs 필터·페이지네이션 + 전 엔드포인트 스모크.
  `conftest.py`에서 `MOCK_DELAY_SECONDS=0`으로 sleep 제거. `pnpm --filter @one-form/backend test`.
- [x] **프론트 테스트(vitest)** — `JobsPage.test.tsx`: 필터 변경 시 role 인코딩 + page=1 리셋 검증.
  `pnpm --filter @one-form/web test`.
- [ ] **E2E 스모크 1개(Playwright)** — 앱 로드 → 탭 이동 → 데이터 렌더. 프록시·라우팅·쿼리 배선 통합 검증.
  (아직: 브라우저 바이너리·양 서버 기동이 무겁고, 목 단계에선 통합 테스트가 API를 이미 커버 —
  실배포 직전에 추가.)
