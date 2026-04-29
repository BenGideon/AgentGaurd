from typing import Any

from sqlalchemy.orm import Session

from app_backend.models.models import Action, ActionPolicy, Agent
from app_backend.services.actions_service import process_action_call
from app_backend.services.tool_service import get_available_tools_for_agent, process_tool_call
from app_backend.utils.schema import normalize_input_schema


def get_available_actions_for_agent(agent: Agent, db: Session) -> list[dict[str, Any]]:
    policies = (
        db.query(ActionPolicy)
        .filter(
            ActionPolicy.workspace_id == agent.workspace_id,
            ActionPolicy.agent_id == agent.id,
            ActionPolicy.effect.in_(["allow", "approval_required"]),
        )
        .all()
    )
    policy_by_action = {policy.action_name: policy for policy in policies}
    if not policy_by_action:
        return []

    actions = (
        db.query(Action)
        .filter(Action.workspace_id == agent.workspace_id, Action.name.in_(policy_by_action.keys()))
        .order_by(Action.name)
        .all()
    )

    return [
        {
            "name": action.name,
            "description": action.description,
            "input_schema": action.input_schema,
            "executor_type": action.executor_type,
            "risk_level": action.risk_level,
            "access": policy_by_action[action.name].effect,
        }
        for action in actions
    ]


def list_mcp_tools(db: Session, agent: Agent) -> dict[str, list[dict[str, Any]]]:
    tool_entries = [
        {
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": normalize_input_schema(tool["input_schema"]),
            "access": tool["access"],
        }
        for tool in get_available_tools_for_agent(agent, db)
    ]
    action_entries = [
        {
            "name": action["name"],
            "description": action["description"],
            "inputSchema": normalize_input_schema(action["input_schema"]),
            "risk_level": action["risk_level"],
            "access": action["access"],
        }
        for action in get_available_actions_for_agent(agent, db)
    ]
    return {"tools": tool_entries + action_entries}


def call_mcp_tool(db: Session, agent: Agent, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    action = (
        db.query(Action)
        .filter(Action.name == tool_name, Action.workspace_id == agent.workspace_id)
        .first()
    )
    if action:
        result = process_action_call(agent, tool_name, arguments, db)

        if result["status"] == "completed":
            tool_result = result.get("result")
            return {
                "status": "completed",
                "risk_level": result.get("risk_level"),
                "policy_match": result.get("policy_match"),
                "tool_result": tool_result,
                "content": [
                    {
                        "type": "text",
                        "text": tool_result.get("message", "Action executed successfully")
                        if isinstance(tool_result, dict)
                        else "Action executed successfully",
                    }
                ],
            }

        if result["status"] == "pending_approval":
            return {
                "status": "pending_approval",
                "approval_id": result["approval_id"],
                "risk_level": result.get("risk_level"),
                "policy_match": result.get("policy_match"),
                "content": [
                    {
                        "type": "text",
                        "text": "Action requires human approval",
                    }
                ],
            }

        return {
            "status": "blocked",
            "risk_level": result.get("risk_level"),
            "policy_match": result.get("policy_match"),
            "content": [
                {
                    "type": "text",
                    "text": "Action is blocked by policy",
                }
            ],
        }

    result = process_tool_call(agent, tool_name, arguments, db)

    if result["status"] == "completed":
        return {
            "status": "completed",
            "tool_result": result.get("tool_result"),
            "content": [
                {
                    "type": "text",
                    "text": result.get("tool_result", {}).get("message", "Tool executed successfully")
                    if isinstance(result.get("tool_result"), dict)
                    else "Tool executed successfully",
                }
            ],
        }

    if result["status"] == "pending_approval":
        return {
            "status": "pending_approval",
            "approval_id": result["approval_id"],
            "content": [
                {
                    "type": "text",
                    "text": "Tool call requires human approval",
                }
            ],
        }

    return {
        "status": "blocked",
        "content": [
            {
                "type": "text",
                "text": "Tool is blocked by policy",
            }
        ],
    }
