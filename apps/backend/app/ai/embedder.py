"""Embedder 포트 + Voyage(실)/목 어댑터. VOYAGE_API_KEY가 있으면 실, 없으면 목.

목은 실 전송(httpx)을 모듈 로드 시 건드리지 않는다 — 키·네트워크 없이 CI 통과.
"""
import hashlib
import re
from math import sqrt
from typing import Protocol

from app.core.config import settings

# ponytail: 해시 bag-of-words 64차원. 같은 토큰이 겹치면 코사인이 오른다 — 의미 임베딩은 아니지만
# 결정적이고 키 없이 돈다. 실 품질이 필요하면 VOYAGE_API_KEY를 넣으면 된다.
DIM = 64
_TOKEN = re.compile(r"[0-9a-zA-Z가-힣+#.]+")


class Embedder(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


def cosine(a: list[float], b: list[float]) -> float:
    """순수 파이썬 코사인 — numpy 없이. 벡터 수백 개 규모라 이걸로 충분."""
    dot = sum(x * y for x, y in zip(a, b))
    na = sqrt(sum(x * x for x in a))
    nb = sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class MockEmbedder:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * DIM
        for token in _TOKEN.findall(text.lower()):
            # 내장 hash()는 프로세스마다 달라진다(PYTHONHASHSEED) — blake2b로 고정.
            digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
            vec[int.from_bytes(digest, "big") % DIM] += 1.0
        return vec


class VoyageEmbedder:
    """voyage-3 (한국어 지원). 공식 SDK 대신 httpx 직접 호출."""

    URL = "https://api.voyageai.com/v1/embeddings"

    def __init__(self, api_key: str):
        self._api_key = api_key

    async def embed(self, texts: list[str]) -> list[list[float]]:
        import httpx  # lazy — 목 경로에선 로드되지 않는다

        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.post(
                self.URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": "voyage-3", "input": texts, "input_type": "document"},
            )
            res.raise_for_status()
            return [item["embedding"] for item in res.json()["data"]]


class GeminiEmbedder:
    """Google Generative Language 임베딩(batchEmbedContents). Voyage와 같은 Embedder 포트.

    # ponytail: LLM과 같은 GEMINI_API_KEY를 쓴다 — 별도 Voyage 키 없이 의미 임베딩.
    """

    URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents"
    MODEL = "gemini-embedding-001"  # embedContent 지원, 3072차원

    def __init__(self, api_key: str):
        self._api_key = api_key

    async def embed(self, texts: list[str]) -> list[list[float]]:
        import httpx  # lazy — 목 경로에선 로드되지 않는다

        body = {
            "requests": [
                {"model": f"models/{self.MODEL}", "content": {"parts": [{"text": t}]}}
                for t in texts
            ]
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(
                    self.URL.format(model=self.MODEL),
                    params={"key": self._api_key},
                    json=body,
                )
                res.raise_for_status()
                return [e["values"] for e in res.json()["embeddings"]]
        except Exception:  # 임베딩 실패로 피드 전체가 죽지 않게 목으로 폴백
            return await MockEmbedder().embed(texts)


def _auto_embedder() -> str:
    """EMBEDDING_PROVIDER 미지정 시 키 있는 것 자동 선택."""
    if settings.VOYAGE_API_KEY:
        return "voyage"
    if settings.GEMINI_API_KEY:
        return "gemini"
    return "mock"


# 임베더 전환은 EMBEDDING_PROVIDER(env) 한 줄 또는 이 함수만 바꾸면 된다 — voyage·gemini 코드는 둘 다 산다.
def get_embedder() -> Embedder:
    """EMBEDDING_PROVIDER로 명시 선택(voyage/gemini/mock), 없으면 키 있는 것 자동."""
    provider = settings.EMBEDDING_PROVIDER or _auto_embedder()
    if provider == "voyage" and settings.VOYAGE_API_KEY:
        return VoyageEmbedder(settings.VOYAGE_API_KEY)
    if provider == "gemini" and settings.GEMINI_API_KEY:
        return GeminiEmbedder(settings.GEMINI_API_KEY)
    return MockEmbedder()
