# 채용공고 API 연동 계획

목 데이터로 채우던 채용공고를 **외부 채용 API 연동 + 마스터 프로필 기반 추천**으로 전환하는 계획.

## 핵심 흐름

```
마스터 프로필 등록 (이력서 업로드 → 파싱)
        │
        ▼
채용 API 조회 (내 스택·직무를 질의)
        │
        ▼
프로필 ↔ 공고 대조 → 매칭 점수·이유 산출
        │
        ▼
추천 공고 노출  (프로필 미등록 시 → 노출 안 함, 등록 CTA)
```

**게이트 규칙:** 마스터 프로필이 등록되지 않았으면 채용공고를 보여주지 않는다.
공고 조회 자체가 프로필을 입력으로 삼기 때문. 미등록 시 "프로필 먼저 등록" CTA만 노출.

## 데이터 소스

| 소스 | API | 상태 |
|---|---|---|
| **잡코리아** | 제휴 API (https://www.jobkorea.co.kr/service/api) | 제휴/키 발급 필요 — 1순위 검토 |
| **사람인** | 공식 Open API (`oapi.saramin.co.kr`, 무료 키) | 보조. 키워드·지역·직무 검색 |
| **공공데이터포털(고용24/워크넷)** | 정부 무료 API | 대체·보완 |
| 원티드 | 공식 공개 API 없음 | 제외 (ToS 위험) |

스크래핑(잡코리아/원티드 HTML 파싱)은 ToS 위반·취약 → 안 함. 반드시 공식 API 경유.

## 매칭 방식 (2단계)

1. **지금(키워드):** 프로필 스택·직무를 API 쿼리 파라미터로 → 이미 어느 정도 관련된 공고 확보.
   `match_reason`은 규칙 기반 placeholder.
2. **나중(임베딩 백본):** 내 경험 임베딩 ↔ 공고 임베딩 유사도로 재순위. `match_reason`도 이때 실제 근거로.
   → pgvector + 임베딩 모델(Voyage/OpenAI). 별도 `app/embeddings/` 공용 도메인.

## 목 → 실제 전환 지점

계층은 그대로. 바꾸는 건 데이터 접근부뿐:

- `app/jobs/repository.py` — `_build_jobs()`(가짜 100개 생성)를 **API 조회 결과 로드**로 교체.
  일단은 API로 긁은 결과를 `jobs/seed.json`으로 덤프해 로드(일회성), 이후 라이브 조회/캐시.
- `router`·`service`(필터·페이지네이션)·`schemas`(`Job`/`JobFeed`)는 유지.
- API 응답 → 우리 `Job` shape 필드 매핑 필요:
  `company / domain / conditions / title / tags / dday / source / match_reason`.
  (API에 없는 `match_reason`은 매칭 단계에서 채움, `domain`은 회사명→도메인 매핑 또는 로고 대체.)

## 프로필 게이트 (구현 상태)

- 현재: `Profile.registered`(bool) 플래그로 프론트에서 게이트. 목은 `registered=true`(등록된 사용자 가정).
- 실제: 인증·프로필 존재 여부로 대체 (`registered` = "마스터 프로필이 존재하는가").
- 프론트 `JobsPage`가 `profileQuery`로 확인 → 미등록이면 공고 조회 안 하고 등록 CTA.

## 단계

- [ ] 소스 확정(잡코리아 제휴 승인 여부 → 안 되면 사람인/공공데이터)
- [ ] API 키 발급 + 응답 필드 조사
- [ ] fetch→seed 스크립트 (키워드 = 내 스택) → `jobs/seed.json`
- [ ] `repository.py`를 seed 로드로 교체
- [ ] 매칭 1단계(키워드/규칙) → `match_reason` 생성
- [ ] (이후) 임베딩 재순위 — docs/TODO.md의 백본과 연계
