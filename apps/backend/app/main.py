from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.companies.router import router as companies_router
from app.essays.router import router as essays_router
from app.forms.router import router as forms_router
from app.jobs.router import router as jobs_router
from app.notifications.router import router as notifications_router
from app.profile.router import router as profile_router
from app.resume.router import router as resume_router

app = FastAPI(title="one-form API")

# ponytail: CORS 허용 포트는 landing/web 포트와 결합. 포트 바꾸면 여기도 같이.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # landing
        "http://localhost:3001",  # web
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


for r in (
    jobs_router,
    profile_router,
    resume_router,
    companies_router,
    essays_router,
    notifications_router,
    forms_router,
):
    app.include_router(r)
