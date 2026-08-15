"""PDF 바이트 → 페이지별 텍스트. 이력서(profile)와 채용공고(companies)가 함께 쓴다.

# ponytail: layout 모드는 표에서 좌표 순서를 보존한다 — 이력서에선 이름이 학력보다 앞에
#   오는지가, 공고에선 '자격요건/우대사항' 열이 섞이지 않는지가 여기서 갈린다.
"""
from io import BytesIO

from pypdf import PdfReader

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_PAGES = 30


def pdf_pages(pdf_bytes: bytes) -> list[str]:
    """페이지 텍스트 리스트. 인용 위치를 살리려고 페이지 경계를 합치지 않는다."""
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
        pages = [page.extract_text(extraction_mode="layout") or "" for page in reader.pages]
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(
            "읽을 수 없는 PDF입니다. 암호화 또는 이미지형 PDF인지 확인해 주세요."
        ) from exc

    if not any(page.strip() for page in pages):
        raise ValueError("텍스트를 추출할 수 없는 PDF입니다. 텍스트형 PDF를 업로드해 주세요.")
    return pages
