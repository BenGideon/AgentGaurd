"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

const alertEvents = [
  { value: "blocked", label: "Action blocked" },
  { value: "approval_required", label: "Approval required" },
  { value: "critical_risk", label: "Critical risk attempted" },
  { value: "approved", label: "Approval completed" },
];

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [form, setForm] = useState({
    name: "",
    url: "",
    events: ["blocked", "approval_required"],
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadAlerts() {
    setLoading(true);
    setError("");
    try {
      setAlerts(await apiFetch("/alerts"));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function toggleEvent(eventName) {
    setForm((current) => {
      const hasEvent = current.events.includes(eventName);
      return {
        ...current,
        events: hasEvent
          ? current.events.filter((item) => item !== eventName)
          : [...current.events, eventName],
      };
    });
  }

  async function createAlert(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");

    try {
      const created = await apiFetch("/alerts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name.trim(),
          url: form.url.trim(),
          events: form.events,
        }),
      });

      setForm({ name: "", url: "", events: ["blocked", "approval_required"] });
      setMessage(`Created alert ${created.name}`);
      await loadAlerts();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function deleteAlert(alert) {
    setMessage("");
    setError("");
    try {
      await apiFetch(`/alerts/${alert.id}`, { method: "DELETE" });
      setMessage(`Deleted alert ${alert.name}`);
      await loadAlerts();
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadAlerts();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Alerts</h1>
        <p className="mt-1 text-sm text-zinc-600">Send webhook notifications when important agent events happen.</p>
      </div>

      {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}
      {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

      <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-zinc-950">Create webhook alert</h2>
        <form className="mt-4 grid gap-4" onSubmit={createAlert}>
          <div className="grid gap-4 md:grid-cols-2">
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
              Webhook URL
              <input
                className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500"
                onChange={(event) => setForm({ ...form, url: event.target.value })}
                placeholder="https://hooks.slack.com/services/..."
                required
                suppressHydrationWarning
                type="url"
                value={form.url}
              />
            </label>
          </div>

          <fieldset className="grid gap-3">
            <legend className="text-sm font-medium text-zinc-700">Events</legend>
            <div className="grid gap-2 md:grid-cols-2">
              {alertEvents.map((event) => (
                <label className="flex items-center gap-2 rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-700" key={event.value}>
                  <input
                    checked={form.events.includes(event.value)}
                    onChange={() => toggleEvent(event.value)}
                    suppressHydrationWarning
                    type="checkbox"
                  />
                  {event.label}
                </label>
              ))}
            </div>
          </fieldset>

          <button
            className="w-fit rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:bg-zinc-400"
            disabled={saving || form.events.length === 0}
            suppressHydrationWarning
            type="submit"
          >
            {saving ? "Creating..." : "Create alert"}
          </button>
        </form>
      </section>

      <section className="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm">
        <div className="border-b border-zinc-200 px-5 py-4">
          <h2 className="text-base font-semibold text-zinc-950">Configured alerts</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-zinc-50 text-zinc-600">
              <tr>
                <th className="px-4 py-3 font-semibold">Name</th>
                <th className="px-4 py-3 font-semibold">Events</th>
                <th className="px-4 py-3 font-semibold">Webhook URL</th>
                <th className="px-4 py-3 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {alerts.map((alert) => (
                <tr key={alert.id}>
                  <td className="whitespace-nowrap px-4 py-3 font-medium text-zinc-950">{alert.name}</td>
                  <td className="px-4 py-3 text-zinc-700">{(alert.events || []).join(", ")}</td>
                  <td className="max-w-md truncate px-4 py-3 font-mono text-xs text-zinc-600">{alert.url}</td>
                  <td className="px-4 py-3">
                    <button className="rounded-md border border-red-200 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50" onClick={() => deleteAlert(alert)} suppressHydrationWarning type="button">
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {!loading && alerts.length === 0 ? (
                <tr><td className="px-4 py-6 text-center text-zinc-600" colSpan="4">No alerts configured.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
        {loading ? <div className="px-5 py-4 text-sm text-zinc-600">Loading alerts...</div> : null}
      </section>
    </div>
  );
}
