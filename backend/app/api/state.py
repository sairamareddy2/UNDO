from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.models import utc_now
from app.schemas import (
    ApplicationStateResponse,
    GroceryItemSchema,
    ReminderSchema,
    DoorLockSchema,
    AuditEventResponse,
)

router = APIRouter()


@router.get("/state", response_model=ApplicationStateResponse)
def get_live_state(db: Session = Depends(get_db)):
    groceries = (
        db.query(models.GroceryItem)
        .filter(models.GroceryItem.is_active == True)  # noqa: E712
        .order_by(models.GroceryItem.created_at.desc())
        .all()
    )
    reminders = (
        db.query(models.Reminder)
        .filter(models.Reminder.is_active == True)  # noqa: E712
        .order_by(models.Reminder.created_at.desc())
        .all()
    )
    doors = db.query(models.DoorLock).all()

    return ApplicationStateResponse(
        groceries=groceries,
        reminders=reminders,
        doors=doors,
    )


@router.get("/state/audit-events", response_model=List[AuditEventResponse])
def get_audit_trail(db: Session = Depends(get_db)):
    events = (
        db.query(models.AuditEvent)
        .order_by(models.AuditEvent.timestamp.desc())
        .limit(100)
        .all()
    )
    return events


@router.post("/state/reset")
def reset_application_state(db: Session = Depends(get_db)):
    """Resets simulated smart home and grocery state to baseline seed data."""
    db.query(models.GroceryItem).delete()
    db.query(models.Reminder).delete()
    db.query(models.DoorLock).delete()

    db.add_all([
        models.DoorLock(id="front_door", name="Front Door Lock", is_locked=True, last_changed_at=utc_now()),
        models.DoorLock(id="back_door", name="Patio Back Door", is_locked=True, last_changed_at=utc_now()),
        models.DoorLock(id="garage_entry", name="Garage Side Door", is_locked=True, last_changed_at=utc_now()),
        models.GroceryItem(name="Organic Whole Milk", quantity=1, category="Dairy", is_active=True, created_at=utc_now()),
        models.GroceryItem(name="Sourdough Bread", quantity=2, category="Bakery", is_active=True, created_at=utc_now()),
        models.Reminder(title="Team Standup Sync", remind_at="10:00 AM", priority="medium", is_active=True, created_at=utc_now()),
    ])
    db.commit()
    return {"status": "SUCCESS", "message": "State reset to default baseline."}
