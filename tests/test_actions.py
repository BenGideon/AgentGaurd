from tests.conftest import create_action


def test_create_list_get_action(client, headers):
    action = create_action(client, headers, "sales.test_action")

    assert action["name"] == "sales.test_action"

    listed = client.get("/actions", headers=headers)
    assert listed.status_code == 200
    assert any(item["name"] == "sales.test_action" for item in listed.json())

    fetched = client.get("/actions/sales.test_action", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "sales.test_action"


def test_duplicate_action_in_same_workspace_fails(client, headers):
    create_action(client, headers, "sales.duplicate")
    response = client.post(
        "/actions",
        headers=headers,
        json={
            "name": "sales.duplicate",
            "description": "Duplicate",
            "executor_type": "mock",
            "risk_level": "medium",
        },
    )
    assert response.status_code == 400
