from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app_backend.core.database import get_db
from app_backend.schemas.secrets import SecretCreate
from app_backend.services import secrets_service
from app_backend.services.workspace_service import get_or_create_workspace

router = APIRouter(prefix="/secrets", tags=["secrets"])


def get_workspace_id(x_workspace_id: str | None = Header(default=None, alias="x-workspace-id")) -> str:
    return x_workspace_id or "default"


@router.post("")
@router.post("/", include_in_schema=False)
def create_secret(
    secret: SecretCreate,
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
):
    get_or_create_workspace(db, workspace_id)
    return secrets_service.create_secret(db, workspace_id, secret)


@router.get("")
@router.get("/", include_in_schema=False)
def list_secrets(workspace_id: str = Depends(get_workspace_id), db: Session = Depends(get_db)):
    return secrets_service.list_secrets(db, workspace_id)


@router.delete("/{name}")
def delete_secret(name: str, workspace_id: str = Depends(get_workspace_id), db: Session = Depends(get_db)):
    return secrets_service.delete_secret(db, workspace_id, name)
