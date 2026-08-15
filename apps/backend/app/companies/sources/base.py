"""SourceProvider 포트 + 공용 HTTP 수집기.

수집기는 전부 SourceDocument로 통일한다(계획서 §4). 네트워크 정책(robots·timeout·
최대 크기)은 여기 한 곳 — provider마다 다시 쓰지 않는다.
"""
import asyncio
import hashlib
import ipaddress
import logging
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from app.companies.schemas import SourceKind, TrustLevel

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10.0
MAX_BYTES = 512 * 1024  # 본문 추출에 충분. 넘으면 잘라서 쓴다
MAX_REDIRECTS = 5
RETRIES = 1  # 일시적 오류 1회 재시도
RETRY_BACKOFF_SECONDS = 0.5

# ponytail: rate limiter 없음 — 분석 1회가 도메인당 요청 2~3건(robots + 본문)이고 결과는
#   24시간 캐시된다. 출처 provider가 늘어 한 도메인을 반복해서 때리게 되면 그때 넣는다.
# HTTP 헤더는 ASCII만 — 한글을 넣으면 httpx가 인코딩 단계에서 UnicodeEncodeError로 죽는다.
USER_AGENT = "one-form-bot/0.1 (+https://one-form.local; company research)"


@dataclass
class SourceDocument:
    url: str
    kind: SourceKind
    trust_level: TrustLevel
    title: str = ""
    publisher: str = ""
    text: str = ""
    published_at: datetime | None = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def content_hash(self) -> str:
        return hashlib.blake2b(self.text.encode(), digest_size=16).hexdigest()


class SourceProvider(Protocol):
    name: str

    async def collect(self, query: dict) -> list[SourceDocument]:
        """실패는 예외로 올린다 — service가 provider별로 잡아 warnings에 넣는다."""
        ...


def publisher_of(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.")


class BlockedUrlError(PermissionError):
    """SSRF 차단 — 사설/루프백/링크로컬 대상, 또는 http(s)가 아닌 스킴."""


async def assert_public_url(url: str) -> None:
    """수집 대상이 공인 인터넷 주소인지 확인한다.

    사용자가 URL을 직접 넣을 수 있으므로(manual provider) 내부망·클라우드 메타데이터
    (169.254.169.254)로 요청을 유도하는 SSRF를 여기서 막는다.

    # ponytail: 이름을 resolve해 검사한 뒤 httpx가 다시 resolve한다 — 그 사이 응답이 바뀌는
    #   DNS rebinding은 못 막는다. 막으려면 resolve한 IP로 직접 연결하고 Host 헤더를 세팅해야
    #   하는데, TLS SNI까지 손대야 해서 지금은 과하다. 내부망이 민감해지면 그때 IP 고정으로.
    """
    parts = urlparse(url)
    if parts.scheme not in {"http", "https"}:
        raise BlockedUrlError(f"http(s) URL이 아닙니다: {url}")
    host = parts.hostname
    if not host:
        raise BlockedUrlError(f"호스트가 없는 URL입니다: {url}")

    try:
        infos = await asyncio.to_thread(
            socket.getaddrinfo, host, None, 0, socket.SOCK_STREAM
        )
    except socket.gaierror as exc:
        raise BlockedUrlError(f"호스트를 찾을 수 없습니다: {host}") from exc

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        # is_global 하나로 사설(10/172.16/192.168)·루프백·링크로컬·예약 대역이 모두 걸린다.
        if not ip.is_global:
            raise BlockedUrlError(f"내부 주소로는 수집하지 않습니다: {host} → {ip}")


async def _robots_allows(client, url: str) -> bool:
    """robots.txt 준수(계획서 §6.3·§11). 못 읽으면 허용으로 본다(대부분 robots가 없다)."""
    parts = urlparse(url)
    try:
        res = await client.get(f"{parts.scheme}://{parts.netloc}/robots.txt")
        if res.status_code != 200:
            return True
        parser = RobotFileParser()
        parser.parse(res.text.splitlines())
        return parser.can_fetch(USER_AGENT, url)
    except Exception:
        return True


async def _get(client, url: str) -> tuple[str, bytes, str, str]:
    """리다이렉트를 직접 따라가며 매 홉을 SSRF 검사한다. → (최종 URL, 본문, 인코딩, content-type)"""
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        await assert_public_url(current)
        if not await _robots_allows(client, current):
            raise PermissionError(f"robots.txt가 수집을 금지합니다: {current}")
        async with client.stream("GET", current) as res:
            if res.is_redirect and res.headers.get("location"):
                current = str(res.url.join(res.headers["location"]))
                continue
            res.raise_for_status()
            body = b""
            async for chunk in res.aiter_bytes():
                body += chunk
                if len(body) >= MAX_BYTES:  # 최대 응답 크기 제한(§11)
                    break
            return (
                current,
                body,
                res.charset_encoding or "utf-8",
                res.headers.get("content-type", ""),
            )
    raise BlockedUrlError(f"리다이렉트가 너무 많습니다: {url}")


def _pdf_text(body: bytes) -> str:
    """페이지 번호를 남긴다 — 인용 위치를 잃지 않으려고(계획서 §6.3)."""
    from app.core.pdf import pdf_pages

    return "\n".join(
        f"[p.{number}] {text.strip()}"
        for number, text in enumerate(pdf_pages(body), start=1)
        if text.strip()
    )


async def fetch(url: str, kind: SourceKind, trust_level: TrustLevel) -> SourceDocument:
    """URL 하나를 SourceDocument로. HTML과 PDF를 다룬다.

    일시적 네트워크 오류는 한 번 재시도한다 — 공고 하나가 잠깐 흔들려 분석 전체가
    partial이 되면 사용자가 원인을 알 수 없다. 차단·robots·4xx는 재시도하지 않는다.
    """
    import httpx  # lazy — 목/오프라인 경로에선 로드되지 않는다

    from app.companies.extraction import extract_html

    async with httpx.AsyncClient(
        timeout=TIMEOUT_SECONDS,
        follow_redirects=False,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        for attempt in range(RETRIES + 1):
            try:
                final_url, body, encoding, content_type = await _get(client, url)
                break
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                retryable = isinstance(exc, httpx.TransportError) or (
                    isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500
                )
                if not retryable or attempt == RETRIES:
                    raise
                logger.info("수집 재시도 %s (%s)", url, type(exc).__name__)
                await asyncio.sleep(RETRY_BACKOFF_SECONDS)

    if "pdf" in content_type.lower() or body[:5] == b"%PDF-":
        text, title, published_at = _pdf_text(body), "", None
    else:
        parsed = extract_html(body.decode(encoding, errors="replace"))
        text, title, published_at = parsed.text, parsed.title, parsed.published_at

    # 다른 호스트로 넘어갔으면 '공식'이라고 못 한다 — 실제로 samsung.com이 대기열
    # 서비스(queue-it.net)로 리다이렉트한다. 남의 도메인 내용에 primary를 붙이면 거짓말이다.
    if trust_level is TrustLevel.primary and publisher_of(final_url) != publisher_of(url):
        trust_level = TrustLevel.secondary
        logger.info("리다이렉트로 호스트가 바뀌어 신뢰도를 낮춤 %s → %s", url, final_url)

    return SourceDocument(
        url=final_url,  # 최종 URL을 출처로 — 리다이렉트 전 주소를 남기면 인용이 어긋난다
        kind=kind,
        trust_level=trust_level,
        title=title,
        publisher=publisher_of(final_url),
        text=text,
        published_at=published_at,
    )
