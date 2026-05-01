from alembic import command
from alembic.config import Config

from app_backend.core.database import SessionLocal
from app_backend.models.models import Agent
from app_backend.services.demo_service import DEMO_AGENT_ID, seed_demo_data


def run_migrations() -> None:
    config = Config("alembic.ini")
    command.upgrade(config, "head")


def main() -> None:
    run_migrations()

    db = SessionLocal()
    try:
        seed_demo_data(db)
        agent = db.query(Agent).filter(Agent.id == DEMO_AGENT_ID, Agent.workspace_id == "default").first()
        api_key = agent.api_key if agent else "not-created"
    finally:
        db.close()

    print("Demo setup complete")
    print(f"Agent API key: {api_key}")
    print("Open: http://localhost:3000/demo")


if __name__ == "__main__":
    main()
