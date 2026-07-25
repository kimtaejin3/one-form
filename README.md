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

## AI 기능 로드맵

one-form의 핵심 기능은 대부분 AI로 구현된다. 지금은 **목(mock) 단계** — 백엔드가
더미를 반환하고, 임베딩·벡터DB·LLM 등 AI 인프라는 아직 없다. 아래는 각 기능을 실제로
어떤 기술로 구현·발전시킬지에 대한 방향이다. (기능↔페이지↔API 매핑은 [docs/IA.md](docs/IA.md) 참고.)

### 쓰는 기술은 사실상 4가지

| 기술 | 하는 일 | 비고 |
| --- | --- | --- |
| **텍스트 임베딩** | 프로필·공고·활동·JD를 같은 벡터 공간에 배치 | IA.md §3.4의 "공유 임베딩 백본". 여러 기능의 공통 기반 |
| **벡터 검색** | 유사도로 관련 문서·경험 검색 | Postgres + `pgvector`면 충분 (별도 벡터DB는 규모 커질 때) |
| **LLM** (예: Claude) | 자소서·브리핑 생성, 이력서 구조화 | 임베딩 검색 결과를 근거로 생성 = RAG |
| **문서 파싱** | PDF/DOCX 이력서 → 텍스트 | 이미지 이력서면 OCR 추가 |

임베딩+검색+LLM은 사실상 하나의 **RAG 파이프라인**이라 실질 덩어리는 ①RAG ②문서 파싱 둘.

### 기능별 적용

| 기능 (기획서) | 쓰는 기술 | 핵심 |
| --- | --- | --- |
| 채용공고 추천 (§4.5) | 임베딩 + 벡터 검색 | 프로필 ↔ 공고 유사도, 매칭 근거 표시 |
| 활동 추천 (§4.6) | 임베딩 + 벡터 검색 | 보유 ↔ 요구 역량 갭 기반 추천 |
| 자소서 초안 (§4.3) | RAG (검색 + LLM) | JD ↔ 내 경험 검색 → 문항별 초안 생성 |
| 기업 브리핑 (§4.4) | RAG (검색 + LLM) | 기업 문서 검색 → 브리프 생성, `Signal.source`에 인용 |
| 이력서 파싱 (§4.1) | 문서 파싱 + LLM | 이력서 → STAR 경험으로 구조화 |
| 양식 변환 (§4.2) | 임베딩 유사도 + LLM | 자사 양식 필드 ↔ 프로필 필드 매핑 |

### 발전 단계

목 → 실제 전환은 각 `repository`의 `mock()` 호출을 진짜 구현으로 바꾸는 것이지만,
아래는 전부 신규 구축 대상이다.

1. **LLM PoC** — RAG 없이 LLM만. 기업명·프로필 → 브리프/초안 생성. 인프라는 LLM
   클라이언트 하나. 기능·스키마·UX를 먼저 검증한다. (엄밀히는 RAG 아님)
2. **코퍼스 소스 결정** — RAG의 검색 대상(기업 사업/제품/IR, 채용공고 JD)을 어디서
   조달할지 정한다. **여기가 가장 큰 공백** — 검색할 문서가 없으면 RAG는 시작할 수 없다.
   ([docs/채용공고-api-연동-계획.md](docs/채용공고-api-연동-계획.md)가 채용공고 조달을 다룬다.)
3. **RAG 구축** — Postgres + pgvector, 임베딩 백본(`app/embeddings/` 공용 도메인),
   벡터 검색을 붙여 완성. 인용을 실제 출처로 채운다.

> RAG의 병목은 벡터DB 세팅이 아니라 **"무슨 문서를 검색할 것인가"**다. 코퍼스부터 정한다.

## 랜딩 페이지 디자인 적용

Claude 디자인에서 HTML 파일(`지원서 통합 플랫폼 랜딩.dc.html`)을 내려받아
`apps/landing/index.html`을 교체하면 됩니다.
