# 이력서 빌더 — 설계 스펙

**날짜:** 2026-08-19
**상태:** 승인됨 (brainstorming) → 구현 계획 대기

## 1. 목표

챗으로 AI에게 명령해 **이력서를 이쁜 PDF로** 만들고, 처음 생성 이후에는
**챗으로 내용·스타일을 실시간으로 바꾸는** 페이지. 왼쪽=자료·템플릿 시작점,
가운데=라이브 미리보기, 오른쪽=AI 챗.

## 2. 확정된 결정 (brainstorming)

| 항목 | 결정 | 이유 |
| --- | --- | --- |
| 자료 소스 | **마스터 프로필 시드 + 자료 추가** | 이미 구조화된 이력서 데이터 재사용, 중복입력 제거 |
| PDF 생성 | **서버 HTML/CSS → PDF (weasyprint)** | 결정적·일관 출력, 템플릿=HTML/CSS, 로컬 렌더(키 불필요) |
| 저장 | **임시(세션) — DB 없음** | MVP, 빌더 자체에 집중 |
| 1차 범위 | **이력서만** (포트폴리오는 phase 2) | 리스크·플랜 축소 |
| 스타일 변경 | **챗으로 스타일도 변경** — 단, 자유 CSS가 아니라 **바운드된 토큰 노브** | 항상 유효·안 깨짐 |
| 편집 방식 | **AI가 구조·스타일을 알아서 편집** (텍스트 직접 타이핑은 보조) | — |

## 3. 핵심 원리

**PDF는 편집하지 않는다. 구조화 데이터를 편집하고 PDF는 매번 재생성한다.**

```
weasyprint( 템플릿 + doc + style ) = PDF
```

- `doc` = 내용(텍스트·순서·포함여부) — 내용 명령이 바꿈
- `style` = 스타일 토큰 묶음 — 스타일 명령이 바꿈
- 챗 turn = `{state, message}` → LLM이 맞는 쪽을 수정한 `state` 반환 → 미리보기·PDF 재생성

내용이든 스타일이든 흐름은 하나: **챗 → 구조화 데이터 수정 → 재생성.**

## 4. 데이터 모델

### 4.1 `ResumeState`

```
ResumeState = { doc: ResumeDoc, style: ResumeStyle }
```
저장 없음 — 프론트 페이지 상태에만 존재. 챗/프리뷰/렌더 엔드포인트는 상태를
통째로 주고받는 **stateless** 방식(문서가 1~2p라 작음).

### 4.2 `ResumeDoc` (내용)

```
ResumeDoc = {
  header:   { name, contact: [str], links: [{label, url}] },
  summary:  str,                         # 자기소개 한 단락 — 챗의 핵심 산출물
  sections: [ { id, type, title, order, visible, items: [ ... ] } ],
}
```
- `type` ∈ career·project·education·skill·award·certificate·language·activity·custom
- `order`·`visible` 로 "학력을 위로", "이 섹션 빼줘" 를 구조로 표현
- 시드가 header/sections를 채우고 `summary`는 비어 시작(챗이 생성)

### 4.3 `ResumeStyle` (스타일 — 바운드된 노브)

```
ResumeStyle = {
  template:      str,     # 베이스 스켈레톤 id (classic·modern …)
  font:          str,     # 허용 폰트 목록 중
  accent_color:  str,     # hex
  density:       str,     # compact | normal | relaxed
  heading_style: str,     # plain | bar | underline
  layout:        str,     # single | two-column
  font_scale:    str,     # S | M | L
}
```
**챗은 이 노브 값만 바꾼다** — 임의 CSS를 생성하지 않는다. 어떤 조합이든 항상
예쁘게 렌더됨. LLM이 *"더 모던하게"* → (모던 폰트 + 촘촘 density + 얇은 heading)
처럼 노브로 번역. 값은 서버에서 스키마로 검증(허용값만 통과).

## 5. 아키텍처 — 3-컬럼 UX

