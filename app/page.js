import Link from "next/link";

const githubUrl = "https://github.com/BenGideon/AgentGaurd";

const demoSteps = [
  "AI generates action",
  "Simulate risk + policy",
  "Require approval",
  "Execute safely",
  "Log everything",
];

const features = [
  "Policy engine (rules + conditions)",
  "Approval workflows",
  "Risk scoring",
  "Alerts (webhooks)",
  "Full audit logs",
  "SDKs (Python + JS)",
];

export default function HomePage() {
  return (
    <div className="space-y-16">
      <section className="grid min-h-[520px] items-center gap-10 py-8 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          <h1 className="max-w-3xl text-5xl font-semibold leading-tight tracking-normal text-zinc-950 md:text-6xl">
            Control what AI agents can do before they do it
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-zinc-600">
            AgentGuard is a safety layer for AI agents. Simulate, approve, and audit every action.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link className="rounded-md bg-zinc-950 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-zinc-800" href="/demo">
              Try Demo
            </Link>
            <a className="rounded-md border border-zinc-300 bg-white px-5 py-3 text-sm font-medium text-zinc-800 shadow-sm hover:bg-zinc-50" href={githubUrl} rel="noreferrer" target="_blank">
              View GitHub
            </a>
          </div>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
          <div className="text-sm font-semibold text-zinc-950">Demo preview</div>
          <div className="mt-4 rounded-md border border-dashed border-zinc-300 bg-zinc-50 p-6">
            <div className="space-y-3 text-sm text-zinc-700">
              <div className="rounded-md bg-white p-3 shadow-sm">AI wants to create a Gmail draft</div>
              <div className="rounded-md bg-amber-50 p-3 text-amber-800">Policy requires human approval</div>
              <div className="rounded-md bg-emerald-50 p-3 text-emerald-800">Reviewer approves and action is logged</div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-zinc-950">The problem</h2>
          <p className="mt-3 text-sm leading-6 text-zinc-600">
            AI agents can send emails, call APIs, and modify systems. But they make mistakes, and there is no control layer.
          </p>
        </div>
        <div className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-zinc-950">The solution</h2>
          <p className="mt-3 text-sm leading-6 text-zinc-600">
            AgentGuard sits between your AI and your systems. It decides what is allowed, requires approval, and logs everything.
          </p>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-zinc-950">How the demo works</h2>
        <div className="mt-5 grid gap-3 md:grid-cols-5">
          {demoSteps.map((step, index) => (
            <div className="rounded-lg border border-zinc-200 bg-white p-4 shadow-sm" key={step}>
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-950 text-sm font-semibold text-white">{index + 1}</div>
              <div className="mt-4 text-sm font-medium leading-6 text-zinc-800">{step}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <h2 className="text-2xl font-semibold text-zinc-950">What you get</h2>
          <p className="mt-3 text-sm leading-6 text-zinc-600">
            A practical gateway for agent actions, built for teams that need safety without stopping automation.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {features.map((feature) => (
            <div className="rounded-lg border border-zinc-200 bg-white p-4 text-sm font-medium text-zinc-800 shadow-sm" key={feature}>
              {feature}
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-start">
          <div>
            <h2 className="text-2xl font-semibold text-zinc-950">Run in 5 minutes</h2>
            <p className="mt-2 text-sm text-zinc-600">Clone, install, seed the demo, and open the guided workflow.</p>
          </div>
          <a className="w-fit rounded-md border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-800 shadow-sm hover:bg-zinc-50" href={githubUrl} rel="noreferrer" target="_blank">
            Run locally
          </a>
        </div>
        <pre className="mt-5 overflow-x-auto rounded-md bg-zinc-950 p-4 text-xs leading-6 text-zinc-50">{`git clone https://github.com/BenGideon/AgentGaurd
cd AgentGuard
pip install -r requirements.txt
npm install
python setup_demo.py
uvicorn app_backend.main:app --reload
npm run dev`}</pre>
      </section>

      <section className="rounded-lg bg-zinc-950 p-8 text-white">
        <h2 className="text-3xl font-semibold tracking-normal">Try the demo and see how AgentGuard controls AI actions.</h2>
        <Link className="mt-6 inline-flex rounded-md bg-white px-5 py-3 text-sm font-medium text-zinc-950 shadow-sm hover:bg-zinc-100" href="/demo">
          Try Demo
        </Link>
      </section>
    </div>
  );
}
