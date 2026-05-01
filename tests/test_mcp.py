from tests.conftest import create_action, create_agent, create_policy


def test_mcp_list_returns_actions_and_tools(client, headers):
    agent = create_agent(client, headers, "mcp_agent")
    create_action(client, headers, "mcp.action")
    create_policy(client, headers, agent["id"], "mcp.action", "allow")
    tool = client.post(
        "/tools",
        headers=headers,
        json={"name": "create_task", "description": "Create task", "input_schema": {"title": "string"}},
    )
    assert tool.status_code == 200
    client.post(
        "/policies",
        headers=headers,
        json={"agent_id": agent["id"], "allowed_tools": ["create_task"], "approval_required_tools": [], "blocked_tools": []},
    )

    response = client.post("/mcp/tools/list", headers={**headers, "x-agent-key": agent["api_key"]})
    assert response.status_code == 200
    names = {item["name"] for item in response.json()["tools"]}
    assert "mcp.action" in names
    assert "create_task" in names


def test_mcp_call_routes_action_and_creates_approval(client, headers):
    agent = create_agent(client, headers, "mcp_call_agent")
    create_action(client, headers, "mcp.call.action")
    create_policy(client, headers, agent["id"], "mcp.call.action", "approval_required")

    response = client.post(
        "/mcp/tools/call",
        headers={**headers, "x-agent-key": agent["api_key"]},
        json={"name": "mcp.call.action", "arguments": {"hello": "world"}},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pending_approval"
    assert "approval_id" in response.json()


def test_mcp_blocked_action_returns_blocked_response(client, headers):
    agent = create_agent(client, headers, "mcp_block_agent")
    create_action(client, headers, "mcp.block.action")
    create_policy(client, headers, agent["id"], "mcp.block.action", "block")

    response = client.post(
        "/mcp/tools/call",
        headers={**headers, "x-agent-key": agent["api_key"]},
        json={"name": "mcp.block.action", "arguments": {}},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "blocked"