```
┌───────────────┬─────────────────────┬───────────────┐
│ 왼쪽: 자료·시작 │ 가운데: 라이브 미리보기 │ 오른쪽: AI 챗   │
│ ▸ 프로필 시드   │  [선택 템플릿+style로   │ 내용·스타일 명령 │
│   (섹션 토글)   │   렌더된 이력서 HTML —  │ ─────────────  │
│ ▸ 자료 추가     │   PDF와 동일 스타일]    │ 대화 로그       │
│   파일·메모·링크 │  [📄 PDF 내려받기]     │ > 입력창        │
│ ▸ 템플릿(프리셋) │                       │               │
└───────────────┴─────────────────────┴───────────────┘
```
- **왼쪽 = 출발점**: 프로필 시드 토글, 자료 추가, 템플릿 프리셋(=style 토큰 시작 묶음) 선택
- **가운데 = 라이브**: state가 바뀔 때마다 백엔드 preview(HTML) 재렌더. 미리보기와 PDF가
  **같은 템플릿 공유** → 스타일 원천 하나
- **오른쪽 = 챗**: 내용·스타일 명령. state가 갱신되면 미리보기 즉시 갱신

**"실시간"의 현실:** 각 명령은 LLM 1회(1~3초)로 명령→구조화 수정을 만들고, 이후
미리보기는 즉시 재렌더. 스트리밍 타이핑 반영은 아님.

## 6. 백엔드 — 새 `app/resume/` 도메인

4파일 패턴 + 템플릿 디렉터리. **repository 없음**(저장 안 함).

| 파일 | 역할 |
| --- | --- |
| `router.py` | 엔드포인트 |
| `schemas.py` | `ResumeDoc`·`ResumeStyle`·`ResumeState` + 요청/응답 (OpenAPI→TS로 프론트 타입 생성) |
| `service.py` | 시드(프로필→doc), 챗(LLM 편집), 템플릿 채우기, weasyprint 렌더 |
| `templates/` | 베이스 이력서 HTML/CSS (Jinja2) + 프리셋 정의 |

### 엔드포인트 (모두 `/api/resume`)

| 메서드·경로 | 입력 | 출력 |
| --- | --- | --- |
| `GET  /templates` | — | `[{id, name, thumbnail, preset: ResumeStyle}]` |
| `POST /seed` | — | `ResumeState` (프로필→doc + 기본 style) |
| `POST /materials/extract` | 업로드 파일(multipart) | `{text}` (**기존 `core/pdf.py` 재사용**) |
| `POST /chat` | `{state, materials, message}` | `{state, reply}` |
| `POST /preview` | `{state}` | `text/html` (가운데 미리보기) |
| `POST /render` | `{state}` | `application/pdf` (다운로드) |

`materials` = 왼쪽에서 추가한 자료를 **LLM 컨텍스트용 텍스트**로 모은 것 —
`[{kind: file|note|link, label, text}]`. state의 출력이 아니라 챗에 주는 참고 입력이라
`ResumeState`에 넣지 않는다(저장 없음). 파일은 `/materials/extract`로 텍스트화해 이 목록에 담김.

### LLM 확장

`app/ai/llm.py`의 기존 `complete_json(prompt, schema)`를 재사용:
- service가 `{현재 state + 자료 + 명령}`으로 프롬프트를 만들고 `complete_json(prompt, RESUME_STATE_SCHEMA)` 호출
- 반환 dict를 Pydantic `ResumeState`로 **검증** → 유효하면 교체, 무효/빈dict면 이전 state 유지 + reply "다시 시도"
- **MockLlm**: `complete_json`이 `{}` 반환(사실 날조 안 함) → 챗은 무변경 + 안내 reply.
  키 없이도 **시드·템플릿·미리보기·PDF는 전부 동작**(weasyprint 로컬). 챗 다듬기만 키 필요.
  - *(선택)* 뻔한 스타일 키워드("글자 크게" 등) 소수는 목에서 결정적으로 처리 — phase 2 표시.

