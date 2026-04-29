"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

const accessOptions = [
  ["allowed", "Allowed"],
  ["approval_required", "Approval required"],
  ["blocked", "Blocked"],
];

function buildAccessMap(policy, tools) {
  const allowed = new Set(policy?.allowed_tools || []);
  const approvalRequired = new Set(policy?.approval_required_tools || []);
  const blocked = new Set(policy?.blocked_tools || []);

  return Object.fromEntries(
    tools.map((tool) => {
      let access = "blocked";
      if (allowed.has(tool.name)) access = "allowed";
      if (approvalRequired.has(tool.name)) access = "approval_required";
      if (blocked.has(tool.name)) access = "blocked";
      return [tool.name, access];
    })
  );
}

function buildPolicyPayload(agentId, accessMap) {
  const payload = {
    agent_id: agentId,
    allowed_tools: [],
    approval_required_tools: [],
    blocked_tools: [],
  };

  for (const [toolName, access] of Object.entries(accessMap)) {
    if (access === "allowed") payload.allowed_tools.push(toolName);
    if (access === "approval_required") payload.approval_required_tools.push(toolName);
    if (access === "blocked") payload.blocked_tools.push(toolName);
  }

  return payload;
}

export default function PoliciesPage() {
  const [agents, setAgents] = useState([]);
  const [tools, setTools] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [accessMap, setAccessMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const [agentList, toolList, policyList] = await Promise.all([
        apiFetch("/agents"),
        apiFetch("/tools"),
        apiFetch("/policies"),
      ]);

      setAgents(agentList);
      setTools(toolList);
      setPolicies(policyList);

      const firstAgentId = selectedAgentId || agentList[0]?.id || "";
      setSelectedAgentId(firstAgentId);
      const firstPolicy = policyList.find((policy) => policy.agent_id === firstAgentId);
      setAccessMap(buildAccessMap(firstPolicy, toolList));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function selectAgent(agentId) {
    setSelectedAgentId(agentId);
    const policy = policies.find((item) => item.agent_id === agentId);
    setAccessMap(buildAccessMap(policy, tools));
    setMessage("");
    setError("");
  }

  async function savePolicy(event) {
    event.preventDefault();
    if (!selectedAgentId) return;

    setSaving(true);
    setMessage("");
    setError("");

    try {
      const payload = buildPolicyPayload(selectedAgentId, accessMap);
      const saved = await apiFetch(`/policies/${selectedAgentId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      setPolicies((current) => {
        const withoutSaved = current.filter((policy) => policy.agent_id !== saved.agent_id);
        return [...withoutSaved, saved].sort((a, b) => a.agent_id.localeCompare(b.agent_id));
      });
      setMessage(`Saved policy for ${saved.agent_id}`);
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
        <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Policies</h1>
        <p className="mt-1 text-sm text-zinc-600">Assign each tool access for an agent.</p>
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
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <label className="grid max-w-md flex-1 gap-1 text-sm font-medium text-zinc-700">
            Agent
            <select
              className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
              disabled={loading || agents.length === 0}
              onChange={(event) => selectAgent(event.target.value)}
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
          <button
            className="w-fit rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm font-medium text-zinc-800 shadow-sm hover:bg-zinc-50"
            onClick={loadData}
            suppressHydrationWarning
            type="button"
          >
            Refresh
          </button>
        </div>

        <form className="mt-5 space-y-4" onSubmit={savePolicy}>
          {tools.map((tool) => (
            <div
              className="grid gap-3 rounded-lg border border-zinc-200 p-4 md:grid-cols-[1fr_220px] md:items-center"
              key={tool.name}
            >
              <div>
                <div className="text-sm font-semibold text-zinc-950">{tool.name}</div>
                <div className="mt-1 text-sm text-zinc-600">{tool.description}</div>
              </div>
              <select
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                onChange={(event) =>
                  setAccessMap({ ...accessMap, [tool.name]: event.target.value })
                }
                suppressHydrationWarning
                value={accessMap[tool.name] || "blocked"}
              >
                {accessOptions.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          ))}

          {!loading && agents.length === 0 ? (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              Create an agent before configuring policies.
            </div>
          ) : null}
          {!loading && tools.length === 0 ? (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              Create a tool before configuring policies.
            </div>
          ) : null}
          {loading ? <div className="text-sm text-zinc-600">Loading policy data...</div> : null}

          <button
            className="rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
            disabled={saving || !selectedAgentId || tools.length === 0}
            suppressHydrationWarning
            type="submit"
          >
            {saving ? "Saving..." : "Save policy"}
          </button>
        </form>
      </section>

      <section className="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm">
        <div className="border-b border-zinc-200 px-5 py-4">
          <h2 className="text-base font-semibold text-zinc-950">Current policies</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-zinc-200 text-left text-sm">
            <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
              <tr>
                <th className="px-4 py-3 font-semibold">Agent</th>
                <th className="px-4 py-3 font-semibold">Allowed</th>
                <th className="px-4 py-3 font-semibold">Approval required</th>
                <th className="px-4 py-3 font-semibold">Blocked</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {policies.map((policy) => (
                <tr key={policy.agent_id} className="align-top">
                  <td className="whitespace-nowrap px-4 py-3 font-medium text-zinc-900">
                    {policy.agent_id}
                  </td>
                  <td className="px-4 py-3 text-zinc-700">{policy.allowed_tools.join(", ") || "-"}</td>
                  <td className="px-4 py-3 text-zinc-700">
                    {policy.approval_required_tools.join(", ") || "-"}
                  </td>
                  <td className="px-4 py-3 text-zinc-700">{policy.blocked_tools.join(", ") || "-"}</td>
                </tr>
              ))}
              {!loading && policies.length === 0 ? (
                <tr>
                  <td className="px-4 py-6 text-center text-zinc-600" colSpan="4">
                    No policies configured.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
