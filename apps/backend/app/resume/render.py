"""weasyprint 얇은 래퍼 — HTML 문자열 → PDF 바이트. state→HTML은 service가 담당."""
import os
import sys

if sys.platform == "darwin":
    _brew_lib = "/opt/homebrew/lib"
    if os.path.isdir(_brew_lib):
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
            _brew_lib + os.pathsep + os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        ).rstrip(os.pathsep)

from weasyprint import HTML


def html_to_pdf(html: str) -> bytes:
    return HTML(string=html).write_pdf()
