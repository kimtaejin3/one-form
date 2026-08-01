from typing import Protocol


class ProfileExtractor(Protocol):
    """PDF 텍스트 페이지를 마스터 프로필 초안으로 바꾸는 교체 가능한 포트."""

    version: str

    def extract(self, pages: list[str]) -> dict: ...
