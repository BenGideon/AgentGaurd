import os

__test__ = False


def main() -> None:
    from agentguard import AgentGuard

    api_key = os.environ.get("AGENTGUARD_AGENT_KEY")
    if not api_key:
        raise SystemExit("Set AGENTGUARD_AGENT_KEY before running this smoke test")

    client = AgentGuard(
        api_key=api_key,
        base_url=os.environ.get("AGENTGUARD_API_URL", "http://localhost:8000"),
    )

    print("list_actions:", client.list_actions())
    print(
        "call_action:",
        client.call_action(
            os.environ.get("AGENTGUARD_ACTION", "sales.create_gmail_draft"),
            {
                "to": "john@example.com",
                "subject": "Smoke test",
                "body": "Hello from the Python SDK smoke test.",
            },
        ),
    )
    print(
        "call_tool:",
        client.call_tool(
            os.environ.get("AGENTGUARD_TOOL", "sales.create_gmail_draft"),
            {
                "to": "john@example.com",
                "subject": "Tool smoke test",
                "body": "Hello from the Python SDK tool call.",
            },
        ),
    )
    print("simulate: not supported by the Python SDK yet")


if __name__ == "__main__":
    main()
