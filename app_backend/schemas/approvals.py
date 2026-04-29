from typing import Any

from pydantic import BaseModel


class ApprovalInputUpdate(BaseModel):
    input: dict[str, Any]
