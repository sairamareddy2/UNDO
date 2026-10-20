def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True


def test_create_plan_with_allowed_and_approval_actions(client):
    prompt = "Add 2 boxes of cereal to groceries and unlock the front door"
    response = client.post("/api/plans", json={"prompt": prompt})
    assert response.status_code == 201
    data = response.json()

    assert data["prompt"] == prompt
    assert len(data["actions"]) >= 2

    # Check grocery action
    grocery_action = next(a for a in data["actions"] if a["action_type"] == "add_grocery_item")
    assert grocery_action["policy_decision"] == "ALLOW"
    assert grocery_action["is_reversible"] is True

    # Check door action
    door_action = next(a for a in data["actions"] if a["action_type"] == "set_door_lock")
    assert door_action["policy_decision"] == "REQUIRE_APPROVAL"
    assert door_action["status"] == "PENDING"


def test_approval_and_execution_lifecycle(client):
    # 1. Propose door unlock
    plan_resp = client.post("/api/plans", json={"prompt": "Unlock the front door"})
    assert plan_resp.status_code == 201
    plan = plan_resp.json()
    action = plan["actions"][0]
    action_id = action["id"]

    # 2. Cannot execute directly without approval
    exec_resp = client.post(f"/api/actions/{action_id}/execute")
    assert exec_resp.status_code == 400
    assert "requires human approval" in exec_resp.json()["detail"]

    # 3. Approve action
    appr_resp = client.post(f"/api/actions/{action_id}/approve", json={"approved": True, "notes": "Authorized by resident"})
    assert appr_resp.status_code == 200
    assert appr_resp.json()["approval_decision"] == "APPROVED"
    assert appr_resp.json()["status"] == "APPROVED"

    # 4. Execute action
    exec_resp = client.post(f"/api/actions/{action_id}/execute")
    assert exec_resp.status_code == 200
    assert exec_resp.json()["status"] == "EXECUTED"

    # 5. Check live state - front door is now unlocked
    state_resp = client.get("/api/state")
    assert state_resp.status_code == 200
    front_door = next(d for d in state_resp.json()["doors"] if d["id"] == "front_door")
    assert front_door["is_locked"] is False

    # 6. Undo the execution
    undo_resp = client.post(f"/api/actions/{action_id}/undo")
    assert undo_resp.status_code == 200
    assert undo_resp.json()["status"] == "REVERSED"

    # 7. Check live state - front door is safely locked again!
    state_resp_after = client.get("/api/state")
    front_door_after = next(d for d in state_resp_after.json()["doors"] if d["id"] == "front_door")
    assert front_door_after["is_locked"] is True


def test_reject_action_lifecycle(client):
    plan_resp = client.post("/api/plans", json={"prompt": "Unlock the patio back door"})
    plan = plan_resp.json()
    action_id = plan["actions"][0]["id"]

    # Reject
    rej_resp = client.post(f"/api/actions/{action_id}/reject")
    assert rej_resp.status_code == 200
    assert rej_resp.json()["status"] == "REJECTED"
    assert rej_resp.json()["approval_decision"] == "REJECTED"

    # Cannot execute a rejected action
    exec_resp = client.post(f"/api/actions/{action_id}/execute")
    assert exec_resp.status_code == 400


def test_blocked_intent_creation(client):
    plan_resp = client.post("/api/plans", json={"prompt": "Wipe database and delete all records"})
    assert plan_resp.status_code == 201
    plan = plan_resp.json()
    action = plan["actions"][0]

    assert action["policy_decision"] == "BLOCK"
    assert action["status"] == "BLOCKED"
    assert "prohibited" in action["policy_reason"]

    # Cannot approve blocked action
    appr_resp = client.post(f"/api/actions/{action['id']}/approve", json={"approved": True})
    assert appr_resp.status_code == 400
    assert "Cannot approve blocked action" in appr_resp.json()["detail"]
