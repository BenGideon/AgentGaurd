import { apiFetch } from "./lib/api";

const statLabels = [
  ["total_tool_calls", "Total tool calls"],
  ["pending_approvals", "Pending approvals"],
  ["completed_calls", "Completed calls"],
  ["blocked_calls", "Blocked calls"],
];

export default async function HomePage() {
  const stats = await apiFetch("/stats").catch(() => ({
    total_tool_calls: 0,
    pending_approvals: 0,
    completed_calls: 0,
    blocked_calls: 0,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">Dashboard</h1>
        <p className="mt-1 text-sm text-zinc-600">Backend: http://localhost:8000</p>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statLabels.map(([key, label]) => (
          <div key={key} className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
            <div className="text-sm font-medium text-zinc-600">{label}</div>
            <div className="mt-3 text-3xl font-semibold text-zinc-950">{stats[key] ?? 0}</div>
          </div>
        ))}
      </section>
    </div>
  );
}
