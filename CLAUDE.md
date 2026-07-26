# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

지원서 통합 플랫폼 "one-form" — Turborepo + pnpm 모노레포. 앱은 세 개:

- `apps/landing` — 랜딩 페이지. Vite 정적 사이트(프레임워크 없음, `index.html` 하나). port 3000
- `apps/web` — 메인 프론트엔드. React 19 + Vite + TypeScript. port 3001
- `apps/backend` — 백엔드. FastAPI + uv (Python 3.11+). port 8000
- `packages/design-system` — 공유 디자인 시스템. React 컴포넌트 + CSS 토큰. 빌드 스텝 없이
  소스(TSX)를 소비 앱의 Vite가 직접 변환

## 필수 환경

- **Node 22 필수** (`.nvmrc`). 이 머신의 기본 Node는 21이라 Vite 8 계열 도구가 죽는다
  (`styleText` 미지원). 명령 실행 전 `nvm use` 또는
  `export PATH=~/.nvm/versions/node/v22.22.2/bin:$PATH`.
- Python 의존성은 pip이 아니라 **uv**로 관리 (`apps/api`에서 `uv sync`).

## 명령어

루트에서:

```bash
pnpm install          # JS 의존성 (landing, web)
pnpm dev              # 세 앱 동시 실행 (turbo run dev)
pnpm build            # landing + web 빌드 (backend는 build 스크립트 없음 — 정상)
pnpm lint             # web은 oxlint 사용
pnpm turbo dev --filter=@one-form/web   # 특정 앱만
```

`apps/backend`에서:

```bash
uv sync               # venv 생성 + 의존성 설치
uv add <pkg>          # 의존성 추가 (pyproject.toml 갱신)
pnpm dev              # uv run uvicorn app.main:app --reload --port 8000
```

## 테스트

- **백엔드(pytest):** `pnpm --filter @one-form/backend test` (또는 `apps/backend`에서 `uv run pytest`).
  `apps/backend/tests/` — jobs 필터·페이지네이션 로직 + 전 엔드포인트 스모크. `conftest.py`가
  `MOCK_DELAY_SECONDS=0`으로 목 sleep을 없애 밀리초로 돈다. 로직·계약(응답 shape)만 검증하고
  순수 목 값은 얕게(200 + 최소 필드)만.
- **프론트(vitest + jsdom):** `pnpm --filter @one-form/web test`. 로직 있는 컴포넌트만
  (`JobsPage.test.tsx`: 필터 변경 → 요청 파라미터·page 리셋). 순수 표시용 컴포넌트는 테스트 안 함.
- **CI:** `.github/workflows/ci.yml` — web(lint·build·test)/backend(pytest)/contract(OpenAPI→TS 드리프트).
- FE↔BE 계약은 테스트가 아니라 OpenAPI→TS 타입 생성으로 컴파일러가 강제(아래 참조). E2E(Playwright)는
  아직 없음(docs/TODO.md).

## 커밋 규칙

- 형식: `type(scope): 제목` (Conventional Commits)
  - type: `feat` `fix` `refactor` `docs` `chore`
  - scope: `landing` `web` `backend`, 루트/공통 설정은 `repo`
- 제목은 한국어 명령형, 50자 이내 (예: `feat(web): 지원서 목록 페이지 추가`)
- 성격이 다른 변경은 커밋을 분리할 것 (여러 앱을 건드려도 목적이 하나면 한 커밋)

## web 코딩 규칙

### FSD (Feature-Sliced Design) 구조

- 레이어: `app → pages → widgets → features → entities → shared` (아래로만 의존).
  - `app` — 진입점·라우팅·프로바이더·전역 스타일 (`app/App.tsx`, `app/providers`, `app/styles`)
  - `pages/<page>/ui/<Page>.tsx` — feature·entity를 조합만. 페이지는 얇게.
  - `widgets/<widget>` — 복합 UI 블록 (`widgets/header`: Header + TabBar)
  - `features/<action>` — 사용자 액션 (`analyze-company`·`generate-draft`·`upload-resume`·`convert-form`).
    `model`(mutation 훅)과 `ui`로 나눈다.
  - `entities/<entity>` — 도메인 (`job`·`profile`·`essay`·`activity`). `model`(타입)·`api`(queryOptions)·`ui`(카드).
  - `shared` — 도메인 무관 (`shared/api` 클라이언트, `shared/ui`: Icon·Loading·AsyncBoundary·Dropzone).
    아이콘 path는 `shared/ui/Icon` 한 곳. `@one-form/design-system`(Button·Card·Input)은 별개 외부 패키지.
- **슬라이스는 `index.ts`(public API)로만 노출**하고, 다른 슬라이스는 `@/<layer>/<slice>`로 임포트한다
  (`@` = `src`, vite·tsconfig alias). 내부 파일 직접 임포트 금지.
- **레이어 경계는 oxlint가 강제한다** (`.oxlintrc.json`의 `no-restricted-imports` overrides).
  상위 레이어를 임포트하면 lint 에러. 새 코드는 알맞은 레이어에 둘 것.

### 데이터·상태

