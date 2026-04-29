import os

from agentguard import AgentGuard


def main() -> None:
    agent_key = os.getenv("AGENTGUARD_AGENT_KEY")
    if not agent_key:
        raise RuntimeError("Missing required environment variable: AGENTGUARD_AGENT_KEY")

    base_url = os.getenv("AGENTGUARD_API_URL", "http://localhost:8000")
    client = AgentGuard(api_key=agent_key, base_url=base_url)

    result = client.call_action(
        "sales.create_gmail_draft",
        {
            "to": "john@example.com",
            "subject": "Follow up",
            "body": "Hi John",
        },
    )

    print(result)


if __name__ == "__main__":
    main()
