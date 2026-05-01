from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app_backend.core.database import get_db
from app_backend.core.security import get_current_workspace_user
from app_backend.schemas.simulator import SimulationRequest
from app_backend.services import simulator_service

router = APIRouter(prefix="/simulate", tags=["simulate"])


@router.post("")
@router.post("/", include_in_schema=False)
def simulate(
    request: SimulationRequest,
    context: dict = Depends(get_current_workspace_user),
    db: Session = Depends(get_db),
):
    return simulator_service.simulate_action(
        db,
        context["workspace_id"],
        request.agent_id,
        request.action,
        request.input,
    )
