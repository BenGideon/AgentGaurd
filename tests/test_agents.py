from tests.conftest import create_agent


def test_create_agent_generates_api_key_and_lists(client, headers):
    agent = create_agent(client, headers, "agent_a")

    assert agent["id"] == "agent_a"
    assert agent["api_key"].startswith("ag_test_")

    response = client.get("/agents", headers=headers)
    assert response.status_code == 200
    assert any(item["id"] == "agent_a" for item in response.json())


def test_duplicate_agent_in_same_workspace_fails(client, headers):
    create_agent(client, headers, "agent_dup")
    response = client.post(
        "/agents",
        headers=headers,
        json={"id": "agent_dup", "name": "Duplicate Agent"},
    )
    assert response.status_code == 400
