# AgentGuard JavaScript SDK

Minimal Node.js / Next.js SDK for calling AgentGuard actions.

## Install

```bash
npm install @agentguard/sdk
```

## Call an action

```js
import { AgentGuard } from "@agentguard/sdk";

const ag = new AgentGuard({
  apiKey: process.env.AGENTGUARD_AGENT_KEY,
  baseUrl: "http://localhost:8000"
});

const result = await ag.callAction("sales.create_gmail_draft", {
  to: "john@gmail.com",
  subject: "Follow up",
  body: "Hi John"
});

if (result.status === "pending_approval") {
  console.log("Approve in AgentGuard:", result.approvalId);
}

if (result.status === "completed") {
  console.log(result.result);
}
```

Blocked actions throw `AgentGuardError`.

```js
import { AgentGuard, AgentGuardError } from "@agentguard/sdk";

try {
  await ag.callAction("external.delete_customer", { id: "123" });
} catch (error) {
  if (error instanceof AgentGuardError) {
    console.error(error.message, error.data);
  }
}
```

## List actions

```js
const actions = await ag.listActions();
console.log(actions);
```

## Simulate a policy decision

`/simulate` is a user-authenticated admin/debug endpoint in AgentGuard. Pass a
Clerk JWT as `authToken`.

```js
const ag = new AgentGuard({
  apiKey: process.env.AGENTGUARD_AGENT_KEY,
  authToken: process.env.AGENTGUARD_USER_TOKEN,
  baseUrl: "http://localhost:8000"
});

const simulation = await ag.simulate({
  action: "sales.create_gmail_draft",
  input: {
    to: "customer@gmail.com",
    subject: "Follow up",
    body: "Hi"
  }
});

console.log(simulation.decision);
console.log(simulation.risk_level);
console.log(simulation.reason);
```

You can pass `agent_id` explicitly if you do not want the SDK to resolve it from
the configured agent API key:

```js
await ag.simulate({
  agent_id: "sales_agent",
  action: "sales.create_gmail_draft",
  input: { to: "customer@gmail.com" }
});
```

## Configuration

```js
new AgentGuard({
  apiKey: "ag_test_...",
  baseUrl: "http://localhost:8000",
  workspaceId: "default",
  authToken: "clerk_jwt_for_admin_simulation"
});
```

Node.js 18+ is required because the SDK uses native `fetch`.
