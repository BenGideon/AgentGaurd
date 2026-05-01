from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app_backend.routers import (
    action_policies,
    action_secret_policies,
    actions,
    agents,
    alerts,
    approvals,
    connectors,
    demo,
    logs,
    mcp,
    me,
    policies,
    secrets,
    simulator,
    stats,
    tools,
)

ROUTE_INVENTORY = [
    "/agents",
    "/actions",
    "/alerts",
    "/action-policies",
    "/action-secret-policies",
    "/approvals",
    "/secrets",
    "/connectors",
    "/demo",
    "/health",
    "/mcp",
    "/logs",
    "/simulate",
    "/stats",
    "/tools",
    "/policies",
    "/tool-call",
    "/me",
]


app = FastAPI(title="AgentGuard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+):3000",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(actions.router)
app.include_router(alerts.router)
app.include_router(action_policies.router)
app.include_router(action_secret_policies.router)
app.include_router(approvals.router)
app.include_router(secrets.router)
app.include_router(connectors.router)
app.include_router(demo.router)
app.include_router(mcp.router)
app.include_router(logs.router)
app.include_router(simulator.router)
app.include_router(stats.router)
app.include_router(tools.router)
app.include_router(policies.router)
app.include_router(me.router)


@app.on_event("startup")
def startup_tasks() -> None:
    from app_backend.core.database import SessionLocal
    from app_backend.services.demo_service import seed_demo_data

    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()

    print("AgentGuard running")
    print("Demo: http://localhost:3000/demo")
    print("API: http://127.0.0.1:8000/docs")
    print("Registered routes:")
    for route in ROUTE_INVENTORY:
        print(f"- {route}")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


__all__ = ["app"]
