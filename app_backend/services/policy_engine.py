import os
from typing import Any

from sqlalchemy.orm import Session

from app_backend.models.models import Action, ActionPolicy, Agent


def is_external_recipient(input_data: dict[str, Any]) -> bool:
    domain = os.getenv("WORKSPACE_EMAIL_DOMAIN", "").strip().lower()
    if not domain:
        return True

    recipient = str(input_data.get("to") or input_data.get("recipient") or input_data.get("email") or "")
    if "@" not in recipient:
        return False
    recipient_domain = recipient.rsplit("@", 1)[-1].lower()
    return recipient_domain != domain


def policy_conditions_match(
    conditions: dict[str, Any] | None,
    action: Action,
    input_data: dict[str, Any],
    risk_level: str,
) -> bool:
    if not conditions:
        return True

    if "risk_level" in conditions and conditions["risk_level"] != risk_level:
        return False

    if "method" in conditions:
        if str(input_data.get("method", "")).upper() != str(conditions["method"]).upper():
            return False

    if "amount_gt" in conditions:
        try:
            if float(input_data.get("amount", 0)) <= float(conditions["amount_gt"]):
                return False
        except (TypeError, ValueError):
            return False

    if "recipient_external" in conditions:
        if is_external_recipient(input_data) != bool(conditions["recipient_external"]):
            return False

    return True


def policy_match_to_dict(policy: ActionPolicy | None) -> dict[str, Any] | None:
    if not policy:
        return None
    return {
        "policy_id": policy.id,
        "effect": policy.effect,
        "matched_conditions": policy.conditions or {},
        "priority": policy.priority,
    }


def evaluate_policy(
    agent: Agent,
    action: Action,
    input_data: dict[str, Any],
    risk_level: str,
    db: Session,
) -> tuple[str, dict[str, Any] | None]:
    policies = (
        db.query(ActionPolicy)
        .filter(
            ActionPolicy.workspace_id == agent.workspace_id,
            ActionPolicy.agent_id == agent.id,
            ActionPolicy.action_name == action.name,
        )
        .order_by(ActionPolicy.priority.desc(), ActionPolicy.id.asc())
        .all()
    )

    for policy in policies:
        if policy_conditions_match(policy.conditions, action, input_data, risk_level):
            return policy.effect, policy_match_to_dict(policy)

    return "block", None
