from pydantic import BaseModel


class DemoEmailRequest(BaseModel):
    email: str
    context: str
