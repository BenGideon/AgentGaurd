"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "../lib/api";

const demoAction = "sales.create_gmail_draft";
const demoAgentId = "sales_agent";

const emptyDraft = {
  to: "",
  subject: "",
  body: "",
};

function Spinner() {
  return (
    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent align-[-2px]" />
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

function decisionTone(decision) {
  if (decision === "block") {
    return {
      label: "Blocked by policy",
      className: "border-red-200 bg-red-50 text-red-800",
      dot: "bg-red-500",
    };
  }

  if (decision === "allow") {
    return {
      label: "Safe to create draft",
      className: "border-emerald-200 bg-emerald-50 text-emerald-800",
      dot: "bg-emerald-500",
    };
  }

  return {
    label: "Requires approval",
    className: "border-amber-200 bg-amber-50 text-amber-800",
    dot: "bg-amber-500",
  };
}

function emailDomain(email) {
  return String(email || "").split("@")[1]?.toLowerCase() || "";
}

function formatPolicyReason(simulation, input) {
  if (!simulation) {
    return "Generate an email to see the policy decision.";
  }

  const conditions = simulation.matched_policy?.conditions || {};
  if (conditions.recipient_external) {
    return `This email is going to an external address (${emailDomain(input.to) || "unknown domain"}), so approval is required.`;
  }

  if (conditions.method) {
    return `The policy matched the ${conditions.method} method for this action.`;
  }

  if (conditions.risk_level) {
    return `The action is marked ${conditions.risk_level} risk, so the matching policy applies.`;
  }

  if (conditions.amount_gt) {
    return `The amount is above ${conditions.amount_gt}, so the matching policy applies.`;
  }

  if (simulation.decision === "allow") {
    return "No blocking or approval policy matched this email, so it can be created safely.";
  }

  if (simulation.decision === "block") {
    return "A blocking policy matched this action, so AgentGuard will not execute it.";
  }

  return simulation.reason || "AgentGuard found a policy that requires human approval.";
}

function PolicyBanner({ simulation, input, loading }) {
  if (loading && !simulation) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white p-4 text-sm text-zinc-700 shadow-sm">
        <div className="flex items-center gap-2 font-medium text-zinc-950">
          <Spinner />
          Simulating policy...
        </div>
      </div>
    );
  }

  if (!simulation) {
    return null;
  }

  const tone = decisionTone(simulation.decision);
  return (
    <div className={`rounded-lg border p-4 shadow-sm ${tone.className}`}>
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="flex items-center gap-2 text-base font-semibold">
            <span className={`h-2.5 w-2.5 rounded-full ${tone.dot}`} />
            {tone.label}
            {loading ? <Spinner /> : null}
          </div>
          <p className="mt-1 text-sm">{formatPolicyReason(simulation, input)}</p>
        </div>
        <div className="grid gap-1 text-sm md:text-right">
          <span>Decision: <strong>{simulation.decision}</strong></span>
          <span>Risk: <strong>{simulation.risk_level || "unknown"}</strong></span>
        </div>
      </div>
    </div>
  );
}

function DemoModeNotice({ status }) {
  if (status && !status.demo_mode) {
    return null;
  }

  return (
    <div className="rounded-lg border border-sky-200 bg-sky-50 p-4 text-sm text-sky-800 shadow-sm">
      <div className="font-semibold">Running in demo mode</div>
      <p className="mt-1">{status?.message || "Mock email creation and fallback AI are enabled, so the demo works without OpenAI or Gmail setup."}</p>
    </div>
  );
}

function ResultSummary({ result }) {
  const payload = result?.result || result?.tool_result || result?.execution_result || result;
  const draft = payload?.draft;

  if (!payload) {
    return null;
  }

  return (
    <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-5 text-emerald-900 shadow-sm">
      <h2 className="text-lg font-semibold">Draft created successfully</h2>
      <p className="mt-1 text-sm">{payload.message || "AgentGuard completed the action and recorded it in the audit log."}</p>
      {payload.draft_id ? <p className="mt-2 text-sm">Draft ID: <span className="font-mono">{payload.draft_id}</span></p> : null}
      {draft ? (
        <div className="mt-4 rounded-md border border-emerald-200 bg-white p-4 text-sm text-zinc-800">
          <div><span className="font-medium text-zinc-950">To:</span> {draft.to}</div>
          <div className="mt-1"><span className="font-medium text-zinc-950">Subject:</span> {draft.subject}</div>
          <p className="mt-3 whitespace-pre-wrap text-zinc-700">{draft.body}</p>
        </div>
      ) : null}
    </div>
  );
}

