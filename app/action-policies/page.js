"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

const defaultConditions = `{
  "recipient_external": true
}`;

export default function ActionPoliciesPage() {
  const [agents, setAgents] = useState([]);
  const [actions, setActions] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [form, setForm] = useState({
    agent_id: "",
    action_name: "",
    effect: "approval_required",
    conditions: defaultConditions,
    priority: 10,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [agentList, actionList, policyList] = await Promise.all([
        apiFetch("/agents"),
        apiFetch("/actions"),
        apiFetch("/action-policies"),
      ]);
      setAgents(agentList);
      setActions(actionList);
      setPolicies(policyList);
      setForm((current) => ({
        ...current,
        agent_id: current.agent_id || agentList[0]?.id || "",
        action_name: current.action_name || actionList[0]?.name || "",
      }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function savePolicy(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");

    try {
      const trimmedConditions = form.conditions.trim();
      const conditions = trimmedConditions ? JSON.parse(trimmedConditions) : null;
      const saved = await apiFetch("/action-policies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_id: form.agent_id,
          action_name: form.action_name,
          effect: form.effect,
          conditions,
          priority: Number(form.priority) || 0,
        }),
      });
      setPolicies((current) => {
        const filtered = current.filter((policy) => policy.id !== saved.id);
        return [...filtered, saved].sort((a, b) => {
          const left = `${a.agent_id}:${a.action_name}:${String(999999 - (a.priority || 0)).padStart(6, "0")}`;
          const right = `${b.agent_id}:${b.action_name}:${String(999999 - (b.priority || 0)).padStart(6, "0")}`;
          return left.localeCompare(right);
        });
      });
      setMessage(`Saved ${saved.effect} policy for ${saved.action_name}`);
    } catch (err) {
      setError(err instanceof SyntaxError ? "Conditions must be valid JSON" : err.message);
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Action Policies</h1>
        <p className="mt-1 text-sm text-zinc-600">Create ordered conditional rules for gateway actions.</p>
      </div>

      {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}
      {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

      <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
        <form className="grid gap-4" onSubmit={savePolicy}>
          <div className="grid gap-4 md:grid-cols-4">
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Agent
              <select className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setForm({ ...form, agent_id: event.target.value })} suppressHydrationWarning value={form.agent_id}>
                {agents.map((agent) => <option key={agent.id} value={agent.id}>{agent.id}</option>)}
              </select>
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Action
              <select className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setForm({ ...form, action_name: event.target.value })} suppressHydrationWarning value={form.action_name}>
                {actions.map((action) => <option key={action.name} value={action.name}>{action.name}</option>)}
              </select>
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Effect
              <select className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setForm({ ...form, effect: event.target.value })} suppressHydrationWarning value={form.effect}>
                <option value="allow">allow</option>
                <option value="approval_required">approval_required</option>
                <option value="block">block</option>
              </select>
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Priority
              <input className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setForm({ ...form, priority: event.target.value })} suppressHydrationWarning type="number" value={form.priority} />
            </label>
          </div>

          <label className="grid gap-1 text-sm font-medium text-zinc-700">
            Conditions JSON
            <textarea className="min-h-40 rounded-md border border-zinc-300 px-3 py-2 font-mono text-xs outline-none focus:border-zinc-500" onChange={(event) => setForm({ ...form, conditions: event.target.value })} suppressHydrationWarning value={form.conditions} />
          </label>

          <button className="w-fit rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:bg-zinc-400" disabled={saving || !form.agent_id || !form.action_name} suppressHydrationWarning type="submit">
            {saving ? "Saving..." : "Save policy"}
          </button>
        </form>
        {loading ? <div className="mt-4 text-sm text-zinc-600">Loading action policy data...</div> : null}
      </section>

      <section className="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm">
        <div className="border-b border-zinc-200 px-5 py-4">
          <h2 className="text-base font-semibold text-zinc-950">Current action policies</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-zinc-200 text-left text-sm">
            <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
              <tr>
                <th className="px-4 py-3 font-semibold">Agent</th>
                <th className="px-4 py-3 font-semibold">Action</th>
                <th className="px-4 py-3 font-semibold">Effect</th>
                <th className="px-4 py-3 font-semibold">Priority</th>
                <th className="px-4 py-3 font-semibold">Conditions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {policies.map((policy) => (
                <tr key={policy.id || `${policy.agent_id}:${policy.action_name}:${policy.priority}`}>
                  <td className="whitespace-nowrap px-4 py-3 font-medium text-zinc-900">{policy.agent_id}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-zinc-700">{policy.action_name}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-zinc-700">{policy.effect}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-zinc-700">{policy.priority}</td>
                  <td className="min-w-80 px-4 py-3">
                    <code className="whitespace-pre-wrap break-words text-xs text-zinc-700">{JSON.stringify(policy.conditions || {})}</code>
                  </td>
                </tr>
              ))}
              {!loading && policies.length === 0 ? (
                <tr><td className="px-4 py-6 text-center text-zinc-600" colSpan="5">No action policies configured.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
