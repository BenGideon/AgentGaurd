from tests.conftest import create_action, create_agent, create_policy


def simulate(client, headers, agent_id, action_name, input_data):
    response = client.post(
        "/simulate",
        headers=headers,
        json={"agent_id": agent_id, "action": action_name, "input": input_data},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_allow_approval_and_block_policies(client, headers):
    agent = create_agent(client, headers, "policy_agent")
    create_action(client, headers, "policy.action")

    create_policy(client, headers, agent["id"], "policy.action", "allow")
    assert simulate(client, headers, agent["id"], "policy.action", {})["decision"] == "allow"

    create_policy(client, headers, agent["id"], "policy.action", "approval_required", {"amount_gt": 100}, 10)
    assert simulate(client, headers, agent["id"], "policy.action", {"amount": 150})["decision"] == "approval_required"

    create_policy(client, headers, agent["id"], "policy.action", "block", {"risk_level": "low"}, 20)
    assert simulate(client, headers, agent["id"], "policy.action", {})["decision"] == "block"


def test_priority_and_conditions(client, headers):
    agent = create_agent(client, headers, "priority_agent")
    create_action(client, headers, "priority.delete_customer")

    create_policy(client, headers, agent["id"], "priority.delete_customer", "allow", None, 0)
    create_policy(client, headers, agent["id"], "priority.delete_customer", "block", {"risk_level": "critical"}, 100)

    result = simulate(client, headers, agent["id"], "priority.delete_customer", {})
    assert result["decision"] == "block"
    assert result["risk_level"] == "critical"


def test_recipient_external_and_delete_method_conditions(client, headers):
    agent = create_agent(client, headers, "condition_agent")
    create_action(client, headers, "condition.gmail")
    create_action(client, headers, "condition.http", executor_type="api_proxy")

    create_policy(
        client,
        headers,
        agent["id"],
        "condition.gmail",
        "approval_required",
        {"recipient_external": True},
        10,
    )
    create_policy(client, headers, agent["id"], "condition.gmail", "allow", None, 0)

    external = simulate(client, headers, agent["id"], "condition.gmail", {"to": "buyer@gmail.com"})
    internal = simulate(client, headers, agent["id"], "condition.gmail", {"to": "teammate@company.com"})
    assert external["decision"] == "approval_required"
    assert internal["decision"] == "allow"

    create_policy(client, headers, agent["id"], "condition.http", "block", {"method": "DELETE"}, 10)
    assert simulate(client, headers, agent["id"], "condition.http", {"method": "DELETE"})["decision"] == "block"
