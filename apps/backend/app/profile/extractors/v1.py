"""v1: 모든 텍스트형 PDF에 적용되는 보수적 연락처·링크 추출기."""
import re

from app.profile.extractors.profile import empty_profile

_EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_PHONE = re.compile(r"(?:\+82[- ]?)?01[016789][- ]?\d{3,4}[- ]?\d{4}")
_URL = re.compile(r"https?://[^\s)>]+", re.IGNORECASE)


def add_links(profile: dict, text: str) -> None:
    urls = list(dict.fromkeys(_URL.findall(text)))

    def label(url: str) -> str:
        host = url.lower()
        if "github.com" in host:
            return "GitHub"
        if "linkedin.com" in host:
            return "LinkedIn"
        if "notion" in host:
            return "Notion"
        return "포트폴리오"

    profile["links"] = [{"label": label(url), "url": url} for url in urls]


class V1ProfileExtractor:
    version = "v1"

    def extract(self, pages: list[str]) -> dict:
        text = "\n".join(pages)
        profile = empty_profile()
        email = _EMAIL.search(text)
        phone = _PHONE.search(text)
        profile["personal"]["email"] = email.group(0) if email and "*" not in email.group(0) else ""
        profile["personal"]["phone"] = phone.group(0) if phone and "*" not in phone.group(0) else ""
        name = re.search(r"(?im)^\s*(?:이름|성명|name)\s*[:：]\s*([^\n]+)$", text)
        if name:
            profile["personal"]["name"] = name.group(1).strip()
        if not profile["personal"]["name"]:
            for line in text.splitlines()[:8]:
                candidate = re.fullmatch(r"\s*([가-힣]{2,5})\s*", line)
                if candidate:
                    profile["personal"]["name"] = candidate.group(1)
                    break
        add_links(profile, text)
        return profile
