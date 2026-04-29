"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

const defaultSchema = `{
  "to": "string",
  "subject": "string",
  "body": "string"
}`;

export default function ToolsPage() {
  const [tools, setTools] = useState([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [inputSchema, setInputSchema] = useState(defaultSchema);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadTools() {
    setLoading(true);
    setError("");
    try {
      setTools(await apiFetch("/tools"));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function createTool(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");

    try {
      let parsedSchema = null;
      if (inputSchema.trim()) {
        parsedSchema = JSON.parse(inputSchema);
      }

      const created = await apiFetch("/tools", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim(),
          input_schema: parsedSchema,
        }),
      });

      setName("");
      setDescription("");
      setInputSchema(defaultSchema);
      setMessage(`Created tool ${created.name}`);
      await loadTools();
    } catch (err) {
      setError(err instanceof SyntaxError ? "input_schema must be valid JSON" : err.message);
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    loadTools();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Tools</h1>
        <p className="mt-1 text-sm text-zinc-600">Register tools and their optional input schemas.</p>
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
        <h2 className="text-base font-semibold text-zinc-950">Create tool</h2>
        <form className="mt-4 grid gap-4" onSubmit={createTool}>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Name
              <input
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                onChange={(event) => setName(event.target.value)}
                required
                suppressHydrationWarning
                value={name}
              />
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Description
              <input
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                onChange={(event) => setDescription(event.target.value)}
                required
                suppressHydrationWarning
                value={description}
              />
            </label>
          </div>
          <label className="grid gap-1 text-sm font-medium text-zinc-700">
            input_schema JSON
            <textarea
              className="min-h-40 rounded-md border border-zinc-300 px-3 py-2 font-mono text-sm outline-none focus:border-zinc-500"
              onChange={(event) => setInputSchema(event.target.value)}
              suppressHydrationWarning
              value={inputSchema}
            />
          </label>
          <div>
            <button
              className="rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
              disabled={saving}
              suppressHydrationWarning
              type="submit"
            >
              {saving ? "Creating..." : "Create tool"}
            </button>
          </div>
        </form>
      </section>

      <section className="grid gap-4">
        {tools.map((tool) => (
          <article key={tool.name} className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-start">
              <div>
                <h2 className="text-base font-semibold text-zinc-950">{tool.name}</h2>
                <p className="mt-1 text-sm text-zinc-600">{tool.description}</p>
              </div>
            </div>
            <pre className="mt-4 max-h-72 overflow-auto rounded-md bg-zinc-950 p-3 text-xs leading-5 text-zinc-50">
              {JSON.stringify(tool.input_schema || {}, null, 2)}
            </pre>
          </article>
        ))}
        {!loading && tools.length === 0 ? (
          <div className="rounded-lg border border-zinc-200 bg-white p-6 text-sm text-zinc-600">
            No tools registered.
          </div>
        ) : null}
        {loading ? <div className="text-sm text-zinc-600">Loading tools...</div> : null}
      </section>
    </div>
  );
}
