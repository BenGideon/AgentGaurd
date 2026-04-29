"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

const emptyForm = { id: "", name: "", api_key: "" };

export default function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadAgents() {
    setLoading(true);
    setError("");
    try {
      setAgents(await apiFetch("/agents"));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function createAgent(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");

    try {
      const body = {
        id: form.id.trim(),
        name: form.name.trim(),
      };
      if (form.api_key.trim()) {
        body.api_key = form.api_key.trim();
      }

      const created = await apiFetch("/agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      setForm(emptyForm);
      setMessage(`Created agent ${created.id}`);
      await loadAgents();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function copyKey(apiKey) {
    await navigator.clipboard.writeText(apiKey);
    setMessage("API key copied");
  }

  useEffect(() => {
    loadAgents();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Agents</h1>
        <p className="mt-1 text-sm text-zinc-600">Register agents and copy their API keys.</p>
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
        <h2 className="text-base font-semibold text-zinc-950">Create agent</h2>
        <form className="mt-4 grid gap-4 md:grid-cols-3" onSubmit={createAgent}>
          <label className="grid gap-1 text-sm font-medium text-zinc-700">
            Agent ID
            <input
              className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
              onChange={(event) => setForm({ ...form, id: event.target.value })}
              required
              suppressHydrationWarning
              value={form.id}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium text-zinc-700">
            Name
            <input
              className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              required
              suppressHydrationWarning
              value={form.name}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium text-zinc-700">
            API key
            <input
              className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
              onChange={(event) => setForm({ ...form, api_key: event.target.value })}
              placeholder="Optional"
              suppressHydrationWarning
              value={form.api_key}
            />
          </label>
          <div className="md:col-span-3">
            <button
              className="rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
              disabled={saving}
              suppressHydrationWarning
              type="submit"
            >
              {saving ? "Creating..." : "Create agent"}
            </button>
          </div>
        </form>
      </section>

      <section className="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm">
        <div className="border-b border-zinc-200 px-5 py-4">
          <h2 className="text-base font-semibold text-zinc-950">Registered agents</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-zinc-200 text-left text-sm">
            <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
              <tr>
                <th className="px-4 py-3 font-semibold">ID</th>
                <th className="px-4 py-3 font-semibold">Name</th>
                <th className="px-4 py-3 font-semibold">API key</th>
                <th className="px-4 py-3 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {agents.map((agent) => (
                <tr key={agent.id} className="align-top">
                  <td className="whitespace-nowrap px-4 py-3 font-medium text-zinc-900">
                    {agent.id}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-zinc-700">{agent.name}</td>
                  <td className="px-4 py-3">
                    <code className="break-all text-xs text-zinc-700">{agent.api_key}</code>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <button
                      className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm font-medium text-zinc-800 hover:bg-zinc-50"
                      onClick={() => copyKey(agent.api_key)}
                      suppressHydrationWarning
                      type="button"
                    >
                      Copy key
                    </button>
                  </td>
                </tr>
              ))}
              {!loading && agents.length === 0 ? (
                <tr>
                  <td className="px-4 py-6 text-center text-zinc-600" colSpan="4">
                    No agents registered.
                  </td>
                </tr>
              ) : null}
              {loading ? (
                <tr>
                  <td className="px-4 py-6 text-center text-zinc-600" colSpan="4">
                    Loading agents...
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
