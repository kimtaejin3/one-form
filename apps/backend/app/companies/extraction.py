"""HTML 본문·제목·발행일 추출.

# ponytail: readability/bs4 대신 stdlib html.parser. 본문 추출 품질이 문제되면
#   그때 trafilatura를 넣는다 — 지금 필요한 건 "제목 + 읽을 수 있는 텍스트"뿐.
"""
from dataclasses import dataclass, field
from datetime import datetime
from html.parser import HTMLParser

_SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}
_BLOCK_TAGS = {"p", "div", "section", "article", "li", "br", "h1", "h2", "h3", "h4", "tr"}
MAX_TEXT_CHARS = 20_000  # LLM 프롬프트에 넣을 상한


@dataclass
class ExtractedDoc:
    title: str = ""
    text: str = ""
    published_at: datetime | None = None
    headings: list[str] = field(default_factory=list)


def _parse_date(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class _Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.doc = ExtractedDoc()
        self._skip = 0
        self._in_title = False
        self._in_heading = False
        self._chunks: list[str] = []
        self._description = ""

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag in _SKIP_TAGS:
            self._skip += 1
        elif tag == "title":
            self._in_title = True
        elif tag in {"h1", "h2", "h3"}:
            self._in_heading = True
            self._chunks.append("\n")
        elif tag in _BLOCK_TAGS:
            self._chunks.append("\n")
        elif tag == "meta":
            self._handle_meta(attr)
        elif tag == "time" and self.doc.published_at is None:
            self.doc.published_at = _parse_date(attr.get("datetime") or "")

    def _handle_meta(self, attr: dict) -> None:
        key = (attr.get("property") or attr.get("name") or "").lower()
        content = attr.get("content", "").strip()
        if not content:
            return
        if key in {"description", "og:description"} and not self._description:
            self._description = content
        elif key in {"article:published_time", "og:updated_time", "date"}:
            if self.doc.published_at is None:
                self.doc.published_at = _parse_date(content)

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS:
            self._skip = max(0, self._skip - 1)
        elif tag == "title":
            self._in_title = False
        elif tag in {"h1", "h2", "h3"}:
            self._in_heading = False

    def handle_data(self, data):
        if self._skip:
            return
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self.doc.title = (self.doc.title + " " + text).strip()
            return
        if self._in_heading and len(self.doc.headings) < 40:
            self.doc.headings.append(text)
        self._chunks.append(text)

    def finish(self) -> ExtractedDoc:
        # meta description을 본문 맨 앞에 — 요약 근거로 가장 밀도가 높다.
        body = " ".join(self._chunks).replace("\n ", "\n")
        lines = [ln.strip() for ln in body.split("\n")]
        joined = "\n".join(ln for ln in lines if ln)
        self.doc.text = ((self._description + "\n" + joined) if self._description else joined)[
            :MAX_TEXT_CHARS
        ]
        return self.doc


def extract_html(html: str) -> ExtractedDoc:
    parser = _Extractor()
    parser.feed(html)
    parser.close()
    return parser.finish()
