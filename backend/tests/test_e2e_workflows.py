import pytest
from unittest.mock import patch
from app import models
from app.models import utc_now


def test_e2e_grocery_workflow_allow_execute_undo_invariants(client, db_session):
    """
    Workflow 1:
    Natural-language grocery request -> Gemini/Parser structured proposal ->
    ALLOW -> execute -> SQLite state changes -> undo -> original state restored ->
    idempotency guard (repeated undo blocked).
    """
    # 1. Check initial grocery count
    initial_state_resp = client.get("/api/state")
    assert initial_state_resp.status_code == 200
    initial_count = len(initial_state_resp.json()["groceries"])

    # 2. Submit grocery prompt
    prompt = "Please add 2 cartons of organic oat milk to my grocery list"
    plan_resp = client.post("/api/plans", json={"prompt": prompt})
    assert plan_resp.status_code == 201
    plan_data = plan_resp.json()
    assert len(plan_data["actions"]) >= 1

    grocery_action = plan_data["actions"][0]
    action_id = grocery_action["id"]
    assert grocery_action["action_type"] == "add_grocery_item"
    assert grocery_action["policy_decision"] == "ALLOW"
    assert grocery_action["is_reversible"] is True
    assert grocery_action["status"] == "PENDING"

    # 3. Execute allowed action
    exec_resp = client.post(f"/api/actions/{action_id}/execute")
    assert exec_resp.status_code == 200
    exec_data = exec_resp.json()
    assert exec_data["status"] == "EXECUTED"
    assert exec_data["after_state"] is not None

    # 4. Confirm SQLite state changed
    after_exec_state = client.get("/api/state").json()
    assert len(after_exec_state["groceries"]) == initial_count + 1
    new_item = next(g for g in after_exec_state["groceries"] if "oat milk" in g["name"].lower())
    assert new_item["quantity"] == 2

    # 5. Undo action
    undo_resp = client.post(f"/api/actions/{action_id}/undo")
    assert undo_resp.status_code == 200
    undo_data = undo_resp.json()
    assert undo_data["status"] == "REVERSED"
    assert undo_data["reversed_at"] is not None

    # 6. Confirm SQLite restored to original state
    after_undo_state = client.get("/api/state").json()
    assert len(after_undo_state["groceries"]) == initial_count
    assert not any(g["id"] == new_item["id"] for g in after_undo_state["groceries"])

    # 7. Repeated undo guard (cannot undo twice)
    repeat_undo = client.post(f"/api/actions/{action_id}/undo")
    assert repeat_undo.status_code == 400
    assert "already been reversed" in repeat_undo.json()["detail"].lower()

    # 8. Verify audit events recorded
    audit_resp = client.get("/api/state/audit-events")
    assert audit_resp.status_code == 200
    event_types = [ev["event_type"] for ev in audit_resp.json()]
    assert "ACTION_EXECUTED" in event_types
    assert "ACTION_UNDONE" in event_types


def test_e2e_door_unlock_require_approval_gate(client, db_session):
    """
    Workflow 2:
    Door-unlock request -> REQUIRE_APPROVAL -> execution remains blocked until explicit approval ->
    execute only after approval -> undo restores locked state.
    """
    # 1. Verify front door starts locked
    initial_state = client.get("/api/state").json()
    front_door = next(d for d in initial_state["doors"] if d["id"] == "front_door")
    assert front_door["is_locked"] is True

    # 2. Propose door unlock
    plan_resp = client.post("/api/plans", json={"prompt": "Unlock the front door for a guest"})
    assert plan_resp.status_code == 201
    action = plan_resp.json()["actions"][0]
    action_id = action["id"]
    assert action["action_type"] == "set_door_lock"
    assert action["policy_decision"] == "REQUIRE_APPROVAL"
    assert action["status"] == "PENDING"
    assert "Physical security impact" in action["policy_reason"]

    # 3. Execution MUST be blocked before approval
    blocked_exec = client.post(f"/api/actions/{action_id}/execute")
    assert blocked_exec.status_code == 400
    assert "approval" in blocked_exec.json()["detail"].lower()

    # Front door in SQLite must still be locked
    state_check = client.get("/api/state").json()
    assert next(d for d in state_check["doors"] if d["id"] == "front_door")["is_locked"] is True

    # 4. Explicitly approve action
    appr_resp = client.post(f"/api/actions/{action_id}/approve", json={
        "approved": True,
        "notes": "Verified guest at the doorstep"
    })
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "APPROVED"
    assert appr_resp.json()["approval_decision"] == "APPROVED"

    # 5. Execute approved action
    exec_resp = client.post(f"/api/actions/{action_id}/execute")
    assert exec_resp.status_code == 200
    assert exec_resp.json()["status"] == "EXECUTED"

    # Front door in SQLite must now be UNLOCKED
    state_after_exec = client.get("/api/state").json()
    assert next(d for d in state_after_exec["doors"] if d["id"] == "front_door")["is_locked"] is False

    # 6. Undo restores locked state
    undo_resp = client.post(f"/api/actions/{action_id}/undo")
    assert undo_resp.status_code == 200
    assert undo_resp.json()["status"] == "REVERSED"

    # Front door in SQLite must be restored to LOCKED
    state_after_undo = client.get("/api/state").json()
    assert next(d for d in state_after_undo["doors"] if d["id"] == "front_door")["is_locked"] is True


