"""Llm 포트 + Gemini·Anthropic(실)/목 어댑터. 키 우선순위: GEMINI > ANTHROPIC > 목.

목은 실 전송(httpx)을 모듈 로드 시 건드리지 않는다 — 키·네트워크 없이 CI 통과.
"""
import json
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

    async def complete_json(self, prompt: str, schema: dict) -> dict:
        """JSON 스키마에 맞는 구조화 출력. 못 하면 빈 dict(호출부가 폴백한다).

        companies/analysis.py가 쓴다 — 목 어댑터는 사실을 지어내지 않으려고 {}를 준다.
        """
        ...


def _parse(text: str, base_rate: int) -> tuple[int, str]:
    """응답 파싱 — 첫 줄 숫자가 매칭률, 둘째 줄이 근거. 형식이 어긋나면 base_rate 유지."""
    head, _, tail = text.strip().partition("\n")
    digits = re.sub(r"\D", "", head)
    rate = max(0, min(100, int(digits))) if digits else base_rate
    return rate, (tail.strip() or head.strip())


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

    async def complete_json(self, prompt: str, schema: dict) -> dict:
        # 목은 기업 사실을 지어내지 않는다 — 구조화 실패로 알리고 호출부가 원문 요약으로 폴백.
        return {}


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
        text = next((b["text"] for b in body["content"] if b["type"] == "text"), "")
        return _parse(text, base_rate)

    async def complete_json(self, prompt: str, schema: dict) -> dict:
        """도구 강제 호출로 구조화 — 텍스트에서 JSON을 긁는 것보다 견고하다."""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                res = await client.post(
                    self.URL,
                    headers={"x-api-key": self._api_key, "anthropic-version": "2023-06-01"},
                    json={
                        "model": self.MODEL,
                        "max_tokens": 4096,
                        "tools": [
                            {"name": "emit", "description": "분석 결과", "input_schema": schema}
                        ],
                        "tool_choice": {"type": "tool", "name": "emit"},
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                res.raise_for_status()
                body = res.json()
            block = next(b for b in body["content"] if b["type"] == "tool_use")
            return block["input"]
        except Exception:
            return {}  # 분석 실패는 호출부가 partial로 표시한다


class GeminiLlm:
    """Google Generative Language API(generateContent). 공식 SDK 대신 httpx 직접 호출.

    # ponytail: 키는 표준 방식대로 query param(?key=)으로 보낸다. 발급받은 키가 AIza… 형식이
    #   아니면(OAuth·Vertex 액세스 토큰 등) 401/403이 난다 — 그땐 params={"key": …}를 빼고
    #   headers={"Authorization": f"Bearer {self._api_key}"}로 바꾸면 된다.
    """

    URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    MODEL = "gemini-flash-latest"  # -latest alias: 특정 버전 하드코딩이 폐기돼 404 나는 걸 피한다

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
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(
                    self.URL.format(model=self.MODEL),
                    params={"key": self._api_key},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        # 구조화 출력(JSON 스키마)으로 rate·reason을 강제 — 텍스트 형식 파싱은 취약해
                        # 마크다운·형식 지시문 에코가 섞였다. 3.x flash는 thinking이 기본 on이라
                        # 예산(사고+본문)을 넉넉히 줘야 JSON이 안 잘린다(thinkingBudget:0은 400).
                        "generationConfig": {
                            "maxOutputTokens": 2048,
                            "responseMimeType": "application/json",
                            "responseSchema": {
                                "type": "OBJECT",
                                "properties": {
                                    "rate": {"type": "INTEGER"},
                                    "reason": {"type": "STRING"},
                                },
                                "required": ["rate", "reason"],
                            },
                        },
                    },
                )
                res.raise_for_status()
                text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                obj = json.loads(text)
                rate = max(0, min(100, int(obj["rate"])))
                reason = str(obj["reason"]).strip()
                if not reason:
                    raise ValueError("빈 근거")
                return rate, reason
        except Exception:  # 인증·네트워크·응답 형태·파싱 실패 — 근거 하나 때문에 피드가 죽으면 안 된다
            return await MockLlm().refine(profile_text, job_text, base_rate, matched)

    async def complete_json(self, prompt: str, schema: dict) -> dict:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                res = await client.post(
                    self.URL.format(model=self.MODEL),
                    params={"key": self._api_key},
                    json={
                        # responseSchema는 Gemini 전용 표기라 JSON 스키마를 그대로 못 넘긴다 —
                        # 스키마는 프롬프트에 싣고 JSON MIME만 강제한다.
                        "contents": [
                            {
                                "parts": [
                                    {
                                        "text": f"{prompt}\n\n[출력 JSON 스키마]\n"
                                        f"{json.dumps(schema, ensure_ascii=False)}"
                                    }
                                ]
                            }
                        ],
                        "generationConfig": {
                            "maxOutputTokens": 8192,
                            "responseMimeType": "application/json",
                        },
                    },
                )
                res.raise_for_status()
                text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}


def get_llm() -> Llm:
    if settings.GEMINI_API_KEY:
        return GeminiLlm(settings.GEMINI_API_KEY)
    if settings.ANTHROPIC_API_KEY:
        return AnthropicLlm(settings.ANTHROPIC_API_KEY)
    return MockLlm()
