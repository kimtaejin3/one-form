# 마스터 프로필 이력서 v3 설계

## 목표

현대적인 섹션형 PDF 이력서에서 사진(있을 때만), 기본 정보, 소개, 기술, 경력, 프로젝트,
오픈소스 기여, 외부 활동, 학력, 수상, 어학, 자격을 마스터 프로필로 구조화한다. 잘못된
`startxref` 때문에 일반 뷰어에서는 열리지만 `pypdf`가 거절하는 PDF도 안전한 범위에서 읽는다.

## 범위에서 제외

- 이미지형 PDF OCR
- 외부 LLM으로 이력서 원문 전송
- 업로드 마법사, 별도 모달, 빈 섹션 카드
- 임의 섹션을 저장하는 범용 key-value 구조

## PDF 입력

기존 10MB, 30페이지, PDF MIME 제한을 유지한다. `pypdf`가 읽지 못하고 마지막
`startxref`가 실제 마지막 classic xref 테이블이 아닌 객체를 가리킬 때만, 메모리상의 PDF
바이트에서 마지막 `xref` 위치로 포인터를 교정해 한 번 재시도한다. 원본 파일은 변경하지 않는다.
복구 후에도 읽히지 않으면 기존 422 오류를 반환한다.

텍스트와 사진은 같은 복구 바이트를 사용한다. 사진은 기존대로 선택값이며, 첫 페이지에 안전
한도 내 지원 이미지가 없으면 빈 문자열을 저장한다.

## 프로필 계약

기존 필드는 유지하고 다음만 추가한다.

- `Personal.headline: str`: 예) `Node.js 기반 풀스택 개발자`
- `Personal.summary: str`: 자기소개 본문
- `SkillGroup`: `category`, `skills[]`
- `OpenSourceContribution`: `repository`, `url`, `highlights[]`
- `Project.organization: str`: 경력 안의 프로젝트 소속 회사
- `Profile.skill_groups[]`
- `Profile.open_source_contributions[]`

`skill_groups`와 `open_source_contributions`는 profile 테이블의 JSONB 컬럼으로 추가한다.
`headline`, `summary`는 기존 personal JSONB 안에, `organization`은 기존 projects JSONB 안에
저장한다. 기존 데이터와 시드는 새 필드의 빈 기본값을 갖는다.

## v3 파서

v3는 v2 결과를 기반으로 하되 `소개`, `기술 스택`, `경력`, `프로젝트`, `오픈소스 기여`,
`외부 활동`, `학력 · 수상 · 자격` 제목으로 구간을 나눈다. 특정 개인 이름이나 회사명을
하드코딩하지 않는다.

- 첫 페이지 첫 줄에서 한글 이름과 영문 이름을 읽고 다음 비어 있지 않은 줄을 headline로 사용
- `github.com/...`처럼 scheme이 없는 링크는 `https://`로 정규화
- 기술 표의 카테고리와 쉼표 구분 기술을 `SkillGroup`으로 보존
- 회사 헤더의 회사, 역할, 기간과 하위 불릿을 `Career`로 저장
- 회사 내부의 이름 있는 작업과 독립 프로젝트를 `Project`로 저장하고 소속을 기록
- 저장소 헤더와 불릿을 `OpenSourceContribution`으로 저장
- 외부 활동, 학력, 수상, 어학, 자격은 기존 타입으로 저장
- 날짜 구분자 `~`, `–`, `-`와 `재직 중/재직중`을 허용

구조를 확실히 판별하지 못한 문장은 추측해 다른 필드로 넣지 않는다. 기존 사람인 형식은 v2
파서 테스트로 계속 보호한다.

## 화면

기존 마스터 프로필 화면과 편집 폼만 확장한다. headline과 summary는 개인정보 아래에,
기술 스택과 오픈소스 기여는 값이 있을 때만 각각 한 섹션으로 표시한다. 프로젝트에는 소속이
있을 때만 함께 표시한다. 새 탐색 UI, 카드 유형, 업로드 단계는 만들지 않는다.

## 검증

- 잘못된 `startxref` PDF의 복구 성공과 복구 불가능 PDF 거절
- 사진 있음/없음 및 기존 이미지 안전 한도
- 섹션형 이력서 fixture의 모든 프로필 필드 추출
- 기존 v1/v2 사람인 이력서 회귀
- DB migration과 seed 기본값
- OpenAPI 타입 재생성 후 프로필 조회·편집 화면 테스트
- 제공된 실제 PDF를 통한 수동 전체 항목 비교

