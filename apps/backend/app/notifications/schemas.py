from pydantic import BaseModel


class Notification(BaseModel):
    id: int
    type: str
    title: str
    message: str
    time: str
    unread: bool
