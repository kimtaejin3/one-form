import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="one-form API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # landing
        "http://localhost:3001",  # web
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ponytail: 목 단계 — DB 없이 1초 지연 후 더미 응답. 실제 구현 시 mock() 호출 제거.
MOCK_DELAY_SECONDS = 1.0


async def mock(data):
    await asyncio.sleep(MOCK_DELAY_SECONDS)
    return data


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ponytail: 목 — 실제 크롤링(§4.4/§4.5) 대신 현실적인 공고 100개를 생성.
_COMPANIES = [
    ("네이버", "navercorp.com"), ("카카오", "kakaocorp.com"), ("토스", "toss.im"),
    ("쿠팡", "coupang.com"), ("라인", "line.me"), ("당근", "daangn.com"),
    ("배달의민족", "woowahan.com"), ("야놀자", "yanolja.com"), ("무신사", "musinsa.com"),
    ("컬리", "kurly.com"), ("오늘의집", "bucketplace.com"), ("직방", "zigbang.com"),
    ("쏘카", "socar.kr"), ("리디", "ridi.com"), ("클래스101", "class101.net"),
    ("뱅크샐러드", "banksalad.com"), ("두나무", "dunamu.com"), ("카카오뱅크", "kakaobank.com"),
    ("네이버웹툰", "navercorp.com"), ("당근페이", "daangn.com"),
]
_ROLES = [
    ("백엔드", "백엔드 개발자", ["Java", "Spring", "MSA"]),
    ("프론트엔드", "프론트엔드 개발자", ["React", "TypeScript", "Next.js"]),
    ("풀스택", "풀스택 개발자", ["Node.js", "React", "AWS"]),
    ("데브옵스", "데브옵스 엔지니어", ["Kubernetes", "Terraform", "AWS"]),
    ("안드로이드", "안드로이드 개발자", ["Kotlin", "Compose"]),
    ("iOS", "iOS 개발자", ["Swift", "SwiftUI"]),
    ("데이터", "데이터 엔지니어", ["Spark", "Airflow", "Python"]),
    ("ML", "ML 엔지니어", ["PyTorch", "MLOps", "Python"]),
]
_EXPERIENCE = ["신입", "경력무관", "1년 이상", "3년 이상", "5년 이상"]
_EMPLOYMENT = ["정규직", "계약직", "인턴", "전환형인턴"]
_LOCATION = ["서울", "경기 판교", "부산", "제주", "원격"]
_SOURCE = ["자사 채용", "원티드", "사람인", "잡코리아", "링크드인"]
_MATCH = [
    "실시간 동기화로 쌓은 대용량 처리 경험이 이 직무와 잘 맞아요",
    "결제 실패율 3.2%→0.4% 개선 경험이 신뢰성 요구와 통해요",
    "CRDT·WebSocket 실시간 협업 경험이 이 포지션과 정확히 맞아요",
    "서비스를 처음부터 설계한 경험이 이 팀의 과제와 어울려요",
    "성능 최적화(로딩 4.1s→1.2s) 경험이 요구 역량과 연결돼요",
]


