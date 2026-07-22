from pydantic import BaseModel


class Connection(BaseModel):
    company: str
    role: str


class Activity(BaseModel):
    id: int
    name: str
    category: str
    organizer: str
    period: str
    dday: str
    fit: int
    fills_gap: list[str]
    expected_experience: str
    connections: list[Connection]
