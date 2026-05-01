import logging
import threading
from datetime import datetime
from typing import Any

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_backend.core.database import SessionLocal
from app_backend.models.models import AlertConfig
from app_backend.schemas.alerts import AlertCreate
from app_backend.utils.redaction import redact_sensitive_data


logger = logging.getLogger(__name__)


VALID_ALERT_EVENTS = {"blocked", "approval_required", "critical_risk", "approved"}


def alert_to_dict(alert: AlertConfig) -> dict[str, Any]:
    return {
        "id": alert.id,
        "workspace_id": alert.workspace_id,
        "name": alert.name,
        "url": alert.url,
        "events": alert.events or [],
        "created_at": alert.created_at,
    }


def create_alert(db: Session, workspace_id: str, payload: AlertCreate) -> dict[str, Any]:
    events = payload.events or []
    unknown_events = [event for event in events if event not in VALID_ALERT_EVENTS]
    if unknown_events:
        raise HTTPException(status_code=400, detail=f"Invalid alert events: {', '.join(unknown_events)}")

    alert = AlertConfig(
        workspace_id=workspace_id,
        name=payload.name,
        url=payload.url,
        events=events,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert_to_dict(alert)


def list_alerts(db: Session, workspace_id: str) -> list[dict[str, Any]]:
    alerts = (
        db.query(AlertConfig)
        .filter(AlertConfig.workspace_id == workspace_id)
        .order_by(AlertConfig.created_at.desc())
        .all()
    )
    return [alert_to_dict(alert) for alert in alerts]


def delete_alert(db: Session, workspace_id: str, alert_id: int) -> dict[str, str]:
    alert = (
        db.query(AlertConfig)
        .filter(AlertConfig.id == alert_id, AlertConfig.workspace_id == workspace_id)
        .first()
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    db.delete(alert)
    db.commit()
    return {"status": "deleted"}


def trigger_alert(event_type: str, payload: dict[str, Any], workspace_id: str) -> None:
    if event_type not in VALID_ALERT_EVENTS:
        logger.warning("Skipping unknown alert event type: %s", event_type)
        return

    safe_payload = redact_sensitive_data(
        {
            "event": event_type,
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **payload,
        }
    )

    thread = threading.Thread(
        target=_deliver_alerts,
        args=(event_type, workspace_id, safe_payload),
        daemon=True,
    )
    thread.start()


def _deliver_alerts(event_type: str, workspace_id: str, payload: dict[str, Any]) -> None:
    db = SessionLocal()
    try:
        alerts = (
            db.query(AlertConfig)
            .filter(AlertConfig.workspace_id == workspace_id)
            .all()
        )
        for alert in alerts:
            if event_type not in (alert.events or []):
                continue
            try:
                requests.post(alert.url, json=payload, timeout=5)
            except Exception as exc:  # pragma: no cover - best-effort delivery
                logger.warning("Alert webhook failed for alert %s: %s", alert.id, exc)
    except Exception as exc:  # pragma: no cover - best-effort delivery
        logger.warning("Alert delivery failed: %s", exc)
    finally:
        db.close()
