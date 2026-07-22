# ponytail: 목 — 실제 크롤링(§4.4/§4.5) 대신 현실적인 공고 100개를 생성.
# 실제 구현 시 all_jobs()를 pgvector 검색 쿼리로 교체.
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


def all_jobs() -> list[dict]:
    return _ALL_JOBS
