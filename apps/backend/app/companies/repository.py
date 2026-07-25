from app.core.mock import mock

# ponytail: 목 — 잘 알려진 기업만 도메인 매핑(로고용), 나머지는 이니셜 폴백.
_DOMAINS = {
    "쿠팡": "coupang.com", "네이버": "navercorp.com", "카카오": "kakaocorp.com",
    "토스": "toss.im", "라인": "line.me", "배달의민족": "woowahan.com", "당근": "daangn.com",
}


async def analyze(name: str):
    return await mock({
        "name": name,
        "domain": _DOMAINS.get(name, ""),
        "summary": "커머스·물류·핀테크를 아우르는 대규모 이커머스 플랫폼.",
        "stage": "상장 · 임직원 5,000+ · 대규모 트래픽",
        "business_areas": ["커머스 플랫폼", "물류 자동화", "구독 서비스"],
        "products": ["로켓배송", "로켓프레시", "쿠팡플레이"],
        "jd_skills": ["React 기반 대규모 SPA 경험", "성능 최적화", "테스트 자동화", "디자인 시스템 운영"],
        "signals": [
            {"label": "채용 확대", "detail": "플랫폼·물류 자동화 조직에서 백엔드 채용이 최근 분기 늘었어요.", "source": "채용공고 추이 · 2026.Q2"},
            {"label": "신규 투자", "detail": "광고·핀테크 부문 투자 확대를 발표했어요.", "source": "IR 자료 · 2026.05"},
            {"label": "기술 전환", "detail": "대규모 트래픽 처리와 데이터 플랫폼 전환을 진행 중이에요.", "source": "기술 블로그 · 2026.04"},
        ],
        "strength_matching": [
            {"company_issue": "물류 대시보드 실시간성 강화", "my_experience": "실시간 협업 노트 서비스 (CRDT·WebSocket)", "fit": 92},
            {"company_issue": "결제 안정성 개선", "my_experience": "결제 실패율 3.2%→0.4% 개선 인턴 경험", "fit": 87},
            {"company_issue": "대시보드 로딩 성능", "my_experience": "주요 지표 로딩 4.1s→1.2s 단축", "fit": 81},
        ],
        "interview_points": [
            {"question": "대용량 트래픽에서 데이터 정합성을 어떻게 보장했나요?", "hint": "결제 멱등성·정산 배치 경험을 STAR로 풀어보세요."},
            {"question": "장애 상황에서의 의사결정 경험은?", "hint": "실패율 개선 인턴 사례와 로그 파이프라인 구축을 연결하세요."},
        ],
        "apply_tips": [
            "JD의 '성능 최적화'와 로딩 4.1s→1.2s 경험을 자소서 첫 문단에 배치하세요.",
            "물류·실시간 도메인이라 CRDT·WebSocket 협업 경험을 강조하면 차별화됩니다.",
        ],
    })
