# one-form

지원서 통합 플랫폼 — Turborepo + pnpm 모노레포.

## 구조

```
apps/
├── landing/   # 랜딩 페이지 (Vite 정적 사이트, port 3000)
├── web/       # 프론트엔드 (React + Vite + TypeScript, port 3001)
└── backend/   # 백엔드 (FastAPI + uv, port 8000)
```

## 요구 사항

- Node 22 (`nvm use` — `.nvmrc` 참고)
- pnpm 9+
- [uv](https://docs.astral.sh/uv/) (Python 패키지 매니저)

## 시작하기

```bash
nvm use
pnpm install                 # JS 의존성 (landing, web)
cd apps/backend && uv sync && cd ../..   # Python 의존성 (backend)

pnpm dev                     # 세 앱 동시 실행
```

- 랜딩: http://localhost:3000
- 웹앱: http://localhost:3001 (`/api/*` 요청은 8000번 FastAPI로 프록시됨)
- API: http://localhost:8000 (문서: http://localhost:8000/docs)

## 명령어

| 명령 | 설명 |
| --- | --- |
| `pnpm dev` | 모든 앱 dev 서버 실행 (turbo) |
| `pnpm build` | landing + web 프로덕션 빌드 |
| `pnpm lint` | lint 실행 |

특정 앱만 실행하려면: `pnpm turbo dev --filter=@one-form/web`

## 랜딩 페이지 디자인 적용

Claude 디자인에서 HTML 파일(`지원서 통합 플랫폼 랜딩.dc.html`)을 내려받아
`apps/landing/index.html`을 교체하면 됩니다.
