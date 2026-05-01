import { AgentGuard } from "../dist/index.js";

const apiKey = process.env.AGENTGUARD_AGENT_KEY;

if (!apiKey) {
  throw new Error("Set AGENTGUARD_AGENT_KEY before running this smoke test");
}

const ag = new AgentGuard({
  apiKey,
  baseUrl: process.env.AGENTGUARD_API_URL || "http://localhost:8000",
  authToken: process.env.AGENTGUARD_USER_TOKEN,
});

console.log("listActions:", await ag.listActions());

if (process.env.AGENTGUARD_USER_TOKEN) {
  console.log(
    "simulate:",
    await ag.simulate({
      action: process.env.AGENTGUARD_ACTION || "sales.create_gmail_draft",
      input: {
        to: "john@example.com",
        subject: "JS smoke simulation",
        body: "Hello from the JavaScript SDK smoke test.",
      },
    })
  );
} else {
  console.log("simulate: skipped because AGENTGUARD_USER_TOKEN is not set");
}

console.log(
  "callAction:",
  await ag.callAction(process.env.AGENTGUARD_ACTION || "sales.create_gmail_draft", {
    to: "john@example.com",
    subject: "JS smoke test",
    body: "Hello from the JavaScript SDK smoke test.",
  })
);
