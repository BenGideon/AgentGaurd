# AgentGuard

Minimal FastAPI backend plus a Next.js dashboard for tool permissions, approvals, and audit logs.

## Backend

Install Python dependencies if needed:

```bash
pip install fastapi uvicorn sqlalchemy
```

Run the API:

```bash
uvicorn app_backend.main:app --reload
```

Compatibility entrypoint:

```bash
uvicorn main:app --reload
```

The backend runs at `http://localhost:8000`.

### Local SQLite migrations

AgentGuard uses Alembic migrations. For a fresh local database, run:

```bash
alembic upgrade head
```

For a throwaway local reset, stop the server and delete `agentguard.db`; the app will
recreate it after you run migrations again.

## API examples

Create an agent. If `api_key` is omitted, AgentGuard generates one with the `ag_test_`
prefix and returns it in the response.

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "id": "sales_agent",
    "name": "Sales Agent"
  }'
```

Create a tool with an optional input schema:

```bash
curl -X POST http://localhost:8000/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "send_email",
    "description": "Send an email",
    "input_schema": {
      "to": "string",
      "subject": "string",
      "body": "string"
    }
  }'
```

Create a policy:

```bash
curl -X POST http://localhost:8000/policies \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "sales_agent",
    "allowed_tools": ["create_task"],
    "approval_required_tools": ["send_email"],
    "blocked_tools": ["delete_customer"]
  }'
```

Discover tools available to an agent:

```bash
curl http://localhost:8000/agent/tools \
  -H "x-agent-key: ag_test_your_key_here"
```

Call a tool. The agent identity comes from `x-agent-key`; do not send `agent_id` in the body.

```bash
curl -X POST http://localhost:8000/tool-call \
  -H "Content-Type: application/json" \
  -H "x-agent-key: ag_test_your_key_here" \
  -d '{
    "tool": "send_email",
    "input": {
      "to": "john@example.com",
      "subject": "Hello",
      "body": "Hello from AgentGuard"
    }
  }'
```

List tools with the MCP-style endpoint:

```bash
curl -X POST http://localhost:8000/mcp/tools/list \
  -H "x-agent-key: ag_test_your_key_here"
```

Example response:

```json
{
  "tools": [
    {
      "name": "send_email",
      "description": "Send an email",
      "inputSchema": {
        "type": "object",
        "properties": {
          "to": { "type": "string" },
          "subject": { "type": "string" },
          "body": { "type": "string" }
        },
        "required": ["to", "subject", "body"]
      },
      "access": "approval_required"
    }
  ]
}
```

Call a tool with the MCP-style endpoint:

```bash
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -H "x-agent-key: ag_test_your_key_here" \
  -d '{
    "name": "send_email",
    "arguments": {
      "to": "john@example.com",
      "subject": "Hello",
      "body": "Hi John"
    }
  }'
```

## Gmail Draft Connector

AgentGuard includes a connector tool named `create_gmail_draft`. It only creates Gmail
drafts. It never sends emails.

Register it like any other tool:

```bash
curl -X POST http://localhost:8000/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "create_gmail_draft",
    "description": "Creates a Gmail draft email. Does not send.",
    "input_schema": {
      "to": "string",
      "subject": "string",
      "body": "string"
    }
  }'
```

Example policy:

```json
{
  "agent_id": "sales_agent",
  "allowed_tools": ["create_task"],
  "approval_required_tools": ["create_gmail_draft"],
  "blocked_tools": ["delete_customer"]
}
```

### Mock mode

Mock mode is the default and does not require Google credentials.

PowerShell:

```powershell
$env:GMAIL_CONNECTOR_MODE = "mock"
```

Bash:

```bash
export GMAIL_CONNECTOR_MODE=mock
```

Example MCP call:

```bash
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -H "x-agent-key: ag_test_your_key_here" \
  -d '{
    "name": "create_gmail_draft",
    "arguments": {
      "to": "john@example.com",
      "subject": "Follow up",
      "body": "Hi John, just checking in."
    }
  }'