export default function DemoPage() {
  const [agents, setAgents] = useState([]);
  const [customerEmail, setCustomerEmail] = useState("customer@gmail.com");
  const [context, setContext] = useState("follow up after pricing call");
  const [draft, setDraft] = useState(emptyDraft);
  const [simulation, setSimulation] = useState(null);
  const [approval, setApproval] = useState(null);
  const [approvalResult, setApprovalResult] = useState(null);
  const [demoStatus, setDemoStatus] = useState(null);
  const [loading, setLoading] = useState("");
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const simulationRequest = useRef(0);

  const salesAgent = useMemo(
    () => agents.find((agent) => agent.id === demoAgentId) || agents[0],
    [agents]
  );

  const currentStage = approvalResult ? 5 : loading === "approve" ? 4 : draft.to ? 3 : loading === "generate" ? 2 : 1;
  const actionDisabled = !draft.to || !simulation || simulation.decision === "block" || loading === "approve" || simulationLoading;
  const primaryLabel = simulation?.decision === "allow" ? "Create Draft" : "Approve & Create Draft";

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

  async function runSimulation(nextDraft) {
    if (!nextDraft.to || !nextDraft.subject || !nextDraft.body) {
      setSimulation(null);
      return;
    }

    const requestId = simulationRequest.current + 1;
    simulationRequest.current = requestId;
    setSimulationLoading(true);
    setError("");

    try {
      const result = await apiFetch("/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_id: demoAgentId,
          action: demoAction,
          input: nextDraft,
        }),
      });

      if (simulationRequest.current === requestId) {
        setSimulation(result);
      }
    } catch (err) {
      if (simulationRequest.current === requestId) {
        setError(err.message);
      }
    } finally {
      if (simulationRequest.current === requestId) {
        setSimulationLoading(false);
      }
    }
  }

  async function generateEmail(event) {
    event.preventDefault();
    setLoading("generate");
    setError("");
    setMessage("");
    setSimulation(null);
    setApproval(null);
    setApprovalResult(null);

    try {
      const generated = await apiFetch("/demo/generate-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: customerEmail, context }),
      });
      setDraft(generated);
      setMessage("Email generated. AgentGuard is evaluating the policy now.");
      await runSimulation(generated);
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
    return found;
  }

  async function approveAndCreateDraft() {
    setLoading("approve");
    setError("");
    setMessage("");
    setApprovalResult(null);

    try {
      if (!salesAgent?.api_key) {
        throw new Error("Demo sales agent is not available yet");
      }
      if (simulation?.decision === "block") {
        throw new Error("This action is blocked by policy");
      }

      const callResult = await apiFetch("/actions/call", {
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

      if (callResult.status === "pending_approval") {
        const pendingApproval = await loadApproval(callResult.approval_id);
        await apiFetch(`/approvals/${pendingApproval.id}/input`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ input: draft }),
        });
        const approved = await apiFetch(`/approvals/${pendingApproval.id}/approve`, { method: "POST" });
        setApproval(null);
        setApprovalResult(approved);
        setMessage("Approval completed. Draft creation was logged and alert webhooks were triggered if configured.");
        return;
      }

      if (callResult.status === "completed") {
        setApprovalResult(callResult);
        setMessage("Draft created immediately. The action was logged and alert webhooks were triggered if configured.");
        return;
      }

      setMessage(`AgentGuard returned: ${callResult.status}`);
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

  function updateDraft(field, value) {
    setDraft((current) => ({ ...current, [field]: value }));
    setApprovalResult(null);
    setMessage("");
  }

  useEffect(() => {
    loadAgents();
  }, []);

  useEffect(() => {
    if (!draft.to || !draft.subject || !draft.body) {
      return undefined;
    }

    const timer = setTimeout(() => {
      runSimulation(draft);
    }, 400);

    return () => clearTimeout(timer);
  }, [draft.to, draft.subject, draft.body]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 lg:flex-row lg:items-end">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Demo: AI Sales Email Agent</h1>
          <p className="mt-1 max-w-3xl text-sm text-zinc-600">
            Generate an email, watch AgentGuard evaluate the policy, approve the final payload, then inspect the audit log.
          </p>
        </div>
        <Link className="w-fit rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm font-medium text-zinc-800 shadow-sm hover:bg-zinc-50" href="/logs?latest=1">
          View Audit Log
        </Link>
      </div>

      <div className="grid gap-2 md:grid-cols-5">
        <StepPill active={currentStage === 1} done={currentStage > 1} label="Generate" number="1" />
        <StepPill active={currentStage === 2} done={currentStage > 2} label="Evaluate" number="2" />
        <StepPill active={currentStage === 3} done={currentStage > 3} label="Review" number="3" />
        <StepPill active={currentStage === 4} done={currentStage > 4} label="Approve" number="4" />
        <StepPill active={currentStage === 5} done={false} label="Done" number="5" />
      </div>

      <DemoModeNotice status={demoStatus} />
      {message ? <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}
      {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}

      <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
          <div>
            <h2 className="text-base font-semibold text-zinc-950">Start with a customer and context</h2>
            <p className="mt-1 text-sm text-zinc-600">The demo will create a safe draft proposal. No email is sent.</p>
          </div>
          <div className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-600">
            Agent: <span className="font-mono text-zinc-950">{salesAgent?.id || demoAgentId}</span>
          </div>
        </div>
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
          <button className="inline-flex w-fit items-center gap-2 rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800 disabled:bg-zinc-400" disabled={loading === "generate"} suppressHydrationWarning type="submit">
            {loading === "generate" ? <Spinner /> : null}
            {loading === "generate" ? "Generating email..." : "Generate Email"}
          </button>
        </form>
      </section>

      {draft.to ? (
        <>
          <PolicyBanner input={draft} loading={simulationLoading} simulation={simulation} />

          <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
              <div>
                <h2 className="text-base font-semibold text-zinc-950">Review and approve the final draft</h2>
                <p className="mt-1 text-sm text-zinc-600">
                  Edits update the simulation live. AgentGuard executes only this final version.
                </p>
              </div>
              {simulation?.matched_policy?.policy_id ? (
                <div className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-600">
                  Matched policy #{simulation.matched_policy.policy_id}
                </div>
              ) : null}
            </div>

            <div className="mt-4 grid gap-3">
              <label className="grid gap-1 text-sm font-medium text-zinc-700">
                To
                <input className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => updateDraft("to", event.target.value)} suppressHydrationWarning value={draft.to} />
              </label>
              <label className="grid gap-1 text-sm font-medium text-zinc-700">
                Subject
                <input className="rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-zinc-500" onChange={(event) => updateDraft("subject", event.target.value)} suppressHydrationWarning value={draft.subject} />
              </label>
              <label className="grid gap-1 text-sm font-medium text-zinc-700">
                Body
                <textarea className="min-h-44 rounded-md border border-zinc-300 px-3 py-2 text-sm leading-6 outline-none focus:border-zinc-500" onChange={(event) => updateDraft("body", event.target.value)} suppressHydrationWarning value={draft.body} />
              </label>
            </div>

            <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center">
              <button className="inline-flex w-fit items-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 disabled:bg-zinc-400" disabled={actionDisabled} onClick={approveAndCreateDraft} suppressHydrationWarning type="button">
                {loading === "approve" ? <Spinner /> : null}
                {loading === "approve" ? "Creating draft..." : primaryLabel}
              </button>
              {simulation?.decision === "block" ? (
                <span className="text-sm font-medium text-red-700">This action is blocked by policy.</span>
              ) : (
                <span className="text-sm text-zinc-600">Approval, execution, alerts, and logs happen in one trusted path.</span>
              )}
              {approval ? (
                <button className="w-fit rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50" disabled={loading === "reject"} onClick={rejectDraft} suppressHydrationWarning type="button">
                  Reject
                </button>
              ) : null}
            </div>
          </section>
        </>
      ) : null}

      {approvalResult ? (
        <section className="space-y-4">
          <ResultSummary result={approvalResult} />
          <div className="flex flex-wrap gap-2">
            <Link className="rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800" href="/logs?latest=1">
              View Audit Log
            </Link>
            <button className="rounded-md border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-800 shadow-sm hover:bg-zinc-50" onClick={() => {
              setDraft(emptyDraft);
              setSimulation(null);
              setApprovalResult(null);
              setApproval(null);
              setMessage("");
              setError("");
            }} type="button">
              Run Again
            </button>
          </div>
        </section>
      ) : null}
    </div>
  );
}
