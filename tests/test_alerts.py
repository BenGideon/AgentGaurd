from tests.conftest import call_action, create_action, create_agent, create_policy


def test_alert_crud(client, headers):
    created = client.post(
        "/alerts",
        headers=headers,
        json={"name": "Webhook", "url": "https://example.com/hook", "events": ["blocked"]},
    )
    assert created.status_code == 200
    alert_id = created.json()["id"]

    listed = client.get("/alerts", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == alert_id for item in listed.json())

    deleted = client.delete(f"/alerts/{alert_id}", headers=headers)
    assert deleted.status_code == 200
    assert not any(item["id"] == alert_id for item in client.get("/alerts", headers=headers).json())


def test_blocked_and_approval_required_alerts_fire(client, headers, monkeypatch):
    delivered = []

    def fake_post(url, json, timeout):
        delivered.append((url, json))

    monkeypatch.setattr("app_backend.services.alert_service.requests.post", fake_post)

    agent = create_agent(client, headers, "alert_agent")
    create_action(client, headers, "alert.blocked")
    create_action(client, headers, "alert.approval")
    create_policy(client, headers, agent["id"], "alert.blocked", "block")
    create_policy(client, headers, agent["id"], "alert.approval", "approval_required")
    client.post(
        "/alerts",
        headers=headers,
        json={
            "name": "All",
            "url": "https://example.com/hook",
            "events": ["blocked", "approval_required", "approved"],
        },
    )

    assert call_action(client, headers, agent["api_key"], "alert.blocked", {"token": "secret"}).status_code == 200
    approval = call_action(client, headers, agent["api_key"], "alert.approval", {}).json()
    assert approval["status"] == "pending_approval"

    assert any(payload["event"] == "blocked" for _, payload in delivered)
    assert any(payload["event"] == "approval_required" for _, payload in delivered)
    assert all("secret" not in str(payload) for _, payload in delivered)


def test_approval_completed_alert_fires(client, headers, monkeypatch):
    delivered = []
    monkeypatch.setattr(
        "app_backend.services.alert_service.requests.post",
        lambda url, json, timeout: delivered.append(json),
    )

    agent = create_agent(client, headers, "approved_alert_agent")
    create_action(client, headers, "approved.alert.action")
    create_policy(client, headers, agent["id"], "approved.alert.action", "approval_required")
    client.post(
        "/alerts",
        headers=headers,
        json={"name": "Approved", "url": "https://example.com/hook", "events": ["approved"]},
    )

    approval_id = call_action(client, headers, agent["api_key"], "approved.alert.action", {}).json()["approval_id"]
    response = client.post(f"/approvals/{approval_id}/approve", headers=headers)
    assert response.status_code == 200
    assert any(payload["event"] == "approved" for payload in delivered)
