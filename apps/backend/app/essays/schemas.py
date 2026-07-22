from pydantic import BaseModel


class DraftRequest(BaseModel):
    essay_id: int
