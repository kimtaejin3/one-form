# one-form IA (Information Architecture)

기획서 V5 기반. 현재는 목(mock) 단계 — web 5개 페이지 + 더미 API.

## 서비스 전체 구조

```mermaid
flowchart TD
    ONEFORM((ONEFORM))
    ONEFORM --> LANDING["랜딩 · apps/landing<br/>서비스 소개 / 전환 유도"]
    ONEFORM --> WEB["웹앱 · apps/web<br/>핵심 워크스페이스"]
    ONEFORM --> EXT["크롬 익스텐션 (예정)<br/>웹 폼 오토필 위젯 §3.3"]

    WEB --> DASH["/ 대시보드<br/>지원 현황 칸반 §4.5"]
    WEB --> PROFILE["/profile 마스터 프로필<br/>이력서 수집 · STAR 경험 §4.1"]
    WEB --> COMPANY["/companies 기업 인텔리전스<br/>기업 브리프 · 강점 매칭 §4.4"]
    WEB --> ESSAY["/essays 자소서 허브<br/>문항 관리 · AI 초안 §4.3"]
    WEB --> FORMS["/forms 양식 변환<br/>자사 양식 매핑 뷰어 §4.2"]
    WEB --> ACT["/activities 활동 추천<br/>역량 갭 기반 동아리·대외활동 §4.6"]
```

## 핵심 유저 플로우

```mermaid
flowchart LR
    U["이력서 업로드"] --> M["마스터 프로필<br/>STAR 구조화"]
    M --> A["타겟 기업 분석"]
    A --> D["AI 자소서 초안"]
    M --> F["자사 양식 변환"]
    D --> S["지원 제출"]
    F --> S
    S --> K["칸반 트래킹<br/>리마인더"]
    K -->|"역량 갭 분석 §4.6"| R["활동 추천"]
    R -.-> M
```

## 페이지 ↔ 기획서 ↔ API 매핑

| 페이지 | 기획서 | 기능 (목 단계) | Mock API |
| --- | --- | --- | --- |
| `/` 대시보드 | §4.5 | 지원 현황 칸반 (작성 중 → 지원 완료 → 서류 합격 → 면접 예정) | `GET /api/applications` |
| `/profile` 마스터 프로필 | §4.1, §5 | 이력서 업로드(수집 목), 기본 스펙, STAR 경험 카드 | `GET /api/profile` · `POST /api/profile/resume` |
| `/companies` 기업 인텔리전스 | §4.4, §5 | 기업명 입력 → 사업/제품/JD 역량/강점 매칭 브리프 | `POST /api/companies/analyze` |
| `/essays` 자소서 허브 | §4.3, §5 | 문항 목록(글자 수·마감), AI 초안 생성 | `GET /api/essays` · `POST /api/essays/draft` |
| `/forms` 양식 변환 | §4.2, §5 | 양식 업로드 → 필드 매핑 시뮬레이션 | `POST /api/forms/convert` |
| `/activities` 활동 추천 | §4.6 | 역량 갭 보완 활동 추천 — 예상 경험·기업/직무 연결 표시 | `GET /api/activities` |

MVP(§5) 중 '크롬 오토필 위젯'은 브라우저 익스텐션이라 web 범위 밖 — 후속 작업.

## Mock 규약

모든 목 엔드포인트는 DB 없이 **1초 지연 후 더미 데이터**를 반환한다
(`apps/backend/app/main.py`의 `mock()` 헬퍼). 실제 구현으로 교체할 때 헬퍼 호출만 걷어내면 된다.
