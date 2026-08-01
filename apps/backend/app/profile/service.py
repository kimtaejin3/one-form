"""마스터 프로필 유스케이스: PDF 텍스트 추출, 초안 구성, 저장.

PDF 레이아웃은 작성 도구마다 달라 정규식으로 모든 항목을 완벽히 구조화할 수 없다.
확실한 연락처·링크만 자동 반영하고, 나머지는 사용자가 편집할 수 있는 빈 구조로 제공한다.
"""
from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from app.core.config import settings
from app.profile.extractors import get_profile_extractor
from app.profile import repository

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_PAGES = 30

def profile_from_pdf(pdf_bytes: bytes) -> dict:
    if not pdf_bytes:
        raise ValueError("비어 있는 파일입니다.")
    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise ValueError("PDF 파일은 10MB 이하만 업로드할 수 있습니다.")
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        if reader.is_encrypted:
            reader.decrypt("")
        if len(reader.pages) > MAX_PAGES:
            raise ValueError("PDF는 30페이지 이하만 업로드할 수 있습니다.")
        # pypdf의 layout 모드는 표에서 좌표 순서를 보존한다. 이름이 학력보다 앞에 오는 실제 이력서에 중요.
        pages = [page.extract_text(extraction_mode="layout") or "" for page in reader.pages]
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("읽을 수 없는 PDF입니다. 암호화 또는 이미지형 PDF인지 확인해 주세요.") from exc

    if not any(page.strip() for page in pages):
        raise ValueError("텍스트를 추출할 수 없는 PDF입니다. 텍스트형 PDF를 업로드해 주세요.")
    return get_profile_extractor(settings.RESUME_EXTRACTOR_VERSION).extract(pages)


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
