"""버전별 이력서 추출 전략의 공개 진입점."""

from app.profile.extractors.registry import get_profile_extractor

__all__ = ["get_profile_extractor"]
