from app.core.mock import mock
from app.jobs import repository
from app.jobs.schemas import JobFeed


async def get_job_feed(
    page: int, size: int, role: str, experience: str, employment: str, location: str
) -> JobFeed:
    filtered = [
        j for j in repository.all_jobs()
        if (not role or j["role_category"] == role)
        and (not experience or j["experience"] == experience)
        and (not employment or j["employment"] == employment)
        and (not location or j["location"] == location)
    ]
    start = (page - 1) * size
    jobs = [
        {
            "id": j["id"],
            "company": j["company"],
            "domain": j["domain"],
            "conditions": f"{j['experience']} · {j['employment']} · {j['location']}",
            "title": j["title"],
            "tags": j["tags"],
            "dday": j["dday"],
            "source": j["source"],
            "match_reason": j["match_reason"],
        }
        for j in filtered[start:start + size]
    ]
    feed = JobFeed(role="백엔드 개발", total=len(filtered), page=page, size=size, jobs=jobs)
    return await mock(feed)
