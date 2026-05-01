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

## Use Case: Stop Risky Agent Actions

This is not theoretical:

- In 2025, Replit's AI agent deleted production data during a coding session despite a code freeze. [Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/ai-coding-platform-goes-rogue-during-code-freeze-and-deletes-entire-company-database-replit-ceo-apologizes-after-ai-engine-says-it-made-a-catastrophic-error-in-judgment-and-destroyed-all-production-data)
- In 2026, a Cursor AI agent reportedly deleted PocketOS production data and backups through cloud API access. [Business Insider](https://www.businessinsider.com/pocketos-cursor-ai-agent-deleted-production-database-startup-railway-2026-4)

AgentGuard is built for this failure mode:

```text
AI wants to delete data or call a risky API
-> AgentGuard simulates policy
-> high-risk action is blocked or requires approval
-> every decision is logged
```

## Status

Early-stage project. Feedback welcome.
