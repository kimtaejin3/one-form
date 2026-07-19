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

테스트는 아직 없다.

## 커밋 규칙

- 형식: `type(scope): 제목` (Conventional Commits)
  - type: `feat` `fix` `refactor` `docs` `chore`
  - scope: `landing` `web` `backend`, 루트/공통 설정은 `repo`
- 제목은 한국어 명령형, 50자 이내 (예: `feat(web): 지원서 목록 페이지 추가`)
- 성격이 다른 변경은 커밋을 분리할 것 (여러 앱을 건드려도 목적이 하나면 한 커밋)

## 아키텍처에서 비자명한 부분

- **backend는 Python 앱이지만 turbo 그래프에 포함된다.** `apps/backend/package.json`의
  dev/start 스크립트가 `uv run uvicorn`을 감싸는 셔틀이라 `pnpm dev` 하나로 세 앱이 뜬다.
- **API 경로는 FastAPI 안에서부터 `/api` 프리픽스를 갖는다** (예: `/api/health`).
  web의 Vite dev 서버가 `/api/*`를 경로 재작성 없이 8000번으로 프록시하기 때문
  (`apps/web/vite.config.ts`). 새 엔드포인트도 `/api/...`로 만들 것.
- **백엔드는 목(mock) 단계다.** 모든 엔드포인트가 `mock()` 헬퍼로 1초 지연 후 더미 데이터를
  반환한다 (DB 없음). 실제 구현 시 `mock()` 호출만 걷어내면 된다. 페이지↔API 매핑과 IA는
  `docs/IA.md` 참고.
- **포트는 CORS와 결합돼 있다.** `apps/backend/app/main.py`의 CORS 허용 목록이
  localhost:3000(landing)/3001(web)로 고정. 포트를 바꾸면 양쪽을 같이 바꿔야 한다.
- **design-system 임포트는 두 갈래다.** 컴포넌트는 `import { Button } from '@one-form/design-system'`,
  전역 스타일은 앱 진입점에서 `import '@one-form/design-system/index.css'` 1회 (컴포넌트가
  CSS를 자동 로드하지 않는다 — 클래스만 붙인다). 토큰 `--of-`, 클래스 `.of-` 프리픽스,
  랜딩의 디자인 값이 원본. 새 컴포넌트는 `src/<이름>.tsx` 추가 + `src/index.ts`에서 export,
  스타일 클래스는 `index.css`에 추가.
- `apps/landing/index.html`은 Claude 디자인(`지원서 통합 플랫폼 랜딩.dc.html`)을
  정적으로 펼친 결과물. 원본 dc.html은 `support.js` 런타임 의존이라 그대로 못 쓰고,
  `<sc-for>` 루프를 데이터로 전개해 변환했다. 랜딩은 빌드 파이프라인 없는 단일 HTML 유지.
