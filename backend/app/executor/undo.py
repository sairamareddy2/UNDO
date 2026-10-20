from sqlalchemy.orm import Session
from app import models
from app.models import utc_now


class UndoError(Exception):
    pass


class UndoManager:
    """
    Handles rollback of executed actions.
    Enforces strict invariants:
    - Action must be in EXECUTED state.
    - Action must be marked is_reversible == True.
    - Action cannot be re-reversed (idempotency / transition guard).
    - Writes an explicit ACTION_UNDONE audit event.
    """

    @classmethod
    def undo_action(cls, db: Session, action: models.Action) -> models.Action:
        if action.status == "REVERSED":
            raise UndoError(f"Action '{action.id}' has already been reversed at {action.reversed_at}.")

        if action.status != "EXECUTED":
            raise UndoError(f"Cannot undo action in '{action.status}' state. Only EXECUTED actions can be undone.")

        if not action.is_reversible:
            raise UndoError(f"Action '{action.id}' ({action.action_type}) does not support reversal.")

        action_type = action.action_type
        before_state = action.before_state or {}
        after_state = action.after_state or {}

        try:
            if action_type == "add_grocery_item":
                cls._undo_add_grocery(db, after_state)
            elif action_type == "create_reminder":
                cls._undo_create_reminder(db, after_state)
            elif action_type == "set_door_lock":
                cls._undo_set_door_lock(db, before_state)
            else:
                raise UndoError(f"No reversal handler registered for action type '{action_type}'.")

            # Update action state
            action.status = "REVERSED"
            action.reversed_at = utc_now()

            # Record audit event
            audit = models.AuditEvent(
                action_id=action.id,
                event_type="ACTION_UNDONE",
                details={
                    "action_type": action.action_type,
                    "reversal_time": action.reversed_at.isoformat(),
                    "restored_before_state": before_state,
                    "undone_after_state": after_state,
                },
                timestamp=action.reversed_at,
            )
            db.add(audit)

            db.commit()
            db.refresh(action)
            return action

        except Exception as e:
            db.rollback()
            raise UndoError(f"Failed to undo action '{action.id}': {str(e)}")

    @classmethod
    def _undo_add_grocery(cls, db: Session, after_state: dict):
        item_id = after_state.get("item_id")
        if item_id:
            item = db.query(models.GroceryItem).filter(models.GroceryItem.id == item_id).first()
            if item:
                db.delete(item)
                db.flush()

    @classmethod
    def _undo_create_reminder(cls, db: Session, after_state: dict):
        reminder_id = after_state.get("reminder_id")
        if reminder_id:
            rem = db.query(models.Reminder).filter(models.Reminder.id == reminder_id).first()
            if rem:
                db.delete(rem)
                db.flush()

    @classmethod
    def _undo_set_door_lock(cls, db: Session, before_state: dict):
        door_id = before_state.get("door_id")
        was_locked = before_state.get("was_locked")
        if door_id and was_locked is not None:
            door = db.query(models.DoorLock).filter(models.DoorLock.id == door_id).first()
            if door:
                door.is_locked = was_locked
                door.last_changed_at = utc_now()
                db.flush()
