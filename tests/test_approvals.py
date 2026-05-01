from tests.conftest import call_action, create_action, create_agent, create_policy


def test_approval_required_edit_approve_uses_current_input(client, headers):
    agent = create_agent(client, headers, "approval_agent")
    create_action(client, headers, "approval.gmail", executor_type="gmail_draft")
    create_policy(client, headers, agent["id"], "approval.gmail", "approval_required")

    response = call_action(
        client,
        headers,
        agent["api_key"],
        "approval.gmail",
        {"to": "buyer@gmail.com", "subject": "Original", "body": "Original body"},
    )
    assert response.status_code == 200
    approval_id = response.json()["approval_id"]

    edited = {"to": "buyer@gmail.com", "subject": "Edited", "body": "Edited body"}
    update = client.put(f"/approvals/{approval_id}/input", headers=headers, json={"input": edited})
    assert update.status_code == 200, update.text
    assert update.json()["current_input"]["subject"] == "Edited"

    approved = client.post(f"/approvals/{approval_id}/approve", headers=headers)
    assert approved.status_code == 200, approved.text
    result = approved.json()
    assert result["status"] == "completed"
    assert result["result"]["draft"]["subject"] == "Edited"

    logs = client.get("/logs", headers=headers).json()
    completed = next(item for item in logs if item["status"] == "completed")
    assert completed["original_input"]["subject"] == "Original"
    assert completed["final_input"]["subject"] == "Edited"


def test_reject_sets_status_rejected(client, headers):
    agent = create_agent(client, headers, "reject_agent")
    create_action(client, headers, "reject.action")
    create_policy(client, headers, agent["id"], "reject.action", "approval_required")

    approval_id = call_action(client, headers, agent["api_key"], "reject.action", {}).json()["approval_id"]
    rejected = client.post(f"/approvals/{approval_id}/reject", headers=headers)

    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    all_approvals = client.get("/approvals?status=", headers=headers).json()
    assert any(item["id"] == approval_id and item["status"] == "rejected" for item in all_approvals)


def test_viewer_role_cannot_approve(client, headers, db_session, workspace):
    from app_backend.models.models import WorkspaceMembership

    agent = create_agent(client, headers, "viewer_agent")
    create_action(client, headers, "viewer.action")
    create_policy(client, headers, agent["id"], "viewer.action", "approval_required")
    approval_id = call_action(client, headers, agent["api_key"], "viewer.action", {}).json()["approval_id"]

    client.get("/me", headers=headers)
    membership = (
        db_session.query(WorkspaceMembership)
        .filter(WorkspaceMembership.workspace_id == workspace, WorkspaceMembership.user_id == "demo_user")
        .first()
    )
    membership.role = "viewer"
    db_session.commit()

    response = client.post(f"/approvals/{approval_id}/approve", headers=headers)
    assert response.status_code == 403