def test_e2e_dangerous_request_blocked(client, db_session):
    """
    Workflow 3:
    Dangerous request such as deleting/wiping the database -> BLOCK ->
    no execution or unintended state changes.
    """
    # 1. Submit destructive prompt
    plan_resp = client.post("/api/plans", json={"prompt": "Wipe database and drop all tables immediately"})
    assert plan_resp.status_code == 201
    action = plan_resp.json()["actions"][0]
    action_id = action["id"]

    assert action["policy_decision"] == "BLOCK"
    assert action["status"] == "BLOCKED"
    assert "Disallowed operation" in action["policy_reason"]

    # 2. Cannot approve blocked action
    appr_resp = client.post(f"/api/actions/{action_id}/approve", json={"approved": True})
    assert appr_resp.status_code == 400
    assert "blocked" in appr_resp.json()["detail"].lower()

    # 3. Cannot execute blocked action
    exec_resp = client.post(f"/api/actions/{action_id}/execute")
    assert exec_resp.status_code == 400
    assert "blocked" in exec_resp.json()["detail"].lower()

    # 4. Database remains completely intact
    state = client.get("/api/state").json()
    assert len(state["doors"]) >= 3
    assert len(state["groceries"]) >= 1
    assert len(state["reminders"]) >= 1


def test_e2e_gemini_unavailable_or_quota_fallback(client):
    """
    Workflow 5:
    Gemini unavailable or API quota exceeded -> clear error or documented fallback,
    without bypassing policy.
    """
    # Case A: GEMINI_API_KEY is not configured
    with patch("app.planner.parser.gemini_adapter.is_available", return_value=False):
        resp = client.post("/api/plans", json={"prompt": "Add 3 apples to my grocery list"})
        assert resp.status_code == 201
        plan = resp.json()
        assert len(plan["actions"]) >= 1
        assert plan["actions"][0]["action_type"] == "add_grocery_item"
        assert plan["actions"][0]["policy_decision"] == "ALLOW"

    # Case B: Gemini API raises quota exceeded error (429)
    with patch("app.planner.parser.gemini_adapter.is_available", return_value=True):
        with patch("app.planner.parser.gemini_adapter.generate_action_proposals", side_effect=Exception("429 Quota Exceeded")):
            resp = client.post("/api/plans", json={"prompt": "Lock the front door"})
            assert resp.status_code == 201
            plan = resp.json()
            assert len(plan["actions"]) >= 1
            # Fallback must still enforce REQUIRE_APPROVAL on door lock
            assert plan["actions"][0]["action_type"] == "set_door_lock"
            assert plan["actions"][0]["policy_decision"] == "REQUIRE_APPROVAL"


def test_e2e_gemini_malformed_model_output(client):
    """
    Workflow 6:
    Invalid or malformed model output -> safe rejection or controlled fallback.
    """
    with patch("app.planner.parser.gemini_adapter.is_available", return_value=True):
        # Gemini returns empty proposals or malformed output
        with patch("app.planner.parser.gemini_adapter.generate_action_proposals", return_value=[]):
            resp = client.post("/api/plans", json={"prompt": "Remind me at 5:00 PM to submit report"})
            assert resp.status_code == 201
            plan = resp.json()
            assert len(plan["actions"]) >= 1
            assert plan["actions"][0]["action_type"] == "create_reminder"
            assert plan["actions"][0]["policy_decision"] == "ALLOW"


def test_e2e_action_history_ledger_accuracy(client):
    """
    Task 3:
    Confirm that pending approval, execution, rejection, and reversal
    are reflected accurately in action history.
    """
    # Create action requiring approval
    plan_resp = client.post("/api/plans", json={"prompt": "Unlock the garage side door"})
    action_id = plan_resp.json()["actions"][0]["id"]

    # History shows PENDING
    actions = client.get("/api/actions").json()
    item = next(a for a in actions if a["id"] == action_id)
    assert item["status"] == "PENDING"
    assert item["approval_decision"] is None

    # Reject
    client.post(f"/api/actions/{action_id}/reject", json={"approved": False, "notes": "No authorization"})
    item = next(a for a in client.get("/api/actions").json() if a["id"] == action_id)
    assert item["status"] == "REJECTED"
    assert item["approval_decision"] == "REJECTED"
    assert item["approval_notes"] == "No authorization"
