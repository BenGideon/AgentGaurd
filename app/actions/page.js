"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

const defaultSchema = `{
  "to": "string",
  "subject": "string",
  "body": "string"
}`;

export default function ActionsPage() {
  const [actions, setActions] = useState([]);
  const [form, setForm] = useState({
    name: "sales.create_gmail_draft",
    description: "Creates a Gmail draft email. Does not send.",
    executor_type: "gmail_draft",
    risk_level: "medium",
    input_schema: defaultSchema,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadActions() {
    setLoading(true);
    setError("");
    try {
      setActions(await apiFetch("/actions"));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function createAction(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");

    try {
      const inputSchema = form.input_schema.trim() ? JSON.parse(form.input_schema) : null;
      const created = await apiFetch("/actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name.trim(),
          description: form.description.trim(),
          executor_type: form.executor_type,
          risk_level: form.risk_level,
          input_schema: inputSchema,
        }),
      });

      setMessage(`Created action ${created.name}`);
      await loadActions();
    } catch (err) {
      setError(err instanceof SyntaxError ? "input_schema must be valid JSON" : err.message);
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    loadActions();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Actions</h1>
        <p className="mt-1 text-sm text-zinc-600">Create generic gateway actions.</p>
      </div>

      {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}
      {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

      <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-zinc-950">Create action</h2>
        <form className="mt-4 grid gap-4" onSubmit={createAction}>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Name
              <input className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setForm({ ...form, name: event.target.value })} required suppressHydrationWarning value={form.name} />
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Description
              <input className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setForm({ ...form, description: event.target.value })} required suppressHydrationWarning value={form.description} />
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Executor type
              <select className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setForm({ ...form, executor_type: event.target.value })} suppressHydrationWarning value={form.executor_type}>
                <option value="gmail_draft">gmail_draft</option>
                <option value="mock">mock</option>
                <option value="webhook">webhook</option>
                <option value="api_proxy">api_proxy</option>
              </select>
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Risk level
              <select className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setForm({ ...form, risk_level: event.target.value })} suppressHydrationWarning value={form.risk_level}>
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
                <option value="critical">critical</option>
              </select>
            </label>
          </div>
          <label className="grid gap-1 text-sm font-medium text-zinc-700">
            input_schema JSON
            <textarea className="min-h-40 rounded-md border border-zinc-300 px-3 py-2 font-mono text-sm outline-none focus:border-zinc-500" onChange={(event) => setForm({ ...form, input_schema: event.target.value })} suppressHydrationWarning value={form.input_schema} />
          </label>
          <button className="w-fit rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:bg-zinc-400" disabled={saving} suppressHydrationWarning type="submit">
            {saving ? "Creating..." : "Create action"}
          </button>
        </form>
      </section>

      <section className="grid gap-4">
        {actions.map((action) => (
          <article className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm" key={action.name}>
            <div className="flex flex-col justify-between gap-2 sm:flex-row">
              <div>
                <h2 className="text-base font-semibold text-zinc-950">{action.name}</h2>
                <p className="mt-1 text-sm text-zinc-600">{action.description}</p>
              </div>
              <div className="text-sm text-zinc-600">{action.executor_type} · {action.risk_level}</div>
            </div>
            <pre className="mt-4 max-h-72 overflow-auto rounded-md bg-zinc-950 p-3 text-xs leading-5 text-zinc-50">{JSON.stringify(action.input_schema || {}, null, 2)}</pre>
          </article>
        ))}
        {!loading && actions.length === 0 ? <div className="rounded-lg border border-zinc-200 bg-white p-6 text-sm text-zinc-600">No actions registered.</div> : null}
        {loading ? <div className="text-sm text-zinc-600">Loading actions...</div> : null}
      </section>
    </div>
  );
}
