from app.core.db import get_sessionmaker
from app.core.mock import mock
from app.profile.models import Profile

# careers/projects의 stack이 매칭 분석(jobs.service._match_analysis)의 '보유 스킬'이다 —
# 공고 요구 스킬(jobs/seed.py)과 문자열이 맞아야 충족으로 잡히니 표기를 함께 관리할 것.
# 의도적으로 일부만 보유한다(SSR·웹뷰·접근성·테스팅·Java 계열 없음) — 다 가지면 부족 스킬이 안 생긴다.
_PROFILE = {
    "registered": True,  # 목: 등록된 사용자 가정. False로 두면 프론트에서 공고 게이트 확인 가능.
    "personal": {
        "photo": "/id-photo.png",
        "name": "김지원",
        "name_en": "Kim Jiwon",
        "name_cn": "金志願",
        "address": "서울특별시 성동구 왕십리로 222, 101동 1004호",
        "phone": "010-1234-5678",
        "email": "jiwon@example.com",
        "emergency_phone": "010-9876-5432",
        "emergency_relation": "부",
    },
    "links": [
        {"label": "GitHub", "url": "https://github.com/jiwon-kim"},
        {"label": "포트폴리오", "url": "https://jiwon.dev"},
        {"label": "블로그", "url": "https://blog.jiwon.dev"},
        {"label": "LinkedIn", "url": "https://linkedin.com/in/jiwon-kim"},
    ],
    "educations": [
        {"school": "한국대학교", "major": "컴퓨터공학과", "period": "2021.03 – 2027.02", "status": "졸업예정", "gpa": "4.1 / 4.5"},
        {"school": "서울고등학교", "major": "이과 계열", "period": "2018.03 – 2021.02", "status": "졸업", "gpa": ""},
    ],
    "awards": [
        {"title": "교내 해커톤 대상", "org": "한국대학교", "date": "2025.11"},
        {"title": "공개SW 개발자대회 장려상", "org": "과학기술정보통신부", "date": "2025.09"},
    ],
    "languages": [
        {"language": "영어", "test": "TOEIC", "score": "900점", "date": "2025.03"},
        {"language": "영어", "test": "OPIc", "score": "IH", "date": "2025.01"},
        {"language": "일본어", "test": "JLPT", "score": "N2", "date": "2024.07"},
    ],
    "certificates": [
        {"name": "정보처리기사", "issuer": "한국산업인력공단", "date": "2024.08"},
        {"name": "SQLD (SQL 개발자)", "issuer": "한국데이터산업진흥원", "date": "2024.05"},
    ],
    "careers": [
        {
            "company": "OO페이 (핀테크 스타트업)",
            "role": "백엔드 엔지니어 인턴",
            "period": "2025.06 – 2025.08",
            "highlights": [
                "결제 실패율 3.2% → 0.4%로 개선 — 로그 파이프라인을 구축해 타임아웃 패턴을 찾고 재시도 정책을 재설계",
                "일 200만 건 결제 트랜잭션의 멱등성 처리 로직 리팩터링으로 중복 결제 클레임 90% 감소",
                "정산 배치 API 신규 개발 및 운영 이관",
            ],
            "stack": [
                "Python", "FastAPI", "PostgreSQL", "Redis", "결제/정산", "로그 파이프라인",
                "멱등성 처리", "대용량 트래픽",
            ],
        },
        {
            "company": "OO소프트",
            "role": "프론트엔드 개발 (파트타임)",
            "period": "2024.07 – 2024.12",
            "highlights": [
                "React 기반 사내 대시보드 신규 구축, 주요 지표 로딩 4.1s → 1.2s 단축",
                "디자인 시스템 컴포넌트 30여 개 구현 및 스토리북 문서화",
            ],
            "stack": ["React", "TypeScript", "Vite", "HTML/CSS", "디자인 시스템", "웹 성능 최적화"],
        },
    ],
    "projects": [
        {
            "name": "one-form — 지원서 통합 플랫폼",
            "role": "풀스택 · 기획",
            "period": "2026.07 – 진행 중",
            "summary": "채용 채널 파편화를 해결하는 지원서 통합 플랫폼. 경험-공고 임베딩 매칭, 기업 분석 RAG, 자소서 자동 생성.",
            "highlights": [
                "Turborepo + pnpm 모노레포(랜딩·웹앱·FastAPI·디자인 시스템) 설계",
                "React 19 + TanStack Query + Suspense, FSD 6레이어 + import 경계 lint 강제",
                "경험↔공고 임베딩 시맨틱 매칭 및 인용 기반 기업 브리핑 RAG 파이프라인 구현",
            ],
            "stack": [
                "React", "TypeScript", "FastAPI", "pgvector", "Claude API",
                "상태관리(TanStack Query)", "모노레포", "임베딩/벡터검색", "LLM/RAG",
            ],
        },
        {
            "name": "실시간 협업 노트 서비스",
            "role": "프론트엔드 · 실시간 동기화",
            "period": "2025.11 · 교내 해커톤",
            "summary": "24시간 해커톤에서 4인 팀으로 개발한 실시간 동시 편집 노트. 심사위원 만장일치 대상.",
            "highlights": [
                "CRDT 기반 동기화 로직 구현, WebSocket 서버 설계",
                "오프라인 편집 후 재접속 시 자동 병합 처리",
            ],
            "stack": ["React", "WebSocket", "CRDT", "Yjs"],
        },
        {
            "name": "오픈소스 CLI 자동화 도구",
            "role": "개인 프로젝트",
            "period": "2025.09",
            "summary": "반복 개발 작업을 자동화하는 CLI 도구. 공개SW 개발자대회 장려상.",
            "highlights": [
                "플러그인 아키텍처 설계로 서드파티 확장 지원",
                "GitHub Actions CI 구축, 테스트 커버리지 85% 유지",
            ],
            "stack": ["Node.js", "TypeScript", "oclif", "CI/CD"],
        },
    ],
    "activities": [
        {"type": "활동", "title": "멋쟁이사자처럼 대학 12기", "org": "한국대학교", "period": "2024.03 – 2024.12", "description": "웹 서비스 팀 프로젝트를 진행하고 데모데이에서 발표."},
        {"type": "활동", "title": "GDSC 웹 스터디 리드", "org": "Google Developer Student Clubs", "period": "2024.03 – 2025.02", "description": "주 1회 프론트엔드 스터디를 운영하고 멤버 12명의 토이 프로젝트를 멘토링."},
        {"type": "교육", "title": "우아한테크코스 프리코스", "org": "우아한형제들", "period": "2025.11 – 2025.12", "description": "JavaScript 미션 4주 과정 수료."},
    ],
}


async def get_profile():
    sm = get_sessionmaker()
    if sm is None:
        return _PROFILE
    async with sm() as s:
        row = await s.get(Profile, 1)
        if row is None:
            return _PROFILE  # 시드 전이면 목으로(빈 화면 방지)
        return {
            "registered": row.registered,
            "personal": row.personal, "links": row.links, "educations": row.educations,
            "awards": row.awards, "languages": row.languages, "certificates": row.certificates,
            "careers": row.careers, "projects": row.projects, "activities": row.activities,
        }


async def save_profile(profile: dict) -> dict:
    """프로필을 단일 JSONB 행으로 저장하고, DB가 없으면 개발용 메모리에 보관한다."""
    global _PROFILE
    sm = get_sessionmaker()
    if sm is None:
        _PROFILE = profile
        return _PROFILE

    async with sm() as s:
        row = await s.get(Profile, 1)
        fields = {key: value for key, value in profile.items() if key != "registered"}
        if row is None:
            row = Profile(id=1, registered=profile["registered"], **fields)
            s.add(row)
        else:
            row.registered = profile["registered"]
            for key, value in fields.items():
                setattr(row, key, value)
        await s.commit()
    return profile
