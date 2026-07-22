from fastapi import APIRouter

from app.forms import repository

router = APIRouter(prefix="/api/forms", tags=["forms"])


@router.post("/convert")
async def convert_form():
    return await repository.convert_form()
