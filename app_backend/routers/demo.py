from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app_backend.core.config import settings
from app_backend.core.database import get_db
from app_backend.core.security import get_current_workspace_user, get_workspace_id
from app_backend.schemas.demo import DemoEmailRequest
from app_backend.services.demo_service import generate_demo_email, seed_demo_data

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/generate-email")
def generate_email(
    request: DemoEmailRequest,
    _context: dict = Depends(get_current_workspace_user),
    _db: Session = Depends(get_db),
):
    return generate_demo_email(request.email, request.context)


@router.get("/status")
def demo_status(workspace_id: str = Depends(get_workspace_id), db: Session = Depends(get_db)):
    seed_demo_data(db, workspace_id)
    return {
        "workspace_id": workspace_id,
        "demo_mode": not settings.OPENAI_API_KEY or settings.GMAIL_CONNECTOR_MODE.lower() == "mock",
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "gmail_mode": settings.GMAIL_CONNECTOR_MODE.lower(),
        "message": (
            "Running in demo mode (mock email + fallback AI)"
            if not settings.OPENAI_API_KEY or settings.GMAIL_CONNECTOR_MODE.lower() == "mock"
            else "Live AI and Gmail mode configured"
        ),
    }
