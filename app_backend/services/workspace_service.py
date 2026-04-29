from sqlalchemy.orm import Session

from app_backend.models.models import Workspace


def ensure_workspace(db: Session, workspace_id: str) -> Workspace:
    workspace = db.get(Workspace, workspace_id)
    if workspace:
        return workspace

    workspace = Workspace(id=workspace_id, name=workspace_id)
    db.add(workspace)
    db.flush()
    return workspace


def get_or_create_workspace(db: Session, workspace_id: str) -> Workspace:
    workspace = db.get(Workspace, workspace_id)
    if workspace:
        return workspace
    workspace = Workspace(id=workspace_id, name=workspace_id)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace
