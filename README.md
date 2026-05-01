# AgentGuard

Control what AI agents can do before they do it.

## What It Does

- Lets AI agents call actions through a safe gateway.
- Simulates policy decisions before anything runs.
- Requires human approval for risky actions.
- Executes approved actions like Gmail drafts or API calls.
- Records audit logs for every decision and result.

## Demo

```text
Generate -> simulate -> approve -> execute -> audit log
```

Open the demo at:

```text
http://localhost:3000/demo
```

## Architecture

```text
Agent -> AgentGuard -> APIs (Gmail, etc.)
          |
          v
   Policies / Approvals / Logs
```

## Quickstart

```bash
git clone https://github.com/BenGideon/AgentGaurd.git
cd AgentGuard

pip install -r requirements.txt
npm install

python setup_demo.py

uvicorn app_backend.main:app --reload
npm run dev
```

Then open:

```text
http://localhost:3000/demo
```

## Demo Mode

AgentGuard works locally without external services:

- No OpenAI key required.
- No Gmail connection required.
- Uses fallback AI generation and mock Gmail draft creation.

## SDK Examples

JavaScript:

```js
import { AgentGuard } from "@agentguard/sdk"

const ag = new AgentGuard({
  apiKey: process.env.AGENTGUARD_AGENT_KEY,
  baseUrl: "http://localhost:8000"
})

const result = await ag.callAction("sales.create_gmail_draft", {
  to: "john@example.com",
  subject: "Follow up",
  body: "Hi John"
})
```

Python:

```python
from agentguard import AgentGuard

ag = AgentGuard(
    api_key="ag_test_...",
    base_url="http://localhost:8000",
)

result = ag.call_action("sales.create_gmail_draft", {
    "to": "john@example.com",
    "subject": "Follow up",
    "body": "Hi John",
})
```

## Why It Exists

AI agents can send emails, call APIs, and change systems. Mistakes happen, so AgentGuard adds policy, approval, and audit controls before actions execute.

## Status

Early-stage project. Feedback welcome.
