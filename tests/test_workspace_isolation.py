from tests.conftest import call_action, create_action, create_agent, create_policy


def test_same_names_can_exist_in_different_workspaces(client):
    headers_a = {"x-workspace-id": "workspace_a"}
    headers_b = {"x-workspace-id": "workspace_b"}

    assert create_action(client, headers_a, "shared.action")["workspace_id"] == "workspace_a"
    assert create_action(client, headers_b, "shared.action")["workspace_id"] == "workspace_b"

    assert client.post("/tools", headers=headers_a, json={"name": "shared_tool", "description": "A"}).status_code == 200
    assert client.post("/tools", headers=headers_b, json={"name": "shared_tool", "description": "B"}).status_code == 200

    assert client.post("/secrets", headers=headers_a, json={"name": "shared_secret", "value": "a"}).status_code == 200
    assert client.post("/secrets", headers=headers_b, json={"name": "shared_secret", "value": "b"}).status_code == 200


def test_agent_key_and_data_do_not_cross_workspaces(client):
    headers_a = {"x-workspace-id": "isolated_a"}
    headers_b = {"x-workspace-id": "isolated_b"}

    agent_a = create_agent(client, headers_a, "isolated_agent")
    create_action(client, headers_a, "isolated.action")
    create_policy(client, headers_a, agent_a["id"], "isolated.action", "allow")

    response = call_action(client, headers_b, agent_a["api_key"], "isolated.action", {})
    assert response.status_code == 401

    assert any(item["name"] == "isolated.action" for item in client.get("/actions", headers=headers_a).json())
    assert not any(item["name"] == "isolated.action" for item in client.get("/actions", headers=headers_b).json())
    assert client.get("/logs", headers=headers_b).json() == []
