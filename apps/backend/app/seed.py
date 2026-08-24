"""python -m app.seed — 목데이터를 DB에 시드(멱등). DATABASE_URL 필요.

기존 목 dict/빌더를 시드 소스로 재사용.
"""
import asyncio

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.db import get_sessionmaker
from app.jobs.models import Job
from app.jobs.repository import _build_jobs
from app.notifications.models import Notification
from app.notifications.repository import _NOTIFICATIONS
from app.profile import repository as profile_repo
from app.profile.models import Profile


async def seed_profile(session) -> None:
    p = profile_repo._PROFILE
    await session.execute(
        pg_insert(Profile).values(
            id=1,
            registered=p["registered"],
            personal=p["personal"], links=p["links"], educations=p["educations"],
            awards=p["awards"], languages=p["languages"], certificates=p["certificates"],
            careers=p["careers"], projects=p["projects"], activities=p["activities"],
        ).on_conflict_do_nothing(index_elements=["id"])
    )


async def seed_jobs(session) -> None:
    for j in _build_jobs():
        await session.execute(
            pg_insert(Job).values(
                id=j["id"], company=j["company"], domain=j["domain"],
                role_category=j["role_category"], experience=j["experience"],
                employment=j["employment"], location=j["location"], title=j["title"],
                dday=j["dday"], source=j["source"], description=j["description"],
                company_info=j["company_info"], match_reason=j["match_reason"],
                tags=j["tags"], responsibilities=j["responsibilities"],
                requirements=j["requirements"], preferred=j["preferred"],
            ).on_conflict_do_nothing(index_elements=["id"])
        )


async def seed_notifications(session) -> None:
    for n in _NOTIFICATIONS:
        await session.execute(
            pg_insert(Notification).values(**n).on_conflict_do_nothing(index_elements=["id"])
        )


async def main() -> None:
    sm = get_sessionmaker()
    if sm is None:
        raise SystemExit("DATABASE_URL이 설정돼 있어야 시드할 수 있습니다.")
    async with sm() as session:
        await seed_profile(session)
        await seed_jobs(session)
        await seed_notifications(session)
        await session.commit()
    print("seed 완료")


if __name__ == "__main__":
    asyncio.run(main())
