from typing import Any

from fastapi import APIRouter, Depends

from app_backend.core.security import get_current_workspace_user

router = APIRouter(tags=["me"])


@router.get("/me")
def get_me(current: dict[str, Any] = Depends(get_current_workspace_user)):
    user = current["user"]
    return {
        "id": user.id,
        "email": user.email,
        "workspace_id": current["workspace_id"],
        "role": current["role"],
    }
