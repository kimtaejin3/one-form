"""Llm 포트 + Anthropic(실)/목 어댑터. ANTHROPIC_API_KEY가 있으면 실, 없으면 목.

목은 실 전송(httpx)을 모듈 로드 시 건드리지 않는다 — 키·네트워크 없이 CI 통과.
"""
import re
from typing import Protocol

from app.core.config import settings

_PROMPT = (
    "지원자 프로필과 채용공고를 비교해 매칭률(0~100)과 한 문장 근거를 한국어로 답하라.\n"
    "근거에는 아래 '겹치는 스킬' 중 이 공고에 특징적인 것을 구체적으로 언급하라"
    "(직무 공통 스킬만 나열하지 말 것).\n"
    "형식: 첫 줄 숫자만, 둘째 줄 근거 한 문장.\n"
    "임베딩 기반 기초 매칭률: {base_rate}\n"
    "겹치는 스킬(프로필 ∩ 자격요건·우대): {matched}\n\n"
    "[프로필]\n{profile_text}\n\n[공고]\n{job_text}"
)


class Llm(Protocol):
    async def refine(
        self, profile_text: str, job_text: str, base_rate: int, matched: list[str]
    ) -> tuple[int, str]: ...


class MockLlm:
    async def refine(
        self, profile_text: str, job_text: str, base_rate: int, matched: list[str]
    ) -> tuple[int, str]:
        # 겹치는 스킬 수만큼 소폭 보정(최대 +5) — 결정적, 0~100 유지.
        rate = max(0, min(100, base_rate + min(len(matched), 5)))
        if matched:
            # matched는 세부 스킬이 앞(service._matched_skills) — 공고마다 다른 근거가 나온다.
            reason = f"프로필의 {' · '.join(matched[:3])} 역량이 이 공고의 요구와 맞습니다"
        else:
            reason = "요구 스킬과 직접 겹치는 경험은 적지만 도메인 경험이 인접합니다"
        return rate, reason


class AnthropicLlm:
    """Claude Messages API. 공식 SDK 대신 httpx 직접 호출."""

    URL = "https://api.anthropic.com/v1/messages"
    MODEL = "claude-opus-5"

    def __init__(self, api_key: str):
        self._api_key = api_key

    async def refine(
        self, profile_text: str, job_text: str, base_rate: int, matched: list[str]
    ) -> tuple[int, str]:
        import httpx  # lazy — 목 경로에선 로드되지 않는다

        prompt = _PROMPT.format(
            base_rate=base_rate,
            matched=" · ".join(matched) or "없음",
            profile_text=profile_text,
            job_text=job_text,
        )
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                self.URL,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": self.MODEL,
                    # 사고(thinking)가 기본 on이라 max_tokens는 사고+본문 합계 — 넉넉히.
                    "max_tokens": 1024,
                    "output_config": {"effort": "low"},
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            res.raise_for_status()
            body = res.json()
        if body.get("stop_reason") == "refusal":
            return base_rate, "매칭 근거를 생성하지 못했습니다"
        # content[0]은 thinking 블록일 수 있다 — text 블록만 고른다.
        text = next(
            (b["text"] for b in body["content"] if b["type"] == "text"), ""
        ).strip()
        head, _, tail = text.partition("\n")
        digits = re.sub(r"\D", "", head)
        rate = max(0, min(100, int(digits))) if digits else base_rate
        return rate, (tail.strip() or head.strip())


def get_llm() -> Llm:
    return AnthropicLlm(settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else MockLlm()
