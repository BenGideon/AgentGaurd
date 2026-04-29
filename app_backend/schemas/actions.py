from typing import Any

from pydantic import BaseModel


class ActionCreate(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] | None = None
    executor_type: str = "mock"
    risk_level: str = "medium"


class ActionCallCreate(BaseModel):
    action: str
    input: dict[str, Any]
