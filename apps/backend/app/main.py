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


@app.get("/api/applications")
async def list_applications():
    return await mock([
        {"id": 1, "company": "네이버", "role": "프론트엔드 개발자", "channel": "자사 홈페이지", "status": "서류 합격", "deadline": "2026-08-01"},
        {"id": 2, "company": "토스", "role": "풀스택 개발자", "channel": "토스 채용", "status": "지원 완료", "deadline": "2026-07-25"},
        {"id": 3, "company": "카카오", "role": "웹 개발자", "channel": "카카오 커리어", "status": "작성 중", "deadline": "2026-07-30"},
        {"id": 4, "company": "쿠팡", "role": "프론트엔드 엔지니어", "channel": "원티드", "status": "면접 예정", "deadline": "2026-08-10"},
        {"id": 5, "company": "라인", "role": "UI 엔지니어", "channel": "자사 홈페이지", "status": "작성 중", "deadline": "2026-08-05"},
    ])


@app.get("/api/profile")
async def get_profile():
    return await mock({
        "name": "김지원",
        "email": "jiwon@example.com",
        "education": "한국대학교 컴퓨터공학과 졸업 예정 (2027.02)",
        "certificates": ["정보처리기사", "SQLD", "TOEIC 900"],
        "experiences": [
            {
                "id": 1,
                "title": "교내 해커톤 우승 — 실시간 협업 노트 서비스",
                "situation": "24시간 해커톤에 4인 팀으로 참가",
                "task": "실시간 동시 편집 기능 담당",
                "action": "CRDT 기반 동기화 로직을 구현하고 WebSocket 서버를 설계",
                "result": "심사위원 만장일치 대상, 교내 서비스로 채택",
                "tags": ["React", "WebSocket", "CRDT"],
            },
            {
                "id": 2,
                "title": "핀테크 스타트업 인턴 — 결제 실패율 개선",
                "situation": "백엔드 팀 인턴으로 합류",
                "task": "간헐적 결제 실패의 원인 분석과 개선",
                "action": "로그 파이프라인을 구축해 타임아웃 패턴을 찾고 재시도 정책을 재설계",
                "result": "결제 실패율 3.2% → 0.4%로 감소",
                "tags": ["Python", "FastAPI", "데이터 분석"],
            },
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
