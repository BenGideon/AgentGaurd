from typing import Any

from pydantic import BaseModel


class ToolCreate(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] | None = None


class ToolCallCreate(BaseModel):
    tool: str
    input: dict[str, Any]