- **데이터 페칭은 TanStack Query v5.** `useEffect`로 직접 fetch하지 말 것.
  - 조회(GET)는 `entities/<e>/api.ts`에 `queryOptions`로 정의하고 페이지에서 `useSuspenseQuery`로 소비
    (`data`가 항상 정의됨 — 로딩/에러 분기 불필요).
  - 변경(POST)은 `features/<action>/model.ts`에 `useMutation` 훅으로 (`isPending`/`data`/`variables`로 상태 표현).
  - 로딩·에러는 페이지가 아니라 `shared/ui/AsyncBoundary`(Suspense + ErrorBoundary)가 담당.
    App의 각 라우트가 이걸로 감싸져 있다.
- `useEffect`는 가급적 지양. 파생 상태는 렌더 중 계산, 서버 상태는 Query에 위임.
- props는 인터페이스가 바로 읽히게. 깊은 props drilling·다수 props 나열 금지.
- 한 컴포넌트 최대 ~500줄. 넘으면 분리.

## 아키텍처에서 비자명한 부분

- **backend는 Python 앱이지만 turbo 그래프에 포함된다.** `apps/backend/package.json`의
  dev/start 스크립트가 `uv run uvicorn`을 감싸는 셔틀이라 `pnpm dev` 하나로 세 앱이 뜬다.
- **API 경로는 FastAPI 안에서부터 `/api` 프리픽스를 갖는다** (예: `/api/health`).
  web의 Vite dev 서버가 `/api/*`를 경로 재작성 없이 8000번으로 프록시하기 때문
  (`apps/web/vite.config.ts`). 새 엔드포인트도 `/api/...`로 만들 것.
- **백엔드는 도메인별 레이어 구조다.** `app/<도메인>/`(jobs·profile·companies·essays·
  activities·notifications·forms)마다 `router`(HTTP)·`repository`(데이터 접근)로 나뉘고,
  POST 바디가 있으면 `schemas`(Pydantic), 로직이 있으면 `service`가 붙는다(현재 jobs만 —
  필터·페이지네이션). `main.py`는 CORS + `include_router`만. 도메인 추가 시 이 4파일 패턴을 따를 것.
- **백엔드는 목(mock) 단계다.** 데이터 접근이 `app/core/mock.py`의 `mock()` 헬퍼로 1초 지연 후
  더미를 반환한다 (DB 없음). 실제 구현 시 각 `repository`의 `mock()` 호출을 진짜 쿼리로 바꾸면
  된다 (router·service·schemas는 그대로). 페이지↔API 매핑과 IA는 `docs/IA.md` 참고.
- **FE↔BE 타입은 백엔드가 단일 소스다.** 백엔드 Pydantic(`app/<도메인>/schemas.py`)이 원본이고,
  프론트 타입은 여기서 생성된다: `gen_openapi.py`가 OpenAPI를 덤프 → `openapi-typescript`가
  `apps/web/src/shared/api/schema.ts`로 변환 → `entities/*/model.ts`가 `components['schemas'][...]`를
  재-export. **프론트에 타입을 손으로 쓰지 말 것.** 새 응답 타입이 필요하면 백엔드 라우터에
  `response_model=`을 지정하고 `pnpm gen:api`(루트)로 재생성. 필드명이 어긋나면 프론트가 컴파일
  에러로 죽는다. `openapi.json`은 중간물(gitignore), `schema.ts`는 커밋(체크아웃 즉시 타입체크되게).
  → 도메인당 `schemas.py` 클래스명은 전역 유일해야 한다(OpenAPI 스키마명 충돌 방지, 예: 프로필의
  `ProfileActivity` vs activities의 `Activity`).
- **포트는 CORS와 결합돼 있다.** `apps/backend/app/main.py`의 CORS 허용 목록이
  localhost:3000(landing)/3001(web)로 고정. 포트를 바꾸면 양쪽을 같이 바꿔야 한다.
- **design-system 임포트는 두 갈래다.** 컴포넌트는 `import { Button } from '@one-form/design-system'`,
  전역 스타일은 앱 진입점에서 `import '@one-form/design-system/index.css'` 1회 (컴포넌트가
  CSS를 자동 로드하지 않는다 — 클래스만 붙인다). 토큰 `--of-`, 클래스 `.of-` 프리픽스,
  랜딩의 디자인 값이 원본. 새 컴포넌트는 `src/<이름>.tsx` 추가 + `src/index.ts`에서 export,
  스타일 클래스는 `index.css`에 추가.
  → **design-system에 컴포넌트를 추가하면 같은 역할의 기존 앱 로컬 UI도 그때 함께 교체한다.**
  (예: jobs 필터의 `FilterSelect`·수제 페이지네이션 → `Dropdown`·`Pagination`으로 교체·삭제)
- `apps/landing/index.html`은 Claude 디자인(`지원서 통합 플랫폼 랜딩.dc.html`)을
  정적으로 펼친 결과물. 원본 dc.html은 `support.js` 런타임 의존이라 그대로 못 쓰고,
  `<sc-for>` 루프를 데이터로 전개해 변환했다. 랜딩은 빌드 파이프라인 없는 단일 HTML 유지.
