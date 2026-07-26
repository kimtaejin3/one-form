# ponytail: 목 — 실제 크롤링(§4.4/§4.5) 대신 (회사 × 직무) 조합으로 유니크 공고를 생성.
# 실제 구현 시 all_jobs()를 pgvector 검색 쿼리로 교체.
from app.jobs.seed import COMPANIES, ROLES

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
_ROLES_PER_COMPANY = 2  # 회사당 2직무 로테이션 → 20 × 2 = 40건, 8직무가 각 5회 등장
_EXPERIENCE = ["신입", "경력무관", "1년 이상", "3년 이상", "5년 이상"]
_EMPLOYMENT = ["정규직", "계약직", "인턴", "전환형인턴"]
_SOURCE = ["자사 채용", "원티드", "사람인", "잡코리아", "링크드인"]
_MATCH = [
    "실시간 동기화로 쌓은 대용량 처리 경험이 이 직무와 잘 맞아요",
    "결제 실패율 3.2%→0.4% 개선 경험이 신뢰성 요구와 통해요",
    "CRDT·WebSocket 실시간 협업 경험이 이 포지션과 정확히 맞아요",
    "서비스를 처음부터 설계한 경험이 이 팀의 과제와 어울려요",
    "성능 최적화(로딩 4.1s→1.2s) 경험이 요구 역량과 연결돼요",
]


def _build_jobs():
    """유니크 (회사 × 직무), 전부 서울. 요구 스킬 = 직무 템플릿 + 회사 강조 스킬(조합마다 다름)."""
    jobs = []
    for company_index, (company, domain) in enumerate(_COMPANIES):
        emphasis_skills = COMPANIES[company]["skills"]
        for slot in range(_ROLES_PER_COMPANY):
            i = company_index * _ROLES_PER_COMPANY + slot
            role_cat, role_title, tags = _ROLES[i % len(_ROLES)]
            role = ROLES[role_cat]
            # 회사 강조 스킬 2개를 직무별로 어긋나게 집어 (회사, 직무)마다 요구/우대가 달라진다.
            required_skill = emphasis_skills[i % len(emphasis_skills)]
            preferred_skill = emphasis_skills[(i + 1) % len(emphasis_skills)]
            jobs.append({
                "id": i + 1,
                "company": company,
                "domain": domain,
                "role_category": role_cat,
                "title": f"[{company}] {role_title} — {required_skill}",
                "tags": list(dict.fromkeys(tags + [required_skill])),  # 회사 강조 스킬이 직무 태그와 겹치면 중복 제거
                "experience": _EXPERIENCE[i % len(_EXPERIENCE)],
                "employment": _EMPLOYMENT[(i // 2) % len(_EMPLOYMENT)],
                "location": "서울",
                "dday": "상시" if i % 4 == 0 else f"D-{(i % 25) + 1}",
                "source": _SOURCE[i % len(_SOURCE)],
                "match_reason": _MATCH[i % len(_MATCH)],
                "description": (
                    f"{company}에서 {required_skill} 영역을 맡을 {role_title}를 찾습니다. "
                    f"{COMPANIES[company]['info']}"
                ),
                "responsibilities": role["responsibilities"] + [f"{required_skill} 관련 과제 설계·개선"],
                "requirements": role["requirements"] + [f"{required_skill} 경험"],
                "preferred": role["preferred"] + [f"{preferred_skill} 경험"],
                "company_info": COMPANIES[company]["info"],
            })
    return jobs


_ALL_JOBS = _build_jobs()


def all_jobs() -> list[dict]:
    return _ALL_JOBS
