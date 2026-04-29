"use client";

import { useEffect, useState } from "react";
import { Fragment } from "react";
import StatusBadge from "../components/StatusBadge";
import { apiFetch } from "../lib/api";

function JsonBlock({ value }) {
  return (
    <pre className="max-h-72 overflow-auto rounded-md bg-zinc-950 p-3 text-xs leading-5 text-zinc-50">
      {JSON.stringify(value || {}, null, 2)}
    </pre>
  );
}

function ResultSummary({ result }) {
  if (!result) {
    return <span className="text-xs text-zinc-400">-</span>;
  }

  return (
    <div className="grid gap-1 text-xs text-zinc-700">
      <span className="font-medium text-zinc-900">{result.message || result.status}</span>
      {result.draft_id ? <span>Draft ID: {result.draft_id}</span> : null}
    </div>
  );
}

export default function LogsPage() {
  const [logs, setLogs] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadLogs() {
    setLoading(true);
    setError("");
    try {
      setLogs(await apiFetch("/logs"));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLogs();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Audit Logs</h1>
          <p className="mt-1 text-sm text-zinc-600">{logs.length} entries</p>
        </div>
        <button className="w-fit rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm font-medium text-zinc-800 shadow-sm hover:bg-zinc-50" onClick={loadLogs} suppressHydrationWarning type="button">
          Refresh
        </button>
      </div>

      {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
      {loading ? <div className="text-sm text-zinc-600">Loading logs...</div> : null}

      <div className="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-zinc-200 text-left text-sm">
            <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
              <tr>
                <th className="px-4 py-3 font-semibold">Timestamp</th>
                <th className="px-4 py-3 font-semibold">Agent</th>
                <th className="px-4 py-3 font-semibold">Action</th>
                <th className="px-4 py-3 font-semibold">Status</th>
                <th className="px-4 py-3 font-semibold">Policy</th>
                <th className="px-4 py-3 font-semibold">Risk</th>
                <th className="px-4 py-3 font-semibold">Approved / Rejected By</th>
                <th className="px-4 py-3 font-semibold">Result</th>
                <th className="px-4 py-3 font-semibold">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {logs.map((log) => (
                <Fragment key={log.id}>
                  <tr key={log.id} className="align-top">
                    <td className="whitespace-nowrap px-4 py-3 text-zinc-600">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="whitespace-nowrap px-4 py-3 font-medium text-zinc-900">{log.agent_id}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-zinc-700">{log.action_name || log.tool}</td>
                    <td className="whitespace-nowrap px-4 py-3"><StatusBadge status={log.status} /></td>
                    <td className="whitespace-nowrap px-4 py-3 text-xs text-zinc-700">
                      {log.policy_effect ? <div>{log.policy_effect}</div> : "-"}
                      {log.matched_policy_id ? <div>Policy #{log.matched_policy_id}</div> : null}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-xs text-zinc-700">{log.risk_level || "-"}</td>
                    <td className="min-w-48 px-4 py-3 text-xs text-zinc-700">
                      {log.approved_by_user_id ? <div>Approved: {log.approved_by_user_id}</div> : null}
                      {log.rejected_by_user_id ? <div>Rejected: {log.rejected_by_user_id}</div> : null}
                      {!log.approved_by_user_id && !log.rejected_by_user_id ? "-" : null}
                    </td>
                    <td className="min-w-48 px-4 py-3"><ResultSummary result={log.execution_result || log.tool_result} /></td>
                    <td className="px-4 py-3">
                      <button className="rounded-md border border-zinc-300 px-2 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-50" onClick={() => setExpandedId(expandedId === log.id ? null : log.id)} suppressHydrationWarning type="button">
                        {expandedId === log.id ? "Hide" : "Expand"}
                      </button>
                    </td>
                  </tr>
                  {expandedId === log.id ? (
                    <tr key={`${log.id}-details`}>
                      <td className="bg-zinc-50 px-4 py-4" colSpan="9">
                        <div className="grid gap-4 lg:grid-cols-4">
                          <div>
                            <div className="mb-2 text-xs font-semibold uppercase text-zinc-500">Original input</div>
                            <JsonBlock value={log.original_input || log.input} />
                          </div>
                          <div>
                            <div className="mb-2 text-xs font-semibold uppercase text-zinc-500">Final input</div>
                            <JsonBlock value={log.final_input || log.input} />
                          </div>
                          <div>
                            <div className="mb-2 text-xs font-semibold uppercase text-zinc-500">Execution result</div>
                            <JsonBlock value={log.execution_result || log.tool_result} />
                          </div>
                          <div>
                            <div className="mb-2 text-xs font-semibold uppercase text-zinc-500">Policy match</div>
                            <JsonBlock value={log.policy_match} />
                          </div>
                        </div>
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              ))}
              {!loading && logs.length === 0 ? (
                <tr><td className="px-4 py-6 text-center text-zinc-600" colSpan="9">No audit logs.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
