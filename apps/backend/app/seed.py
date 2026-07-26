"""python -m app.seed — 목데이터를 DB에 시드(멱등). DATABASE_URL 필요.

기존 목 dict/빌더를 시드 소스로 재사용. 유저 상태(essay_answer)는 시드하지 않는다.
"""
import asyncio

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.db import get_sessionmaker
from app.essays import repository as essays_repo
from app.essays.models import EssayCompany, EssayQuestion


async def seed_essays(session) -> None:
    for q in essays_repo._QUESTIONS:
        await session.execute(
            pg_insert(EssayQuestion).values(**q).on_conflict_do_nothing(index_elements=["id"])
        )
    for c in essays_repo._COMPANIES:
        await session.execute(
            pg_insert(EssayCompany).values(
                name=c["name"], deadline=c["deadline"], question_ids=c["question_ids"]
            ).on_conflict_do_nothing(index_elements=["name"])
        )


async def main() -> None:
    sm = get_sessionmaker()
    if sm is None:
        raise SystemExit("DATABASE_URL이 설정돼 있어야 시드할 수 있습니다.")
    async with sm() as session:
        await seed_essays(session)
        await session.commit()
    print("seed 완료")


if __name__ == "__main__":
    asyncio.run(main())
