"""활성 소스 선택 — 키 있는 실 소스들, 하나도 없으면 목.

# ponytail: 여러 소스가 켜지면 결과를 단순 concat만 한다(회사×공고 중복 제거·병합은 범위 밖).
"""
from app.jobs.sources import jobkorea, mock, saramin, wanted
from app.jobs.sources.base import JobSource


def active_sources() -> list[JobSource]:
    real = [s for s in (saramin.get_source(), jobkorea.get_source(), wanted.get_source()) if s]
    return real or [mock.get_source()]
