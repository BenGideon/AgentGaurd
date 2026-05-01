import json
from typing import Any

from sqlalchemy.orm import Session

from app_backend.core.config import settings
from app_backend.models.models import Action, ActionPolicy, Agent
from app_backend.services.agents_service import generate_agent_api_key
from app_backend.services.workspace_service import ensure_workspace


DEMO_AGENT_ID = "sales_agent"
DEMO_ACTION_NAME = "sales.create_gmail_draft"


def seed_demo_data(db: Session, workspace_id: str = "default") -> None:
    ensure_workspace(db, workspace_id)

    agent = (
        db.query(Agent)
        .filter(Agent.workspace_id == workspace_id, Agent.id == DEMO_AGENT_ID)
        .first()
    )
    if not agent:
        agent = Agent(
            id=DEMO_AGENT_ID,
            workspace_id=workspace_id,
            name="Sales Email Agent",
            api_key=f"ag_test_sales_demo_{generate_agent_api_key().removeprefix('ag_test_')}",
        )
        db.add(agent)

    action = (
        db.query(Action)
        .filter(Action.workspace_id == workspace_id, Action.name == DEMO_ACTION_NAME)
        .first()
    )
    if not action:
        action = Action(
            workspace_id=workspace_id,
            name=DEMO_ACTION_NAME,
            description="Creates a Gmail draft email for sales follow-up. Does not send.",
            input_schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
            executor_type="gmail_draft",
            risk_level="medium",
        )
        db.add(action)

    existing_policies = (
        db.query(ActionPolicy)
        .filter(
            ActionPolicy.workspace_id == workspace_id,
            ActionPolicy.agent_id == DEMO_AGENT_ID,
            ActionPolicy.action_name == DEMO_ACTION_NAME,
        )
        .all()
    )
    external_policy = next(
        (policy for policy in existing_policies if policy.conditions == {"recipient_external": True}),
        None,
    )
    if not external_policy:
        db.add(
            ActionPolicy(
                workspace_id=workspace_id,
                agent_id=DEMO_AGENT_ID,
                action_name=DEMO_ACTION_NAME,
                effect="approval_required",
                conditions={"recipient_external": True},
                priority=10,
            )
        )

    allow_policy = next(
        (policy for policy in existing_policies if not policy.conditions),
        None,
    )
    if not allow_policy:
        db.add(
            ActionPolicy(
                workspace_id=workspace_id,
                agent_id=DEMO_AGENT_ID,
                action_name=DEMO_ACTION_NAME,
                effect="allow",
                conditions=None,
                priority=0,
            )
        )

    db.commit()


def generate_demo_email(email: str, context: str) -> dict[str, str]:
    if settings.OPENAI_API_KEY:
        generated = _generate_with_openai(email, context)
        if generated:
            return generated
    return _fallback_email(email, context)


def _generate_with_openai(email: str, context: str) -> dict[str, str] | None:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write concise B2B sales follow-up emails. "
                        "Return only valid JSON with keys to, subject, body. "
                        "Never include markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Recipient: {email}\nContext: {context}",
                },
            ],
            temperature=0.4,
        )
        content = response.choices[0].message.content or ""
        parsed = json.loads(content)
        return _normalize_email(parsed, email, context)
    except Exception:
        return None


def _normalize_email(data: dict[str, Any], email: str, context: str) -> dict[str, str]:
    return {
        "to": str(data.get("to") or email),
        "subject": str(data.get("subject") or "Following up"),
        "body": str(data.get("body") or _fallback_email(email, context)["body"]),
    }


def _fallback_email(email: str, context: str) -> dict[str, str]:
    clean_context = context.strip() or "our recent conversation"
    return {
        "to": email,
        "subject": "Following up on our conversation",
        "body": (
            f"Hi,\n\nThanks again for taking the time to discuss {clean_context}. "
            "I wanted to follow up with a quick note and see if there are any questions I can help answer.\n\n"
            "Best,\nSales Team"
        ),
    }
