from pydantic import BaseModel


class AgentCreate(BaseModel):
    id: str
    name: str
    api_key: str | None = None
