from fastapi import APIRouter

from app.companies import repository
from app.companies.schemas import CompanyAnalyzeRequest

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.post("/analyze")
async def analyze_company(req: CompanyAnalyzeRequest):
    return await repository.analyze(req.name)
