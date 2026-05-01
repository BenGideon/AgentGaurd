from typing import Any

from pydantic import BaseModel


class SimulationRequest(BaseModel):
    agent_id: str
    action: str
    input: dict[str, Any] = {}
