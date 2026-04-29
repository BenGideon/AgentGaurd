from pydantic import BaseModel


class SecretCreate(BaseModel):
    name: str
    value: str
    description: str | None = None
