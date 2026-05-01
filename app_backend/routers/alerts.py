from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app_backend.core.database import get_db
from app_backend.core.security import get_workspace_id
from app_backend.schemas.alerts import AlertCreate
from app_backend.services import alert_service
from app_backend.services.workspace_service import ensure_workspace

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("")
@router.post("/", include_in_schema=False)
def create_alert(
    alert: AlertCreate,
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
):
    ensure_workspace(db, workspace_id)
    return alert_service.create_alert(db, workspace_id, alert)


@router.get("")
@router.get("/", include_in_schema=False)
def list_alerts(workspace_id: str = Depends(get_workspace_id), db: Session = Depends(get_db)):
    return alert_service.list_alerts(db, workspace_id)


@router.delete("/{alert_id}")
def delete_alert(alert_id: int, workspace_id: str = Depends(get_workspace_id), db: Session = Depends(get_db)):
    return alert_service.delete_alert(db, workspace_id, alert_id)
