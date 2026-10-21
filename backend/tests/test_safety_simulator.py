import pytest
from unittest.mock import patch
from app import models
from app.models import utc_now
from app.services.safety_simulator import SafetySimulator
from app.policy.engine import PolicyDecision
from app.schemas import SafetyReportResponse, ReversibilityReport


def test_valid_grocery_simulation_preserves_real_db(db_session):
    """1. Valid grocery addition is simulated without modifying the real database."""
    initial_grocery_count = db_session.query(models.GroceryItem).count()

    report = SafetySimulator.simulate_action(
        real_db=db_session,
        action_type="add_grocery_item",
        parameters={"name": "Organic Almond Milk", "quantity": 2, "category": "Dairy"},
        title="Add 2 cartons of Organic Almond Milk",
    )

    assert isinstance(report, SafetyReportResponse)
    assert report.overall_status == "SAFE IN SIMULATION"
    assert report.risk_level == "LOW"
    assert report.policy_decision == PolicyDecision.ALLOW
    assert report.reversibility.result == "VERIFIED_REVERSIBLE"
    assert report.reversibility.state_restored is True
    assert len(report.proposed_changes) == 1
    assert report.proposed_changes[0].affected_records == 1

    # Verify real DB was not altered
    final_grocery_count = db_session.query(models.GroceryItem).count()
    assert final_grocery_count == initial_grocery_count
    assert db_session.query(models.GroceryItem).filter(models.GroceryItem.name == "Organic Almond Milk").count() == 0


def test_valid_reminder_simulation_isolated(db_session):
    """2. Valid reminder operation is simulated in isolation."""
    initial_reminder_count = db_session.query(models.Reminder).count()

    report = SafetySimulator.simulate_action(
        real_db=db_session,
        action_type="create_reminder",
        parameters={"title": "Pick up dry cleaning", "remind_at": "4:00 PM", "priority": "medium"},
    )

    assert report.overall_status == "SAFE IN SIMULATION"
    assert report.policy_decision == PolicyDecision.ALLOW
    assert report.reversibility.result == "VERIFIED_REVERSIBLE"

    # Verify real DB remains unchanged
    assert db_session.query(models.Reminder).count() == initial_reminder_count
    assert db_session.query(models.Reminder).filter(models.Reminder.title == "Pick up dry cleaning").count() == 0


def test_simulated_door_action_preserves_approval_requirement(db_session):
    """3. Door action requires human approval and does not bypass policy in simulation."""
    front_door = db_session.query(models.DoorLock).filter(models.DoorLock.id == "front_door").first()
    assert front_door.is_locked is True

    report = SafetySimulator.simulate_action(
        real_db=db_session,
        action_type="set_door_lock",
        parameters={"door_id": "front_door", "target_state": "unlocked"},
    )

    assert report.policy_decision == PolicyDecision.REQUIRE_APPROVAL
    assert report.requires_approval is True
    assert report.risk_level == "HIGH"
    assert "Physical security" in report.policy_reason

    # Real door must remain locked
    db_session.refresh(front_door)
    assert front_door.is_locked is True


def test_blocked_destructive_request_remains_blocked(db_session):
    """4. Blocked destructive request remains blocked with CRITICAL risk and 0 affected records."""
    report = SafetySimulator.simulate_action(
        real_db=db_session,
        action_type="wipe_database",
        parameters={},
    )

    assert report.policy_decision == PolicyDecision.BLOCK
    assert report.overall_status == "BLOCKED BY POLICY"
    assert report.risk_level == "CRITICAL"
    assert report.reversibility.result == "NOT_REVERSIBLE"
    assert report.proposed_changes[0].affected_records == 0
    assert report.proposed_changes[0].change_type == "BLOCKED"


def test_invalid_parameters_produce_clear_validation_result(db_session):
    """5. Invalid parameters produce a clear validation failure."""
    report = SafetySimulator.simulate_action(
        real_db=db_session,
        action_type="add_grocery_item",
        parameters={"name": "", "quantity": -5},
    )

    assert report.policy_decision == PolicyDecision.BLOCK
    validation_scenario = next(s for s in report.failure_scenarios if s.category == "Input Validation")
    assert validation_scenario.status == "FAILED"
    assert "Invalid" in validation_scenario.observed


def test_simulated_db_failures_do_not_damage_real_db(db_session):
    """6. Persistence failure injection in simulation does not damage the real DB."""
    groceries_before = db_session.query(models.GroceryItem).count()
    reminders_before = db_session.query(models.Reminder).count()
    doors_before = [(d.id, d.is_locked) for d in db_session.query(models.DoorLock).all()]

    report = SafetySimulator.simulate_action(
        real_db=db_session,
        action_type="add_grocery_item",
        parameters={"name": "Oat Milk", "quantity": 1},
    )

    # Persistence isolation scenario passed
    persistence_scenario = next(s for s in report.failure_scenarios if s.category == "Persistence & Constraints")
    assert persistence_scenario.status == "PASSED"

    # Real DB untouched
    assert db_session.query(models.GroceryItem).count() == groceries_before
    assert db_session.query(models.Reminder).count() == reminders_before
    assert [(d.id, d.is_locked) for d in db_session.query(models.DoorLock).all()] == doors_before


def test_supported_action_marked_reversible_only_after_state_comparison(db_session):
    """7. Supported action marked reversible only after verified state comparison."""
    report = SafetySimulator.simulate_action(
        real_db=db_session,
        action_type="add_grocery_item",
        parameters={"name": "Apples", "quantity": 6},
    )

    assert report.reversibility.result == "VERIFIED_REVERSIBLE"
    assert report.reversibility.rollback_tested is True
    assert report.reversibility.state_restored is True
    assert "Deterministic deletion" in report.reversibility.recovery_method


