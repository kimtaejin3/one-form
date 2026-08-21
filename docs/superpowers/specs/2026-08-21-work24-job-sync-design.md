# 고용24 채용공고 동기화 설계

## 목적

one-form의 목 채용공고를 고용24의 실제 IT·소프트웨어 채용공고로 보강한다. 고용24 장애나 지연이 사용자 요청에 전파되지 않도록 하루 한 번 DB에 동기화하고, 기존 프로필 매칭·필터·상세 흐름은 그대로 사용한다.

## 선행 조건

1. 고용24 기업회원 가입
2. 채용정보 Open API 이용 신청과 승인
3. 인증키 발급
4. IT·소프트웨어 직종코드 확정
5. 실제 목록·상세 XML을 비식별 fixture로 저장해 문서와 실응답의 차이 확인

고용24 Open API는 기업회원 전용이며 인증키 심사를 거친다. 목록은 페이지당 최대 100건의 XML을 반환한다.

- 소개·신청: <https://www.work24.go.kr/cm/e/a/0110/selectOpenApiIntro.do>
- 목록 API: <https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L01.do>
- 상세 API: <https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210D01.do>

## 범위

### 포함

- 전국 IT·소프트웨어 직종 공고 목록 수집
- 신규·수정 공고의 상세 조회
- 고용24 공고 DB upsert
- 사라지거나 마감된 공고 비활성화
- 비활성 공고 30일 보관 후 삭제
- 기존 채용공고 추천·필터·상세 API에서 활성 공고 사용
- 상세 화면의 고용24 출처 문구와 원문 링크
- 외부 cron이 호출할 동기화 CLI

### 제외

- 요청 시 고용24 실시간 조회
- Celery, Redis, APScheduler 같은 스케줄러 인프라
- 동기화 관리자 화면과 이력 테이블
- 공고 내용을 LLM으로 재분류하는 처리
- 모든 직종 수집
- 고용24 지원서 제출
- 사업자등록번호와 채용 담당자 연락처 저장

## 구조

```text
외부 cron: 하루 1회
  → Work24 동기화 CLI
  → 목록 API 전체 조회(IT 직종)
  → 신규·수정 공고만 상세 API 조회
  → job 테이블 upsert
  → 이번 동기화에서 사라진 공고 비활성화
  → 30일 지난 비활성 공고 삭제
  → 기존 jobs service가 활성 DB 공고로 추천·필터·상세 제공
```

기존 `app.jobs.sources` 구조와 `jobs` 도메인을 재사용한다.

- `jobs/sources/work24.py`: HTTP 호출, XML 파싱, 고용24 응답 정규화
- `jobs/sync.py`: 페이지 순회, 변경 판정, 상세 조회, 저장 조율, CLI 진입점
- `jobs/repository.py`: source 기준 조회, upsert, 비활성화, 30일 삭제
- 기존 `jobs/service.py`: 활성 공고 조회 후 프로필 매칭. 외부 API를 직접 호출하지 않는다.

동기화는 `python -m app.jobs.sync` 한 명령으로 실행한다. 배포 환경의 cron이 이 명령을 하루 한 번 호출한다.

## 설정

- `WORK24_API_KEY`: 승인받은 인증키
- `WORK24_OCCUPATION_CODES`: 고용24 IT 직종코드를 `|`로 연결한 값

두 설정이 없으면 동기화 CLI는 명확한 오류로 종료한다. 웹 앱 기동과 기존 목 데이터 사용은 막지 않는다.

## 데이터 모델

기존 `job.id` 정수 기본키는 one-form 내부 상세 URL용으로 유지한다. 다음 컬럼을 추가한다.

| 컬럼 | 타입/제약 | 용도 |
|---|---|---|
| `source_id` | Text, nullable | 고용24 `wantedAuthNo`; 기존 목 데이터는 null |
| `source_url` | Text, nullable | 고용24 원문 상세 링크 |
| `source_updated_at` | DateTime, nullable | 고용24 `smodifyDtm` 변경 판정 |
| `posted_at` | Date, nullable | 등록일 |
| `closes_at` | Date, nullable | 마감일; 채용시까지는 null |
| `active` | Boolean, not null, default true | 피드·상세 노출 여부 |
| `last_seen_at` | DateTime, nullable | 마지막 정상 동기화에서 발견한 시각 |

`(source, source_id)`에 unique 제약을 둔다. 기존 목 데이터는 `source_id=null`, `active=true`로 마이그레이션한다.

## 고용24 필드 매핑

