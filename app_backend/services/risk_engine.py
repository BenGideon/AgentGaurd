from typing import Any

from app_backend.models.models import Action


def calculate_risk(action: Action, input_data: dict[str, Any]) -> str:
    action_name = action.name.lower()
    if "delete" in action_name:
        return "critical"
    if "refund" in action_name:
        return "high"

    if action.executor_type == "api_proxy":
        method = str(input_data.get("method", "")).upper()
        if method == "DELETE":
            return "critical"
        if method in ["POST", "PATCH", "PUT"]:
            return "medium"
        if method == "GET":
            return "low"

    if "email" in action_name or "gmail" in action_name:
        return "medium"
    return "low"
