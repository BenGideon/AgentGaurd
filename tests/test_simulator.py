from tests.conftest import create_action, create_agent, create_policy


def test_simulator_does_not_execute_create_approval_or_log(client, headers):
    agent = create_agent(client, headers, "sim_agent")
    create_action(client, headers, "sim.action")
    create_policy(client, headers, agent["id"], "sim.action", "approval_required")

    before_approvals = client.get("/approvals", headers=headers).json()
    before_logs = client.get("/logs", headers=headers).json()

    response = client.post(
        "/simulate",
        headers=headers,
        json={"agent_id": agent["id"], "action": "sim.action", "input": {"hello": "world"}},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["decision"] == "approval_required"
    assert result["risk_level"] == "low"
    assert result["matched_policy"]["effect"] == "approval_required"

    assert client.get("/approvals", headers=headers).json() == before_approvals
    assert client.get("/logs", headers=headers).json() == before_logs
