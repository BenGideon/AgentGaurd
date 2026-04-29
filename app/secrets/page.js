"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

export default function SecretsPage() {
  const [secrets, setSecrets] = useState([]);
  const [form, setForm] = useState({ name: "", value: "", description: "" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadSecrets() {
    setLoading(true);
    setError("");
    try {
      setSecrets(await apiFetch("/secrets"));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function createSecret(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");

    try {
      const created = await apiFetch("/secrets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name.trim(),
          value: form.value,
          description: form.description.trim() || null,
        }),
      });

      setForm({ name: "", value: "", description: "" });
      setMessage(`Created secret ${created.name}`);
      await loadSecrets();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function deleteSecret(name) {
    setMessage("");
    setError("");

    try {
      await apiFetch(`/secrets/${encodeURIComponent(name)}`, { method: "DELETE" });
      setMessage(`Deleted secret ${name}`);
      await loadSecrets();
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadSecrets();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Secrets</h1>
        <p className="mt-1 text-sm text-zinc-600">Store server-side credentials for API proxy actions.</p>
      </div>

      {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}
      {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

      <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-zinc-950">Create secret</h2>
        <form className="mt-4 grid gap-4" onSubmit={createSecret}>
          <div className="grid gap-4 md:grid-cols-3">
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
              Value
              <input
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                onChange={(event) => setForm({ ...form, value: event.target.value })}
                required
                suppressHydrationWarning
                type="password"
                value={form.value}
              />
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Description
              <input
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                suppressHydrationWarning
                value={form.description}
              />
            </label>
          </div>
          <button className="w-fit rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:bg-zinc-400" disabled={saving} suppressHydrationWarning type="submit">
            {saving ? "Creating..." : "Create secret"}
          </button>
        </form>
      </section>

      <section className="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm">
        <div className="border-b border-zinc-200 px-5 py-4">
          <h2 className="text-base font-semibold text-zinc-950">Stored secrets</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-zinc-50 text-zinc-600">
              <tr>
                <th className="px-4 py-3 font-semibold">Name</th>
                <th className="px-4 py-3 font-semibold">Description</th>
                <th className="px-4 py-3 font-semibold">Created</th>
                <th className="px-4 py-3 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {secrets.map((secret) => (
                <tr key={secret.name}>
                  <td className="whitespace-nowrap px-4 py-3 font-medium text-zinc-950">{secret.name}</td>
                  <td className="px-4 py-3 text-zinc-700">{secret.description || "-"}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-zinc-700">{new Date(secret.created_at).toLocaleString()}</td>
                  <td className="px-4 py-3">
                    <button className="rounded-md border border-red-200 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50" onClick={() => deleteSecret(secret.name)} suppressHydrationWarning type="button">
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {!loading && secrets.length === 0 ? (
                <tr><td className="px-4 py-6 text-center text-zinc-600" colSpan="4">No secrets stored.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
        {loading ? <div className="px-5 py-4 text-sm text-zinc-600">Loading secrets...</div> : null}
      </section>
    </div>
  );
}
