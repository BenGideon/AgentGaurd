from types import SimpleNamespace

from tests.conftest import call_action, create_action, create_agent, create_policy


def test_api_proxy_with_unallowed_secret_is_blocked(client, headers):
    agent = create_agent(client, headers, "secret_policy_agent")
    create_action(client, headers, "secret.proxy", executor_type="api_proxy")
    create_policy(client, headers, agent["id"], "secret.proxy", "allow")
    client.post("/secrets", headers=headers, json={"name": "hubspot_token", "value": "secret-token"})

    response = call_action(
        client,
        headers,
        agent["api_key"],
        "secret.proxy",
        {
            "url": "https://example.com/api",
            "method": "GET",
            "auth": {"type": "bearer", "secret_name": "hubspot_token"},
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "blocked"
    assert "secret-token" not in response.text


def test_api_proxy_with_allowed_secret_can_proceed_and_redacts_logs(client, headers, monkeypatch):
    def fake_request(method, url, **kwargs):
        assert kwargs["headers"]["Authorization"] == "Bearer secret-token"
        return SimpleNamespace(
            status_code=200,
            headers={"authorization": "upstream-secret"},
            json=lambda: {"received_token": "secret-token"},
            text="",
        )

    monkeypatch.setattr("app_backend.services.api_proxy.requests.request", fake_request)

    agent = create_agent(client, headers, "allowed_secret_agent")
    create_action(client, headers, "allowed.secret.proxy", executor_type="api_proxy")
    create_policy(client, headers, agent["id"], "allowed.secret.proxy", "allow")
    client.post("/secrets", headers=headers, json={"name": "hubspot_token", "value": "secret-token"})
    policy = client.post(
        "/action-secret-policies",
        headers=headers,
        json={
            "agent_id": agent["id"],
            "action_name": "allowed.secret.proxy",
            "allowed_secrets": ["hubspot_token"],
        },
    )
    assert policy.status_code == 200

    response = call_action(
        client,
        headers,
        agent["api_key"],
        "allowed.secret.proxy",
        {
            "url": "https://example.com/api",
            "method": "GET",
            "auth": {"type": "bearer", "secret_name": "hubspot_token"},
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert "secret-token" not in response.text
    logs = client.get("/logs", headers=headers)
    assert "secret-token" not in logs.text
    assert "hubspot_token" in logs.text
