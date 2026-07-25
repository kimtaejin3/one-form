"""매칭 랭킹 품질 오프라인 eval — 라벨 픽스처로 recall@k 측정.

MockEmbedder라 API 키·네트워크 없이 돈다. `uv run python -m scripts.eval_matching`
(apps/backend에서 — `-m`이라야 app 패키지가 import된다).
# ponytail: 픽스처 1건짜리 최소 eval — "관련 공고를 위로 올리는가"만 못박는다.
"""
import asyncio

from app.ai.embedder import MockEmbedder, cosine

PROFILE = (
    "백엔드 엔지니어 인턴 결제 실패율 개선 로그 파이프라인 재시도 정책 "
    "멱등성 처리 정산 배치 API Python FastAPI PostgreSQL Redis"
)

# (공고 텍스트, 관련 여부)
JOBS = [
    ("백엔드 개발자 결제 정산 API FastAPI PostgreSQL Redis Python", True),
    ("백엔드 개발자 대용량 트랜잭션 멱등성 처리 Python Redis", True),
    ("서버 엔지니어 결제 시스템 로그 파이프라인 재시도 정책", True),
    ("iOS 개발자 Swift SwiftUI 앱 UI 애니메이션", False),
    ("안드로이드 개발자 Kotlin Compose 모바일 화면", False),
    ("퍼블리셔 HTML CSS 마크업 반응형 웹 디자인", False),
]


async def run_eval(k: int = 3) -> dict:
    embedder = MockEmbedder()
    vectors = await embedder.embed([PROFILE] + [text for text, _ in JOBS])
    profile_vector, job_vectors = vectors[0], vectors[1:]

    ranked = sorted(
        zip(job_vectors, JOBS), key=lambda pair: -cosine(profile_vector, pair[0])
    )
    relevant_total = sum(1 for _, label in JOBS if label)
    hits = sum(1 for _, (_, label) in ranked[:k] if label)
    return {"k": k, "hits": hits, "relevant": relevant_total, "recall": hits / relevant_total}


if __name__ == "__main__":
    result = asyncio.run(run_eval())
    print(f"recall@{result['k']} = {result['recall']:.2f} ({result['hits']}/{result['relevant']})")
