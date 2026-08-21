"""weasyprint 얇은 래퍼 — HTML 문자열 → PDF 바이트. state→HTML은 service가 담당."""
import os
import sys

if sys.platform == "darwin":
    # cffi's dlopen doesn't search Homebrew's lib dir by default on macOS, so
    # weasyprint's native libs (libgobject 등) fail to load without this.
    # Prepend the Homebrew prefixes (arm64 /opt/homebrew, Intel /usr/local).
    for _lib in ("/opt/homebrew/lib", "/usr/local/lib"):
        if os.path.isdir(_lib):
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
                _lib + os.pathsep + os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
            ).rstrip(os.pathsep)

from weasyprint import HTML


def html_to_pdf(html: str) -> bytes:
    return HTML(string=html).write_pdf()
