from typing import Any

from pydantic import BaseModel


class MCPToolCallCreate(BaseModel):
    name: str
    arguments: dict[str, Any]