| 고용24 | one-form |
|---|---|
| `wantedAuthNo` | `source_id` |
| `corpNm` | `company` |
| `homePg` | `domain` |
| `wantedTitle` | `title` |
| `jobsCd`, `jobsNm` | `role_category`, `tags` |
| `enterTpNm` | `experience` |
| `empTpNm` | `employment` |
| `workRegion` | `location` |
| `jobCont` | `description`, 비어 있지 않은 줄을 `responsibilities`로 사용 |
| `eduNm`, `certificate` | `requirements` |
| `pfCond`, `etcPfCond`, `compAbl` | `preferred` |
| `keywordList` | `tags` |
| `busiCont` | `company_info` |
| `regDt`, `receiptCloseDt` | `posted_at`, `closes_at`, `dday` |
| 공식 상세 URL | `source_url` |

`jobsCd`는 승인 후 받은 공식 공통코드 목록을 기준으로 one-form의 기존 `role_category` 값에 명시적으로 매핑한다. CLI 시작 시 설정된 모든 직종코드에 매핑이 있는지 검사하고, 응답에 매핑되지 않은 `jobsCd`가 있으면 동기화를 실패 처리한다. 임의의 `기타` 분류는 만들지 않는다.

`match_reason`은 동기화 단계에서 만들지 않는다. 기존 매칭 서비스가 프로필과 공고를 비교해 채운다.

## 동기화 알고리즘

1. 목록 API를 `display=100`, 최신순, 전국 IT 직종코드로 마지막 페이지까지 조회한다.
2. 목록의 `wantedAuthNo`와 `smodifyDtm`을 기존 DB와 비교한다.
3. 신규이거나 `smodifyDtm`이 달라진 공고만 상세 API를 조회한다.
4. 상세 조회는 `asyncio.Semaphore(5)`로 동시성을 제한한다.
5. 모든 목록·상세 조회와 XML 검증이 끝난 뒤 한 DB 트랜잭션으로 신규·수정 공고를 upsert하고 확인된 공고의 `last_seen_at`을 갱신한다.
6. 동기화를 완주했을 때만 이번 실행에서 확인되지 않은 기존 고용24 공고를 `active=false`로 바꾼다.
7. `active=false`이고 `last_seen_at`이 30일보다 오래된 고용24 공고를 삭제한다.

마감일이 지난 공고는 목록 존재 여부와 관계없이 비활성화한다. `closes_at=null`인 채용시까지 공고는 목록에서 사라질 때 비활성화한다.

## 오류 처리

- 네트워크 타임아웃, 비정상 HTTP 상태, API 오류 응답, 잘못된 XML, 필수 식별자 누락 중 하나라도 발생하면 CLI는 0이 아닌 코드로 종료한다.
- 실패한 실행에서는 기존 공고를 비활성화하거나 삭제하지 않는다.
- 웹 앱은 마지막으로 성공한 DB 스냅샷을 계속 제공한다.
- 개별 XML 텍스트가 비어 있는 것은 빈 값으로 정규화하지만 `wantedAuthNo`, 회사명, 제목이 없으면 해당 실행을 실패 처리한다.
- 인증키는 서버 환경 변수에서만 읽고 로그·응답·프론트 번들에 포함하지 않는다.

## API와 UI 계약

기존 피드 응답은 유지한다. 상세 응답에 `source_url`을 추가하고, 고용24 공고일 때 다음 요소를 기존 상세 페이지 하단에만 표시한다.

- `고용24에서 원문 보기` 외부 링크
- `본 자료는 고용노동부 고용24(www.work24.go.kr)에서 제공된 정보이며, 무단복제 및 배포를 금지합니다.`

새 페이지, 관리자 카드, 동기화 상태 UI는 만들지 않는다.

## 테스트와 완료 기준

### 백엔드

- 비식별 목록 XML 파싱·정규화
- 비식별 상세 XML 파싱·정규화
- 신규·수정·미변경 공고 분기
- `(source, source_id)` upsert와 중복 방지
- IT 직종코드 요청 파라미터
- 상세 동시성 상한
- 완주한 동기화만 누락 공고 비활성화
- 마감 공고 비활성화
- 비활성 30일 후 삭제
- API·XML 오류 시 기존 공고 유지와 CLI 실패 코드
- 활성 공고만 기존 피드·상세에 노출

### 프론트

- 고용24 상세 공고의 원문 링크와 필수 출처 문구
- 다른 소스에는 고용24 출처 문구 미표시

### 통합

- 실제 승인 키로 목록 1페이지와 상세 1건을 수동 실행해 fixture와 필드 드리프트 확인
- 동기화 2회 실행 시 두 번째 실행에서 미변경 상세 재호출이 없음
- `pytest`, web test, lint, build, OpenAPI→TypeScript 생성 결과 통과

## 운영 순서

1. 기업회원 가입과 API 승인
2. 실제 XML 샘플 확보·비식별 fixture 작성
3. 스키마·마이그레이션과 XML 어댑터 구현
4. 저장소·동기화 CLI 구현
5. 기존 피드·상세 연결
6. 필수 출처 UI 추가
7. 수동 실키 검증
8. 배포 cron에 하루 한 번 CLI 등록
