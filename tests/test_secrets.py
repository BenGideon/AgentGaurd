def test_secret_crud_never_returns_value(client, headers):
    created = client.post(
        "/secrets",
        headers=headers,
        json={"name": "api_token", "value": "super-secret", "description": "Token"},
    )
    assert created.status_code == 200
    assert "value" not in created.json()

    listed = client.get("/secrets", headers=headers)
    assert listed.status_code == 200
    assert any(item["name"] == "api_token" for item in listed.json())
    assert all("value" not in item for item in listed.json())

    deleted = client.delete("/secrets/api_token", headers=headers)
    assert deleted.status_code == 200
    assert not any(item["name"] == "api_token" for item in client.get("/secrets", headers=headers).json())


def test_secret_names_are_workspace_scoped(client):
    headers_a = {"x-workspace-id": "secret_ws_a"}
    headers_b = {"x-workspace-id": "secret_ws_b"}

    assert client.post("/secrets", headers=headers_a, json={"name": "shared", "value": "a"}).status_code == 200
    assert client.post("/secrets", headers=headers_b, json={"name": "shared", "value": "b"}).status_code == 200

    assert len([item for item in client.get("/secrets", headers=headers_a).json() if item["name"] == "shared"]) == 1
    assert len([item for item in client.get("/secrets", headers=headers_b).json() if item["name"] == "shared"]) == 1
