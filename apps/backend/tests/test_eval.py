"""eval 스모크 — 목 임베더로 관련 공고가 상위 k에 올라오는지."""
import asyncio

from scripts.eval_matching import run_eval


def test_recall_at_k():
    result = asyncio.run(run_eval(k=3))
    assert result["recall"] >= 0.66  # 관련 3건 중 2건 이상이 상위 3위 안에