```

### Live mode

1. Enable the Gmail API in Google Cloud.
2. Create OAuth Desktop App credentials.
3. Download the file as `credentials.json` into the backend root.
4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run the backend in live mode.

PowerShell:

```powershell
$env:GMAIL_CONNECTOR_MODE = "live"
uvicorn app_backend.main:app --reload
```

Bash:

```bash
export GMAIL_CONNECTOR_MODE=live
uvicorn app_backend.main:app --reload
```

6. The first live call opens the OAuth browser flow and creates `token.json`.

This connector only calls Gmail draft creation. It never sends emails.

## Running a real agent

`agent_client.py` is a tiny AI agent client. It accepts a user instruction, asks OpenAI
to draft email JSON, then calls AgentGuard's MCP endpoint for `create_gmail_draft`.
It only requests Gmail draft creation. It never sends emails.

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Start AgentGuard first:

```bash
uvicorn app_backend.main:app --reload
```

Make sure the agent you use has a policy that includes:

```json
{
  "approval_required_tools": ["create_gmail_draft"]
}
```

Mac/Linux environment:

```bash
export OPENAI_API_KEY="your_openai_api_key"
export AGENTGUARD_API_URL="http://localhost:8000"
export AGENTGUARD_AGENT_KEY="ag_test_your_agent_key"
export OPENAI_MODEL="gpt-4.1-mini"
```

Windows PowerShell environment:

```powershell
$env:OPENAI_API_KEY = "your_openai_api_key"
$env:AGENTGUARD_API_URL = "http://localhost:8000"
$env:AGENTGUARD_AGENT_KEY = "ag_test_your_agent_key"
$env:OPENAI_MODEL = "gpt-4.1-mini"
```

Run the agent:

```bash
python agent_client.py "Follow up with John about our pricing call"
```

If the instruction does not include an email address, the agent uses:

```text
john@example.com
```

Expected flow:

1. The agent prints generated email JSON.
2. The agent calls `POST /mcp/tools/call` with `create_gmail_draft`.
3. AgentGuard returns `pending_approval` if the policy requires approval.
4. Open `http://localhost:3000/approvals`.
5. Click `Approve & Create Draft`.
6. The Gmail draft connector creates a draft in mock or live mode.
7. The Logs page shows the result.

## AgentGuard Gateway

AgentGuard Gateway lets agents call generic actions instead of hardcoded tools. An action
has a name, description, input schema, executor type, and risk level. An action policy
decides whether a specific agent can call that action.

Action policy effects:

- `allow`: execute immediately
- `approval_required`: create a pending approval
- `block`: deny and log

Gateway calls use the same `x-agent-key` header as tool calls.

Create an action:

```bash
curl -X POST http://localhost:8000/actions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sales.create_gmail_draft",
    "description": "Creates a Gmail draft for sales follow-up. Does not send.",
    "executor_type": "gmail_draft",
    "risk_level": "medium",
    "input_schema": {
      "to": "string",
      "subject": "string",
      "body": "string"
    }
  }'
```

Create an action policy:

```bash
curl -X POST http://localhost:8000/action-policies \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "sales_agent",
    "action_name": "sales.create_gmail_draft",
    "effect": "approval_required"
  }'
```

Call an action:

```bash
curl -X POST http://localhost:8000/actions/call \
  -H "Content-Type: application/json" \
  -H "x-agent-key: ag_test_your_key_here" \
  -d '{
    "action": "sales.create_gmail_draft",
    "input": {
      "to": "john@example.com",
      "subject": "Follow up",
      "body": "Hi John"
    }
  }'
```

If approval is required, approve it:

```bash
curl -X POST http://localhost:8000/approvals/1/approve
```

MCP compatibility:

- `POST /mcp/tools/list` includes available actions as callable tools.
- `POST /mcp/tools/call` routes to actions when the requested name matches an action.
- Existing tool behavior is preserved.

# Action Schema v1

Actions are machine-readable capabilities that agents can discover and call through
AgentGuard. They describe what the action does, what input it accepts, how it executes,
and how risky it is.

Fields:

