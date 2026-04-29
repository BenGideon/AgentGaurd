import base64
from datetime import datetime, timedelta
import hashlib
import hmac
import json
from typing import Any
from urllib.parse import urlencode

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_backend.core.config import settings
from app_backend.models.models import Connector
from app_backend.services.workspace_service import ensure_workspace

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.compose"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"


def connector_to_dict(connector: Connector) -> dict[str, Any]:
    return {
        "provider": connector.provider,
        "connected": True,
        "connected_email": connector.connected_email,
        "expires_at": connector.expires_at,
    }


def list_connectors(db: Session, workspace_id: str) -> list[dict[str, Any]]:
    connectors = (
        db.query(Connector)
        .filter(Connector.workspace_id == workspace_id)
        .order_by(Connector.provider)
        .all()
    )
    return [connector_to_dict(connector) for connector in connectors]


def encode_oauth_state(data: dict[str, Any]) -> str:
    secret = settings.OAUTH_STATE_SECRET or settings.CLERK_SECRET_KEY or "agentguard-dev-state"
    payload = dict(data)
    message = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload["sig"] = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def decode_oauth_state(state: str) -> dict[str, Any]:
    try:
        padded = state + "=" * (-len(state) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc

    signature = payload.pop("sig", None)
    secret = settings.OAUTH_STATE_SECRET or settings.CLERK_SECRET_KEY or "agentguard-dev-state"
    message = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    if not signature or not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=400, detail="Invalid OAuth state signature")
    return payload


def get_google_oauth_config() -> tuple[str, str, str]:
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth requires GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI",
        )
    return client_id, client_secret, redirect_uri


def build_gmail_oauth_url(workspace_id: str) -> dict[str, str]:
    client_id, _, redirect_uri = get_google_oauth_config()
    state = encode_oauth_state({"workspace_id": workspace_id})
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": GMAIL_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return {"url": f"{GOOGLE_AUTH_URL}?{urlencode(params)}"}


def refresh_gmail_token(connector: Connector, db: Session) -> Connector:
    if not connector.refresh_token:
        raise HTTPException(status_code=400, detail="Gmail connector is missing refresh token")

    client_id, client_secret, _ = get_google_oauth_config()
    response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": connector.refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=10,
    )
    if not response.ok:
        raise HTTPException(status_code=400, detail=f"Gmail token refresh failed: {response.text}")

    payload = response.json()
    connector.access_token = payload["access_token"]
    connector.expires_at = datetime.utcnow() + timedelta(seconds=payload.get("expires_in", 3600))
    if payload.get("scope"):
        connector.scopes = payload["scope"]
    db.commit()
    db.refresh(connector)
    return connector


def handle_gmail_callback(db: Session, code: str, state: str) -> str:
    decoded_state = decode_oauth_state(state)
    workspace_id = decoded_state.get("workspace_id")
    if not workspace_id:
        raise HTTPException(status_code=400, detail="OAuth state missing workspace_id")

    ensure_workspace(db, workspace_id)
    client_id, client_secret, redirect_uri = get_google_oauth_config()
    token_response = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    if not token_response.ok:
        raise HTTPException(status_code=400, detail=f"Gmail OAuth token exchange failed: {token_response.text}")

    token_payload = token_response.json()
    access_token = token_payload["access_token"]
    refresh_token = token_payload.get("refresh_token")
    expires_at = datetime.utcnow() + timedelta(seconds=token_payload.get("expires_in", 3600))
    scopes = token_payload.get("scope", GMAIL_SCOPE)

    profile_response = requests.get(
        GMAIL_PROFILE_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    connected_email = None
    if profile_response.ok:
        connected_email = profile_response.json().get("emailAddress")

    connector = (
        db.query(Connector)
        .filter(Connector.workspace_id == workspace_id, Connector.provider == "gmail")
        .first()
    )
    if connector:
        connector.access_token = access_token
        if refresh_token:
            connector.refresh_token = refresh_token
        connector.scopes = scopes
        connector.expires_at = expires_at
        connector.connected_email = connected_email
    else:
        connector = Connector(
            workspace_id=workspace_id,
            provider="gmail",
            access_token=access_token,
            refresh_token=refresh_token,
            scopes=scopes,
            expires_at=expires_at,
            connected_email=connected_email,
        )
        db.add(connector)

    db.commit()
    return f"{settings.FRONTEND_URL}/connector-success?provider=gmail"


def delete_gmail_connector(db: Session, workspace_id: str) -> dict[str, str]:
    connector = (
        db.query(Connector)
        .filter(Connector.workspace_id == workspace_id, Connector.provider == "gmail")
        .first()
    )
    if connector:
        db.delete(connector)
        db.commit()
    return {"status": "disconnected", "provider": "gmail"}
