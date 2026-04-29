"use client";

import { SignInButton, UserButton, useUser } from "@clerk/nextjs";
import Link from "next/link";

export default function AppHeader() {
  const { user } = useUser();

  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-5 py-4">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <Link href="/" className="text-lg font-semibold text-zinc-950">
            AgentGuard
          </Link>
          <div className="flex items-center gap-3 text-sm text-zinc-600">
            {user ? (
              <>
                <span>{user.primaryEmailAddress?.emailAddress}</span>
                <UserButton />
              </>
            ) : (
              <SignInButton mode="modal">
                <button className="rounded-md bg-zinc-950 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-zinc-800" type="button">
                  Sign in
                </button>
              </SignInButton>
            )}
          </div>
        </div>

        <nav className="flex flex-wrap items-center gap-1 text-sm font-medium text-zinc-600">
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/">
            Home
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/test-agent">
            Test Agent
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/agents">
            Agents
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/tools">
            Tools
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/actions">
            Actions
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/policies">
            Policies
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/action-policies">
            Action Policies
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/secrets">
            Secrets
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/connectors">
            Connectors
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/action-secret-policies">
            Secret Policies
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/approvals">
            Approvals
          </Link>
          <Link className="rounded-md px-3 py-2 hover:bg-zinc-100 hover:text-zinc-950" href="/logs">
            Logs
          </Link>
        </nav>
      </div>
    </header>
  );
}
