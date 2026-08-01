"""추출기 레지스트리. 새 버전은 클래스를 추가하고 여기만 등록하면 된다."""
from app.profile.extractors.base import ProfileExtractor
from app.profile.extractors.v1 import V1ProfileExtractor
from app.profile.extractors.v2 import V2ProfileExtractor

_EXTRACTORS: dict[str, ProfileExtractor] = {
    "v1": V1ProfileExtractor(),
    "v2": V2ProfileExtractor(),
}


def get_profile_extractor(version: str) -> ProfileExtractor:
    try:
        return _EXTRACTORS[version]
    except KeyError as exc:
        raise ValueError(f"지원하지 않는 이력서 추출기 버전입니다: {version}") from exc
