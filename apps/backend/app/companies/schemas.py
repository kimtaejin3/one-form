from pydantic import BaseModel


class CompanyAnalyzeRequest(BaseModel):
    name: str
