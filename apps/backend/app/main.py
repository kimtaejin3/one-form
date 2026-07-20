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


@app.get("/api/jobs")
async def list_jobs():
    # ponytail: 목 — 실제로는 마스터 프로필 직무로 매칭 필터. 지금은 개발 직무 고정.
    return await mock({
        "role": "백엔드 개발",
        "jobs": [
            {"id": 1, "company": "네이버", "domain": "navercorp.com", "conditions": "경력무관 · 정규직 · 경기 판교", "title": "[NAVER] 검색 플랫폼 백엔드 개발자", "tags": ["검색", "대용량트래픽", "Java"], "dday": "D-7", "source": "자사 채용", "match_reason": "실시간 동기화로 쌓은 대용량 처리 경험이 검색 트래픽 설계와 잘 맞아요"},
            {"id": 2, "company": "카카오", "domain": "kakaocorp.com", "conditions": "3년 이상 · 정규직 · 제주", "title": "[카카오] 커머스 백엔드 엔지니어", "tags": ["커머스", "Spring", "MSA"], "dday": "D-12", "source": "원티드", "match_reason": "결제 안정화 프로젝트 경험이 커머스 백엔드의 신뢰성 요구와 통해요"},
            {"id": 3, "company": "토스", "domain": "toss.im", "conditions": "경력무관 · 정규직 · 서울", "title": "[토스] Server Developer (Backend)", "tags": ["핀테크", "Kotlin", "대용량"], "dday": "상시", "source": "자사 채용", "match_reason": "결제 실패율 3.2%→0.4% 개선 경험이 핀테크 서버 직무에 딱 맞아요"},
            {"id": 4, "company": "쿠팡", "domain": "coupang.com", "conditions": "3년 이상 · 정규직 · 서울", "title": "[쿠팡] Backend Engineer, 물류 플랫폼", "tags": ["물류", "대규모시스템", "AWS"], "dday": "D-20", "source": "링크드인", "match_reason": "실시간 시스템 설계 경험이 대규모 물류 플랫폼과 연결돼요"},
            {"id": 5, "company": "라인", "domain": "line.me", "conditions": "경력무관 · 정규직 · 서울", "title": "[LINE] 메신저 백엔드 개발자", "tags": ["메신저", "실시간", "Java"], "dday": "D-5", "source": "자사 채용", "match_reason": "CRDT·WebSocket 실시간 협업 경험이 메신저 백엔드와 정확히 맞아요"},
            {"id": 6, "company": "당근", "domain": "daangn.com", "conditions": "3년 이하 · 정규직 · 서울", "title": "[당근] 커뮤니티 서버 개발자", "tags": ["로컬커뮤니티", "Go", "Kubernetes"], "dday": "상시", "source": "원티드", "match_reason": "서비스를 처음부터 설계한 경험이 커뮤니티 서버 개발과 잘 어울려요"},
        ],
    })


@app.get("/api/profile")
async def get_profile():
    return await mock({
        "personal": {
            "name": "김지원",
            "name_en": "Kim Jiwon",
            "name_cn": "金志願",
            "address": "서울특별시 성동구 왕십리로 222, 101동 1004호",
            "phone": "010-1234-5678",
            "email": "jiwon@example.com",
            "emergency_phone": "010-9876-5432",
            "emergency_relation": "부",
        },
        "educations": [
            {"school": "한국대학교 컴퓨터공학과", "period": "2021.03 – 2027.02", "status": "졸업 예정", "note": "학점 4.1 / 4.5"},
            {"school": "서울고등학교", "period": "2018.03 – 2021.02", "status": "졸업", "note": "이과"},
        ],
        "awards": [
            {"title": "교내 해커톤 대상", "org": "한국대학교", "date": "2025.11"},
            {"title": "공개SW 개발자대회 장려상", "org": "과학기술정보통신부", "date": "2025.09"},
        ],
        "languages": [
            {"name": "영어", "test": "TOEIC", "score": "900"},
            {"name": "영어", "test": "OPIc", "score": "IH"},
            {"name": "일본어", "test": "JLPT", "score": "N2"},
        ],
        "certificates": ["정보처리기사", "SQLD"],
        "career": [
            {"type": "경험", "title": "핀테크 스타트업 백엔드 인턴", "org": "OO페이", "period": "2025.06 – 2025.08", "description": "결제 시스템 안정화 프로젝트에 참여해 실패율 개선 작업을 담당."},
            {"type": "활동", "title": "멋쟁이사자처럼 대학 12기", "org": "한국대학교", "period": "2024.03 – 2024.12", "description": "웹 서비스 팀 프로젝트를 진행하고 데모데이에서 발표."},
            {"type": "교육", "title": "우아한테크코스 프리코스", "org": "우아한형제들", "period": "2025.11 – 2025.12", "description": "JavaScript 미션 4주 과정을 수료."},
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


@app.get("/api/activities")
async def list_activities():
    return await mock([
        {
            "id": 1,
            "name": "멋쟁이사자처럼 대학 13기",
            "category": "IT 동아리",
            "period": "2026.09 – 2027.02",
            "fit": 94,
            "fills_gap": ["실서비스 배포 경험", "협업 프로젝트 리드"],
            "expected_experience": "아이디어톤부터 런칭까지 팀 프로젝트를 이끌며 기획–개발–배포 전 과정을 STAR 경험으로 정리할 수 있습니다.",
            "connections": [
                {"company": "토스", "role": "풀스택 개발자"},
                {"company": "카카오", "role": "웹 개발자"},
            ],
        },
        {
            "id": 2,
            "name": "DND 12기",
            "category": "IT 동아리",
            "period": "2026.08 – 2026.10",
            "fit": 91,
            "fills_gap": ["디자이너 협업", "짧은 주기 배포"],
            "expected_experience": "디자이너와 8주간 사이드 프로젝트를 완성하며 직군 간 협업과 일정 관리 경험을 확보합니다.",
            "connections": [{"company": "네이버", "role": "프론트엔드 개발자"}],
        },
        {
            "id": 3,
            "name": "오픈소스 컨트리뷰션 아카데미",
            "category": "대외활동",
            "period": "2026.08 – 2026.11",
            "fit": 88,
            "fills_gap": ["대규모 코드베이스 분석", "코드 리뷰 대응"],
            "expected_experience": "실제 오픈소스에 PR을 머지시키며 리뷰 대응과 코드 품질 개선 사례를 축적합니다.",
            "connections": [
                {"company": "라인", "role": "UI 엔지니어"},
                {"company": "네이버", "role": "프론트엔드 개발자"},
            ],
        },
        {
            "id": 4,
            "name": "쿠팡 물류 테크 해커톤",
            "category": "대외활동",
            "period": "2026.09 (48시간)",
            "fit": 85,
            "fills_gap": ["커머스·물류 도메인 이해", "실시간 데이터 처리"],
            "expected_experience": "물류 도메인 문제를 48시간 안에 해결한 경험 — 기존 CRDT·WebSocket 경험과 묶어 실시간 처리 강점을 강화합니다.",
            "connections": [{"company": "쿠팡", "role": "프론트엔드 엔지니어"}],
        },
        {
            "id": 5,
            "name": "구름톤 유니브",
            "category": "대외활동",
            "period": "2026.10",
            "fit": 79,
            "fills_gap": ["빠른 프로토타이핑", "네트워킹"],
            "expected_experience": "짧은 몰입 기간에 완성한 프로토타입으로 실행력을 보여주는 에피소드를 만듭니다.",
            "connections": [{"company": "토스", "role": "풀스택 개발자"}],
        },
    ])


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
