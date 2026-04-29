const styles = {
  completed: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  pending: "bg-amber-50 text-amber-700 ring-amber-200",
  blocked: "bg-red-50 text-red-700 ring-red-200",
  rejected: "bg-zinc-100 text-zinc-700 ring-zinc-200",
};

export default function StatusBadge({ status }) {
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${
        styles[status] || "bg-sky-50 text-sky-700 ring-sky-200"
      }`}
    >
      {status}
    </span>
  );
}
