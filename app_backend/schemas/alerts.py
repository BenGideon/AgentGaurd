from pydantic import BaseModel


class AlertCreate(BaseModel):
    name: str
    url: str
    events: list[str]
