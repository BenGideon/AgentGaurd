"use client";

import { useUser } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

function JsonBlock({ value }) {
  return (
    <pre className="max-h-48 overflow-auto rounded-md bg-zinc-950 p-3 text-xs leading-5 text-zinc-50">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

export default function ApprovalsPage() {
  const { isSignedIn, isLoaded } = useUser();
  const [approvals, setApprovals] = useState([]);
  const [workspaceUser, setWorkspaceUser] = useState(null);
  const [drafts, setDrafts] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [message, setMessage] = useState("");

  function hydrateDrafts(pendingApprovals) {
    const nextDrafts = {};
    pendingApprovals.forEach((approval) => {
      const input = approval.current_input || approval.input || {};
      nextDrafts[approval.id] = {
        input,
        json: JSON.stringify(input, null, 2),
      };
    });
    setDrafts(nextDrafts);
  }

  async function loadApprovals() {
    setLoading(true);
    setError("");
    try {
      const [me, pendingApprovals] = await Promise.all([
        apiFetch("/me"),
        apiFetch("/approvals?status=pending"),
      ]);
      setWorkspaceUser(me);
      setApprovals(pendingApprovals);
      hydrateDrafts(pendingApprovals);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function updateGmailDraft(id, field, value) {
    setDrafts((current) => ({
      ...current,
      [id]: {
        ...current[id],
        input: {
          ...(current[id]?.input || {}),
          [field]: value,
        },
      },
    }));
  }

  function updateJsonDraft(id, value) {
    setDrafts((current) => ({
      ...current,
      [id]: {
        ...(current[id] || {}),
        json: value,
      },
    }));
  }

  function getDraftInput(approval) {
    const draft = drafts[approval.id];
    const isGmailDraft = approval.tool === "create_gmail_draft" || approval.action_name?.includes("gmail");
    if (isGmailDraft) {
      return draft?.input || approval.current_input || approval.input || {};
    }
    return JSON.parse(draft?.json || "{}");
  }

  async function saveApprovalInput(approval) {
    setBusyId(approval.id);
    setError("");
    setMessage("");
    try {
      const input = getDraftInput(approval);
      const updated = await apiFetch(`/approvals/${approval.id}/input`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input }),
      });
      setApprovals((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setDrafts((current) => ({
        ...current,
        [updated.id]: {
          input: updated.current_input,
          json: JSON.stringify(updated.current_input, null, 2),
        },
      }));
      setMessage(`Saved changes for approval #${approval.id}`);
    } catch (err) {
      setError(err instanceof SyntaxError ? "Input JSON must be valid" : err.message);
    } finally {
      setBusyId(null);
    }
  }

  async function decideApproval(approval, action) {
    setBusyId(approval.id);
    setError("");
    setLastResult(null);
    setMessage("");
    try {
      const result = await apiFetch(`/approvals/${approval.id}/${action}`, { method: "POST" });
      setLastResult(result);
      await loadApprovals();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  useEffect(() => {
    if (isLoaded && isSignedIn) {
      loadApprovals();
    } else if (isLoaded && !isSignedIn) {
      setLoading(false);
    }
  }, [isLoaded, isSignedIn]);

  const canReview = workspaceUser && ["admin", "reviewer"].includes(workspaceUser.role);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Approvals</h1>
          <p className="mt-1 text-sm text-zinc-600">
            {approvals.length} pending{workspaceUser ? ` · role: ${workspaceUser.role}` : ""}
          </p>
        </div>
        <button
          className="w-fit rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm font-medium text-zinc-800 shadow-sm hover:bg-zinc-50"
          onClick={loadApprovals}
          suppressHydrationWarning
          type="button"
        >
          Refresh
        </button>
      </div>

      {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
      {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}
      {isLoaded && !isSignedIn ? <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">Sign in to review approvals.</div> : null}
      {workspaceUser?.role === "viewer" ? <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">Viewers can inspect approvals but cannot edit, approve, or reject them.</div> : null}
      {lastResult ? (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
          <div className="font-medium">{lastResult.status === "completed" ? "Approval completed" : "Approval updated"}</div>
          {lastResult.result || lastResult.tool_result ? <JsonBlock value={lastResult.result || lastResult.tool_result} /> : null}
        </div>
      ) : null}

      {loading ? <div className="text-sm text-zinc-600">Loading approvals...</div> : null}
      {!loading && approvals.length === 0 ? <div className="rounded-lg border border-zinc-200 bg-white p-6 text-sm text-zinc-600">No pending approvals.</div> : null}

      <section className="grid gap-4">
        {approvals.map((approval) => {
          const isGmailDraft = approval.tool === "create_gmail_draft" || approval.action_name?.includes("gmail");
          const draft = drafts[approval.id] || { input: approval.current_input || approval.input || {}, json: "{}" };

          return (
            <article key={approval.id} className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
              <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
                <div className="space-y-2">
                  <div className="text-sm font-semibold text-zinc-950">Approval #{approval.id}</div>
                  <div className="grid gap-x-6 gap-y-1 text-sm text-zinc-600 sm:grid-cols-2">
                    <div><span className="font-medium text-zinc-800">Agent:</span> {approval.agent_id}</div>
                    <div><span className="font-medium text-zinc-800">Action:</span> {approval.action_name || approval.tool}</div>
                    <div className="sm:col-span-2"><span className="font-medium text-zinc-800">Created:</span> {new Date(approval.created_at || approval.timestamp).toLocaleString()}</div>
                  </div>
                </div>
              </div>

              <div className="mt-4 grid gap-4">
                <div>
                  <div className="mb-2 text-xs font-semibold uppercase text-zinc-500">Original proposal</div>
                  <JsonBlock value={approval.original_input || approval.input} />
                </div>

                {isGmailDraft ? (
                  <div className="grid gap-3">
                    <label className="grid gap-1 text-sm font-medium text-zinc-700">
                      To
                      <input className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" disabled={!canReview} onChange={(event) => updateGmailDraft(approval.id, "to", event.target.value)} suppressHydrationWarning value={draft.input?.to || ""} />
                    </label>
                    <label className="grid gap-1 text-sm font-medium text-zinc-700">
                      Subject
                      <input className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" disabled={!canReview} onChange={(event) => updateGmailDraft(approval.id, "subject", event.target.value)} suppressHydrationWarning value={draft.input?.subject || ""} />
                    </label>
                    <label className="grid gap-1 text-sm font-medium text-zinc-700">
                      Body
                      <textarea className="min-h-36 rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" disabled={!canReview} onChange={(event) => updateGmailDraft(approval.id, "body", event.target.value)} suppressHydrationWarning value={draft.input?.body || ""} />
                    </label>
                  </div>
                ) : (
                  <label className="grid gap-1 text-sm font-medium text-zinc-700">
                    Editable input JSON
                    <textarea className="min-h-48 rounded-md border border-zinc-300 px-3 py-2 font-mono text-xs outline-none focus:border-zinc-500" disabled={!canReview} onChange={(event) => updateJsonDraft(approval.id, event.target.value)} suppressHydrationWarning value={draft.json} />
                  </label>
                )}
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <button className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm font-medium text-zinc-800 shadow-sm hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50" disabled={busyId === approval.id || !canReview} onClick={() => saveApprovalInput(approval)} suppressHydrationWarning type="button">
                  Save Changes
                </button>
                <button className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-emerald-300" disabled={busyId === approval.id || !canReview} onClick={() => decideApproval(approval, "approve")} suppressHydrationWarning type="button">
                  {isGmailDraft ? "Approve & Create Draft" : "Approve & Execute"}
                </button>
                <button className="rounded-md bg-red-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-red-300" disabled={busyId === approval.id || !canReview} onClick={() => decideApproval(approval, "reject")} suppressHydrationWarning type="button">
                  Reject
                </button>
              </div>
            </article>
          );
        })}
      </section>
    </div>
  );
}
