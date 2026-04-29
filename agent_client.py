import json
import os
import re
import sys

import requests
from openai import OpenAI


DEFAULT_AGENTGUARD_API_URL = "http://localhost:8000"
DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_TO = "john@example.com"


def extract_email(instruction: str) -> str:
    match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", instruction)
    return match.group(0) if match else DEFAULT_TO


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def generate_email_json(instruction: str) -> dict:
    client = OpenAI(api_key=require_env("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    default_to = extract_email(instruction)

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You draft Gmail email content for AgentGuard. "
                    "Return only valid JSON with exactly these keys: to, subject, body. "
                    "Never send email. Never call tools. "
                    f"If no recipient email is clear, use {default_to}."
                ),
            },
            {
                "role": "user",
                "content": instruction,
            },
        ],
    )

    content = response.choices[0].message.content or "{}"
    draft = json.loads(content)

    return {
        "to": draft.get("to") or default_to,
        "subject": draft.get("subject") or "Follow up",
        "body": draft.get("body") or instruction,
    }


def call_agentguard(draft: dict) -> dict:
    api_url = os.getenv("AGENTGUARD_API_URL", DEFAULT_AGENTGUARD_API_URL).rstrip("/")
    agent_key = require_env("AGENTGUARD_AGENT_KEY")

    response = requests.post(
        f"{api_url}/mcp/tools/call",
        headers={
            "Content-Type": "application/json",
            "x-agent-key": agent_key,
        },
        json={
            "name": "create_gmail_draft",
            "arguments": draft,
        },
        timeout=30,
    )

    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text}

    if response.status_code >= 400:
        raise RuntimeError(
            f"AgentGuard returned HTTP {response.status_code}: {json.dumps(payload, indent=2)}"
        )

    return payload


def main() -> int:
    if len(sys.argv) < 2:
        print('Usage: python agent_client.py "Follow up with John about our pricing call"')
        return 1

    instruction = " ".join(sys.argv[1:]).strip()
    if not instruction:
        print("Instruction cannot be empty")
        return 1

    try:
        draft = generate_email_json(instruction)
        print("Generated email JSON:")
        print(json.dumps(draft, indent=2))

        result = call_agentguard(draft)
        print("\nAgentGuard response:")
        print(json.dumps(result, indent=2))

        if result.get("status") == "pending_approval":
            print(
                f"\nPending approval #{result.get('approval_id')}. "
                "Open the AgentGuard dashboard and approve it."
            )
        elif result.get("status") == "completed":
            print("\nTool result:")
            print(json.dumps(result.get("tool_result"), indent=2))
        elif result.get("status") == "blocked":
            print("\nBlocked by AgentGuard policy.")

        return 0
    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