def test_failed_rollback_produces_honest_failure_status(db_session):
    """8. A failed rollback produces an honest failure status."""
    with patch("app.executor.undo.UndoManager.undo_action", side_effect=Exception("Simulated undo failure")):
        report = SafetySimulator.simulate_action(
            real_db=db_session,
            action_type="add_grocery_item",
            parameters={"name": "Cheddar Cheese", "quantity": 1},
        )

        assert report.reversibility.result == "ROLLBACK_FAILED"
        assert report.overall_status == "ROLLBACK UNVERIFIED"
        rollback_scenario = next(s for s in report.failure_scenarios if s.name == "Rollback & State Recovery Invariant")
        assert rollback_scenario.status == "FAILED"


def test_approval_expiration_honestly_reported_as_unsupported(db_session):
    """9 & 10. Unsupported expiry behavior is honestly reported as UNSUPPORTED, never falsely verified."""
    report = SafetySimulator.simulate_action(
        real_db=db_session,
        action_type="set_door_lock",
        parameters={"door_id": "front_door", "target_state": "unlocked"},
    )

    expiry_scenario = next(s for s in report.failure_scenarios if s.name == "Approval Expiration Check")
    assert expiry_scenario.status == "UNSUPPORTED"
    assert "does not support expiration timestamps" in expiry_scenario.observed


def test_continuing_to_execution_reruns_policy_and_authorization(client, db_session):
    """11. Simulation does not authorize execution; execution strictly checks policy and approval."""
    # Create a plan with a door unlock action
    plan_res = client.post("/api/plans", json={"prompt": "Unlock the front door"})
    assert plan_res.status_code == 201
    plan_data = plan_res.json()
    action = plan_data["actions"][0]
    action_id = action["id"]
    assert action["policy_decision"] == "REQUIRE_APPROVAL"

    # Simulate safety for this action
    sim_res = client.post("/api/safety/simulate", json={"action_id": action_id})
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["requires_approval"] is True

    # Attempt execution directly without human approval -> must be rejected by execution endpoint
    exec_res = client.post(f"/api/actions/{action_id}/execute")
    assert exec_res.status_code == 400
    assert "requires human approval" in exec_res.json()["detail"].lower()

    # Now approve the action explicitly
    appr_res = client.post(f"/api/actions/{action_id}/approve", json={"approved": True, "notes": "Approved by user"})
    assert appr_res.status_code == 200

    # Now execution succeeds
    exec_res_2 = client.post(f"/api/actions/{action_id}/execute")
    assert exec_res_2.status_code == 200
    assert exec_res_2.json()["status"] == "EXECUTED"


def test_blocked_action_cannot_be_executed_after_simulation(client, db_session):
    """12 & 13. Blocked action cannot be executed even if simulated."""
    plan_res = client.post("/api/plans", json={"prompt": "Please wipe the database immediately"})
    assert plan_res.status_code == 201
    action = plan_res.json()["actions"][0]
    action_id = action["id"]
    assert action["policy_decision"] == "BLOCK"

    # Simulate safety
    sim_res = client.post("/api/safety/simulate", json={"action_id": action_id})
    assert sim_res.status_code == 200
    assert sim_res.json()["overall_status"] == "BLOCKED BY POLICY"

    # Execution endpoint must reject blocked action
    exec_res = client.post(f"/api/actions/{action_id}/execute")
    assert exec_res.status_code == 400
    assert "blocked by security policy" in exec_res.json()["detail"].lower()


def test_safety_simulate_api_schema(client, db_session):
    """14. The safety simulation endpoint returns the documented response schema."""
    response = client.post(
        "/api/safety/simulate",
        json={
            "action_type": "add_grocery_item",
            "parameters": {"name": "Bananas", "quantity": 5, "category": "Produce"},
            "title": "Add 5 Bananas",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "simulation_id" in data
    assert data["action_type"] == "add_grocery_item"
    assert data["overall_status"] == "SAFE IN SIMULATION"
    assert data["risk_level"] == "LOW"
    assert data["policy_decision"] == "ALLOW"
    assert "initial_state_summary" in data
    assert "proposed_changes" in data
    assert "failure_scenarios" in data
    assert "reversibility" in data
    assert "warnings" in data
    assert "limitations" in data


def test_state_conflict_warning_for_redundant_door_lock(db_session):
    """15. Redundant door lock transition triggers WARNING status and conflict warning."""
    # Baseline front door is already locked
    report = SafetySimulator.simulate_action(
        real_db=db_session,
        action_type="set_door_lock",
        parameters={"door_id": "front_door", "target_state": "locked"},
    )

    assert report.overall_status == "WARNINGS FOUND"
    assert any("already LOCKED" in w for w in report.warnings)
    conflict_scenario = next(s for s in report.failure_scenarios if s.category == "State Conflict")
    assert conflict_scenario.status == "WARNING"


def test_bulk_purchase_triggers_medium_risk_and_approval(db_session):
    """16. Bulk purchase (> 100) triggers REQUIRE_APPROVAL and MEDIUM risk."""
    report = SafetySimulator.simulate_action(
        real_db=db_session,
        action_type="add_grocery_item",
        parameters={"name": "Bottled Water", "quantity": 150},
    )

    assert report.policy_decision == PolicyDecision.REQUIRE_APPROVAL
    assert report.requires_approval is True
    assert report.risk_level == "MEDIUM"