- `name`: Unique action name, usually namespaced by domain.
- `description`: Human-readable explanation of what the action does.
- `input_schema`: JSON or JSON Schema describing required input.
- `executor_type`: Backend executor to use, such as `gmail_draft`, `mock`, `webhook`, or `api_proxy`.
- `risk_level`: Default risk label, such as `low`, `medium`, `high`, or `critical`.

Example:

```json
{
  "name": "sales.create_gmail_draft",
  "description": "Creates a Gmail draft. Does not send.",
  "input_schema": {
    "type": "object",
    "properties": {
      "to": { "type": "string" },
      "subject": { "type": "string" },
      "body": { "type": "string" }
    },
    "required": ["to", "subject", "body"]
  },
  "executor_type": "gmail_draft",
  "risk_level": "medium"
}
```

Action policies decide what an agent can do with an action. `ActionPolicy.effect` can be:

- `allow`: execute immediately
- `approval_required`: create a pending approval before execution
- `block`: deny the action and log it

## API Proxy Executor

The `api_proxy` executor lets AgentGuard proxy controlled HTTP requests to external APIs.
It keeps the request behind AgentGuard policy, risk scoring, approvals, and audit logs.

Create an action:

```json
{
  "name": "external.http_request",
  "description": "Proxy a controlled HTTP request to an external API.",
  "executor_type": "api_proxy",
  "risk_level": "medium",
  "input_schema": {
    "type": "object",
    "properties": {
      "url": { "type": "string" },
      "method": { "type": "string" },
      "headers": { "type": "object" },
      "query": { "type": "object" },
      "body": { "type": "object" }
    },
    "required": ["url", "method"]
  }
}
```

Call it with the Python SDK:

```python
from agentguard import AgentGuard

ag = AgentGuard(api_key="ag_test_...")

result = ag.call_action("external.http_request", {
    "url": "https://httpbin.org/post",
    "method": "POST",
    "body": {
        "hello": "world"
    }
})

print(result)
```

Security limits for v1.2:

- Allowed methods: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`.
- Localhost and private network URLs are blocked.
- Requests use a 10 second timeout.
- Redirects are not followed.

## Secrets

Agents should not pass raw API keys, bearer tokens, or passwords in action input.
Store those values in AgentGuard, then reference them by name from `api_proxy`
actions. Secret values are never returned by the API.

Create a secret:

```bash
curl -X POST http://localhost:8000/secrets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hubspot_token",
    "value": "pat-...",
    "description": "HubSpot private app token"
  }'
```

List secrets:

```bash
curl http://localhost:8000/secrets
```

Delete a secret:

```bash
curl -X DELETE http://localhost:8000/secrets/hubspot_token
```

API proxy with bearer auth:

```json
{
  "url": "https://api.example.com/resource",
  "method": "POST",
  "auth": {
    "type": "bearer",
    "secret_name": "hubspot_token"
  },
  "body": {}
}
```

AgentGuard injects:

```http
Authorization: Bearer <secret value>
```

API proxy with API key header auth:

```json
{
  "url": "https://api.example.com/resource",
  "method": "GET",
  "auth": {
    "type": "api_key_header",
    "secret_name": "my_api_key",
    "header_name": "X-API-Key"
  }
}
```

Basic auth is also supported with `username_secret` and `password_secret`.

Local development currently stores secrets in SQLite as plaintext. This is not
production-safe. A production deployment should use encryption or a KMS-backed
secret store.

## Scoped Secrets

Secrets must be explicitly allowed per agent and action before an `api_proxy`
action can use them. This prevents an agent that can call one action from
referencing unrelated API credentials by name.

Create or replace an action secret policy:

```bash
curl -X POST http://localhost:8000/action-secret-policies \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "sales_agent",
    "action_name": "hubspot.create_contact",
    "allowed_secrets": ["hubspot_token"]
  }'
