from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app_backend.core.database import get_db
from app_backend.core.security import get_current_workspace_user
from app_backend.services import connectors_service

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.get("")
@router.get("/", include_in_schema=False)
def list_connectors(
    current: dict[str, Any] = Depends(get_current_workspace_user),
    db: Session = Depends(get_db),
):
    return connectors_service.list_connectors(db, current["workspace_id"])


@router.get("/gmail/connect")
def connect_gmail(current: dict[str, Any] = Depends(get_current_workspace_user)):
    return connectors_service.build_gmail_oauth_url(current["workspace_id"])


@router.get("/gmail/callback")
def gmail_oauth_callback(code: str, state: str, db: Session = Depends(get_db)):
    return RedirectResponse(connectors_service.handle_gmail_callback(db, code, state))


@router.delete("/gmail")
def disconnect_gmail(
    current: dict[str, Any] = Depends(get_current_workspace_user),
    db: Session = Depends(get_db),
):
    return connectors_service.delete_gmail_connector(db, current["workspace_id"])
