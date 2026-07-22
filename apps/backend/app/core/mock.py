import asyncio

# ponytail: 목 단계 — DB 없이 1초 지연 후 더미 응답. 실제 구현 시 repository에서 mock() 호출만 제거.
MOCK_DELAY_SECONDS = 1.0


async def mock(data):
    await asyncio.sleep(MOCK_DELAY_SECONDS)
    return data