```

Policy shape:

```json
{
  "agent_id": "sales_agent",
  "action_name": "hubspot.create_contact",
  "allowed_secrets": ["hubspot_token"]
}
```

Behavior:

- If an action input references no secrets, existing `api_proxy` behavior is preserved.
- If an action input references a secret and no matching action secret policy exists, the call is blocked.
- If an action input references a secret outside `allowed_secrets`, the call is blocked.
- `secret_name`, `username_secret`, and `password_secret` references may appear in logs, but secret values and injected auth headers are redacted.

## Workspaces (Multi-Tenant)

AgentGuard supports multiple independent workspaces. Each workspace has isolated:

- agents
- tools and actions
- policies and scoped secret policies
- secrets
- approvals
- audit logs

For v1.5, workspace selection is header-based:

```text
x-workspace-id: default
```

If the header is missing, AgentGuard uses the `default` workspace. New local
databases auto-create the default workspace, and existing local dev data is
assigned to `default` during startup migration.

Example action call:

```bash
curl -X POST http://localhost:8000/actions/call \
  -H "Content-Type: application/json" \
  -H "x-agent-key: ag_test_..." \
  -H "x-workspace-id: default" \
  -d '{
    "action": "sales.create_gmail_draft",
    "input": {
      "to": "john@example.com",
      "subject": "Follow up",
      "body": "Hi John"
    }
  }'
```

API keys are resolved inside the workspace, so an agent key must belong to the
workspace named by `x-workspace-id`. Secrets are also scoped by workspace, so a
secret named `hubspot_token` in one workspace is separate from a secret with the
same name in another workspace.

## Authentication & Roles

AgentGuard uses Clerk for human user authentication. Agents still authenticate
with `x-agent-key`; users authenticate with:

```text
Authorization: Bearer <Clerk JWT>
```

Backend Clerk verification uses JWKS. Set:

```bash
CLERK_JWKS_URL=https://<your-clerk-domain>/.well-known/jwks.json
CLERK_ISSUER_URL=https://<your-clerk-domain>
```

The dashboard uses Clerk's Next.js package. Set:

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

Users belong to workspaces through `workspace_memberships`.

Roles:

- `admin`: can approve/reject actions.
- `reviewer`: can approve/reject actions.
- `viewer`: read-only; cannot approve/reject.

For v1.6, the first signed-in user in the `default` workspace is automatically
created as an `admin`. Approval endpoints enforce user auth:

- `POST /approvals/{id}/approve`
- `POST /approvals/{id}/reject`

Agents can never approve because approval endpoints require a Clerk user JWT,
not an agent API key.

## Approval Editing

When an agent proposes an action that requires approval, AgentGuard stores both:

- `original_input`: the payload proposed by the agent
- `current_input`: the reviewer-editable payload

Reviewers with the `admin` or `reviewer` role can edit pending approvals before
execution:

```bash
curl -X PUT http://localhost:8000/approvals/1/input \
  -H "Authorization: Bearer <Clerk JWT>" \
  -H "x-workspace-id: default" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "to": "john@example.com",
      "subject": "Follow up",
      "body": "Hi John, following up on pricing."
    }
  }'
```

Approving executes `current_input`, not the original agent proposal:

```bash
curl -X POST http://localhost:8000/approvals/1/approve \
  -H "Authorization: Bearer <Clerk JWT>" \
  -H "x-workspace-id: default"
