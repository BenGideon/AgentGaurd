from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app_backend.core.database import get_db
from app_backend.core.security import get_current_workspace_user, get_workspace_id
from app_backend.schemas.approvals import ApprovalInputUpdate
from app_backend.services import approval_service

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("")
@router.get("/", include_in_schema=False)
def get_approvals(
    status: str = "pending",
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
):
    return approval_service.list_approvals(db, workspace_id, status)


@router.put("/{approval_id}/input")
def update_approval_input(
    approval_id: int,
    update: ApprovalInputUpdate,
    current: dict[str, Any] = Depends(get_current_workspace_user),
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
):
    return approval_service.update_approval_input(db, workspace_id, approval_id, update.input, current)


@router.post("/{approval_id}/approve")
def approve_tool_call(
    approval_id: int,
    current: dict[str, Any] = Depends(get_current_workspace_user),
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
):
    return approval_service.approve_approval(db, workspace_id, approval_id, current)


@router.post("/{approval_id}/reject")
def reject_tool_call(
    approval_id: int,
    current: dict[str, Any] = Depends(get_current_workspace_user),
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
):
    return approval_service.reject_approval(db, workspace_id, approval_id, current)
