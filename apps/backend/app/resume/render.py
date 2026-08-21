"""weasyprint 얇은 래퍼 — HTML 문자열 → PDF 바이트. state→HTML은 service가 담당."""
from weasyprint import HTML


def html_to_pdf(html: str) -> bytes:
    return HTML(string=html).write_pdf()
