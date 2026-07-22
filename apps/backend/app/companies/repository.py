from app.core.mock import mock


async def analyze(name: str):
    return await mock({
        "name": name,
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
