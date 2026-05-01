"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../lib/api";

const demoAction = "sales.create_gmail_draft";
const demoAgentId = "sales_agent";

const emptyDraft = {
  to: "",
  subject: "",
  body: "",
};

function JsonBlock({ value }) {
  return (
    <pre className="max-h-72 overflow-auto rounded-md bg-zinc-950 p-3 text-xs leading-5 text-zinc-50">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

function StepPill({ active, done, label, number }) {
  return (
    <div className={`flex items-center gap-2 rounded-md border px-3 py-2 text-sm ${active ? "border-zinc-950 bg-zinc-950 text-white" : done ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-zinc-200 bg-white text-zinc-600"}`}>
      <span className="flex h-6 w-6 items-center justify-center rounded-full border border-current text-xs">{number}</span>
      {label}
    </div>
  );
}

export default function DemoPage() {
  const [agents, setAgents] = useState([]);
  const [customerEmail, setCustomerEmail] = useState("customer@gmail.com");
  const [context, setContext] = useState("follow up after pricing call");
  const [draft, setDraft] = useState(emptyDraft);
  const [simulation, setSimulation] = useState(null);
  const [actionResult, setActionResult] = useState(null);
  const [approval, setApproval] = useState(null);
  const [approvalResult, setApprovalResult] = useState(null);
  const [demoStatus, setDemoStatus] = useState(null);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const salesAgent = useMemo(
    () => agents.find((agent) => agent.id === demoAgentId) || agents[0],
    [agents]
  );

  const currentStage = approvalResult ? 5 : approval ? 4 : actionResult ? 3 : simulation ? 3 : draft.to ? 2 : 1;

  async function loadAgents() {
    try {
      const [agentList, status] = await Promise.all([
        apiFetch("/agents"),
        apiFetch("/demo/status"),
      ]);
      setAgents(agentList);
      setDemoStatus(status);
    } catch (err) {
      setError(err.message);
    }
  }

  async function generateEmail(event) {
    event.preventDefault();
    setLoading("generate");
    setError("");
    setMessage("");
    setSimulation(null);
    setActionResult(null);
    setApproval(null);
    setApprovalResult(null);

    try {
      const generated = await apiFetch("/demo/generate-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: customerEmail, context }),
      });
      setDraft(generated);
      setMessage("Email generated. Review and edit the preview before simulating policy.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  async function simulatePolicy() {
    setLoading("simulate");
    setError("");
    setMessage("");
    setSimulation(null);

    try {
      const result = await apiFetch("/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_id: demoAgentId,
          action: demoAction,
          input: draft,
        }),
      });
      setSimulation(result);
      setMessage(`Simulation complete: ${result.decision}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  async function sendToAgentGuard() {
    setLoading("send");
    setError("");
    setMessage("");
    setActionResult(null);
    setApproval(null);
    setApprovalResult(null);

    try {
      if (!salesAgent?.api_key) {
        throw new Error("Demo sales agent is not available yet");
      }

      const result = await apiFetch("/actions/call", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-agent-key": salesAgent.api_key,
        },
        body: JSON.stringify({
          action: demoAction,
          input: draft,
        }),
      });
      setActionResult(result);

      if (result.status === "pending_approval") {
        await loadApproval(result.approval_id);
        setMessage(`Approval #${result.approval_id} created. Webhook alert sent if configured.`);
      } else if (result.status === "completed") {
        setApprovalResult(result);
        setMessage("Action completed immediately. Webhook alert sent if configured.");
      } else {
        setMessage(`Action result: ${result.status}`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  async function loadApproval(approvalId) {
    const approvals = await apiFetch("/approvals?status=pending");
    const found = approvals.find((item) => item.id === approvalId) || approvals.find((item) => item.action_name === demoAction);
    if (!found) {
      throw new Error("Approval was created but could not be loaded");
    }
    setApproval(found);
    setDraft(found.current_input || found.input || draft);
  }

  async function approveDraft() {
    setLoading("approve");
    setError("");
    setMessage("");

    try {
      if (!approval) {
        throw new Error("No approval selected");
      }
      await apiFetch(`/approvals/${approval.id}/input`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: draft }),
      });
      const result = await apiFetch(`/approvals/${approval.id}/approve`, { method: "POST" });
      setApprovalResult(result);
      setApproval(null);
      setMessage("Draft created successfully. Approval-completed alert sent if configured.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  async function rejectDraft() {
    setLoading("reject");
    setError("");
    setMessage("");
    try {
      if (!approval) {
        throw new Error("No approval selected");
      }
      const result = await apiFetch(`/approvals/${approval.id}/reject`, { method: "POST" });
      setApprovalResult(result);
      setApproval(null);
      setMessage("Approval rejected.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  useEffect(() => {
    loadAgents();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Demo: AI Sales Email Agent</h1>
        <p className="mt-1 text-sm text-zinc-600">
          AI proposes an email, AgentGuard simulates policy, asks for approval, creates a Gmail draft, sends alerts, and records logs.
        </p>
      </div>

      <div className="grid gap-2 md:grid-cols-5">
        <StepPill active={currentStage === 1} done={currentStage > 1} label="Generate" number="1" />
        <StepPill active={currentStage === 2} done={currentStage > 2} label="Simulate" number="2" />
        <StepPill active={currentStage === 3} done={currentStage > 3} label="Review" number="3" />
        <StepPill active={currentStage === 4} done={currentStage > 4} label="Approve" number="4" />
        <StepPill active={currentStage === 5} done={false} label="Done" number="5" />
      </div>

      {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}
      {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
      {demoStatus?.demo_mode ? (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          {demoStatus.message}
        </div>
      ) : null}

      <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-zinc-950">1. Generate sales email</h2>
        <form className="mt-4 grid gap-4" onSubmit={generateEmail}>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Customer email
              <input className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setCustomerEmail(event.target.value)} required suppressHydrationWarning type="email" value={customerEmail} />
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Context
              <input className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setContext(event.target.value)} required suppressHydrationWarning value={context} />
            </label>
          </div>
          <button className="w-fit rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:bg-zinc-400" disabled={loading === "generate"} suppressHydrationWarning type="submit">
            {loading === "generate" ? "Generating..." : "Generate Email"}
          </button>
        </form>
      </section>

      {draft.to ? (
        <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
            <div>
              <h2 className="text-base font-semibold text-zinc-950">2. Editable email preview</h2>
              <p className="mt-1 text-sm text-zinc-600">This is the payload the agent wants to submit.</p>
            </div>
            <button className="w-fit rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm font-medium text-zinc-800 shadow-sm hover:bg-zinc-50 disabled:opacity-50" disabled={loading === "simulate"} onClick={simulatePolicy} suppressHydrationWarning type="button">
              {loading === "simulate" ? "Simulating..." : "Simulate Policy"}
            </button>
          </div>
          <div className="mt-4 grid gap-3">
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              To
              <input className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setDraft({ ...draft, to: event.target.value })} suppressHydrationWarning value={draft.to} />
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Subject
              <input className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setDraft({ ...draft, subject: event.target.value })} suppressHydrationWarning value={draft.subject} />
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Body
              <textarea className="min-h-40 rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setDraft({ ...draft, body: event.target.value })} suppressHydrationWarning value={draft.body} />
            </label>
          </div>
        </section>
      ) : null}

      {simulation ? (
        <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
            <div>
              <h2 className="text-base font-semibold text-zinc-950">3. Policy simulation</h2>
              <div className="mt-2 grid gap-1 text-sm text-zinc-700">
                <div><span className="font-medium text-zinc-950">Decision:</span> {simulation.decision}</div>
                <div><span className="font-medium text-zinc-950">Risk:</span> {simulation.risk_level}</div>
                <div><span className="font-medium text-zinc-950">Reason:</span> {simulation.reason}</div>
              </div>
            </div>
            <button className="w-fit rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:bg-zinc-400" disabled={loading === "send"} onClick={sendToAgentGuard} suppressHydrationWarning type="button">
              {loading === "send" ? "Sending..." : "Send to AgentGuard"}
            </button>
          </div>
          <div className="mt-4">
            <JsonBlock value={simulation.matched_policy || {}} />
          </div>
        </section>
      ) : null}

      {approval ? (
        <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold text-zinc-950">4. Human approval</h2>
          <p className="mt-1 text-sm text-zinc-600">Approval #{approval.id} is pending. Edit the final payload, then approve or reject.</p>
          <div className="mt-4 grid gap-3">
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              To
              <input className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setDraft({ ...draft, to: event.target.value })} suppressHydrationWarning value={draft.to} />
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Subject
              <input className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setDraft({ ...draft, subject: event.target.value })} suppressHydrationWarning value={draft.subject} />
            </label>
            <label className="grid gap-1 text-sm font-medium text-zinc-700">
              Body
              <textarea className="min-h-40 rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => setDraft({ ...draft, body: event.target.value })} suppressHydrationWarning value={draft.body} />
            </label>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 disabled:bg-emerald-300" disabled={loading === "approve"} onClick={approveDraft} suppressHydrationWarning type="button">
              {loading === "approve" ? "Creating Draft..." : "Approve & Create Draft"}
            </button>
            <button className="rounded-md bg-red-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-red-700 disabled:bg-red-300" disabled={loading === "reject"} onClick={rejectDraft} suppressHydrationWarning type="button">
              Reject
            </button>
          </div>
        </section>
      ) : null}

      {approvalResult ? (
        <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
            <div>
              <h2 className="text-base font-semibold text-zinc-950">5. Done</h2>
              <p className="mt-1 text-sm text-zinc-600">The final action result is recorded in audit logs.</p>
            </div>
            <Link className="w-fit rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm font-medium text-zinc-800 shadow-sm hover:bg-zinc-50" href="/logs">
              View logs
            </Link>
          </div>
          <div className="mt-4">
            <JsonBlock value={approvalResult} />
          </div>
        </section>
      ) : null}
    </div>
  );
}
