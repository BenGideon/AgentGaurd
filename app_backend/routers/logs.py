from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app_backend.core.database import get_db
from app_backend.services.audit_service import list_logs

router = APIRouter(prefix="/logs", tags=["logs"])


def get_workspace_id(x_workspace_id: str | None = Header(default=None, alias="x-workspace-id")) -> str:
    return x_workspace_id or "default"


@router.get("")
@router.get("/", include_in_schema=False)
def get_logs(workspace_id: str = Depends(get_workspace_id), db: Session = Depends(get_db)):
    return list_logs(db, workspace_id)
