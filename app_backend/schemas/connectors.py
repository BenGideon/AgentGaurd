from datetime import datetime

from pydantic import BaseModel


class ConnectorResponse(BaseModel):
    provider: str
    connected: bool
    connected_email: str | None = None
    expires_at: datetime | None = None
