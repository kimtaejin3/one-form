"""공식 홈페이지 수집기.

# ponytail: 도메인은 큐레이션 맵이다. 검색엔진으로 추측하면 엉뚱한 회사를 '공식(primary)'
#   출처로 단정할 위험이 있다 — 모르는 기업은 사용자가 URL을 넣게 하고(manual) 여기선 건너뛴다.
#   아래 도메인은 전부 실제로 응답과 <title>을 확인해 채택했다. 추가할 때도 같은 방식으로.
"""
from app.companies.schemas import SourceKind, TrustLevel
from app.companies.sources import base
from app.companies.sources.base import SourceDocument

# 키는 service.normalize()를 통과한 형태(소문자·공백 제거·법인 접미사 제거)여야 한다.
# 값은 지주/법인 사이트를 우선한다 — 제품 사이트보다 기업 정보가 많다(navercorp > naver).
DOMAINS = {
    # 대기업·제조·통신
    "삼성전자": "samsung.com",
    "삼성sds": "samsungsds.com",
    "lg전자": "lge.com",
    "lgcns": "lgcns.com",
    "sk하이닉스": "skhynix.com",
    "sk텔레콤": "sktelecom.com",
    "skt": "sktelecom.com",
    "kt": "kt.com",
    "lg유플러스": "lguplus.com",
    "현대자동차": "hyundai.com",
    "기아": "kia.com",
    "포스코": "posco.co.kr",
    # 플랫폼·커머스
    "네이버": "navercorp.com",
    "네이버웹툰": "webtoonscorp.com",
    "카카오": "kakaocorp.com",
    "라인": "linecorp.com",
    "라인플러스": "linecorp.com",
    "쿠팡": "coupang.com",
    "우아한형제들": "woowahan.com",
    "배달의민족": "woowahan.com",
    "배민": "woowahan.com",
    "당근": "daangn.com",
    "당근마켓": "daangn.com",
    "무신사": "musinsa.com",
    "컬리": "kurly.com",
    "마켓컬리": "kurly.com",
    "버킷플레이스": "bucketplace.com",
    "오늘의집": "bucketplace.com",
    "야놀자": "yanolja.com",
    "여기어때": "gccompany.co.kr",
    "여기어때컴퍼니": "gccompany.co.kr",
    "직방": "zigbang.com",
    "쏘카": "socar.kr",
    "리디": "ridicorp.com",
    "티맵모빌리티": "tmapmobility.com",
    # 핀테크
    "토스": "toss.im",
    "비바리퍼블리카": "toss.im",
    "두나무": "dunamu.com",
    "카카오뱅크": "kakaobank.com",
    "카카오페이": "kakaopay.com",
    # 게임·엔터
    "넥슨": "nexon.com",
    "엔씨소프트": "ncsoft.com",
    "넷마블": "netmarble.com",
    "크래프톤": "krafton.com",
    "스마일게이트": "smilegate.com",
    "펄어비스": "pearlabyss.com",
    "하이브": "hybecorp.com",
    # B2B·글로벌
    "센드버드": "sendbird.com",
    "몰로코": "moloco.com",
    "하이퍼커넥트": "hyperconnect.com",
}


def domain_for(normalized_name: str) -> str:
    return DOMAINS.get(normalized_name, "")


class OfficialSiteSource:
    name = "official"

    async def collect(self, query: dict) -> list[SourceDocument]:
        domain = domain_for(query["normalized_name"])
        if not domain:
            return []  # 모르는 도메인 — 실패가 아니라 '수집 없음'
        return [
            await base.fetch(
                f"https://{domain}",
                kind=SourceKind.official_site,
                trust_level=TrustLevel.primary,
            )
        ]
