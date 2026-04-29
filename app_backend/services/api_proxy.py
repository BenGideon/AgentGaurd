import ipaddress
import socket
from typing import Any
from urllib.parse import urlparse

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_backend.models.models import ActionSecretPolicy
from app_backend.services.secrets_service import get_secret_value
from app_backend.utils.redaction import redact_sensitive_data


def parse_proxy_host(url: str) -> str | None:
    return urlparse(url).hostname


def is_blocked_proxy_host(hostname: str) -> bool:
    blocked_names = {"localhost"}
    normalized = hostname.lower().strip("[]")
    if normalized in blocked_names:
        return True

    addresses = []
    try:
        addresses.append(ipaddress.ip_address(normalized))
    except ValueError:
        try:
            for result in socket.getaddrinfo(normalized, None):
                addresses.append(ipaddress.ip_address(result[4][0]))
        except socket.gaierror:
            raise HTTPException(status_code=400, detail="Could not resolve proxy URL host")

    return any(
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_unspecified
        for address in addresses
    )


def referenced_secret_names(input_data: dict[str, Any]) -> list[str]:
    auth_config = input_data.get("auth")
    if not isinstance(auth_config, dict):
        return []

    names = [
        auth_config.get("secret_name"),
        auth_config.get("username_secret"),
        auth_config.get("password_secret"),
    ]
    return sorted({name for name in names if isinstance(name, str) and name})


def validate_action_secret_access(
    agent_id: str,
    action_name: str,
    input_data: dict[str, Any],
    workspace_id: str,
    db: Session,
) -> dict[str, str] | None:
    requested_secrets = referenced_secret_names(input_data)
    if not requested_secrets:
        return None

    policy = (
        db.query(ActionSecretPolicy)
        .filter(
            ActionSecretPolicy.workspace_id == workspace_id,
            ActionSecretPolicy.agent_id == agent_id,
            ActionSecretPolicy.action_name == action_name,
        )
        .first()
    )
    if not policy:
        return {"status": "blocked", "message": "Secret not allowed for this agent/action"}

    allowed = set(policy.allowed_secrets or [])
    if any(secret_name not in allowed for secret_name in requested_secrets):
        return {"status": "blocked", "message": "Secret not allowed for this agent/action"}

    return None


def execute_api_proxy(
    input_data: dict[str, Any],
    db: Session,
    agent_id: str | None = None,
    action_name: str | None = None,
    workspace_id: str = "default",
) -> dict[str, Any]:
    if referenced_secret_names(input_data):
        if not agent_id or not action_name:
            return {"status": "blocked", "message": "Secret not allowed for this agent/action"}
        secret_violation = validate_action_secret_access(agent_id, action_name, input_data, workspace_id, db)
        if secret_violation:
            return secret_violation

    url = input_data.get("url")
    method = str(input_data.get("method", "")).upper()
    headers = dict(input_data.get("headers") or {})
    body = input_data.get("body")
    query = input_data.get("query") or {}
    auth_config = input_data.get("auth")
    request_auth = None

    if not url:
        return {"status": "error", "message": "api_proxy requires url"}
    if method not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
        return {"status": "error", "message": "api_proxy method must be GET, POST, PUT, PATCH, or DELETE"}
    if not isinstance(headers, dict):
        return {"status": "error", "message": "api_proxy headers must be an object"}
    if not isinstance(query, dict):
        return {"status": "error", "message": "api_proxy query must be an object"}
    if auth_config is not None and not isinstance(auth_config, dict):
        return {"status": "error", "message": "api_proxy auth must be an object"}

    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"] or not parsed.hostname:
        return {"status": "error", "message": "api_proxy url must be http or https"}
    if is_blocked_proxy_host(parsed.hostname):
        return {"status": "error", "message": "api_proxy blocked localhost or internal network URL"}

    if auth_config:
        auth_type = auth_config.get("type")

        if auth_type == "bearer":
            secret_name = auth_config.get("secret_name")
            secret_value = get_secret_value(db, workspace_id, secret_name) if secret_name else None
            if not secret_value:
                return {"status": "error", "message": f"Secret not found: {secret_name}"}
            headers["Authorization"] = f"Bearer {secret_value}"

        elif auth_type == "api_key_header":
            secret_name = auth_config.get("secret_name")
            header_name = auth_config.get("header_name")
            secret_value = get_secret_value(db, workspace_id, secret_name) if secret_name else None
            if not secret_value:
                return {"status": "error", "message": f"Secret not found: {secret_name}"}
            if not header_name:
                return {"status": "error", "message": "api_key_header auth requires header_name"}
            headers[header_name] = secret_value

        elif auth_type == "basic":
            username_secret = auth_config.get("username_secret")
            password_secret = auth_config.get("password_secret")
            username = get_secret_value(db, workspace_id, username_secret) if username_secret else None
            password = get_secret_value(db, workspace_id, password_secret) if password_secret else None
            if not username:
                return {"status": "error", "message": f"Secret not found: {username_secret}"}
            if not password:
                return {"status": "error", "message": f"Secret not found: {password_secret}"}
            request_auth = (username, password)

        else:
            return {"status": "error", "message": "api_proxy auth type must be bearer, api_key_header, or basic"}

    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            params=query,
            json=body,
            auth=request_auth,
            timeout=10,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        return {"status": "error", "message": f"api_proxy request failed: {exc}"}

    try:
        response_body = response.json()
    except ValueError:
        response_body = response.text

    return {
        "status": "success",
        "proxy": {
            "url": url,
            "method": method,
            "status_code": response.status_code,
            "response_body": redact_sensitive_data(response_body),
            "response_headers": redact_sensitive_data(dict(response.headers)),
        },
    }
