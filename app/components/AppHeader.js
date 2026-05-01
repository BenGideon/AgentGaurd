"use client";

import { SignInButton, UserButton, useUser } from "@clerk/nextjs";
import Link from "next/link";

function AuthControls() {
  const { user } = useUser();

  if (user) {
    return (
      <>
        <span>{user.primaryEmailAddress?.emailAddress}</span>
        <UserButton />
      </>
    );
  }

  return (
    <SignInButton mode="modal">
      <button className="rounded-md bg-zinc-950 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800" type="button">
        Sign in
      </button>
    </SignInButton>
  );
}

export default function AppHeader() {
  const clerkConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-5 py-4">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <Link href="/" className="text-lg font-semibold text-zinc-950">
            AgentGuard
          </Link>
          <div className="flex items-center gap-3 text-sm text-zinc-600">
            {clerkConfigured ? <AuthControls /> : <span>Local demo mode</span>}
          </div>
        </div>

        <nav className="flex flex-wrap items-center gap-1 text-sm font-medium text-zinc-600">
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/demo">
            Demo
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/simulator">
            Simulator
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/alerts">
            Alerts
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/logs">
            Logs
          </Link>
          <a className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="https://github.com/BenGideon/AgentGaurd" rel="noreferrer" target="_blank">
            GitHub
          </a>
        </nav>
      </div>
    </header>
  );
}
