import Link from "next/link";

export default function ConnectorSuccessPage({ searchParams }) {
  const provider = searchParams?.provider || "Connector";
  const label = provider === "gmail" ? "Gmail" : provider;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">
          {label} connected successfully
        </h1>
        <p className="mt-1 text-sm text-zinc-600">AgentGuard can now use this workspace connector.</p>
      </div>
      <Link className="inline-flex rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800" href="/connectors">
        Back to connectors
      </Link>
    </div>
  );
}
