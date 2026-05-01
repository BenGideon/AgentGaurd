import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session", autouse=True)
def test_database(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("agentguard-db") / "test.db"
    if db_path.exists():
        db_path.unlink()
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ.pop("CLERK_JWKS_URL", None)
    os.environ["GMAIL_CONNECTOR_MODE"] = "mock"
    os.environ["WORKSPACE_EMAIL_DOMAIN"] = "company.com"

    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
    command.upgrade(config, "head")
    yield db_path


@pytest.fixture(scope="session")
def app(test_database):
    from app_backend.main import app

    return app


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def workspace():
    return f"ws_{uuid4().hex}"


@pytest.fixture()
def headers(workspace):
    return {"x-workspace-id": workspace}


@pytest.fixture()
def db_session(test_database):
    from app_backend.core.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_agent(client, headers, agent_id="agent"):
    response = client.post(
        "/agents",
        headers=headers,
        json={"id": agent_id, "name": "Test Agent"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def create_action(client, headers, name="test.action", executor_type="mock", risk_level="medium"):
    response = client.post(
        "/actions",
        headers=headers,
        json={
            "name": name,
            "description": "Test action",
            "executor_type": executor_type,
            "risk_level": risk_level,
            "input_schema": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                    "amount": {"type": "number"},
                    "method": {"type": "string"},
                    "url": {"type": "string"},
                },
            },
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def create_policy(client, headers, agent_id, action_name, effect, conditions=None, priority=0):
    response = client.post(
        "/action-policies",
        headers=headers,
        json={
            "agent_id": agent_id,
            "action_name": action_name,
            "effect": effect,
            "conditions": conditions,
            "priority": priority,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def call_action(client, headers, api_key, action_name, input_data):
    request_headers = {**headers, "x-agent-key": api_key}
    return client.post(
        "/actions/call",
        headers=request_headers,
        json={"action": action_name, "input": input_data},
    )
