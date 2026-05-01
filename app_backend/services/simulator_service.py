from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_backend.models.models import Action, Agent
from app_backend.services.policy_engine import evaluate_policy
from app_backend.services.risk_engine import calculate_risk


def _format_matched_policy(policy_match: dict[str, Any] | None) -> dict[str, Any] | None:
    if not policy_match:
        return None
    return {
        "policy_id": policy_match.get("policy_id"),
        "effect": policy_match.get("effect"),
        "conditions": policy_match.get("matched_conditions") or {},
        "priority": policy_match.get("priority"),
    }


def _build_reason(decision: str, matched_policy: dict[str, Any] | None) -> str:
    if not matched_policy:
        return "No matching policy; default block"

    conditions = matched_policy.get("conditions") or {}
    if not conditions:
        return f"Policy {matched_policy.get('policy_id')} matched without conditions"

    parts = [f"{key} = {value}" for key, value in conditions.items()]
    return "; ".join(parts) or f"Policy effect = {decision}"


def simulate_action(
    db: Session,
    workspace_id: str,
    agent_id: str,
    action_name: str,
    input_data: dict[str, Any],
) -> dict[str, Any]:
    agent = (
        db.query(Agent)
        .filter(Agent.workspace_id == workspace_id, Agent.id == agent_id)
        .first()
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    action = (
        db.query(Action)
        .filter(Action.workspace_id == workspace_id, Action.name == action_name)
        .first()
    )
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    risk_level = calculate_risk(action, input_data)
    decision, policy_match = evaluate_policy(agent, action, input_data, risk_level, db)
    matched_policy = _format_matched_policy(policy_match)

    return {
        "decision": decision,
        "risk_level": risk_level,
        "matched_policy": matched_policy,
        "reason": _build_reason(decision, matched_policy),
    }
