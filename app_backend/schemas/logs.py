from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    workspace_id: str
    agent_id: str
    status: str
    created_at: datetime
    action_name: str | None = None
    tool: str | None = None
    input: dict[str, Any] | None = None
