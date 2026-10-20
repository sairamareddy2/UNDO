import pytest
from app import models
from app.executor.executor import ActionExecutor
from app.executor.undo import UndoManager, UndoError


def test_undo_add_grocery(db_session):
    plan = models.ActionPlan(prompt="Add Greek Yogurt", status="PENDING")
    db_session.add(plan)
    db_session.flush()

    action = models.Action(
        plan_id=plan.id,
        action_type="add_grocery_item",
        title="Add 1x Greek Yogurt",
        parameters={"name": "Greek Yogurt", "quantity": 1, "category": "Dairy"},
        policy_decision="ALLOW",
        policy_reason="Allowed list addition",
        status="PENDING",
        is_reversible=True,
    )
    db_session.add(action)
    db_session.commit()

    # First execute
    ActionExecutor.execute_action(db_session, action)
    assert action.status == "EXECUTED"
    item_id = action.after_state["item_id"]

    # Verify item exists
    assert db_session.query(models.GroceryItem).filter(models.GroceryItem.id == item_id).first() is not None

    # Now Undo!
    reversed_action = UndoManager.undo_action(db_session, action)

    assert reversed_action.status == "REVERSED"
    assert reversed_action.reversed_at is not None

    # Verify item is removed from database
    assert db_session.query(models.GroceryItem).filter(models.GroceryItem.id == item_id).first() is None

    # Verify audit event for reversal
    undo_audit = (
        db_session.query(models.AuditEvent)
        .filter(models.AuditEvent.action_id == action.id, models.AuditEvent.event_type == "ACTION_UNDONE")
        .first()
    )
    assert undo_audit is not None


def test_undo_door_lock_restores_previous_state(db_session):
    door = db_session.query(models.DoorLock).filter(models.DoorLock.id == "front_door").first()
    assert door.is_locked is True

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

    # Execute (door unlocks)
    ActionExecutor.execute_action(db_session, action)
    db_session.refresh(door)
    assert door.is_locked is False

    # Undo (door locks back to original true)
    reversed_action = UndoManager.undo_action(db_session, action)
    assert reversed_action.status == "REVERSED"

    db_session.refresh(door)
    assert door.is_locked is True


def test_cannot_undo_twice(db_session):
    plan = models.ActionPlan(prompt="Add Apples", status="PENDING")
    db_session.add(plan)
    db_session.flush()

    action = models.Action(
        plan_id=plan.id,
        action_type="add_grocery_item",
        title="Add 5x Apples",
        parameters={"name": "Honeycrisp Apples", "quantity": 5, "category": "Produce"},
        policy_decision="ALLOW",
        policy_reason="Allowed list addition",
        status="PENDING",
        is_reversible=True,
    )
    db_session.add(action)
    db_session.commit()

    ActionExecutor.execute_action(db_session, action)
    UndoManager.undo_action(db_session, action)

    # Second undo must fail
    with pytest.raises(UndoError) as exc_info:
        UndoManager.undo_action(db_session, action)
    assert "already been reversed" in str(exc_info.value)


def test_cannot_undo_unexecuted_action(db_session):
    plan = models.ActionPlan(prompt="Add Oranges", status="PENDING")
    db_session.add(plan)
    db_session.flush()

    action = models.Action(
        plan_id=plan.id,
        action_type="add_grocery_item",
        title="Add 3x Oranges",
        parameters={"name": "Navel Oranges", "quantity": 3},
        policy_decision="ALLOW",
        policy_reason="Allowed list addition",
        status="PENDING",
        is_reversible=True,
    )
    db_session.add(action)
    db_session.commit()

    with pytest.raises(UndoError) as exc_info:
        UndoManager.undo_action(db_session, action)
    assert "Cannot undo action in 'PENDING' state" in str(exc_info.value)


def test_cannot_undo_non_reversible_action(db_session):
    plan = models.ActionPlan(prompt="Blocked action", status="PENDING")
    db_session.add(plan)
    db_session.flush()

    action = models.Action(
        plan_id=plan.id,
        action_type="wipe_database",
        title="Wipe DB",
        parameters={},
        policy_decision="BLOCK",
        policy_reason="Prohibited",
        status="EXECUTED",  # hypothetical corrupt status
        is_reversible=False,
    )
    db_session.add(action)
    db_session.commit()

    with pytest.raises(UndoError) as exc_info:
        UndoManager.undo_action(db_session, action)
    assert "does not support reversal" in str(exc_info.value)
