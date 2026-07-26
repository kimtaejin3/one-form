from sqlalchemy import select

from app.activities.models import Activity
from app.core.db import get_sessionmaker

# ponytail: 목 — 실제 크롤링 대신 현실적인 활동 20건을 큐레이션.
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


async def list_activities():
    sm = get_sessionmaker()
    if sm is None:
        return _ACTIVITIES
    async with sm() as s:
        rows = (await s.execute(select(Activity).order_by(Activity.id))).scalars().all()
        if not rows:
            return _ACTIVITIES
        return [
            {"id": r.id, "name": r.name, "category": r.category, "organizer": r.organizer,
             "period": r.period, "dday": r.dday, "fit": r.fit,
             "expected_experience": r.expected_experience,
             "fills_gap": r.fills_gap, "connections": r.connections}
            for r in rows
        ]
