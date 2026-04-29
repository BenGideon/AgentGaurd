"use client";

import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../lib/api";

const draftDefaults = {
  to: "john@example.com",
  subject: "Follow up",
  body: "Hi John, just checking in.",
};

function JsonBlock({ value }) {
  return (
    <pre className="max-h-72 overflow-auto rounded-md bg-zinc-950 p-3 text-xs leading-5 text-zinc-50">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

export default function TestAgentPage() {
  const [agents, setAgents] = useState([]);
  const [tools, setTools] = useState([]);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [selectedTool, setSelectedTool] = useState("create_gmail_draft");
  const [form, setForm] = useState(draftDefaults);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.id === selectedAgentId),
    [agents, selectedAgentId]
  );

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [agentList, toolList] = await Promise.all([apiFetch("/agents"), apiFetch("/tools")]);
      setAgents(agentList);
      setTools(toolList);
      setSelectedAgentId((current) => current || agentList[0]?.id || "");
      setSelectedTool(
        toolList.some((tool) => tool.name === "create_gmail_draft")
          ? "create_gmail_draft"
          : toolList[0]?.name || "create_gmail_draft"
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function copyKey() {
    if (!selectedAgent?.api_key) return;
    await navigator.clipboard.writeText(selectedAgent.api_key);
    setMessage("API key copied");
  }

  async function simulateAgentCall(event) {
    event.preventDefault();
    setSubmitting(true);
    setMessage("");
    setError("");
    setResult(null);

    try {
      if (!selectedAgent) {
        throw new Error("Select an agent first");
      }

      const response = await apiFetch("/mcp/tools/call", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-agent-key": selectedAgent.api_key,
        },
        body: JSON.stringify({
          name: selectedTool,
          arguments: {
            to: form.to,
            subject: form.subject,
            body: form.body,
          },
        }),
      });

      setResult(response);
      if (response.status === "pending_approval") {
        setMessage(`Approval required: #${response.approval_id}`);
      } else if (response.status === "completed") {
        setMessage(response.tool_result?.message || "Tool completed");
      } else {
        setMessage("Tool call was blocked");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Test Agent</h1>
        <p className="mt-1 text-sm text-zinc-600">
          Simulate an agent asking AgentGuard to create a Gmail draft.
        </p>
      </div>

      {message ? (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
          {message}
        </div>
      ) : null}
      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
        <form className="space-y-5" onSubmit={simulateAgentCall}>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Agent
              <select
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                disabled={loading || agents.length === 0}
                onChange={(event) => setSelectedAgentId(event.target.value)}
                suppressHydrationWarning
                value={selectedAgentId}
              >
                {agents.map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.id} - {agent.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Tool
              <select
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                onChange={(event) => setSelectedTool(event.target.value)}
                suppressHydrationWarning
                value={selectedTool}
              >
                {tools.map((tool) => (
                  <option key={tool.name} value={tool.name}>
                    {tool.name}
                  </option>
                ))}
                {!tools.some((tool) => tool.name === "create_gmail_draft") ? (
                  <option value="create_gmail_draft">create_gmail_draft</option>
                ) : null}
              </select>
            </label>
          </div>

          <div className="rounded-md border border-zinc-200 bg-zinc-50 p-3">
            <div className="text-xs font-semibold uppercase text-zinc-500">Selected API key</div>
            <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <code className="break-all text-xs text-zinc-700">
                {selectedAgent?.api_key || "No agent selected"}
              </code>
              <button
                className="w-fit rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm font-medium text-zinc-800 hover:bg-zinc-50"
                disabled={!selectedAgent}
                onClick={copyKey}
                suppressHydrationWarning
                type="button"
              >
                Copy key
              </button>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              To
              <input
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                onChange={(event) => setForm({ ...form, to: event.target.value })}
                required
                suppressHydrationWarning
                type="email"
                value={form.to}
              />
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Subject
              <input
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                onChange={(event) => setForm({ ...form, subject: event.target.value })}
                required
                suppressHydrationWarning
                value={form.subject}
              />
            </label>
          </div>

          <label className="grid gap-1 text-sm font-medium text-zinc-700">
            Body
            <textarea
              className="min-h-36 rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
              onChange={(event) => setForm({ ...form, body: event.target.value })}
              required
              suppressHydrationWarning
              value={form.body}
            />
          </label>

          <button
            className="rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
            disabled={submitting || !selectedAgent}
            suppressHydrationWarning
            type="submit"
          >
            {submitting ? "Simulating..." : "Simulate Agent Call"}
          </button>
        </form>
      </section>

      {result ? (
        <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold text-zinc-950">Result</h2>
          <div className="mt-3 grid gap-3 text-sm text-zinc-700">
            <div>
              <span className="font-medium text-zinc-900">Status:</span> {result.status}
            </div>
            {result.approval_id ? (
              <div>
                <span className="font-medium text-zinc-900">Approval ID:</span>{" "}
                {result.approval_id}
              </div>
            ) : null}
            {result.content?.[0]?.text ? (
              <div>
                <span className="font-medium text-zinc-900">Message:</span>{" "}
                {result.content[0].text}
              </div>
            ) : null}
          </div>
          <div className="mt-4">
            <JsonBlock value={result} />
          </div>
        </section>
      ) : null}
    </div>
  );
}
