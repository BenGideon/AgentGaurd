# AgentGuard Python SDK

Tiny Python client for AgentGuard Gateway.

## Install locally

From this folder:

```bash
pip install -e .
```

## Environment

```bash
export AGENTGUARD_AGENT_KEY="ag_test_your_agent_key"
export AGENTGUARD_API_URL="http://localhost:8000"
```

PowerShell:

```powershell
$env:AGENTGUARD_AGENT_KEY = "ag_test_your_agent_key"
$env:AGENTGUARD_API_URL = "http://localhost:8000"
```

## Example

```python
from agentguard import AgentGuard

ag = AgentGuard(api_key="ag_test_...")

result = ag.call_action(
    "sales.create_gmail_draft",
    {
        "to": "john@example.com",
        "subject": "Follow up",
        "body": "Hi John",
    },
)

print(result)
```

If the action policy requires approval, AgentGuard returns `pending_approval` with an
`approval_id`. Approve it from the dashboard or with `POST /approvals/{id}/approve`.

## Methods

- `list_actions()`
- `call_action(action, input)`
- `list_tools()`
- `call_tool(name, arguments)`
- `get_logs()`

Non-2xx responses raise `AgentGuardError` with the status code and response text.

## Smoke Test

```bash
python examples/create_gmail_draft.py
```
