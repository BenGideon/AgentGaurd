from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import Depends, Header, HTTPException
from jwt import PyJWKClient
from sqlalchemy.orm import Session

from app_backend.core.config import settings
from app_backend.core.database import get_db
from app_backend.models.models import Agent, User, WorkspaceMembership
from app_backend.services.workspace_service import ensure_workspace


@dataclass(frozen=True)
class WorkspaceUserContext:
    user: object
    role: str
    workspace_id: str


APPROVER_ROLES = {"admin", "reviewer"}

CLERK_JWKS_CLIENT = PyJWKClient(settings.CLERK_JWKS_URL) if settings.CLERK_JWKS_URL else None


def get_workspace_id(x_workspace_id: str | None = Header(default=None, alias="x-workspace-id")) -> str:
    return x_workspace_id or "default"


def decode_clerk_token(token: str) -> dict[str, Any]:
    if not CLERK_JWKS_CLIENT:
        raise HTTPException(
            status_code=500,
            detail="Clerk JWT verification is not configured. Set CLERK_JWKS_URL.",
        )

    try:
        signing_key = CLERK_JWKS_CLIENT.get_signing_key_from_jwt(token)
        options = {"verify_aud": False}
        kwargs: dict[str, Any] = {"algorithms": ["RS256"], "options": options}
        if settings.CLERK_ISSUER_URL:
            kwargs["issuer"] = settings.CLERK_ISSUER_URL
        return jwt.decode(token, signing_key.key, **kwargs)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Clerk token: {exc}") from exc


def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        if not settings.CLERK_JWKS_URL:
            user = db.get(User, "demo_user")
            if user:
                return user
            user = User(id="demo_user", email="demo@agentguard.local")
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        raise HTTPException(status_code=401, detail="Missing Authorization bearer token")

    token = authorization.split(" ", 1)[1].strip()
    claims = decode_clerk_token(token)
    user_id = claims.get("sub")
    email = (
        claims.get("email")
        or claims.get("email_address")
        or claims.get("primary_email_address")
        or f"{user_id}@unknown.local"
    )
    if not user_id:
        raise HTTPException(status_code=401, detail="Clerk token missing subject")

    user = db.get(User, user_id)
    if user:
        if user.email != email:
            user.email = email
        return user

    user = User(id=user_id, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_workspace_user(
    workspace_id: str = Depends(get_workspace_id),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ensure_workspace(db, workspace_id)
    membership = (
        db.query(WorkspaceMembership)
        .filter(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user.id,
        )
        .first()
    )

    if not membership and (workspace_id == "default" or not settings.CLERK_JWKS_URL):
        existing_membership_count = (
            db.query(WorkspaceMembership)
            .filter(WorkspaceMembership.workspace_id == workspace_id)
            .count()
        )
        if existing_membership_count == 0:
            membership = WorkspaceMembership(
                workspace_id=workspace_id,
                user_id=user.id,
                role="admin",
            )
            db.add(membership)
            db.commit()
            db.refresh(membership)

    if not membership:
        raise HTTPException(status_code=403, detail="User is not a member of this workspace")

    return {"user": user, "role": membership.role, "workspace_id": workspace_id}


def get_current_agent(
    x_agent_key: str | None = Header(default=None, alias="x-agent-key"),
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
) -> Agent:
    if not x_agent_key:
        raise HTTPException(status_code=401, detail="Missing x-agent-key header")

    ensure_workspace(db, workspace_id)
    agent = (
        db.query(Agent)
        .filter(Agent.api_key == x_agent_key, Agent.workspace_id == workspace_id)
        .first()
    )
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid x-agent-key header")

    return agent
