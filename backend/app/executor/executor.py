import datetime
from typing import Any, Dict
from sqlalchemy.orm import Session
from app import models
from app.models import utc_now


class ActionExecutionError(Exception):
    pass


class ActionExecutor:
    """
    Executes validated and approved actions against the database.
    Captures exact before-and-after state snapshots for audit and reversibility.
    """

    @classmethod
    def execute_action(cls, db: Session, action: models.Action) -> models.Action:
        if action.status == "EXECUTED":
            raise ActionExecutionError(f"Action '{action.id}' is already executed.")

        if action.policy_decision == "BLOCK":
            action.status = "BLOCKED"
            action.error_message = f"Cannot execute blocked action: {action.policy_reason}"
            db.commit()
            raise ActionExecutionError(action.error_message)

        if action.policy_decision == "REQUIRE_APPROVAL" and action.approval_decision != "APPROVED":
            action.status = "PENDING"
            raise ActionExecutionError(f"Action '{action.id}' requires approval before execution.")

        action_type = action.action_type
        params = action.parameters or {}

        try:
            if action_type == "add_grocery_item":
                cls._execute_add_grocery(db, action, params)
            elif action_type == "create_reminder":
                cls._execute_create_reminder(db, action, params)
            elif action_type == "set_door_lock":
                cls._execute_set_door_lock(db, action, params)
            else:
                raise ActionExecutionError(f"Unsupported action execution type: '{action_type}'")

            action.status = "EXECUTED"
            action.executed_at = utc_now()

            # Record audit event
            audit = models.AuditEvent(
                action_id=action.id,
                event_type="ACTION_EXECUTED",
                details={
                    "action_type": action.action_type,
                    "execution_result": action.execution_result,
                    "before_state": action.before_state,
                    "after_state": action.after_state,
                },
                timestamp=action.executed_at,
            )
            db.add(audit)

            # Check if all actions in plan are executed
            plan = action.plan
            if plan:
                all_actions = plan.actions
                if all(a.status in ("EXECUTED", "REVERSED", "REJECTED", "BLOCKED") for a in all_actions):
                    plan.status = "COMPLETED"
                    plan.updated_at = utc_now()

            db.commit()
            db.refresh(action)
            return action

        except Exception as e:
            db.rollback()
            action.status = "FAILED"
            action.error_message = str(e)
            db.commit()
            raise ActionExecutionError(f"Execution failed: {str(e)}")

    @classmethod
    def _execute_add_grocery(cls, db: Session, action: models.Action, params: Dict[str, Any]):
        name = params.get("name", "Item")
        quantity = int(params.get("quantity", 1))
        category = params.get("category", "General")

        action.before_state = {"action": "add_grocery_item", "item_exists": False}

        item = models.GroceryItem(
            name=name,
            quantity=quantity,
            category=category,
            is_active=True,
            created_at=utc_now(),
        )
        db.add(item)
        db.flush()

        action.after_state = {
            "item_id": item.id,
            "name": item.name,
            "quantity": item.quantity,
            "category": item.category,
            "is_active": True,
        }
        action.execution_result = {
            "status": "SUCCESS",
            "message": f"Successfully added {quantity}x '{name}' ({category}) to grocery list.",
            "item_id": item.id,
        }

    @classmethod
    def _execute_create_reminder(cls, db: Session, action: models.Action, params: Dict[str, Any]):
        title = params.get("title", "Task")
        remind_at = params.get("remind_at", "Later")
        priority = params.get("priority", "medium")

        action.before_state = {"action": "create_reminder", "reminder_exists": False}

        reminder = models.Reminder(
            title=title,
            remind_at=remind_at,
            priority=priority,
            is_active=True,
            created_at=utc_now(),
        )
        db.add(reminder)
        db.flush()

        action.after_state = {
            "reminder_id": reminder.id,
            "title": reminder.title,
            "remind_at": reminder.remind_at,
            "priority": reminder.priority,
            "is_active": True,
        }
        action.execution_result = {
            "status": "SUCCESS",
            "message": f"Scheduled reminder '{title}' for {remind_at} ({priority} priority).",
            "reminder_id": reminder.id,
        }

    @classmethod
    def _execute_set_door_lock(cls, db: Session, action: models.Action, params: Dict[str, Any]):
        door_id = params.get("door_id")
        target_state = params.get("target_state", "locked").lower()
        should_lock = target_state == "locked"

        door = db.query(models.DoorLock).filter(models.DoorLock.id == door_id).first()
        if not door:
            # Create if missing
            door = models.DoorLock(
                id=door_id,
                name=door_id.replace("_", " ").title(),
                is_locked=not should_lock,
                last_changed_at=utc_now(),
            )
            db.add(door)
            db.flush()

        # Capture snapshot of before state
        action.before_state = {
            "door_id": door.id,
            "name": door.name,
            "was_locked": door.is_locked,
            "last_changed_at": door.last_changed_at.isoformat() if door.last_changed_at else None,
        }

        # Apply state change
        door.is_locked = should_lock
        door.last_changed_at = utc_now()

        # Capture after state
        action.after_state = {
            "door_id": door.id,
            "name": door.name,
            "is_locked": door.is_locked,
            "last_changed_at": door.last_changed_at.isoformat(),
        }
        action.execution_result = {
            "status": "SUCCESS",
            "message": f"{door.name} is now {'LOCKED' if door.is_locked else 'UNLOCKED'}.",
            "door_id": door.id,
            "is_locked": door.is_locked,
        }
