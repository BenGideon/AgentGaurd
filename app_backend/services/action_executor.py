from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_backend.core.config import settings
from app_backend.models.models import Action
from app_backend.models.models import Connector
from app_backend.services.api_proxy import execute_api_proxy
from app_backend.services.connectors_service import refresh_gmail_token


ActionExecutor = Callable[[Action, dict[str, Any]], dict[str, Any]]

BASE_DIR = Path(__file__).resolve().parents[2]


def require_input_fields(input_data: dict[str, Any], fields: list[str]) -> None:
    missing = [field for field in fields if not input_data.get(field)]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required input fields: {', '.join(missing)}")


def create_gmail_draft(
    input_data: dict[str, Any],
    db: Session | None = None,
    workspace_id: str = "default",
) -> dict[str, Any]:
    require_input_fields(input_data, ["to", "subject", "body"])

    to = input_data["to"]
    subject = input_data["subject"]
    body = input_data["body"]
    mode = settings.GMAIL_CONNECTOR_MODE.lower()

    if mode == "mock":
        return {
            "status": "success",
            "message": "Mock Gmail draft created",
            "draft": {
                "to": to,
                "subject": subject,
                "body": body,
            },
        }

    if mode != "live":
        return {
            "status": "error",
            "message": "GMAIL_CONNECTOR_MODE must be mock or live",
        }

    if db is not None:
        connector = (
            db.query(Connector)
            .filter(Connector.workspace_id == workspace_id, Connector.provider == "gmail")
            .first()
        )
        if not connector:
            return {"status": "error", "message": "Gmail not connected"}

        try:
            if connector.expires_at and connector.expires_at <= datetime.utcnow() + timedelta(minutes=2):
                connector = refresh_gmail_token(connector, db)

            from app_backend.services.gmail_service import create_draft_with_access_token

            draft = create_draft_with_access_token(
                connector.access_token,
                to=to,
                subject=subject,
                body=body,
            )
            return {
                "status": "success",
                "message": "Gmail draft created",
                "draft_id": draft.get("draft_id"),
                "metadata": draft.get("response"),
            }
        except HTTPException:
            raise
        except Exception as exc:
            return {
                "status": "error",
                "message": f"Gmail draft creation failed: {exc}",
            }

    if not (BASE_DIR / "credentials.json").exists():
        return {
            "status": "error",
            "message": "Gmail live mode requires credentials.json",
        }

    try:
        from app_backend.services.gmail_service import create_draft

        draft = create_draft(to=to, subject=subject, body=body)
        return {
            "status": "success",
            "message": "Gmail draft created",
            "draft_id": draft.get("draft_id"),
            "metadata": draft.get("response"),
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Gmail draft creation failed: {exc}",
        }


def execute_action(
    action: Action,
    input_data: dict[str, Any],
    db: Session | None = None,
    agent_id: str | None = None,
    workspace_id: str = "default",
) -> dict[str, Any]:
    if action.executor_type == "gmail_draft":
        return create_gmail_draft(input_data, db=db, workspace_id=workspace_id)
    if action.executor_type == "mock":
        return {
            "status": "success",
            "message": "Mock action executed",
            "action": action.name,
            "input": input_data,
        }
    if action.executor_type == "webhook":
        return {
            "status": "success",
            "message": "Webhook executor not implemented",
            "action": action.name,
            "input": input_data,
        }
    if action.executor_type == "api_proxy":
        if db is None:
            return {"status": "error", "message": "api_proxy executor requires database access"}
        return execute_api_proxy(
            input_data,
            db,
            agent_id=agent_id,
            action_name=action.name,
            workspace_id=workspace_id,
        )

    return {
        "status": "error",
        "message": f"Unknown action executor_type: {action.executor_type}",
    }


def send_email(input_data: dict[str, Any]) -> dict[str, Any]:
    print("Email sent", input_data)
    return {"status": "success", "message": "Email sent"}


def create_task(input_data: dict[str, Any]) -> dict[str, Any]:
    print("Task created", input_data)
    return {"status": "success", "message": "Task created"}


def update_customer_note(input_data: dict[str, Any]) -> dict[str, Any]:
    print("Note updated", input_data)
    return {"status": "success", "message": "Note updated"}


def delete_customer(input_data: dict[str, Any]) -> dict[str, Any]:
    print("Customer deleted", input_data)
    return {"status": "success", "message": "Customer deleted"}


FAKE_TOOLS = {
    "send_email": send_email,
    "create_task": create_task,
    "update_customer_note": update_customer_note,
    "delete_customer": delete_customer,
    "create_gmail_draft": create_gmail_draft,
}


def execute_tool(tool_name: str, input_data: dict[str, Any]) -> dict[str, Any] | None:
    tool = FAKE_TOOLS.get(tool_name)
    if not tool:
        raise HTTPException(status_code=400, detail=f"No fake implementation for tool '{tool_name}'")
    return tool(input_data)


def ensure_tool_result_success(tool_result: dict[str, Any] | None) -> None:
    if isinstance(tool_result, dict) and tool_result.get("status") == "error":
        raise HTTPException(status_code=400, detail=tool_result.get("message", "Tool failed"))
