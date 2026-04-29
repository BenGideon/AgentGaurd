"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

export default function ConnectorsPage() {
  const [connectors, setConnectors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const gmail = connectors.find((connector) => connector.provider === "gmail");

  async function loadConnectors() {
    setLoading(true);
    setError("");
    try {
      setConnectors(await apiFetch("/connectors"));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function connectGmail() {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await apiFetch("/connectors/gmail/connect");
      window.location.href = result.url;
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  async function disconnectGmail() {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await apiFetch("/connectors/gmail", { method: "DELETE" });
      setMessage("Gmail disconnected");
      await loadConnectors();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    loadConnectors();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Connectors</h1>
        <p className="mt-1 text-sm text-zinc-600">Connect workspace accounts used by AgentGuard executors.</p>
      </div>

      {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}
      {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

      <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-base font-semibold text-zinc-950">Gmail</h2>
            {gmail ? (
              <p className="mt-1 text-sm text-zinc-600">
                Connected as {gmail.connected_email || "Gmail account"}
              </p>
            ) : (
              <p className="mt-1 text-sm text-zinc-600">Not connected</p>
            )}
          </div>
          {gmail ? (
            <button
              className="w-fit rounded-md border border-red-200 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={busy}
              onClick={disconnectGmail}
              suppressHydrationWarning
              type="button"
            >
              Disconnect
            </button>
          ) : (
            <button
              className="w-fit rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
              disabled={busy || loading}
              onClick={connectGmail}
              suppressHydrationWarning
              type="button"
            >
              Connect Gmail
            </button>
          )}
        </div>
      </section>
    </div>
  );
}