### 템플릿 = 파라메트릭

베이스 HTML(Jinja) 하나당 `doc`를 순회 렌더하고, CSS는 `style` 토큰을 Jinja로 **인라인
보간**(예: `color: {{ style.accent_color }}`) — weasyprint CSS 변수 지원 여부와 무관하게 확실.
MVP 베이스 템플릿 **2종**(classic·modern), 각각 프리셋 제공. 추가는 파일 얹고 목록 등록.

### 새 의존성

- **weasyprint** (백엔드 `pyproject.toml`). `pypdf`(업로드 추출)는 이미 있음.
- weasyprint 네이티브 의존: pango·cairo·gdk-pixbuf → **개발/CI에 설치 필요**
  (mac: `brew install pango`, CI: apt). 한글 폰트(Pretendard 등)를 번들·임베드.

## 7. 프론트 — FSD

| 슬라이스 | 내용 |
| --- | --- |
| `pages/resume-builder/` | 3-컬럼 조립(얇게), `ResumeState` 페이지 상태 보유 |
| `features/resume-chat/` | `model`(챗 useMutation: message→state 교체) + `ui`(챗 패널) |
| `features/resume-materials/` | 자료 추가(업로드·메모·링크) + 템플릿 프리셋 선택. **`shared/ui/Dropzone` 재사용** |
| `entities/resume/` | `model`(schema.ts에서 타입 재-export) + `api`(templates queryOptions) |

- 라우트 `/resume` 추가 + **TabBar에 "이력서 빌더" 탭**
- 미리보기: 백엔드 preview HTML을 iframe/컨테이너에 표시. state 바뀔 때만 재렌더(타이핑마다 아님)
- 상태: `ResumeState`는 페이지 React 상태(저장 없음). 챗 mutation이 새 state 반환 → setState → 미리보기 갱신

## 8. 에러 처리

- LLM 무효/빈 출력 → 이전 state 유지 + "다시 시도" reply (PDF 안 망침)
- 파일 추출 → `core/pdf.py` 한도(크기·페이지) 재사용. 비-PDF 텍스트는 텍스트로, 미지원 형식은 에러 메시지
- weasyprint 렌더 실패 → 500 + 메시지, 프론트 토스트
- 프로필 미등록 → seed가 빈 최소 doc 반환(자료만으로도 시작 가능)

## 9. 테스트

- **백엔드(pytest):** seed(프로필→doc 매핑), render(weasyprint 산출물이 `%PDF`로 시작·비어있지 않음),
  chat(목이면 state 불변 + reply), 스키마 검증(잘못된 LLM 출력 거부), 엔드포인트 스모크(200+shape)
- **프론트(vitest):** `resume-chat` model(메시지 전송 → 반환 state 반영). 순수 표시용은 테스트 안 함
- **계약:** `ResumeState` 등은 백엔드 Pydantic이 원천 → `pnpm gen:api`로 프론트 타입 생성

## 10. YAGNI — phase 2

- 포트폴리오(프로젝트 쇼케이스·이미지) — 이력서 빌더 완성 후 템플릿 종류로 확장
- DB 저장·문서 여러 개·버전
- 링크 자동 크롤링(MVP는 링크를 참고 텍스트로만)
- 수동 리치 편집기(드래그 정렬 UI) — MVP는 챗+토글
- doc 패치(diff) 방식 — MVP는 챗이 전체 state 반환(작음). 커지면 패치
- 스타일 명령 결정적 파서(LLM 우회 즉시 반영)

## 11. 재사용 vs 신규

- **재사용:** 마스터 프로필 데이터(시드), `core/pdf.py`(업로드 추출), `ai/llm.py`(complete_json + 키 게이팅),
  `shared/ui/Dropzone`, 디자인 시스템, OpenAPI→TS 타입 생성
- **신규:** `app/resume/` 도메인 + 템플릿, `pages/resume-builder`·`features/resume-*`·`entities/resume`,
  weasyprint 의존성
