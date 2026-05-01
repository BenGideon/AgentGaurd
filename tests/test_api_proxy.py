from types import SimpleNamespace

from tests.conftest import call_action, create_action, create_agent, create_policy


def test_api_proxy_blocks_localhost(client, headers):
    agent = create_agent(client, headers, "proxy_block_agent")
    create_action(client, headers, "proxy.block", executor_type="api_proxy")
    create_policy(client, headers, agent["id"], "proxy.block", "allow")

    response = call_action(
        client,
        headers,
        agent["api_key"],
        "proxy.block",
        {"url": "http://localhost:1234", "method": "GET"},
    )
    assert response.status_code == 400
    assert "blocked localhost" in response.text


def test_api_proxy_allows_mocked_external_get_and_post(client, headers, monkeypatch):
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return SimpleNamespace(
            status_code=200,
            headers={"content-type": "application/json"},
            json=lambda: {"ok": True, "method": method},
            text='{"ok": true}',
        )

    monkeypatch.setattr("app_backend.services.api_proxy.requests.request", fake_request)

    agent = create_agent(client, headers, "proxy_agent")
    create_action(client, headers, "proxy.external", executor_type="api_proxy")
    create_policy(client, headers, agent["id"], "proxy.external", "allow")

    get_response = call_action(
        client,
        headers,
        agent["api_key"],
        "proxy.external",
        {"url": "https://example.com/resource", "method": "GET"},
    )
    post_response = call_action(
        client,
        headers,
        agent["api_key"],
        "proxy.external",
        {"url": "https://example.com/resource", "method": "POST", "body": {"hello": "world"}},
    )

    assert get_response.status_code == 200
    assert post_response.status_code == 200
    assert get_response.json()["result"]["proxy"]["response_body"]["ok"] is True
    assert [call[0] for call in calls] == ["GET", "POST"]


def test_delete_method_risk_is_critical(client, headers):
    agent = create_agent(client, headers, "proxy_delete_agent")
    create_action(client, headers, "proxy.delete", executor_type="api_proxy")
    create_policy(client, headers, agent["id"], "proxy.delete", "block", {"risk_level": "critical"}, 10)

    response = call_action(
        client,
        headers,
        agent["api_key"],
        "proxy.delete",
        {"url": "https://example.com/resource", "method": "DELETE"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "blocked"
    assert response.json()["risk_level"] == "critical"
