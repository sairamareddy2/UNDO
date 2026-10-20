import pytest
from app import models
from app.executor.executor import ActionExecutor, ActionExecutionError


def test_execute_add_grocery_success(db_session):
    plan = models.ActionPlan(prompt="Add almond milk to groceries", status="PENDING")
    db_session.add(plan)
    db_session.flush()

    action = models.Action(
        plan_id=plan.id,
        action_type="add_grocery_item",
        title="Add 2x Almond Milk",
        parameters={"name": "Almond Milk", "quantity": 2, "category": "Dairy"},
        policy_decision="ALLOW",
        policy_reason="Standard addition within limit",
        status="PENDING",
        is_reversible=True,
    )
    db_session.add(action)
    db_session.commit()

    # Execute action
    executed = ActionExecutor.execute_action(db_session, action)

    assert executed.status == "EXECUTED"
    assert executed.executed_at is not None
    assert executed.after_state is not None
    assert executed.after_state["name"] == "Almond Milk"
    assert executed.after_state["quantity"] == 2

    # Verify item exists in simulated_groceries table
    item = db_session.query(models.GroceryItem).filter(models.GroceryItem.name == "Almond Milk").first()
    assert item is not None
    assert item.quantity == 2
    assert item.is_active is True

    # Verify audit event
    audit = db_session.query(models.AuditEvent).filter(models.AuditEvent.action_id == action.id).first()
    assert audit is not None
    assert audit.event_type == "ACTION_EXECUTED"


def test_execute_create_reminder_success(db_session):
    plan = models.ActionPlan(prompt="Remind me to submit project at 3pm", status="PENDING")
    db_session.add(plan)
    db_session.flush()

    action = models.Action(
        plan_id=plan.id,
        action_type="create_reminder",
        title="Reminder: Submit Project at 3:00 PM",
        parameters={"title": "Submit Project", "remind_at": "3:00 PM", "priority": "high"},
        policy_decision="ALLOW",
        policy_reason="Notification within safe params",
        status="PENDING",
        is_reversible=True,
    )
    db_session.add(action)
    db_session.commit()

    executed = ActionExecutor.execute_action(db_session, action)
    assert executed.status == "EXECUTED"

    rem = db_session.query(models.Reminder).filter(models.Reminder.title == "Submit Project").first()
    assert rem is not None
    assert rem.remind_at == "3:00 PM"


def test_execute_door_lock_success(db_session):
    plan = models.ActionPlan(prompt="Unlock front door", status="PENDING")
    db_session.add(plan)
    db_session.flush()

    action = models.Action(
        plan_id=plan.id,
        action_type="set_door_lock",
        title="Unlock Front Door",
        parameters={"door_id": "front_door", "target_state": "unlocked"},
        policy_decision="REQUIRE_APPROVAL",
        policy_reason="Physical security entry point change",
        status="APPROVED",
        approval_decision="APPROVED",
        is_reversible=True,
    )
    db_session.add(action)
    db_session.commit()

    executed = ActionExecutor.execute_action(db_session, action)
    assert executed.status == "EXECUTED"
    assert executed.before_state["was_locked"] is True
    assert executed.after_state["is_locked"] is False

    door = db_session.query(models.DoorLock).filter(models.DoorLock.id == "front_door").first()
    assert door.is_locked is False


def test_cannot_execute_unapproved_action(db_session):
    plan = models.ActionPlan(prompt="Unlock front door", status="PENDING")
    db_session.add(plan)
    db_session.flush()

    action = models.Action(
        plan_id=plan.id,
        action_type="set_door_lock",
        title="Unlock Front Door",
        parameters={"door_id": "front_door", "target_state": "unlocked"},
        policy_decision="REQUIRE_APPROVAL",
        policy_reason="Physical security entry point change",
        status="PENDING",
        approval_decision=None,
        is_reversible=True,
    )
    db_session.add(action)
    db_session.commit()

    with pytest.raises(ActionExecutionError) as exc_info:
        ActionExecutor.execute_action(db_session, action)
    assert "requires approval" in str(exc_info.value)


def test_cannot_execute_blocked_action(db_session):
    plan = models.ActionPlan(prompt="Wipe database", status="PENDING")
    db_session.add(plan)
    db_session.flush()

    action = models.Action(
        plan_id=plan.id,
        action_type="wipe_database",
        title="Wipe database",
        parameters={},
        policy_decision="BLOCK",
        policy_reason="Prohibited action",
        status="BLOCKED",
        is_reversible=False,
    )
    db_session.add(action)
    db_session.commit()

    with pytest.raises(ActionExecutionError) as exc_info:
        ActionExecutor.execute_action(db_session, action)
    assert "blocked action" in str(exc_info.value)
