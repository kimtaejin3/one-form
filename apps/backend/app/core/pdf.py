"""PDF 바이트 → 페이지별 텍스트. 이력서(profile)와 채용공고(companies)가 함께 쓴다.

# ponytail: layout 모드는 표에서 좌표 순서를 보존한다 — 이력서에선 이름이 학력보다 앞에
#   오는지가, 공고에선 '자격요건/우대사항' 열이 섞이지 않는지가 여기서 갈린다.
"""
from base64 import b64encode
from io import BytesIO
import logging
import re

from PIL import Image
from pypdf import PdfReader
from pypdf.generic._image_xobject import _xobj_to_image

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_PAGES = 30
MAX_PHOTO_BYTES = 2 * 1024 * 1024
MAX_PHOTO_PIXELS = 8_000_000
MAX_PHOTO_DECODE_PIXELS = 16_000_000
MAX_PHOTO_CANDIDATES = 8

_IMAGE_MIME = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}
_logger = logging.getLogger(__name__)
_FINAL_STARTXREF = re.compile(rb"startxref\s+(\d+)\s+%%EOF\s*$")


def _repair_final_startxref(pdf_bytes: bytes) -> bytes:
    match = _FINAL_STARTXREF.search(pdf_bytes)
    actual = pdf_bytes.rfind(b"\nxref\n") + 1
    pointer = int(match.group(1)) if match else -1
    pointer_object = re.match(rb"\s*(\d+)\s+\d+\s+obj\b", pdf_bytes[pointer:]) if pointer >= 0 else None
    final_section = pdf_bytes[actual:] if actual > 0 else b""
    final_xref = re.search(
        rb"^xref\n.*\ntrailer\s*<<(?P<trailer>.*?)>>\s*startxref\s+\d+\s+%%EOF\s*$",
        final_section,
        re.DOTALL,
    )
    root = re.search(rb"/Root\s+(\d+)\s+0\s+R", final_xref.group("trailer")) if final_xref else None
    target = pdf_bytes[pointer : pdf_bytes.find(b"endobj", pointer)] if pointer_object else b""
    target_is_root_catalog = bool(
        root
        and pointer_object
        and int(root.group(1)) == int(pointer_object.group(1))
        and re.search(rb"/Type\s*/Catalog\b", target)
    )
    final_single = re.search(rb"^xref\s+(\d+)\s+1\s+0*(\d+)\s+\d+\s+n\s+trailer", final_section)
    safe_incremental = bool(
        final_xref and final_single
        and b"/Prev" in final_xref.group("trailer")
        and target_is_root_catalog
        and int(final_single.group(1)) == int(pointer_object.group(1))
        and int(final_single.group(2)) == pointer
    )
    if (
        not match
        or actual <= 0
        or pointer == actual
        or not pointer_object
        or not final_xref
        or final_section.count(b"%%EOF") != 1
        or b"/XRefStm" in final_xref.group("trailer")
        or not target_is_root_catalog
        or (b"/Prev" in final_xref.group("trailer") and not safe_incremental)
    ):
        return pdf_bytes
    return pdf_bytes[: match.start(1)] + str(actual).encode() + pdf_bytes[match.end(1) :]


def _pdf_reader(pdf_bytes: bytes) -> PdfReader:
    try:
        return PdfReader(BytesIO(pdf_bytes))
    except Exception:
        repaired = _repair_final_startxref(pdf_bytes)
        if repaired == pdf_bytes:
            raise
        return PdfReader(BytesIO(repaired))


def _photo_candidates(page):
    candidates = []
    visited = set()

    def visit(container):
        resources = container.get("/Resources")
        if not resources or not (xobjects := resources.get_object().get("/XObject")):
            return
        for reference in xobjects.get_object().values():
            xobject = reference.get_object()
            marker = id(xobject)
            if marker in visited:
                continue
            visited.add(marker)
            if xobject.get("/Subtype") == "/Form":
                visit(xobject)
                continue
            if xobject.get("/Subtype") != "/Image":
                continue
            pixels = int(xobject.get("/Width", 0)) * int(xobject.get("/Height", 0))
            if 0 < pixels <= MAX_PHOTO_PIXELS:
                candidates.append((pixels, "xobject", xobject))

    visit(page)

    inline = []
    inline_pixels = 0
    inline_bytes = 0
    content = page.get_contents()
    for params, operator in content.operations if content is not None else []:
        if operator != b"INLINE IMAGE":
            continue
        settings = params["settings"]
        pixels = int(settings.get("/Width", settings.get("/W", 0))) * int(
            settings.get("/Height", settings.get("/H", 0))
        )
        data_size = len(params["data"])
        if pixels <= 0 or pixels > MAX_PHOTO_PIXELS or data_size > MAX_PHOTO_BYTES:
            inline = []
            break
        inline.append((pixels, "inline", f"~{len(inline)}~"))
        inline_pixels += pixels
        inline_bytes += data_size
    if inline_pixels <= MAX_PHOTO_PIXELS and inline_bytes <= MAX_PHOTO_BYTES:
        candidates.extend(inline)
    return sorted(candidates, key=lambda item: item[0], reverse=True)


def pdf_pages(pdf_bytes: bytes) -> list[str]:
    """페이지 텍스트 리스트. 인용 위치를 살리려고 페이지 경계를 합치지 않는다."""
    if not pdf_bytes:
        raise ValueError("비어 있는 파일입니다.")
    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise ValueError("PDF 파일은 10MB 이하만 업로드할 수 있습니다.")
    try:
        reader = _pdf_reader(pdf_bytes)
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


def pdf_photo_data_url(pdf_bytes: bytes) -> str:
    """첫 페이지 내장 이미지 중 가장 큰 브라우저 지원 이미지를 data URL로 반환한다."""
    try:
        # Pillow는 설정값의 2배부터 해제 폭탄을 거절하므로 8MP에서 막히게 절반을 지정한다.
        Image.MAX_IMAGE_PIXELS = MAX_PHOTO_PIXELS // 2
        reader = _pdf_reader(pdf_bytes)
        if reader.is_encrypted:
            reader.decrypt("")
        page = reader.pages[0]
        decoded_pixels = 0
        for index, (pixels, kind, candidate) in enumerate(_photo_candidates(page)):
            if index >= MAX_PHOTO_CANDIDATES or decoded_pixels + pixels > MAX_PHOTO_DECODE_PIXELS:
                break
            decoded_pixels += pixels
            try:
                if kind == "xobject":
                    extension, data, image = _xobj_to_image(candidate)
                    extension = extension.lstrip(".").lower()
                else:
                    image_file = page.images[candidate]
                    extension = image_file.name.rsplit(".", 1)[-1].lower()
                    data, image = image_file.data, image_file.image
            except Exception:
                _logger.info("PDF 내장 이미지 하나를 건너뜁니다.", exc_info=True)
                continue
            if (
                extension in _IMAGE_MIME
                and image.width * image.height <= MAX_PHOTO_PIXELS
                and len(data) <= MAX_PHOTO_BYTES
            ):
                encoded = b64encode(data).decode("ascii")
                return f"data:{_IMAGE_MIME[extension]};base64,{encoded}"
        return ""
    except Exception:
        _logger.info("PDF 사진 추출을 건너뜁니다.", exc_info=True)
        return ""  # 사진 추출 실패가 이력서 텍스트 파싱까지 막으면 안 된다.