```

Example:

- Agent proposes: `Hi John...`
- Reviewer edits: `Hi John, following up on pricing...`
- Reviewer approves
- Gmail draft is created with the edited body

Audit logs include who approved or rejected the action, the original input, the
final input, and the execution result. Sensitive fields are redacted before logs
are returned.

## Advanced Policy Engine

Action policies support JSON conditions and priority-based evaluation. AgentGuard
loads policies for the workspace, agent, and action, sorts by `priority`
descending, and applies the first matching policy.

If `conditions` is `null` or `{}`, the policy always matches. If no policy
matches, the action is blocked by default.

Supported v2.0 conditions:

- `risk_level`: matches calculated risk, such as `critical`
- `method`: matches `api_proxy` HTTP method, such as `DELETE`
- `amount_gt`: matches `input.amount > value`
- `recipient_external`: compares email recipient domain to `WORKSPACE_EMAIL_DOMAIN`

External Gmail review example:

```json
{
  "agent_id": "sales_agent",
  "action_name": "sales.create_gmail_draft",
  "effect": "approval_required",
  "conditions": {
    "recipient_external": true
  },
  "priority": 10
}
```

Block dangerous API proxy deletes:

```json
{
  "agent_id": "ops_agent",
  "action_name": "external.http_request",
  "effect": "block",
  "conditions": {
    "method": "DELETE"
  },
  "priority": 100
}
```

Policy matches are returned in action responses and audit logs:

```json
{
  "policy_match": {
    "policy_id": 12,
    "effect": "approval_required",
    "matched_conditions": {
      "recipient_external": true
    },
    "priority": 10
  }
}
```

## Gmail Connector (Production OAuth)

In production, users connect Gmail from the dashboard instead of using local
`credentials.json` and `token.json` files.

Flow:

1. A workspace user opens `Connectors`.
2. They click `Connect Gmail`.
3. Google OAuth consent redirects back to the backend callback.
4. AgentGuard stores the Gmail tokens for that workspace.
5. `gmail_draft` actions use the workspace Gmail connector automatically.

Backend environment variables:

```text
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://api.yourdomain.com/connectors/gmail/callback
FRONTEND_URL=https://app.yourdomain.com
OAUTH_STATE_SECRET=...
GMAIL_CONNECTOR_MODE=live
```

The required Google scope is:

```text
https://www.googleapis.com/auth/gmail.compose
```

The Gmail connector only creates drafts. It never sends email.

Tokens are stored per workspace in the `connectors` table and are never returned
by the API. For now, tokens are stored in plaintext for implementation
simplicity. Production deployments should encrypt connector tokens or store them
with a KMS-backed secret system.

Local development can still use `GMAIL_CONNECTOR_MODE=mock`. The old
`credentials.json` / `token.json` flow remains as a fallback only for local
backend calls without workspace connector context.

## Production Deployment

AgentGuard uses SQLite for local development and Postgres for production. Set
`DATABASE_URL` to enable Postgres:

```bash
DATABASE_URL=postgresql://user:password@host:5432/agentguard
```

`postgres://` URLs are also accepted and normalized to `postgresql://`.

### Backend

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn app_backend.main:app --host 0.0.0.0 --port 8000
```

Render or Railway can use either the start command above, or the included
`Dockerfile`, which runs:

```bash
alembic upgrade head && uvicorn app_backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Backend environment variables:

```text
DATABASE_URL=postgresql://...
CLERK_SECRET_KEY=...
CLERK_JWKS_URL=https://<your-clerk-domain>/.well-known/jwks.json
CLERK_ISSUER_URL=https://<your-clerk-domain>
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://api.yourdomain.com/connectors/gmail/callback
FRONTEND_URL=https://app.yourdomain.com
OAUTH_STATE_SECRET=...
GMAIL_CONNECTOR_MODE=live
OPENAI_API_KEY=...
```

### Frontend

Deploy the Next.js dashboard to Vercel and set:

```text
NEXT_PUBLIC_AGENTGUARD_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
NEXT_PUBLIC_AGENTGUARD_WORKSPACE_ID=default
```

`NEXT_PUBLIC_AGENTGUARD_API_URL` replaces local `http://localhost:8000` in
production. `NEXT_PUBLIC_API_BASE_URL` is still accepted as a legacy fallback.

### Database

Postgres is required for production. SQLite is intended only for local dev.
Schema changes are managed by Alembic migrations in `alembic/versions`.

For existing local SQLite databases from earlier MVP versions, either keep using
the existing database for local testing and mark it as migrated:

```bash
alembic stamp head
```

Or create a fresh local database with:

```bash
alembic upgrade head
```

## Frontend

Install Node dependencies:

```bash
npm install
```

Run the dashboard:

```bash
npm run dev
```

Open `http://localhost:3000`.

The dashboard assumes the API is available at `http://localhost:8000`. To override it:

```bash
NEXT_PUBLIC_AGENTGUARD_API_URL=http://localhost:8000 npm run dev
```

The dashboard sends `x-workspace-id: default` by default. To point it at another
workspace:

```bash
NEXT_PUBLIC_AGENTGUARD_WORKSPACE_ID=customer-a npm run dev
```
