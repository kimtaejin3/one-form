"""마스터 프로필 유스케이스: PDF 텍스트 추출, 초안 구성, 저장.

PDF 레이아웃은 작성 도구마다 달라 정규식으로 모든 항목을 완벽히 구조화할 수 없다.
확실한 연락처·링크만 자동 반영하고, 나머지는 사용자가 편집할 수 있는 빈 구조로 제공한다.
"""
from __future__ import annotations

from app.core.config import settings
from app.core.pdf import (  # noqa: F401 — 상수는 기존 임포트 호환
    MAX_FILE_SIZE,
    MAX_PAGES,
    pdf_pages,
    pdf_photo_data_url,
)
from app.profile.extractors import get_profile_extractor
from app.profile import repository


def profile_from_pdf(pdf_bytes: bytes) -> dict:
    profile = get_profile_extractor(settings.RESUME_EXTRACTOR_VERSION).extract(pdf_pages(pdf_bytes))
    profile["personal"]["photo"] = pdf_photo_data_url(pdf_bytes)
    return profile


def _filled_count(value: object) -> int:
    if isinstance(value, dict):
        return sum(_filled_count(item) for item in value.values())
    if isinstance(value, list):
        return len(value) + sum(_filled_count(item) for item in value)
    return int(bool(value))


async def upload_resume(pdf_bytes: bytes, filename: str) -> dict:
    profile = profile_from_pdf(pdf_bytes)
    await repository.save_profile(profile)
    parsed_fields = _filled_count(profile)
    return {
        "profile": profile,
        "parsed_fields": parsed_fields,
        "message": f"{filename}에서 {parsed_fields}개 항목을 추출했습니다. 내용을 확인하고 보완해 주세요.",
    }


async def update_profile(profile: dict) -> dict:
    return await repository.save_profile(profile)