def _build_jobs():
    jobs = []
    for i in range(100):
        company, domain = _COMPANIES[i % len(_COMPANIES)]
        role_cat, role_title, tags = _ROLES[i % len(_ROLES)]
        experience = _EXPERIENCE[i % len(_EXPERIENCE)]
        employment = _EMPLOYMENT[(i // 2) % len(_EMPLOYMENT)]
        location = _LOCATION[(i // 3) % len(_LOCATION)]
        source = _SOURCE[i % len(_SOURCE)]
        dday = "상시" if i % 4 == 0 else f"D-{(i % 25) + 1}"
        jobs.append({
            "id": i + 1,
            "company": company,
            "domain": domain,
            "role_category": role_cat,
            "title": f"[{company}] {role_title}" + (" (신입)" if experience == "신입" else ""),
            "tags": tags,
            "experience": experience,
            "employment": employment,
            "location": location,
            "dday": dday,
            "source": source,
            "match_reason": _MATCH[i % len(_MATCH)],
        })
    return jobs


_ALL_JOBS = _build_jobs()


@app.get("/api/jobs")
async def list_jobs(
    page: int = 1,
    size: int = 12,
    role: str = "",
    experience: str = "",
    employment: str = "",
    location: str = "",
):
    filtered = [
        j for j in _ALL_JOBS
        if (not role or j["role_category"] == role)
        and (not experience or j["experience"] == experience)
        and (not employment or j["employment"] == employment)
        and (not location or j["location"] == location)
    ]
    start = (page - 1) * size
    page_jobs = [
        {
            "id": j["id"],
            "company": j["company"],
            "domain": j["domain"],
            "conditions": f"{j['experience']} · {j['employment']} · {j['location']}",
            "title": j["title"],
            "tags": j["tags"],
            "dday": j["dday"],
            "source": j["source"],
            "match_reason": j["match_reason"],
        }
        for j in filtered[start:start + size]
    ]
    return await mock({
        "role": "백엔드 개발",
        "total": len(filtered),
        "page": page,
        "size": size,
        "jobs": page_jobs,
    })


@app.get("/api/profile")
async def get_profile():
    return await mock({
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
                "stack": ["Python", "FastAPI", "PostgreSQL", "Redis"],
            },
            {
                "company": "OO소프트",
                "role": "프론트엔드 개발 (파트타임)",
                "period": "2024.07 – 2024.12",
                "highlights": [
                    "React 기반 사내 대시보드 신규 구축, 주요 지표 로딩 4.1s → 1.2s 단축",
                    "디자인 시스템 컴포넌트 30여 개 구현 및 스토리북 문서화",
                ],
                "stack": ["React", "TypeScript", "Vite"],
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
                "stack": ["React", "TypeScript", "FastAPI", "pgvector", "Claude API"],
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
                "stack": ["Node.js", "TypeScript", "oclif"],
            },
        ],
        "activities": [
            {"type": "활동", "title": "멋쟁이사자처럼 대학 12기", "org": "한국대학교", "period": "2024.03 – 2024.12", "description": "웹 서비스 팀 프로젝트를 진행하고 데모데이에서 발표."},
            {"type": "활동", "title": "GDSC 웹 스터디 리드", "org": "Google Developer Student Clubs", "period": "2024.03 – 2025.02", "description": "주 1회 프론트엔드 스터디를 운영하고 멤버 12명의 토이 프로젝트를 멘토링."},
            {"type": "교육", "title": "우아한테크코스 프리코스", "org": "우아한형제들", "period": "2025.11 – 2025.12", "description": "JavaScript 미션 4주 과정 수료."},
        ],
    })


@app.post("/api/profile/resume")
async def upload_resume():
    return await mock({
        "parsed_fields": 12,
        "new_experiences": 3,
        "message": "이력서에서 12개 필드를 추출해 마스터 프로필에 반영했습니다.",
    })


class CompanyAnalyzeRequest(BaseModel):
    name: str


@app.post("/api/companies/analyze")
async def analyze_company(req: CompanyAnalyzeRequest):
    return await mock({
        "name": req.name,
        "business_areas": ["커머스 플랫폼", "물류 자동화", "구독 서비스"],
        "products": ["로켓배송", "로켓프레시", "쿠팡플레이"],
        "jd_skills": ["React 기반 대규모 SPA 경험", "성능 최적화", "테스트 자동화", "디자인 시스템 운영"],
        "strength_matching": [
            {
                "company_issue": "물류 대시보드 실시간성 강화",
                "my_experience": "실시간 협업 노트 서비스 (CRDT·WebSocket)",
                "fit": 92,
            },
            {
                "company_issue": "결제 안정성 개선",
                "my_experience": "결제 실패율 3.2%→0.4% 개선 인턴 경험",
                "fit": 87,
            },
        ],
    })


@app.get("/api/essays")
async def list_essays():
    return await mock([
        {"id": 1, "company": "네이버", "question": "본인이 주도적으로 문제를 해결한 경험을 서술하시오.", "char_limit": 1000, "deadline": "2026-07-28", "status": "작성 중"},
        {"id": 2, "company": "토스", "question": "지원 직무에 필요한 역량을 갖추기 위해 노력한 과정을 서술하시오.", "char_limit": 1500, "deadline": "2026-07-25", "status": "초안 완료"},
        {"id": 3, "company": "카카오", "question": "카카오 서비스 중 개선하고 싶은 것과 그 이유는?", "char_limit": 800, "deadline": "2026-07-30", "status": "미작성"},
    ])


class DraftRequest(BaseModel):
    essay_id: int


@app.post("/api/essays/draft")
async def generate_draft(req: DraftRequest):
    return await mock({
        "essay_id": req.essay_id,
        "draft": "[AI 초안] 지난해 교내 해커톤에서 실시간 협업 노트 서비스를 개발하며 CRDT 동기화라는 낯선 문제를 24시간 안에 풀어야 했습니다. 문서를 뒤지는 대신 실패 케이스를 좁혀가는 실험을 반복했고, 결국 안정적인 동시 편집을 구현해 대상을 받았습니다. 이 문제 해결 방식은 귀사가 집중하는 실시간 데이터 처리 과제에 그대로 기여할 수 있는 역량이라 확신합니다.",
    })


_ACTIVITIES = [
    # 공모전 / 해커톤
    {"id": 1, "name": "제12회 공개SW 개발자대회", "category": "공모전", "organizer": "정보통신산업진흥원", "period": "2026.06 – 09", "dday": "D-30", "fit": 91, "fills_gap": ["오픈소스 기여", "대규모 코드베이스 분석"], "expected_experience": "실제 오픈소스에 PR을 머지시키며 리뷰 대응과 코드 품질 개선 사례를 축적합니다.", "connections": [{"company": "라인", "role": "백엔드 개발자"}, {"company": "네이버", "role": "백엔드 개발자"}]},
    {"id": 2, "name": "구름톤 유니브 해커톤", "category": "공모전", "organizer": "구름(goorm)", "period": "2026.10", "dday": "D-45", "fit": 84, "fills_gap": ["빠른 프로토타이핑", "네트워킹"], "expected_experience": "짧은 몰입 기간에 완성한 프로토타입으로 실행력을 보여주는 에피소드를 만듭니다.", "connections": [{"company": "토스", "role": "풀스택 개발자"}]},
    {"id": 3, "name": "카카오 아레나 추천 알고리즘 대회", "category": "공모전", "organizer": "카카오", "period": "상시", "dday": "상시", "fit": 78, "fills_gap": ["추천 시스템", "데이터 분석"], "expected_experience": "추천 모델을 직접 튜닝하며 임베딩·랭킹 경험을 확보해 데이터 직무 강점을 만듭니다.", "connections": [{"company": "카카오", "role": "ML 엔지니어"}]},
    {"id": 4, "name": "핀테크 아이디어 공모전", "category": "공모전", "organizer": "한국핀테크지원센터", "period": "2026.07", "dday": "D-20", "fit": 82, "fills_gap": ["핀테크 도메인", "기획"], "expected_experience": "금융 도메인 문제를 정의하고 해결안을 설계한 경험으로 핀테크 지원 스토리를 강화합니다.", "connections": [{"company": "토스", "role": "서버 개발자"}, {"company": "카카오뱅크", "role": "백엔드 개발자"}]},
    {"id": 5, "name": "대학생 빅데이터 분석 경진대회", "category": "공모전", "organizer": "통계청", "period": "2026.09", "dday": "D-33", "fit": 76, "fills_gap": ["데이터 분석", "Python"], "expected_experience": "공공 데이터를 분석·시각화한 경험으로 데이터 엔지니어 지원 근거를 만듭니다.", "connections": [{"company": "쿠팡", "role": "데이터 엔지니어"}]},
    # 동아리 / 학회
    {"id": 6, "name": "멋쟁이사자처럼 대학 13기", "category": "동아리", "organizer": "전국 대학 연합", "period": "2026.09 – 2027.02", "dday": "모집중", "fit": 94, "fills_gap": ["실서비스 배포", "협업 프로젝트 리드"], "expected_experience": "아이디어톤부터 런칭까지 팀을 이끌며 기획–개발–배포 전 과정을 STAR로 정리합니다.", "connections": [{"company": "토스", "role": "풀스택 개발자"}, {"company": "카카오", "role": "웹 개발자"}]},
    {"id": 7, "name": "SOPT 35기", "category": "동아리", "organizer": "대학생 연합 IT벤처", "period": "2026.09 – 2027.02", "dday": "D-15", "fit": 90, "fills_gap": ["직군 간 협업", "서비스 런칭"], "expected_experience": "기획·디자인·개발이 한 팀으로 앱을 런칭하며 협업 커뮤니케이션 경험을 쌓습니다.", "connections": [{"company": "당근", "role": "안드로이드 개발자"}]},
    {"id": 8, "name": "DND 12기", "category": "동아리", "organizer": "개발자·디자이너 연합", "period": "2026.08 – 2026.10", "dday": "D-9", "fit": 91, "fills_gap": ["디자이너 협업", "짧은 주기 배포"], "expected_experience": "디자이너와 8주간 사이드 프로젝트를 완성하며 직군 간 협업과 일정 관리 경험을 확보합니다.", "connections": [{"company": "네이버", "role": "프론트엔드 개발자"}]},
    {"id": 9, "name": "YAPP 25기", "category": "동아리", "organizer": "연합 앱 개발 동아리", "period": "2026.09 – 2027.01", "dday": "D-18", "fit": 86, "fills_gap": ["앱 서비스 출시", "협업"], "expected_experience": "앱을 스토어에 실제 출시하며 출시·운영 경험을 확보합니다.", "connections": [{"company": "당근", "role": "iOS 개발자"}]},
    {"id": 10, "name": "Depromeet 16기", "category": "동아리", "organizer": "개발자·디자이너·기획자 연합", "period": "2026.09", "dday": "D-22", "fit": 88, "fills_gap": ["사이드 프로젝트", "협업"], "expected_experience": "한 사이클 동안 서비스를 완성하며 팀 개발 프로세스 경험을 만듭니다.", "connections": [{"company": "무신사", "role": "프론트엔드 개발자"}]},
    # 대외활동 / 인턴
    {"id": 11, "name": "우아한테크코스 7기", "category": "대외활동", "organizer": "우아한형제들", "period": "2026.02 – 2026.12", "dday": "D-40", "fit": 95, "fills_gap": ["실무 수준 코드리뷰", "대규모 미션"], "expected_experience": "10개월간 실무 수준의 코드리뷰를 받으며 설계·테스트 역량을 실전 경험으로 만듭니다.", "connections": [{"company": "배달의민족", "role": "백엔드 개발자"}, {"company": "토스", "role": "서버 개발자"}]},
    {"id": 12, "name": "네이버 부스트캠프 웹·모바일", "category": "대외활동", "organizer": "네이버 커넥트재단", "period": "2026.07 – 2026.12", "dday": "D-25", "fit": 93, "fills_gap": ["챌린지형 학습", "협업"], "expected_experience": "챌린지·멤버십 과정에서 CS와 협업을 깊게 다지며 개발 기본기를 강화합니다.", "connections": [{"company": "네이버", "role": "백엔드 개발자"}]},
    {"id": 13, "name": "삼성 청년 SW 아카데미(SSAFY)", "category": "대외활동", "organizer": "삼성전자", "period": "2026.07 – 2027.06", "dday": "D-30", "fit": 89, "fills_gap": ["1년 몰입 교육", "프로젝트"], "expected_experience": "1년간 몰입 교육과 프로젝트로 폭넓은 스택 경험과 취업 연계를 확보합니다.", "connections": [{"company": "쿠팡", "role": "풀스택 개발자"}]},
    {"id": 14, "name": "토스 NEXT 인턴십", "category": "대외활동", "organizer": "비바리퍼블리카", "period": "2026.06 – 2026.08", "dday": "D-7", "fit": 90, "fills_gap": ["실서비스 인턴", "대용량 트래픽"], "expected_experience": "실서비스 코드베이스에서 인턴 프로젝트를 수행하며 대용량 처리 경험을 만듭니다.", "connections": [{"company": "토스", "role": "서버 개발자"}]},
    {"id": 15, "name": "카카오 테크 캠퍼스", "category": "대외활동", "organizer": "카카오", "period": "2026.03 – 2026.11", "dday": "D-14", "fit": 87, "fills_gap": ["현업 멘토링", "프로젝트"], "expected_experience": "현업 개발자 멘토링 아래 프로젝트를 완성하며 실무 감각을 확보합니다.", "connections": [{"company": "카카오", "role": "백엔드 개발자"}]},
    # 교육 / 부트캠프
    {"id": 16, "name": "우아한테크코스 프리코스", "category": "교육", "organizer": "우아한형제들", "period": "2026.11 – 2026.12", "dday": "D-50", "fit": 92, "fills_gap": ["JavaScript 미션", "TDD"], "expected_experience": "4주 미션에서 TDD와 클린코드를 연습하며 코드 품질 감각을 만듭니다.", "connections": [{"company": "배달의민족", "role": "프론트엔드 개발자"}]},
    {"id": 17, "name": "프로그래머스 데브코스 백엔드", "category": "교육", "organizer": "프로그래머스", "period": "2026.08 – 2027.02", "dday": "D-16", "fit": 88, "fills_gap": ["백엔드 심화", "팀 프로젝트"], "expected_experience": "백엔드 심화 커리큘럼과 팀 프로젝트로 실전형 포트폴리오를 확보합니다.", "connections": [{"company": "라인", "role": "백엔드 개발자"}]},
    {"id": 18, "name": "K-디지털 트레이닝 클라우드(국비)", "category": "교육", "organizer": "고용노동부", "period": "2026.09 – 2027.03", "dday": "D-28", "fit": 78, "fills_gap": ["클라우드", "국비 지원"], "expected_experience": "AWS·컨테이너 기반 실습으로 데브옵스 기초 역량을 만듭니다.", "connections": [{"company": "쿠팡", "role": "데브옵스 엔지니어"}]},
    {"id": 19, "name": "42 서울", "category": "교육", "organizer": "이노베이션 아카데미", "period": "상시", "dday": "상시", "fit": 81, "fills_gap": ["자기주도 학습", "CS 기초"], "expected_experience": "동료 학습과 프로젝트로 CS 기본기와 문제 해결력을 다집니다.", "connections": [{"company": "네이버", "role": "백엔드 개발자"}]},
    {"id": 20, "name": "인프런 워밍업 클럽 (CS)", "category": "교육", "organizer": "인프런", "period": "2026.07", "dday": "D-5", "fit": 74, "fills_gap": ["CS 기초 다지기"], "expected_experience": "운영체제·네트워크 기초를 단기 집중으로 정리해 면접 대비 기반을 만듭니다.", "connections": [{"company": "카카오", "role": "백엔드 개발자"}]},
]


@app.get("/api/activities")
async def list_activities():
    return await mock(_ACTIVITIES)


@app.post("/api/forms/convert")
async def convert_form():
    return await mock({
        "form_name": "지원서_양식.docx",
        "mappings": [
            {"form_field": "성명", "profile_field": "이름", "confidence": 100},
            {"form_field": "학력 사항", "profile_field": "학력", "confidence": 97},
            {"form_field": "경력 및 프로젝트", "profile_field": "STAR 경험 2건", "confidence": 91},
            {"form_field": "자격증", "profile_field": "자격증 3건", "confidence": 99},
            {"form_field": "자기소개", "profile_field": "자소서 허브 초안", "confidence": 78},
        ],
    })
