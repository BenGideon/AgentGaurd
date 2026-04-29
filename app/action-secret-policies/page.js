"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

export default function ActionSecretPoliciesPage() {
  const [agents, setAgents] = useState([]);
  const [actions, setActions] = useState([]);
  const [secrets, setSecrets] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [form, setForm] = useState({ agent_id: "", action_name: "", allowed_secrets: [] });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [agentList, actionList, secretList, policyList] = await Promise.all([
        apiFetch("/agents"),
        apiFetch("/actions"),
        apiFetch("/secrets"),
        apiFetch("/action-secret-policies"),
      ]);
      setAgents(agentList);
      setActions(actionList);
      setSecrets(secretList);
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

  function toggleSecret(secretName) {
    setForm((current) => {
      const selected = new Set(current.allowed_secrets);
      if (selected.has(secretName)) {
        selected.delete(secretName);
      } else {
        selected.add(secretName);
      }
      return { ...current, allowed_secrets: Array.from(selected).sort() };
    });
  }

  async function savePolicy(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");

    try {
      const saved = await apiFetch("/action-secret-policies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      setPolicies((current) => {
        const filtered = current.filter(
          (policy) => !(policy.agent_id === saved.agent_id && policy.action_name === saved.action_name)
        );
        return [...filtered, saved].sort((a, b) => `${a.agent_id}:${a.action_name}`.localeCompare(`${b.agent_id}:${b.action_name}`));
      });
      setMessage(`Saved secret policy for ${saved.action_name}`);
    } catch (err) {
      setError(err.message);
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
        <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Action Secret Policies</h1>
        <p className="mt-1 text-sm text-zinc-600">Allow specific secrets for each agent and action pair.</p>
      </div>

      {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}
      {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

      <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
        <form className="grid gap-4" onSubmit={savePolicy}>
          <div className="grid gap-4 md:grid-cols-3">
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Agent
              <select className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setForm({ ...form, agent_id: event.target.value })} suppressHydrationWarning value={form.agent_id}>
                {agents.map((agent) => <option key={agent.id} value={agent.id}>{agent.id}</option>)}
              </select>
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700 md:col-span-2">
              Action
              <select className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setForm({ ...form, action_name: event.target.value })} suppressHydrationWarning value={form.action_name}>
                {actions.map((action) => <option key={action.name} value={action.name}>{action.name}</option>)}
              </select>
            </label>
          </div>

          <div className="grid gap-2">
            <div className="text-sm font-medium text-zinc-700">Allowed secrets</div>
            <div className="grid gap-2 rounded-md border border-zinc-200 p-3 sm:grid-cols-2 lg:grid-cols-3">
              {secrets.map((secret) => (
                <label className="flex items-center gap-2 text-sm text-zinc-700" key={secret.name}>
                  <input
                    checked={form.allowed_secrets.includes(secret.name)}
                    className="h-4 w-4"
                    onChange={() => toggleSecret(secret.name)}
                    suppressHydrationWarning
                    type="checkbox"
                  />
                  <span>{secret.name}</span>
                </label>
              ))}
              {!loading && secrets.length === 0 ? <div className="text-sm text-zinc-600">No secrets created yet.</div> : null}
            </div>
          </div>

          <button className="w-fit rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:bg-zinc-400" disabled={saving || !form.agent_id || !form.action_name} suppressHydrationWarning type="submit">
            {saving ? "Saving..." : "Save secret policy"}
          </button>
        </form>
        {loading ? <div className="mt-4 text-sm text-zinc-600">Loading secret policy data...</div> : null}
      </section>

      <section className="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm">
        <div className="border-b border-zinc-200 px-5 py-4">
          <h2 className="text-base font-semibold text-zinc-950">Current secret policies</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-zinc-200 text-left text-sm">
            <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
              <tr>
                <th className="px-4 py-3 font-semibold">Agent</th>
                <th className="px-4 py-3 font-semibold">Action</th>
                <th className="px-4 py-3 font-semibold">Allowed secrets</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {policies.map((policy) => (
                <tr key={`${policy.agent_id}:${policy.action_name}`}>
                  <td className="whitespace-nowrap px-4 py-3 font-medium text-zinc-900">{policy.agent_id}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-zinc-700">{policy.action_name}</td>
                  <td className="px-4 py-3 text-zinc-700">{policy.allowed_secrets.join(", ") || "-"}</td>
                </tr>
              ))}
              {!loading && policies.length === 0 ? (
                <tr><td className="px-4 py-6 text-center text-zinc-600" colSpan="3">No action secret policies configured.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
