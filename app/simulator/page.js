"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

const defaultInput = `{
  "to": "customer@gmail.com",
  "subject": "Follow up",
  "body": "Hi"
}`;

export default function SimulatorPage() {
  const [agents, setAgents] = useState([]);
  const [actions, setActions] = useState([]);
  const [form, setForm] = useState({
    agent_id: "",
    action: "",
    input: defaultInput,
  });
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [agentList, actionList] = await Promise.all([
        apiFetch("/agents"),
        apiFetch("/actions"),
      ]);
      setAgents(agentList);
      setActions(actionList);
      setForm((current) => ({
        ...current,
        agent_id: current.agent_id || agentList[0]?.id || "",
        action: current.action || actionList[0]?.name || "",
      }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function simulate(event) {
    event.preventDefault();
    setSimulating(true);
    setError("");
    setResult(null);

    try {
      const input = form.input.trim() ? JSON.parse(form.input) : {};
      const response = await apiFetch("/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_id: form.agent_id,
          action: form.action,
          input,
        }),
      });
      setResult(response);
      setForm((current) => ({ ...current, input: JSON.stringify(input, null, 2) }));
    } catch (err) {
      setError(err instanceof SyntaxError ? "Input must be valid JSON" : err.message);
    } finally {
      setSimulating(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Policy Simulator</h1>
        <p className="mt-1 text-sm text-zinc-600">Preview risk and policy decisions without executing actions.</p>
      </div>

      {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

      <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
        <form className="grid gap-4" onSubmit={simulate}>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Agent
              <select
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                disabled={loading}
                onChange={(event) => setForm({ ...form, agent_id: event.target.value })}
                suppressHydrationWarning
                value={form.agent_id}
              >
                {agents.map((agent) => <option key={agent.id} value={agent.id}>{agent.id}</option>)}
              </select>
            </label>

            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Action
              <select
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                disabled={loading}
                onChange={(event) => setForm({ ...form, action: event.target.value })}
                suppressHydrationWarning
                value={form.action}
              >
                {actions.map((action) => <option key={action.name} value={action.name}>{action.name}</option>)}
              </select>
            </label>
          </div>

          <label className="grid gap-1 text-sm font-medium text-zinc-700">
            Input JSON
            <textarea
              className="min-h-56 rounded-md border border-zinc-300 px-3 py-2 font-mono text-xs outline-none focus:border-zinc-500"
              onChange={(event) => setForm({ ...form, input: event.target.value })}
              suppressHydrationWarning
              value={form.input}
            />
          </label>

          <button
            className="w-fit rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:bg-zinc-400"
            disabled={simulating || loading || !form.agent_id || !form.action}
            suppressHydrationWarning
            type="submit"
          >
            {simulating ? "Simulating..." : "Simulate"}
          </button>
        </form>
        {loading ? <div className="mt-4 text-sm text-zinc-600">Loading simulator data...</div> : null}
      </section>

      {result ? (
        <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold text-zinc-950">Simulation result</h2>
          <dl className="mt-4 grid gap-3 text-sm md:grid-cols-2">
            <div>
              <dt className="font-medium text-zinc-500">Decision</dt>
              <dd className="mt-1 font-semibold text-zinc-950">{result.decision}</dd>
            </div>
            <div>
              <dt className="font-medium text-zinc-500">Risk</dt>
              <dd className="mt-1 font-semibold text-zinc-950">{result.risk_level}</dd>
            </div>
            <div className="md:col-span-2">
              <dt className="font-medium text-zinc-500">Matched policy</dt>
              <dd className="mt-1 font-mono text-xs text-zinc-800">
                {result.matched_policy ? JSON.stringify(result.matched_policy, null, 2) : "No matching policy"}
              </dd>
            </div>
            <div className="md:col-span-2">
              <dt className="font-medium text-zinc-500">Reason</dt>
              <dd className="mt-1 text-zinc-800">{result.reason}</dd>
            </div>
          </dl>
        </section>
      ) : null}
    </div>
  );
}
